import random
import re

from django.conf import settings
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.template import loader, Context, Template
from django.template.loader import get_template
from django.contrib import messages
from django.http import HttpResponse
from products.models import Product, Category
from orgs.models import UserProfile
from decorators import current_org_required
from helpers.views import get_query
from products.forms import ProductsPDFForm


@login_required
@current_org_required
def index(request):
    """
    Shows the list of Products:
    each Category followed by a table of all the Products in that category.
    """
    user = request.user
    org = request.session['current_org']
    try:
        profile = UserProfile.objects.get(user=user, org=org)
    except MultipleObjectsReturned as mor_ex:
        profile = UserProfile.objects.filter(user=user, org=org)[0]
    except ObjectDoesNotExist as odne_ex:
        profile = None
    unrestricted_qtys = user.has_perm('orders.change_order') or profile.unrestricted_qtys
    user_is_manager = user.has_perm('orders.change_order')
    categories = Category.objects.filter(org=org).order_by('sort', 'name')
    products = Product.objects.filter(categories__in=categories, status__exact='av').distinct().order_by('sort', 'name') 
    return render(request, 'products/product_list.html', {
        'profile': profile,
        'products': products,
        'categories': categories,
        'ignore_pa': profile.ignore_pa if profile is not None else None,
        'unrestricted_qtys': unrestricted_qtys,
        'user_is_manager': user_is_manager,
    })


def search(request):
    query_string, found_products = '', ''
    user = request.user
    org = request.session['current_org']
    profile = UserProfile.objects.get(user=user, org=org)
    unrestricted_qtys = user.has_perm('orders.change_order') or profile.unrestricted_qtys
    if ('q' in request.GET) and request.GET['q'].strip():
        query_string = request.GET['q']
        product_query = get_query(query_string, ['name', 'part_number'])
        found_products = Product.objects.filter(product_query).filter(categories__org=request.session['current_org']).order_by('-name')

    return render(request, 'products/product_list.html', {
        'profile': profile,
        'ignore_pa': profile.ignore_pa,
        'unrestricted_qtys': unrestricted_qtys,
        'search': True,
        'query_string': query_string,
        'products': found_products,
        'categories': [1, ]  # hack to reuse product list template,
                             # which loops through categories
    })


@login_required
def create_pdf(request):
    """
    CREATE PDF
    """
    if request.method == 'POST':
        # print('request', request.__dict__)
        # print('request.FILES', dir(request.FILES))
        form = ProductsPDFForm(request.POST, request.FILES)
        preview = {}
        if form.is_valid():  # set session vars
            for file_key, file_val in request.FILES.iteritems():
                print('file_k', file_key)
                print('file_v', file_val)
                path = handle_uploaded_file(file_val)
                preview[file_key] = path
                print('path', path)
            preview['firstTextBox'] = request.POST.get('title', None)
            preview['secondTextBox'] = request.POST.get('secondTextBox', None)
            # preview['report_name'] = request.POST.get('report_name', None)

            createPreviewFromFiles(request, preview)
            # return render(request, 'orders/create_pdf.html', {
            #     'preview': preview
            # })
        else:
            print('form.errors', form.errors)
            warning_msg = "e|There was a problem with your submission. Fields:{} required" \
                          .format(', '.join(list(key for key, value in form.errors.iteritems())))
            messages.warning(request, warning_msg)

    return render(request, 'products/create_pdf.html', {})

def createPreviewFromFiles(request, files):
    from weasyprint import HTML

    html_template = get_template('pdf/temp_1.html')
    context = Context(files)
    print('files',files)
    rendered_template = html_template.render(context)
    print('rendered_template',rendered_template)
    pdf_file = HTML(string=rendered_template, base_url=request.build_absolute_uri()).write_pdf('report.pdf')
    print('pdf',pdf_file)
    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = 'filename="temp_1.pdf"'
    messages.success(request, "s|The PDF successully created")
    return response


def handle_uploaded_file(f):
    """
    Writes an uploaded file to the filesystem.
    This is currently putting uploads in the *public* media directory
    so they're easily accessible to Mimic staff.
    We randomize the filename, default permissions are 644,
    and there is no PHP or equiv on this server,
    but be aware other security issues. Note that lighttpd has an x-sendfile module,
    so that you could store the file somewhere non-public and deliver it to Mimic staff that way.
    """
    filename = sanitize_filename(f.name)
    path = '/uploads/%s' % filename
    destination = open('{0}{1}'.format(settings.STATICFILES_DIRS[0].encode('utf8'), path), 'wb+')
    for chunk in f.chunks():
        destination.write(chunk)
    url = '%s%s' % (settings.STATIC_URL, path)
    return url


def sanitize_filename(name):
    """
    Given a filename string:
        * Adds a 4-letter random string at the beginning. 
          This in theory makes the file harder to find for a malicious user,
          but also allows legit users to upload a file more than once
          (eg perhaps revisions) without overwriting it each time.
        * Replaces any non-alphanumeric character with an underscore.
          (Note that there is the regexp shortcut '\W'
          for non-alphanumeric characters, but that also includes periods
          which we want to keep for filenames.) This makes for clean,
          clickable URLs for some email clients (which would
          eg choke on a filename with spaces).
    """
    rstr = ''
    chars = random.sample(['B','C','D','F','G','H','J','K','L','M','N','P','Q','R','S','T','V','W','X','Z'], 4) 
    for c in chars: rstr += c
    r = re.compile('[^a-zA-Z0-9_.]')
    filename = r.sub('_', name)
    return '%s-%s' % (rstr, filename)