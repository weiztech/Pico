import unicodedata
from django.template import loader
from django.contrib.auth import get_user_model
from django.core.mail import EmailMultiAlternatives

User = get_user_model()


def _unicode_ci_compare(s1, s2):
    """
    Perform case-insensitive comparison of two identifiers, using the
    recommended algorithm from Unicode Technical Report 36, section
    2.11.2(B)(2).
    """
    return (
        unicodedata.normalize("NFKC", s1).casefold()
        == unicodedata.normalize("NFKC", s2).casefold()
    )


def get_users(email):
    """Given an email, return matching user(s) who should receive an email."""
    email_field_name = User.get_email_field_name()
    active_users = User._default_manager.filter(
        **{
            "%s__iexact" % email_field_name: email,
            "is_active": True,
        }
    )
    return (
        u
        for u in active_users
        if u.has_usable_password()
        and _unicode_ci_compare(email, getattr(u, email_field_name))
    )


def send_mail(
    subject_template_name,
    email_template_name,
    context,
    from_email,
    to_email,
):
    """
    Send a django.core.mail.EmailMultiAlternatives to `to_email`.
    """
    subject = loader.render_to_string(subject_template_name, context)
    # Email subject *must not* contain newlines
    subject = "".join(subject.splitlines())
    body = loader.render_to_string(email_template_name, context)

    email_message = EmailMultiAlternatives(
        subject,
        body,
        from_email,
        [
            to_email,
        ],
    )

    email_message.send()
