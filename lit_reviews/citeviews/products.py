import os
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.shortcuts import render, get_object_or_404

from client_portal.models import Client, Project
from lit_reviews.models import LiteratureReview, Manufacturer, Device
from accounts.models import User
from lit_reviews.forms import (
    DeviceForm,
    CreateClientForm,
    ProjectForm,
    ProjectPublicForm,
)
from lit_reviews.helpers.project import clone_project
from backend.logger import logger
from lit_reviews.custom_permissions import protected_project


@protected_project
def product_details(request, id):
    # Device Form
    review = LiteratureReview.objects.get(id=id)
    device = review.device
    form = DeviceForm(request.POST or None, instance=device)
    client_logo = review.client.logo
    client_logo_size = None
    
    try:
        if client_logo:
            client_logo_size = review.client.logo.size
            client_logo_size = str("{:.2f}".format(client_logo_size / 1024)) + " KB." if client_logo_size < (1024*1024) else str("{:.2f}".format(client_logo_size / (1024*1024))) + " MB."  
    except:
        logger.error("Couldn't load client logo size")    

    # Client Form
    client = review.client
    client_form = CreateClientForm(request.POST or None,request.FILES or None, instance=client,prefix="client_form")
    
    # Project Form
    CELERY_DEFAULT_QUEUE = os.getenv("CELERY_DEFAULT_QUEUE", "")
    review = get_object_or_404(LiteratureReview, pk=id)
    project = Project.objects.filter(lit_review=review).first()
    if not project:
        Project.objects.create(lit_review=review, client=client)

    project_form = ProjectForm(request.POST or None, instance=project) if CELERY_DEFAULT_QUEUE == "MAIN_PROD" else ProjectPublicForm(request.POST or None, instance=project)
    
    if request.method == "POST":        
        if form.is_valid() and client_form.is_valid() and project_form.is_valid():
            form.save()
            client_form.save()
            project_form.save()
            return HttpResponseRedirect(
                reverse("lit_reviews:product_details", args=[str(id)])
            )
        else:   
            if form.errors:
                error = form.errors
            elif client_form.errors:
                error = client_form.errors
            elif project_form.errors:
                error = project_form.errors
        
            return render(
                request,
                "lit_reviews/product_details.html",
                {
                    "form": form,
                    "helper": form.helper,
                    "template_error": error,
                    "client_form":client_form,
                    "client_helper": client_form.helper,
                    "project_form": project_form,
                    "hide_body_conent": True,
                    "client_logo": client_logo,
                    "client_logo_size": client_logo_size,
                },
            )
    else:
        return render(
            request,
            "lit_reviews/product_details.html",
            {
                "form": form,
                "helper": form.helper,
                "client_form":client_form,
                "client_helper": client_form.helper,
                "project_form": project_form,
                "hide_body_conent": True,
                "client_logo": client_logo,
                "client_logo_size": client_logo_size,
            },
        )


def create_literaturereview(request):
    template_file_name = (
        "lit_reviews/create_literaturereview_form.html",
    )

    if request.method == "POST":
        # get form data
        if request.user.client:
            client = request.user.client
        else:
            client = request.POST.get('client')
        device = request.POST.get('device')
        is_archived = request.POST.get('is_archived')
        if is_archived == "true":
            is_archived = True
        else:
            is_archived = False
        # authorized_users = request.POST.getlist('authorized_users')

        # review type 
        review_type = request.POST.get("review_type")

        # create client fields
        client_name = request.POST.get('client_name')
        short_name = request.POST.get('short_name')
        long_name = request.POST.get('long_name')
        address = request.POST.get('address')
        logo = request.FILES.get('logo')

        # create device fields
        device_name = request.POST.get('device_name')
        manufacturer_id = request.POST.get('manufacturer_id')
        manufacturer_name = request.POST.get('manufacturer_name')
        classification = request.POST.get('classification')
        markets = request.POST.get('markets')

        # cration inputs
        client_creation = request.POST.get('client-creation')
        device_creation = request.POST.get('device-creation')
        manufacture_creation = request.POST.get('manufacturer-creation')

        # project fields
        project_name = request.POST.get('project_name')
        project_type = request.POST.get('project_type')

        # copied project data
        is_copy = request.POST.get("is_copy", False)
        copied_lit_review_id = request.POST.get("copied_project", "")

        # client creation
        if client_creation == 'true':
            new_client = Client.objects.create(
                name=client_name,
                short_name=short_name,
                long_name=long_name,
                full_address_string=address,
                logo=logo
            )
            new_client.save()
        else:
            if request.user.client:
                new_client = request.user.client
            else:
                new_client = Client.objects.filter(id=client).first()

        if review_type == "SIMPLE":
            new_device = None

        else:
            if device_creation == 'true':
                if manufacture_creation == 'true':
                    manufacturer= Manufacturer.objects.create(name=manufacturer_name)
                else:
                    manufacturer= Manufacturer.objects.filter(id=manufacturer_id).first()
                new_device = Device.objects.create(
                    name = device_name,
                    manufacturer = manufacturer,
                    classification = classification,
                    markets = markets
                )
                new_device.save()
            else:
                new_device = Device.objects.filter(id=device).first()

        literature_review = LiteratureReview.objects.create(
            client = new_client,
            device = new_device,
            is_archived = is_archived,
            review_type = review_type,
        )
        literature_review.save()

        authorized_users = User.objects.all()
        for user in authorized_users:
            literature_review.authorized_users.add(user)
            
        literature_review.save()
        # create new project
        project = Project.objects.create(
            project_name = project_name,
            type = project_type,
            client = new_client,
            lit_review = literature_review
        )
        project.save()

        if is_copy:
            copied_project_lit_review = LiteratureReview.objects.get(id=copied_lit_review_id) 
            clone_project(copied_project_lit_review, literature_review)


        print("creation successful", literature_review)
        return HttpResponseRedirect(
            reverse("lit_reviews:literature_review_detail", args=[str(literature_review.id)])
        )
    else:
        # send data
        if request.user.client:
            client_list = None
            lit_reviews = LiteratureReview.objects.filter(client=request.user.client).order_by("-project__project_name").distinct()
            device_list = Device.objects.filter(literaturereview__in=lit_reviews).distinct()
            manufacturer_list = Manufacturer.objects.filter(device__in=device_list).distinct()

        else:
            client_list = Client.objects.all()
            device_list = Device.objects.all()
            manufacturer_list = Manufacturer.objects.all()
            lit_reviews = LiteratureReview.objects.all().order_by("-project__project_name")          

        return render(
            request,
            template_file_name,
            {
                "client_list": client_list,
                "device_list": device_list,
                "manufacturer_list":manufacturer_list,
                "lit_reviews": lit_reviews,
            },
        )