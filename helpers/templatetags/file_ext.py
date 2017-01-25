from django import template
import os.path
register = template.Library()

@register.inclusion_tag('templatetags/file_icon.html')
def get_filetype(file):
    """
    Grabs the file extension (everything after the last ".")
    of `file` for use in rendering an accurate icon.
    The `known_exts` list keeps track of filetypes there are icons
    for -- if the current filetype does not match anything on this list,
    a blank string is returned to the template to avoid voluminous if statements.
    """
    known_exts = [
        'pdf',
        'zip',
        'gz',
        'psd',
        'tif',
        'tiff',
        'ai',
        'eps',
        'jpg',
        'xls',
        'doc',
        'txt',
        'png'
    ]
    name_pieces = file.file.name.split('.')
    extension = name_pieces[-1].encode('utf-8').lower()
    if extension not in known_exts:
        extension = ''
    return {
        'extension': extension
    }


@register.assignment_tag(takes_context=True)
def checkexistfile(context, file):
    """ Check download file for existing """
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.isfile(os.path.join(BASE_DIR, file.file.name))
