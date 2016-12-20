from django.shortcuts import get_object_or_404, render

# ...
def page(request):
    return render(request, 'page.html', {})