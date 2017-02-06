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
from models import Brochure
from itertools import repeat
from forms import PersonalInfoForm

def collect_menu_data():
    import json
    templates = Brochure.objects.all()
    elems = {}
    elems['feature_prop'] = {'title': 'Feature Properties'}
    elems['num_of_images'] = {'title': 'Number of photos'}
    try:
        temps = serializers.serialize('json', templates)
        for temp in templates:
            if temp.feature_prop.encode('utf-8') in elems['feature_prop']:
                elems['feature_prop'][temp.feature_prop.encode('utf-8')] += 1
            else:
                elems['feature_prop'][temp.feature_prop.encode('utf-8')] = 1

            if temp.num_of_images in elems['num_of_images']:
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
    templates = Brochure.objects.all()
    elems = collect_menu_data()
    print ('templates', templates[0].__dict__)
    return render(request, 'brochures/brochures_list.html', {
        'templates': templates,
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
            for key, val in request._post.iteritems():
                if key.startswith('text'):
                    preview[key] = request.POST.get(key, None)
            if request.POST.get('report_name', None):
                preview['report_name'] = request.POST.get('report_name', None)
            else:
                preview['report_name'] = 'Report'
            return create_preview_from_files(request, preview, template_name)
        else:
            print('form.errors', form.errors)
            warning_msg = "e|There was a problem with your submission. Fields:{} required" \
                          .format(', '.join(list(key for key, value in form.errors.iteritems())))
            messages.warning(request, warning_msg)

    template = get_object_or_404(Brochure, id=template_id)
    formated_template_name = 'pdf/{}.html'.format(template_name)

    return render(request,
                  'brochures/create_pdf.html', {
                      'formated_template_name': formated_template_name,
                      'template': template
                  }
                 )


def create_preview_from_files(request, files, template_name):
    """
    Create pdf from form data
    """
    from weasyprint import HTML

    html_template = get_template('pdf/{}.html'.format(template_name))
    context = Context({'context':files})
    rendered_template = html_template.render(context)

    if settings.STATIC_ROOT:
        target = '{0}/pdf/{1}.pdf'.format(settings.STATIC_ROOT, files['report_name'])
    else:
        target = '{0}/static/pdf/{1}.pdf'.format(settings.BASE_DIR, files['report_name'])

    pdf_file = HTML(string=rendered_template, base_url=request.build_absolute_uri()).write_pdf(target)

    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = 'filename="temp_1.pdf"'
    messages.success(request, "s|The PDF successully created: \
                    <a href='{0}{1}.pdf' target='_blank'>Download</a>".format('/static/pdf/', files['report_name']))

    template = get_object_or_404(Brochure, id=template_id)
    formated_template_name = 'pdf/{}.html'.format(template_name)

    return render(request, 'brochures/create_pdf.html', {
        'formated_template_name': formated_template_name,
        'template': template,
        'preview': files
    })


@login_required
def get_brochure_modal_data(request):
    # print("request", request.__dict__)
    import json
    template_id = request.GET.get('id')
    template = Brochure.objects.get(pk=template_id)
    description = template.description if template else ''
    return HttpResponse(json.dumps({'description': description}))



def render_view(request, template_name):
    """
    Render single template.
    Uses to render template within create_pdf page 
    """
    print('template_name', template_name)
    return render(request, 'pdf/{}.html'.format(template_name), {
        # 'formated_template_name': formated_template_name,
        # 'template': template,
        # 'preview': files
    })


def personal_info(request):
    """
    Repsonal Info
    """
    if request.method == 'POST':
        form = PersonalInfoForm(data=request.POST)
        if form.is_valid():
            request.session['first_name'] = request.POST.get('first_name', None)
            request.session['last_name'] = request.POST.get('last_name', None)
            request.session['title'] = request.POST.get('title', None)
            request.session['email'] = request.POST.get('email', None)
            request.session['website'] = request.POST.get('website', None)
            request.session['phone1'] = request.POST.get('phone1', None)
            request.session['phone2'] = request.POST.get('phone2', None)
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
    if request.method == 'GET':
        print('session', request.session['first_name'])
        return render(request, 'brochures/property_info.html', {})
    else:
        return HttpResponseRedirect(reverse('brochures:detail'))


def detail(request):
    """
    property info
    """
    if request.method == 'GET':
        return render(request, 'brochures/detail.html', {})
    else:
        return HttpResponseRedirect(reverse('brochures:preview'))


def preview(request):
    """
    property info
    """
    if request.method == 'GET':
        return render(request, 'brochures/preview.html', {})
    else:
        return HttpResponseRedirect(reverse('brochures:ship_and_mail'))


def ship_and_mail(request):
    """
    property info
    """
    if request.method == 'GET':
        return render(request, 'brochures/shipping.html', {})
    else:
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
