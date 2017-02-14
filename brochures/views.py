import random
import re

from django.conf import settings
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.core import serializers
from django.template import Context
from django.template.loader import get_template
from django.contrib import messages
from django.http import HttpResponse, HttpResponseRedirect
from forms import BrochuresPDFForm
from addresses.forms import AddressForm
from addresses.models import Address
from orders.models import Cart
from models import Brochure, BrochureTemplate
from itertools import repeat
from forms import PersonalInfoForm, PropertyInfoForm


def collect_menu_data():
    import json
    brochures = Brochure.objects.all()
    elems = {}
    elems['feature_prop'] = {'title': 'Feature Properties'}
    elems['num_of_images'] = {'title': 'Number of photos'}
    try:
        temps = serializers.serialize('json', brochures)
        for temp in brochures:
            if temp.feature_prop.encode('utf-8') in elems['feature_prop']:
                elems['feature_prop'][temp.feature_prop.encode('utf-8')] += 1
            else:
                elems['feature_prop'][temp.feature_prop.encode('utf-8')] = 1

            if "photos {}".format(temp.num_of_images) in elems['num_of_images']:
                elems['num_of_images']['{} {}'.format('photos', temp.num_of_images)] += 1
            else:
                elems['num_of_images']['{} {}'.format('photos', temp.num_of_images)] = 1
    finally:
        return elems


@login_required
def create_menu_elems(request):
    """
    Gets: templates from DB and count all fields
    Returns: dict with counted fields
    """
    try:
        return HttpResponse(json.dumps(collect_menu_data()))
    except Exception as ex:
        return HttpResponse(ex, status_code=500)


@login_required
def index(request):
    """
    Shows the list of Brochures:
    """
    brochures = Brochure.objects.all()
    elems = collect_menu_data()
    return render(request, 'brochures/brochures_list.html', {
        'brochures': brochures,
        'menu_data': elems
        })


@login_required
def create_pdf(request, template_name, template_id):
    """
    CREATE PDF
    * GET  query: get brochure object and drow it's template
      formated_template_name is path to brochure template what will be included on page
    * POST query: get query params and put them to pdf fields
    """
    messages.warning(request, '')
    if request.method == 'POST':
        # print('request', request.__dict__)
        form = BrochuresPDFForm(request.POST, request.FILES)
        preview = {}
        if form.is_valid():
            for file_key, file_val in request.FILES.iteritems():
                path = handle_uploaded_file(file_val)
                preview[file_key] = path
            for key, _ in request._post.iteritems():
                if key.startswith('text'):
                    preview[key] = request.POST.get(key, None)
            if request.POST.get('report_name', None) or request.POST.get('report_name', None) == 'Report':
                preview['report_name'] = request.POST.get('report_name', None)
            else:
                from datetime import datetime
                formated_date = datetime.now().strftime("%m_%d_%y__%H_%M")
                preview['report_name'] = 'Report_{}'.format(formated_date)
            return create_preview_from_files(request, preview, template_name)
        else:
            print('form.errors', form.errors)
            warning_msg = "e|There was a problem with your submission. Fields:{} required" \
                          .format(', '.join(list(key for key, value in form.errors.iteritems())))
            messages.warning(request, warning_msg)

    brochure = get_object_or_404(Brochure, id=template_id)
    formated_template_name = 'pdf/{}.html'.format(template_name)

    return render(request,
                  'brochures/create_pdf.html', {
                      'formated_template_name': formated_template_name,
                      'brochure': brochure
                  })


def create_preview_from_files(request, files, template):
    """
    Create pdf from form data
    """
    from weasyprint import HTML
    template_file = template.getName().split('/')[-1]

    template_id = template.id
    html_template = get_template('pdf/{}'.format(template_file))
    context = Context({'context': files})
    rendered_template = html_template.render(context)

    if settings.STATIC_ROOT:
        target = '{0}/pdf/{1}.pdf'.format(settings.STATIC_ROOT, files['report_name'])
    else:
        target = '{0}/static/pdf/{1}.pdf'.format(settings.BASE_DIR, files['report_name'])

    pdf_file = HTML(string=rendered_template, base_url=request.build_absolute_uri()).write_pdf(target)
    url_to_pdf = '{0}{1}.pdf'.format('/static/pdf/', files['report_name'])
    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = 'filename="temp_1.pdf"'

    request.session['url_to_pdf'] = url_to_pdf
    return HttpResponseRedirect(reverse('brochures:preview'))


@login_required
def get_brochure_modal_data(request):
    import json
    template_id = request.GET.get('id')
    template = Brochure.objects.get(pk=template_id)
    description = template.description if template else ''
    return HttpResponse(json.dumps({'description': description}))


def render_view(request, template_id):
    """
    Render single template.
    Uses to render template within create_pdf page
    """
    template = get_object_or_404(BrochureTemplate, id=template_id)
    template_file = template.getName().split('/')[-1]
    return render(request, 'pdf/{}'.format(template_file), {})


def personal_info(request):
    """
    Personal Info
    """
    if request.is_ajax() and request.method == "GET":
        request.session['brochure_info'] = dict(template_id=int(request.GET['template_id']))
        return HttpResponse('200')
    if request.method == 'POST':
        form = PersonalInfoForm(data=request.POST)
        if form.is_valid():
            request.session['brochure_info']['first_name'] = request.POST.get('first_name', None)
            request.session['brochure_info']['last_name'] = request.POST.get('last_name', None)
            request.session['brochure_info']['title'] = request.POST.get('title', None)
            request.session['brochure_info']['email'] = request.POST.get('email', None)
            request.session['brochure_info']['website'] = request.POST.get('website', None)
            request.session['brochure_info']['phone1'] = request.POST.get('phone1', None)
            request.session['brochure_info']['phone2'] = request.POST.get('phone2', None)
            request.session.save()
            return HttpResponseRedirect(reverse('brochures:property_info'))
        else:
            print("form.errors", form.errors)
    else:
        form = PersonalInfoForm()

    return render(request, 'brochures/personal_info.html', {'form': form})


