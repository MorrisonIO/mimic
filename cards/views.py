import random
import re
import os

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
from forms import CardsPDFForm
from addresses.forms import AddressForm
from addresses.models import Address
from orders.models import Cart
from models import Card, CardTemplate
from itertools import repeat
from forms import PersonalInfoForm, PropertyInfoForm
from decorators import current_org_required


def collect_menu_data(cards):
    """
    Collect data for menu information
    E.g.: number of images or number of cards types
    """
    cards = cards or []
    elems = {}
    elems['feature_prop'] = {'title': 'Feature Properties'}
    elems['num_of_images'] = {'title': 'Number of photos'}
    try:
        temps = serializers.serialize('json', cards)
        for temp in cards:
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


@current_org_required
@login_required
def index(request):
    """
    Shows the list of Cards:
    """
    org = request.session.get('current_org', None)
    cards = Card.objects.filter(org=org)
    elems = collect_menu_data(cards)
    return render(request, 'cards/cards_list.html', {
        'cards': cards,
        'menu_data': elems
        })


@login_required
def create_pdf(request, template_name, template_id):
    """
    CREATE PDF
    * GET  query: get card object and drow it's template
      formated_template_name is path to card template what will be included on page
    * POST query: get query params and put them to pdf fields
    """
    messages.warning(request, '')
    if request.method == 'POST':
        form = CardsPDFForm(request.POST, request.FILES)
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
            warning_msg = "e|There was a problem with your submission. Fields:{} required" \
                          .format(', '.join(list(key for key, value in form.errors.iteritems())))
            messages.warning(request, warning_msg)

    card = get_object_or_404(Card, id=template_id)
    formated_template_name = 'pdf/{}.html'.format(template_name)

    return render(request,
                  'cards/create_pdf.html', {
                      'formated_template_name': formated_template_name,
                      'card': card
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
    rendered_template = html_template.render({'context': files})

    if settings.STATIC_ROOT:
        target = '{0}/pdf/{1}.pdf'.format(settings.STATIC_ROOT, files['report_name'])
    else:
        target = '{0}/static/pdf/{1}.pdf'.format(settings.BASE_DIR, files['report_name'])

    pdf_file = HTML(string=rendered_template, base_url=request.build_absolute_uri()).write_pdf(target)
    url_to_pdf = '{0}{1}.pdf'.format('/static/pdf/', files['report_name'])
    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = 'filename="temp_1.pdf"'

    remove_files(files)

    request.session['url_to_pdf'] = url_to_pdf
    return HttpResponseRedirect(reverse('cards:preview'))


@login_required
def get_card_modal_data(request):
    import json
    card_id = request.GET.get('id')
    card = Card.objects.get(pk=card_id)
    description = card.description if card else ''
    preview_images = []
    for img in card.preview_images.all():
        url = img.preview_img.file.name[len(settings.BASE_DIR):]
        name = img.name
        preview_images.append({'url': url, 'name': name})
    return HttpResponse(json.dumps({'description': description, 'preview_images': preview_images}))


def render_view(request, template_id):
    """
    Render single template.
    Uses to render template within create_pdf page
    """
    template = get_object_or_404(CardTemplate, id=template_id)
    template_file = template.getName().split('/')[-1]
    return render(request, 'pdf/{}'.format(template_file), {'context':{}})


def personal_info(request):
    """
    Personal Info
    """
    if request.is_ajax() and request.method == "GET":
        request.session['card_info'] = dict(template_id=int(request.GET['template_id']))
        return HttpResponse('200')
    if request.method == 'POST':
        form = PersonalInfoForm(data=request.POST)
        if form.is_valid():
            request.session['card_info']['first_name'] = request.POST.get('first_name', None)
            request.session['card_info']['last_name'] = request.POST.get('last_name', None)
            request.session['card_info']['title'] = request.POST.get('title', None)
            request.session['card_info']['email'] = request.POST.get('email', None)
            request.session['card_info']['website'] = request.POST.get('website', None)
            request.session['card_info']['phone1'] = request.POST.get('phone1', None)
            request.session['card_info']['phone2'] = request.POST.get('phone2', None)
            request.session.save()
            return HttpResponseRedirect(reverse('cards:property_info'))
        else:
            print("form.errors", form.errors)
    else:
        form = PersonalInfoForm()

    card_info = request.session.get('card_info', None)

    if not card_info or 'template_id' not in card_info:
        return HttpResponseRedirect(reverse('cards:cards'))

    return render(request, 'cards/personal_info.html', {'form': form})


def property_info(request):
    """
    property info
    """
    card_info = request.session['card_info']
    if not card_info or 'template_id' not in card_info:
        return HttpResponseRedirect(reverse('cards:cards'))
    if request.method == 'POST':
        form = PropertyInfoForm(data=request.POST)
        request.session['card_info']['property_address1'] = request.POST.get('property_address1', None)
        request.session['card_info']['property_address2'] = request.POST.get('property_address2', None)
        request.session['card_info']['property_city'] = request.POST.get('property_city', None)
        request.session['card_info']['property_state'] = request.POST.get('property_state', None)
        request.session['card_info']['property_code'] = request.POST.get('property_code', None)
        request.session['card_info']['property_price'] = request.POST.get('property_price', None)
        request.session.save()
        return HttpResponseRedirect(reverse('cards:detail'))
    else:
        form = PropertyInfoForm()
    print('card info porp get', request.session['card_info'])
    return render(request, 'cards/property_info.html', {'form': form})


def creator(request):
    return render(request, 'cards/creator.html', {})


def creator_data(request):
    if request.method == 'POST':
        ui_text = request.POST.get('ui_text')
        ui_template = Template(ui_text)
        return HttpResponse(ui_template.render({}))


def detail_page(request):
    """
    property info
    """
    import base64

    messages.warning(request, '')
    session = request.session.get('card_info', None)

    if not session or 'template_id' not in session:
        return HttpResponseRedirect(reverse('cards:cards'))

    card_id = session['template_id']
    card = get_object_or_404(Card, id=card_id)
    template = get_object_or_404(CardTemplate, id=card.template_id)
    template_path = template.getName()
    template_file_name = template_path.split('/')[-1]
    if request.method == 'POST':
        form = PropertyInfoForm(data=request.POST)
        preview = {}
        if form.is_valid():
            for file_key, file_val in request.FILES.iteritems():
                path = handle_uploaded_file(file_val)		 #base64.b64encode(file_val.read()).decode()
                preview[file_key] = path #"data:image/jpg;charset=utf-8;base64,{}".format(path)
            for key, _ in request._post.iteritems():
                if key.startswith('text'):
                    preview[key] = request.POST.get(key, None)
            if request.POST.get('report_name', None):
                preview['report_name'] = request.POST.get('report_name', None)
            else:
                preview['report_name'] = 'Report'

            # request.session['card_info']['property_address1'] = request.POST.get('property_address1', None)
            # request.session['card_info']['property_address2'] = request.POST.get('property_address2', None)
            # request.session['card_info']['property_city'] = request.POST.get('property_city', None)
            # request.session['card_info']['property_state'] = request.POST.get('property_state', None)
            # request.session['card_info']['property_code'] = request.POST.get('property_code', None)
            # request.session['card_info']['property_price'] = request.POST.get('property_price', None)
            # request.session.save()
            return create_preview_from_files(request, preview, template)

    form = PropertyInfoForm()
    formated_template_name = 'pdf/{}'.format(template_file_name)
    return render(request, 'cards/detail.html', {
        'formated_template_name': formated_template_name,
        'template': card,
        'form': form
        })


def preview_page(request):
    """
    property info
    """
    session = request.session.get('card_info', None)
    if not session or 'template_id' not in session:
        return HttpResponseRedirect(reverse('cards:cards'))

    if request.method == 'GET':
        url_to_pdf = request.session.get('url_to_pdf', None)
        return render(request, 'cards/preview.html', {'url_to_pdf': url_to_pdf})
    else:
        request.session['card_info']['coating'] = request.POST.get('coating', None)
        request.session.save()
        return HttpResponseRedirect(reverse('cards:ship_and_mail'))


def ship_and_mail(request):
    """
    property info
    """
    session = request.session.get('card_info', None)
    if not session or 'template_id' not in session:
        return HttpResponseRedirect(reverse('cards:cards'))

    addresses = Address.objects.filter(owners__in=[request.user])
    card_info = request.session.get('card_info', {})
    if request.method == 'GET':
        from datetime import datetime, timedelta
        # delivery_date = datetime.now().strftime("%d %B %Y")
        form = AddressForm()
        return render(request, 'cards/shipping.html', {
            'form': form,
            'addresses': addresses,
            'card_info': card_info
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
                return render(request, 'cards/shipping.html', {
                    'form': form,
                    'addresses': addresses,
                    'card_info': card_info
                })

        else:
            form = AddressForm()
            address_id = request.POST.get('shipto_address', None)
            address = get_object_or_404(Address, pk=address_id)
            request.session['shipto_address'] = address

        cart = request.session.get('cart', None) or Cart()
        template_id = request.session['card_info']['template_id']
        card = Card.objects.get(id=template_id)
        unique_id = 'pdf_q{}'.format(card.id)
        cart.add_item(card, unique_id, request.POST.get('quantity', 20))
        request.session['cart'] = cart
        request.session['card_info'] = None
        messages.success(request, "s|Your card was successfully added to cart.")
        return HttpResponseRedirect(reverse('cards:cards'))



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
    path = 'uploads/%s' % filename
    folder_path = settings.MEDIA_ROOT
    if not os.path.isdir(folder_path + 'uploads'):
        os.mkdir(folder_path + 'uploads')
    destination = open('{0}{1}'.format(folder_path.encode('utf8'), path), 'wb+')
    for chunk in f.chunks():
        destination.write(chunk)
    url = '%s%s' % (settings.MEDIA_URL, path)
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


def remove_files(files):
    """
    Remove files from disk
    """
    for k,v in files.iteritems():
        if k.startswith('image'): os.remove(settings.BASE_DIR + v)
