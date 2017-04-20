from django.http import HttpResponseRedirect, HttpResponse, HttpResponseServerError
from django.shortcuts import render, get_object_or_404
from django.template import RequestContext, loader, Context
from django.core.mail import mail_managers, send_mail
from django.core.urlresolvers import reverse
from django.core.files import File
from uploads.forms import UploadFileForm
from django.conf import settings 
from django.core.cache import cache
from .models import Upload
import re
import os
import random

def sanitize_filename(name):
    """
    Given a filename string:
        * Adds a 4-letter random string at the beginning. This in theory makes the file harder to find for a malicious user, but also allows legit users to upload a file more than once (eg perhaps revisions) without overwriting it each time.
        * Replaces any non-alphanumeric character with an underscore. (Note that there is the regexp shortcut '\W' for non-alphanumeric characters, but that also includes periods which we want to keep for filenames.) This makes for clean, clickable URLs for some email clients (which would eg choke on a filename with spaces).
    """
    rstr = ''
    chars = random.sample(['B','C','D','F','G','H','J','K','L','M','N','P','Q','R','S','T','V','W','X','Z'], 4) 
    for c in chars: rstr += c
    r = re.compile('[^a-zA-Z0-9_.]')
    filename = r.sub('_', name)
    return '%s-%s' % (rstr, filename)


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


def show_list(request):
    return render(request, 'uploads/list.html', {})


def upload_file(request):
    """
    Displays and validates the upload form, and redirects to a confirmation page after the upload completes.
    """
    message = None
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            file = request.FILES['file']
            path = handle_uploaded_file(file)
            uploaded = Upload()
            uploaded.name = form.cleaned_data['title'] or "File"
            uploaded.file = File(open('{}{}'.format(settings.BASE_DIR, path), 'wb+')) #request.FILES['file']
            uploaded.comments = form.cleaned_data['comments']
            uploaded.is_deletable = True
            uploaded.user_name = form.cleaned_data['name']
            uploaded.email = form.cleaned_data['email']
            try:
                uploaded.save()
            except Exception as ex:
                message = "Error: There was a problem with your submission. Refer to the messages below and try again."
                return render(request, 'uploads/upload.html', {
                    'form': form,
                    'message': message,
                })

            # send mail to staff
            t = loader.get_template('emails/file_uploaded.txt')
            subject = "File Upload"
            c = Context({
                'file': file,
                'path': uploaded.file.name,
                'file_url': request.build_absolute_uri(uploaded.file.name),
                'form': request.POST,
            })
            body = t.render(c)
            mail_managers(subject, body, fail_silently=False)

            if request.user.is_authenticated() or form.cleaned_data['email']:
                if request.user.is_authenticated():
                    recipient = request.user.email
                else:
                    recipient = form.cleaned_data['email']
                t = loader.get_template('emails/user_file_uploaded.txt')
                subject = "[Mimic OOS] File Upload Confirmed"
                body = t.render(c)
                send_mail(subject, body, 'orders@mimicprint.com', [recipient], fail_silently=False)

            return HttpResponseRedirect(reverse('uploads:upload_ok'))
        else:
            message = "Error: There was a problem with your submission. Refer to the messages below and try again."
    else:
        form = UploadFileForm()
    return render(request, 'uploads/upload.html', {
        'form': form,
        'message': message,
    })


def upload_progress(request):
    """
    Return JSON object with information about the progress of an upload.
    """
    progress_id = ''
    if 'X-Progress-ID' in request.GET:
        progress_id = request.GET['X-Progress-ID']
    elif 'X-Progress-ID' in request.META:
        progress_id = request.META['X-Progress-ID']
    elif 'X-Progress-Id' in request.GET:
        progress_id = request.META['X-Progress-Id']
    elif 'X-Progress-Id' in request.META:
        progress_id = request.META['X-Progress-Id']
    if progress_id:
        import simplejson
        cache_key = "%s_%s" % (request.META['REMOTE_ADDR'], progress_id)
        data = cache.get(cache_key)
        json = simplejson.dumps(data)
        return HttpResponse(json)
    else:
        return HttpResponseServerError('Server Error: You must provide X-Progress-ID header or query param.')