def property_info(request):
    """
    property info
    """

    if request.method == 'POST':
        form = PropertyInfoForm(data=request.POST)
        request.session['brochure_info']['property_address1'] = request.POST.get('property_address1', None)
        request.session['brochure_info']['property_address2'] = request.POST.get('property_address2', None)
        request.session['brochure_info']['property_city'] = request.POST.get('property_city', None)
        request.session['brochure_info']['property_state'] = request.POST.get('property_state', None)
        request.session['brochure_info']['property_code'] = request.POST.get('property_code', None)
        request.session['brochure_info']['property_price'] = request.POST.get('property_price', None)
        request.session.save()
        return HttpResponseRedirect(reverse('brochures:detail'))
    else:
        form = PropertyInfoForm()
    print('brochure info porp get', request.session['brochure_info'])
    return render(request, 'brochures/property_info.html', {'form': form})


def detail_page(request):
    """
    property info
    """
    messages.warning(request, '')
    session = request.session.get('brochure_info', None)
    brochure_id = session['template_id']
    brochure = get_object_or_404(Brochure, id=brochure_id)
    template = get_object_or_404(BrochureTemplate, id=brochure.template_id)
    template_path = template.getName()
    template_file_name = template_path.split('/')[-1]
    if request.method == 'POST':
        form = PropertyInfoForm(data=request.POST)
        preview = {}
        if form.is_valid():
            for file_key, file_val in request.FILES.iteritems():
                path = handle_uploaded_file(file_val)
                preview[file_key] = path
            for key, _ in request._post.iteritems():
                if key.startswith('text'):
                    preview[key] = request.POST.get(key, None)
            if request.POST.get('report_name', None):
                preview['report_name'] = request.POST.get('report_name', None)
            else:
                preview['report_name'] = 'Report'

            # request.session['brochure_info']['property_address1'] = request.POST.get('property_address1', None)
            # request.session['brochure_info']['property_address2'] = request.POST.get('property_address2', None)
            # request.session['brochure_info']['property_city'] = request.POST.get('property_city', None)
            # request.session['brochure_info']['property_state'] = request.POST.get('property_state', None)
            # request.session['brochure_info']['property_code'] = request.POST.get('property_code', None)
            # request.session['brochure_info']['property_price'] = request.POST.get('property_price', None)
            # request.session.save()
            return create_preview_from_files(request, preview, template)

    form = PropertyInfoForm()
    formated_template_name = 'pdf/{}'.format(template_file_name)
    return render(request, 'brochures/detail.html', {
        'formated_template_name': formated_template_name,
        'template': brochure,
        'form': form
        })


def preview_page(request):
    """
    property info
    """
    if request.method == 'GET':
        url_to_pdf = request.session.get('url_to_pdf', None)
        return render(request, 'brochures/preview.html', {'url_to_pdf': url_to_pdf})
    else:
        request.session['brochure_info']['coating'] = request.POST.get('coating', None)
        request.session.save()
        return HttpResponseRedirect(reverse('brochures:ship_and_mail'))


def ship_and_mail(request):
    """
    property info
    """
    addresses = Address.objects.filter(owners__in=[request.user])
    brochure_info = request.session.get('brochure_info', {})
    if request.method == 'GET':
        from datetime import datetime, timedelta
        # delivery_date = datetime.now().strftime("%d %B %Y")
        form = AddressForm()
        return render(request, 'brochures/shipping.html', {
            'form': form,
            'addresses': addresses,
            'brochure_info': brochure_info
        })
    else:
        if not request.POST.get('shipto_address', None):
            form = AddressForm(request.POST)
            if form.is_valid():
                new_addr = form.save()
                if request.POST.get('add_to_ab', None):
                    new_addr.owners.add(request.user)
                    # messages.success(request, "s|The address was added to your Address Book.")
                    new_addr.save()
                request.session['shipto_address'] = new_addr
            else:
                messages.warning(request, "e|There was a problem with your submission. \
                                           Refer to the messages below and try again.")
                return render(request, 'brochures/shipping.html', {
                    'form': form,
                    'addresses': addresses,
                    'brochure_info': brochure_info
                })

        else:
            form = AddressForm()
            address_id = request.POST.get('shipto_address', None)
            address = get_object_or_404(Address, pk=address_id)
            request.session['shipto_address'] = address

        cart = request.session.get('cart', None) or Cart()
        template_id = request.session['brochure_info']['template_id']
        brochure = Brochure.objects.get(id=template_id)
        unique_id = 'pdf_q{}'.format(brochure.id)
        cart.add_item(brochure, unique_id, request.POST.get('quantity', 20))
        request.session['cart'] = cart
        request.session['brochure_info'] = None
        messages.success(request, "s|Your brochure was successfully added to cart.")
        return HttpResponseRedirect(reverse('brochures:brochures'))



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
    folder_path = settings.STATIC_ROOT if settings.STATIC_ROOT else settings.STATICFILES_DIRS[0]
    destination = open('{0}{1}'.format(folder_path.encode('utf8'), path), 'wb+')
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
