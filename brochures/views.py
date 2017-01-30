import random
import re

from django.conf import settings
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.template import Context
from django.template.loader import get_template
from django.contrib import messages
from django.http import HttpResponse
from forms import BrochuresPDFForm
from models import Brochure
from itertools import repeat


@login_required
def index(request):
    """
    Shows the list of Brochures:
    """
    templates = Brochure.objects.all()
    return render(request, 'brochures/brochures_list.html', {'templates': templates})


@login_required
def create_pdf(request, template_name):
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

    template = get_object_or_404(Brochure, template=template_name)
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
    context = Context(files)
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

    template = get_object_or_404(Brochure, template=template_name)
    formated_template_name = 'pdf/{}.html'.format(template_name)

    return render(request, 'brochures/create_pdf.html', {
        'formated_template_name': formated_template_name,
        'template': template,
        'preview': files
    })


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
