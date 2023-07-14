from django.shortcuts import render


def page_not_found(request, exception):
    return render(request, 'pages/404.html', status=404)


def csrf_failure(request, reason=''):
    return render(request, 'pages/403csrf.html', status=403)


def tr_handler500(request):
    return render(request=request, template_name='pages/500.html', status=500)