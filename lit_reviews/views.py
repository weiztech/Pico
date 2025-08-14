from django.shortcuts import render
from django.http import HttpResponseServerError
from django.template.context import RequestContext
from django.template.loader import get_template


def error_404(request,exception):
        referring_page = request.META.get('HTTP_REFERER', '/literature_reviews')
        context = {"exception":exception, "referring_page": referring_page}
        # return render(request,'404.html', context=context)
        t = get_template('404.html')
        response = HttpResponseServerError(t.render(context))
        response.status_code = 404
        return response


def error_403(request, exception):
        referring_page = request.META.get('HTTP_REFERER', '/literature_reviews')
        context = {"referring_page": referring_page}
        # return render(request,'403.html', context=context)
        t = get_template('403.html')
        response = HttpResponseServerError(t.render(context))
        response.status_code = 403
        return response


def error_500(request):
        referring_page = request.META.get('HTTP_REFERER', '/literature_reviews')
        context = {"referring_page": referring_page}
        t = get_template('500.html')
        response = HttpResponseServerError(t.render(context))
        response.status_code = 500
        return response
