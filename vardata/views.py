# coding: utf8

from cStringIO import StringIO
import reportlab
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, elevenSeventeen
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics, pdfdoc
from reportlab.platypus import Paragraph, Frame, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle, PropertySet
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
from reportlab.lib.colors import Color, HexColor, CMYKColor
from reportlab.pdfbase.ttfonts import TTFont
from django.http import HttpResponseRedirect, HttpResponse
from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.conf import settings
import os
import string
from time import time
from orders.models import OrderedItem
from vardata.models import *
import re
import cgi

from pyPdf import PdfFileWriter, PdfFileReader
from pyPdf.pdf import PageObject, RectangleObject, NameObject
from StringIO import StringIO

PAGE_BOXES = ("/MediaBox", "/CropBox", "/BleedBox", "/TrimBox", "/ArtBox")

def copyPage(page):
    newpage = PageObject(page.pdf)
    newpage.update(page)
    for attr in PAGE_BOXES:
        if page.has_key(attr):
            newpage[NameObject(attr)] = RectangleObject(list(page[attr]))
    return newpage

def merge_pdfs(*readers):
    output = PdfFileWriter()
    readers = [(r.numPages, r) for r in readers]
    totalpages = max([r[0] for r in readers])

    for idx in range(totalpages):
        page = None

        for pages, pdf in readers:
            if pages > idx:
                ppage = pdf.getPage(idx)

                if page is None:
                    page = copyPage(ppage)
                else:
                    page.mergePage(ppage)

        output.addPage(page)

    return output


def escape(data):
    """
    Given a dictionary `data`, converts instances of XML reserved characters
    (eg '&', '<') to their HTML entity equivalents ('&amp;', '&lt;'). Regular
    unicode characters remain unaltered. Escaping is required for all
    strings being passed to reportlab, or else they will not appear.
    """
    for d in data:
        try:
            data[d] = cgi.escape(data[d])
        except AttributeError:
            pass
    return data


def phone_parts(phone):
    """
    Takes a phone number string in any format, like "(905) 415-2772 ext 25", and returns it as a list of the various parts ('areacode', 'trunk', 'rest of number', 'optional extension') ie ('905', '415', '2772', '25'). Note that we must receive an area code. If 'phone' is not a suitable string (ie the regex can't be found), we return an obviously false number so the user can go back and correct it.

    Regex taken from http://diveintopython.org/regular_expressions/phone_numbers.html.
    """
    phonePattern = re.compile(r'''
                # don't match beginning of string, number can start anywhere
    (\d{3})*    # area code is 3 digits (e.g. '800'). Not optional, but the user might forget so we put the *
    \D*         # optional separator is any number of non-digits
    (\d{3})     # trunk is 3 digits (e.g. '555')
    \D*         # optional separator
    (\d{4})     # rest of number is 4 digits (e.g. '1212')
    \D*         # optional separator
    (\d*)       # extension is optional and can be any number of digits
    $           # end of string
    ''', re.VERBOSE)

    # We have no way of doing validation on the form, so if the regex doesn't
    # match (eg, the user enters "foo") we have to return something or else
    # when we try to access the dictionary to put on the card it will break.
    # So we return something that's obviously wrong as a failsafe.
    if phonePattern.search(phone) is None:
        return ('xxx', 'xxx', 'xxxx', 'xxx')

    # regex found, return all the pieces
    parts = phonePattern.search(phone).groups()
    return (parts[0], parts[1], parts[2], parts[3])

@login_required
def index(request):
    """
    This view is not visited directly, it exists only for URL resolving/permalinks to work.
    """
    return HttpResponseRedirect(reverse('oos_home'))

# Mimic
#{{{ mimic_stylesheet
def mimic_stylesheet():
    stylesheet = {}

    # Register all required fonts
    folder = settings.FONT_DIR # from settings.py
    registered = pdfmetrics.getRegisteredFontNames()

    afmFile = os.path.join(folder, 'DIN-MediumAlternate.afm')
    pfbFile = os.path.join(folder, 'DIN-MediumAlternate.pfb')
    faceName = 'DIN-MediumAlternate'
    if faceName not in registered:
        justFace = pdfmetrics.EmbeddedType1Face(afmFile, pfbFile)
        pdfmetrics.registerTypeFace(justFace)
        justFont = pdfmetrics.Font('DIN-MediumAlternate', faceName, 'WinAnsiEncoding')
        pdfmetrics.registerFont(justFont)

    afmFile = os.path.join(folder, 'DIN-LightAlternate.afm')
    pfbFile = os.path.join(folder, 'DIN-LightAlternate.pfb')
    faceName = 'DIN-LightAlternate'
    if faceName not in registered:
        justFace = pdfmetrics.EmbeddedType1Face(afmFile, pfbFile)
        pdfmetrics.registerTypeFace(justFace)
        justFont = pdfmetrics.Font(faceName, faceName, 'WinAnsiEncoding')
        pdfmetrics.registerFont(justFont)

    p = ParagraphStyle('medium', None)
    p.fontName = 'DIN-MediumAlternate'
    p.fontSize = 10
    p.alignment = TA_RIGHT
    p.textColor = HexColor(0x990000)
    stylesheet['medium'] = p

    p = ParagraphStyle('light', None)
    p.fontName = 'DIN-MediumAlternate'
    p.fontSize = 7
    p.leading = 10
    p.alignment = TA_RIGHT
    p.textColor = HexColor(0x990000)
    stylesheet['light'] = p

    return stylesheet
#}}}
#{{{ MimicBc_1up
def MimicBc_1up(request):
    # Create output filenames
    timestamp = str(time()).replace('.','')
    pdf_file = "%s/previews/%s.pdf" % (settings.MEDIA_ROOT, timestamp)
    img_file = "%s/previews/%s.gif" % (settings.MEDIA_ROOT, timestamp)

    # Set some document specifics
    pagesize = (inch*3.5, inch*1.75) # 252 x 126
    bg_image = "vardata_images/MimicBc_bg.tiff"
    fonts = mimic_stylesheet()
    medium_style = fonts['medium']
    light_style = fonts['light']

    # Get the info that the user entered. These fields should match what's in the model.
    form_data = request.session.get('form_data', None)
    first_name = form_data['first_name']
    last_name = form_data['last_name']
    email = form_data['email']
    cell = form_data['cell']
    extension = form_data['extension']
    full_name = '%s %s' % (first_name, last_name)
    net_info = 'www.mimicprint.com %s' % email
    phone_info = '905.415.2772 x%s       905.415.2005    %s' % (extension, cell)

    # Format the lines and add them to the document
    name_line = []
    contact_line = []
    name_line.append(Paragraph(full_name, medium_style))
    contact_line.append(Paragraph(net_info, light_style))
    contact_line.append(Paragraph('20 steelcase rd w #13 markham on canada l3r1b2', light_style))
    contact_line.append(Paragraph(phone_info, light_style))
    c = canvas.Canvas(filename=pdf_file, pagesize=pagesize, pageCompression=1)
    c.drawImage(bg_image, 0, 0, width=252, height=126, mask=None)

    f = Frame(0, 0, 3.5*inch, 1.75*inch, showBoundary=0, rightPadding=0.46*inch, topPadding=0.65*inch)
    f.addFromList(name_line,c)
    f = Frame(0, 0, 3.5*inch, 1.75*inch, showBoundary=0, rightPadding=0.46*inch, topPadding=1.18*inch)
    f.addFromList(contact_line,c)

    # Close the PDF object cleanly
    c.showPage()
    c.save()

    # Create a preview image
    command = 'convert -page 252x126 %s %s' % (pdf_file, img_file)
    os.system(command)

    # Set session variable so we can pass filename back to preview
    request.session['filename_prefix'] = timestamp

    return HttpResponseRedirect(reverse('orders:vardata_preview'))
#}}}
#{{{ MimicBc_print
def MimicBc_print(request, ordereditem_id):
    ordereditem = OrderedItem.objects.get(pk=ordereditem_id)

    # Create output filename
    filename = "%s-%s.pdf" % (ordereditem.order.name, ordereditem_id)

    # Set some document specifics
    response = HttpResponse(mimetype='application/pdf')
    response['Content-Disposition'] = 'attachment; filename=%s' % filename # force save as dialog
    pagesize = (inch*3.5, inch*1.75) # 252 x 126
    bg_image = "vardata_images/MimicBc_bg.tiff"
    fonts = mimic_stylesheet()
    medium_style = fonts['medium']
    light_style = fonts['light']

    # Get the info stored in the DB. Refer to the model for the field names
    data = MimicBc.objects.get(ordereditem = ordereditem_id)
    # careful of required fields...
    first_name = data.first_name
    last_name = data.last_name
    email = data.email
    cell = data.cell
    extension = data.extension
    full_name = '%s %s' % (first_name, last_name)
    net_info = 'www.mimicprint.com %s' % email
    phone_info = '905.415.2772 x%s       905.415.2005    %s' % (extension, cell)

    # Format the lines and add them to the document
    name_line = []
    contact_line = []
    name_line.append(Paragraph(full_name, medium_style))
    contact_line.append(Paragraph(net_info, light_style))
    contact_line.append(Paragraph('20 steelcase rd w #13 markham on canada l3r1b2', light_style))
    contact_line.append(Paragraph(phone_info, light_style))
    c = canvas.Canvas(response, pagesize=pagesize, pageCompression=1)
    c.drawImage(bg_image, 0, 0, width=252, height=126, mask=None)

    f = Frame(0, 0, 3.5*inch, 1.75*inch, showBoundary=0, rightPadding=0.46*inch, topPadding=0.65*inch)
    f.addFromList(name_line,c)
    f = Frame(0, 0, 3.5*inch, 1.75*inch, showBoundary=0, rightPadding=0.46*inch, topPadding=1.18*inch)
    f.addFromList(contact_line,c)

    # Close the PDF object cleanly
    c.showPage()
    c.save()

    return response
#}}}

# TLA
#{{{ tla_stylesheet
def tla_stylesheet():
    stylesheet = {}

    # Register all required fonts
    folder = settings.FONT_DIR # from settings.py
    registered = pdfmetrics.getRegisteredFontNames()

    afmFile = os.path.join(folder, 'Myriad-Roman.afm')
    pfbFile = os.path.join(folder, 'Myriad-Roman.pfb')
    faceName = 'Myriad-Roman'
    if faceName not in registered:
        justFace = pdfmetrics.EmbeddedType1Face(afmFile, pfbFile)
        pdfmetrics.registerTypeFace(justFace)
        justFont = pdfmetrics.Font('Myriad-Roman', faceName, 'WinAnsiEncoding')
        pdfmetrics.registerFont(justFont)

    afmFile = os.path.join(folder, 'Myriad-Italic.afm')
    pfbFile = os.path.join(folder, 'Myriad-Italic.pfb')
    faceName = 'Myriad-Italic'
    if faceName not in registered:
        justFace = pdfmetrics.EmbeddedType1Face(afmFile, pfbFile)
        pdfmetrics.registerTypeFace(justFace)
        justFont = pdfmetrics.Font(faceName, faceName, 'WinAnsiEncoding')
        pdfmetrics.registerFont(justFont)

    afmFile = os.path.join(folder, 'Myriad-Bold.afm')
    pfbFile = os.path.join(folder, 'Myriad-Bold.pfb')
    faceName = 'Myriad-Bold'
    if faceName not in registered:
        justFace = pdfmetrics.EmbeddedType1Face(afmFile, pfbFile)
        pdfmetrics.registerTypeFace(justFace)
        justFont = pdfmetrics.Font(faceName, faceName, 'WinAnsiEncoding')
        pdfmetrics.registerFont(justFont)

    p = ParagraphStyle('roman', None)
    p.fontName = 'Myriad-Roman'
    p.fontSize = 8
    p.leading = 9
    p.alignment = TA_RIGHT
    p.textColor = HexColor(0x000000)
    stylesheet['roman'] = p

    p = ParagraphStyle('italic', None)
    p.fontName = 'Myriad-Italic'
    p.fontSize = 8
    p.leading = 9
    p.alignment = TA_RIGHT
    p.textColor = HexColor(0x000000)
    stylesheet['italic'] = p

    p = ParagraphStyle('bold', None)
    p.fontName = 'Myriad-Bold'
    p.fontSize = 12
    p.leading = 12
    p.alignment = TA_RIGHT
    p.textColor = HexColor(0x000000)
    stylesheet['bold'] = p

    p = ParagraphStyle('blue', None)
    p.fontName = 'Myriad-Roman'
    p.fontSize = 8
    p.leading = 9
    p.alignment = TA_RIGHT
    p.textColor = HexColor(0x1b1464)
    stylesheet['blue'] = p

    p = ParagraphStyle('spacer', None)
    p.spaceAfter = 9
    stylesheet['spacer'] = p

    return stylesheet
#}}}
#{{{ TlaBc_1up
def TlaBc_1up(request):
    # Create output filenames
    timestamp = str(time()).replace('.','')
    pdf_file = "%s/previews/%s.pdf" % (settings.MEDIA_ROOT, timestamp)
    img_file = "%s/previews/%s.gif" % (settings.MEDIA_ROOT, timestamp)

    # Set some document specifics
    pagesize = (inch*3.5, inch*2) # width, height. Measured at 72dpi, so this is 252x144
    bg_image = "%s/vardata_images/TlaBc_bg.tif" % settings.MEDIA_ROOT
    fonts = tla_stylesheet()

    # Get the info that the user entered. These fields should match what's in the model.
    form_data = request.session.get('form_data', None)
    first_name = form_data['first_name']
    last_name = form_data['last_name']
    title = form_data['title']
    email = form_data['email']
    cell = phone_parts(form_data['cell'])
    full_name = '%s %s' % (first_name, last_name)
    tel_line = '<font name="Myriad-Italic" color="0x666666">tel</font> (416) 456-7890'
    cell_line = '<font name="Myriad-Italic" color="0x666666">cell</font> (%s) %s-%s' % (cell[0], cell[1], cell[2])
    fax_line = '<font name="Myriad-Italic" color="0x666666">fax</font> (416) 456-7891'
    email_line = '<font name="Myriad-Italic" color="0x666666">email</font> %s@tlacorp.com' % email
    web_line = 'www.tlacorp.com'

    # Format the lines and add them to the document
    info = []
    info.append(Paragraph(full_name, fonts['bold']))
    info.append(Paragraph(title, fonts['italic']))
    info.append(Paragraph("", fonts['spacer']))
    info.append(Paragraph("123 Whatever Ave, Suite 456", fonts['roman']))
    info.append(Paragraph("Anytown, ON M1A 2B3 Canada", fonts['roman']))
    info.append(Paragraph("", fonts['spacer']))
    info.append(Paragraph(tel_line, fonts['roman']))
    info.append(Paragraph(fax_line, fonts['roman']))
    info.append(Paragraph(cell_line, fonts['roman']))
    info.append(Paragraph(email_line, fonts['roman']))
    info.append(Paragraph("", fonts['spacer']))
    info.append(Paragraph(web_line, fonts['blue']))
    c = canvas.Canvas(filename=pdf_file, pagesize=pagesize, pageCompression=1)
    c.drawImage(bg_image, 0, 0, width=252, height=144, mask=None)
    f = Frame(0, 0, 3.5*inch, 2*inch, showBoundary=0, rightPadding=0.25*inch, topPadding=0.25*inch)
    f.addFromList(info,c)

    # Close the PDF object cleanly
    c.showPage()
    c.save()

    # Create a preview image
    command = 'convert -page 252x144 %s %s' % (pdf_file, img_file)
    os.system(command)

    # Set session variable so we can pass filename back to preview
    request.session['filename_prefix'] = timestamp

    return HttpResponseRedirect(reverse('orders:vardata_preview'))
#}}}
#{{{ TlaBc_print
def TlaBc_print(request, ordereditem_id):
    ordereditem = OrderedItem.objects.get(pk=ordereditem_id)
    data = TlaBc.objects.get(ordereditem = ordereditem_id)

    # Set some document specifics
    filename = "%s-%s.pdf" % (ordereditem.order.name, ordereditem_id)
    response = HttpResponse(mimetype='application/pdf')
    response['Content-Disposition'] = 'attachment; filename=%s' % filename # force save as dialog
    pagesize = (inch*17, inch*11) # width, height. Measured at 72dpi, so this is 1224x792
    bg_image = "%s/vardata_images/TlaBc_bg_print.tif" % settings.MEDIA_ROOT
    fonts = tla_stylesheet()

    # Measurements of page
    left_margin = 0.75*inch  # distance from edge of page to leftmost cropmark
    bottom_margin = 0.5*inch # distance from edge of page to bottommost cropmark
    horiz_offset = 4*inch    # distance between the start of one piece & the next (ie left side to left side)
    vert_offset = 2*inch     # same but from top to top
    num_cols = 4             # number of columns of pieces
    num_rows = 5             # number of rows of pieces
    total_pieces = num_cols * num_rows

    # Format the lines and add them to the document
    tel_line = '<font name="Myriad-Italic" color="0x666666">tel</font> (416) 456-7890'
    cell = phone_parts(data.cell)
    cell_line = '<font name="Myriad-Italic" color="0x666666">cell</font> (%s) %s-%s' % (cell[0], cell[1], cell[2])
    fax_line = '<font name="Myriad-Italic" color="0x666666">fax</font> (416) 456-7891'
    email_line = '<font name="Myriad-Italic" color="0x666666">email</font> %s@tlacorp.com' % data.email
    web_line = 'www.tlacorp.com'
    info_block = []
    info_block.append(Paragraph("%s %s" % (data.first_name, data.last_name), fonts['bold']))
    info_block.append(Paragraph(data.title, fonts['italic']))
    info_block.append(Paragraph("", fonts['spacer']))
    info_block.append(Paragraph("123 Whatever Ave, Suite 456", fonts['roman']))
    info_block.append(Paragraph("Anytown, ON M1A 2B3 Canada", fonts['roman']))
    info_block.append(Paragraph("", fonts['spacer']))
    info_block.append(Paragraph(tel_line, fonts['roman']))
    info_block.append(Paragraph(fax_line, fonts['roman']))
    info_block.append(Paragraph(cell_line, fonts['roman']))
    info_block.append(Paragraph(email_line, fonts['roman']))
    info_block.append(Paragraph("", fonts['spacer']))
    info_block.append(Paragraph(web_line, fonts['blue']))
    info = []
    info.extend(total_pieces*info_block)

    # Loop through rows & columns and draw all the pieces
    c = canvas.Canvas(response, pagesize=pagesize, pageCompression=1)
    c.drawImage(bg_image, 0, 0, width=1224, height=792, mask=None)
    for row in range(num_rows):
        for col in range(num_cols):
            f = Frame(left_margin+(col*horiz_offset), (row*vert_offset)+bottom_margin, 3.5*inch, 2*inch, rightPadding=0.25*inch, topPadding=0.25*inch)
            f.addFromList(info,c)

    # Close the PDF object cleanly
    c.showPage()
    c.save()
    return response
#}}}

# Harris
#{{{ harris_stylesheet
def harris_stylesheet():
    stylesheet = {}

    # Register all required fonts
    folder = settings.FONT_DIR # from settings.py
    registered = pdfmetrics.getRegisteredFontNames()

    afmFile = os.path.join(folder, 'Frutiger-BoldItalic.afm')
    pfbFile = os.path.join(folder, 'Frutiger-BoldItalic.pfb')
    faceName = 'Frutiger-BoldItalic'
    if faceName not in registered:
        justFace = pdfmetrics.EmbeddedType1Face(afmFile, pfbFile)
        pdfmetrics.registerTypeFace(justFace)
        justFont = pdfmetrics.Font('Frutiger-BoldItalic', faceName, 'WinAnsiEncoding')
        pdfmetrics.registerFont(justFont)

    afmFile = os.path.join(folder, 'Frutiger-Roman.afm')
    pfbFile = os.path.join(folder, 'Frutiger-Roman.pfb')
    faceName = 'Frutiger-Roman'
    if faceName not in registered:
        justFace = pdfmetrics.EmbeddedType1Face(afmFile, pfbFile)
        pdfmetrics.registerTypeFace(justFace)
        justFont = pdfmetrics.Font(faceName, faceName, 'WinAnsiEncoding')
        pdfmetrics.registerFont(justFont)

    p = ParagraphStyle('name', None)
    p.fontName = 'Frutiger-BoldItalic'
    p.fontSize = 36
    p.leading = 9
    p.alignment = TA_CENTER
    p.textColor = HexColor(0x000000)
    stylesheet['name'] = p

    p = ParagraphStyle('course', None)
    p.fontName = 'Frutiger-BoldItalic'
    p.fontSize = 28
    p.leading = 9
    p.alignment = TA_CENTER
    p.textColor = HexColor(0x000000)
    stylesheet['course'] = p

    p = ParagraphStyle('date', None)
    p.fontName = 'Frutiger-Roman'
    p.fontSize = 10
    p.leading = 9
    p.alignment = TA_CENTER
    p.textColor = HexColor(0x000000)
    stylesheet['date'] = p

    return stylesheet
#}}}
#{{{ HarrisCertificate_1up
def HarrisCertificate_1up(request):
    # Create output filenames
    timestamp = str(time()).replace('.','')
    pdf_file = "%s/previews/%s.pdf" % (settings.MEDIA_ROOT, timestamp)
    img_file = "%s/previews/%s.gif" % (settings.MEDIA_ROOT, timestamp)

    # Set some document specifics
    pagesize = (inch*11, inch*8.5) # width, height. Measured at 72dpi, so this is 792x612
    bg_image = "%s/vardata_images/HarrisCertificate_bg_1up.tif" % settings.MEDIA_ROOT
    fonts = harris_stylesheet()

    # Get the info that the user entered. These fields should match what's in the model.
    form_data = request.session.get('form_data', None)
    name = form_data['name']
    course = form_data['course']
    date = form_data['date']
    instructor = form_data['instructor']

    # Format the lines and add them to the document
    name_line = []
    name_line.append(Paragraph(name, fonts['name']))
    course_line = []
    course_line.append(Paragraph(course, fonts['course']))
    date_line = []
    date_line.append(Paragraph(date, fonts['date']))

    # Sig image files are 3" x 0.75" at 300dpi, transparent GIFs
    if instructor == 'Robert Amoroso':
        img = "%s/vardata_images/harris_sigs/robert_a.gif" % settings.MEDIA_ROOT
    elif instructor == 'David Armstrong':
        img = "%s/vardata_images/harris_sigs/david_a.gif" % settings.MEDIA_ROOT
    elif instructor == 'Jay Burdsal':
        img = "%s/vardata_images/harris_sigs/jay_b.gif" % settings.MEDIA_ROOT
    elif instructor == 'GC': #### TODO ####
        img = "%s/vardata_images/harris_sigs/gc.gif" % settings.MEDIA_ROOT
    elif instructor == 'Connie C Gordon':
        img = "%s/vardata_images/harris_sigs/connie_g.gif" % settings.MEDIA_ROOT
    elif instructor == 'Geoff Howells':
        img = "%s/vardata_images/harris_sigs/geoff_h.gif" % settings.MEDIA_ROOT
    elif instructor == 'Harry Johnson':
        img = "%s/vardata_images/harris_sigs/harry_j.gif" % settings.MEDIA_ROOT
    elif instructor == 'David LaFleche':
        img = "%s/vardata_images/harris_sigs/david_l.gif" % settings.MEDIA_ROOT
    elif instructor == 'Manuel Minut':
        img = "%s/vardata_images/harris_sigs/manuel_m.gif" % settings.MEDIA_ROOT
    elif instructor == 'Yamunesh Rastogi':
        img = "%s/vardata_images/harris_sigs/yamunesh_r.gif" % settings.MEDIA_ROOT
    elif instructor == 'Kevin Shaw':
        img = "%s/vardata_images/harris_sigs/kevin_s.gif" % settings.MEDIA_ROOT
    elif instructor == 'Mark Trevena':
        img = "%s/vardata_images/harris_sigs/mark_t.gif" % settings.MEDIA_ROOT
    else:
        img = ''
    inst_line = "Instructor &#8212; %s" % instructor
    sig = []
    sig.append(Image(img, width=3*inch, height=0.75*inch))
    sig.append(Paragraph(inst_line, fonts['date']))

    c = canvas.Canvas(filename=pdf_file, pagesize=pagesize, pageCompression=1)
    c.drawImage(bg_image, 0, 0, width=792, height=612, mask=None)
    f = Frame(0, 0, 11*inch, 8.5*inch, showBoundary=0, rightPadding=0, topPadding=4.15*inch)
    f.addFromList(name_line,c)
    f = Frame(0, 0, 11*inch, 8.5*inch, showBoundary=0, rightPadding=0, topPadding=5.05*inch)
    f.addFromList(course_line,c)
    f = Frame(0, 0, 11*inch, 8.5*inch, showBoundary=0, rightPadding=0, topPadding=6*inch)
    f.addFromList(date_line,c)
    f = Frame(522, 36, 3*inch, 1.18*inch, showBoundary=0, rightPadding=0, topPadding=0) # origin of 522 means 7.25" from left, 36 is 0.5" from bottom
    f.addFromList(sig,c)


    # Close the PDF object cleanly
    c.showPage()
    c.save()

    # Create a preview image
    command = 'convert -page 792x612 %s %s' % (pdf_file, img_file)
    os.system(command)

    # Set session variable so we can pass filename back to preview
    request.session['filename_prefix'] = timestamp

    return HttpResponseRedirect(reverse('orders:vardata_preview'))
#}}}
#{{{ HarrisCertificate_print
def HarrisCertificate_print(request, ordereditem_id):
    ordereditem = OrderedItem.objects.get(pk=ordereditem_id)

    # Create output filename
    filename = "%s-%s.pdf" % (ordereditem.order.name, ordereditem_id)

    # Set some document specifics
    response = HttpResponse(mimetype='application/pdf')
    response['Content-Disposition'] = 'attachment; filename=%s' % filename # force save as dialog
    pagesize = (inch*11.833, inch*9.333) # width, height. Measured at 72dpi, so this is 852x672
    bg_image = "%s/vardata_images/HarrisCertificate_bg_print.tif" % settings.MEDIA_ROOT
    fonts = harris_stylesheet()

    # Get the info stored in the DB. Refer to the model for the field names
    data = HarrisCertificate.objects.get(ordereditem = ordereditem_id)
    name = data.name
    course = data.course
    date = data.date
    instructor = data.instructor

    # Format the lines and add them to the document
    name_line = []
    name_line.append(Paragraph(name, fonts['name']))
    course_line = []
    course_line.append(Paragraph(course, fonts['course']))
    date_line = []
    date_line.append(Paragraph(date, fonts['date']))

    # Sig image files are 3" x 0.75" at 300dpi, transparent GIFs
    if instructor == 'Robert Amoroso':
        img = "%s/vardata_images/harris_sigs/robert_a.gif" % settings.MEDIA_ROOT
    elif instructor == 'David Armstrong':
        img = "%s/vardata_images/harris_sigs/david_a.gif" % settings.MEDIA_ROOT
    elif instructor == 'Jay Burdsal':
        img = "%s/vardata_images/harris_sigs/jay_b.gif" % settings.MEDIA_ROOT
    elif instructor == 'GC': #### TODO ####
        img = "%s/vardata_images/harris_sigs/gc.gif" % settings.MEDIA_ROOT
    elif instructor == 'Connie C Gordon':
        img = "%s/vardata_images/harris_sigs/connie_g.gif" % settings.MEDIA_ROOT
    elif instructor == 'Geoff Howells':
        img = "%s/vardata_images/harris_sigs/geoff_h.gif" % settings.MEDIA_ROOT
    elif instructor == 'Harry Johnson':
        img = "%s/vardata_images/harris_sigs/harry_j.gif" % settings.MEDIA_ROOT
    elif instructor == 'David LaFleche':
        img = "%s/vardata_images/harris_sigs/david_l.gif" % settings.MEDIA_ROOT
    elif instructor == 'Manuel Minut':
        img = "%s/vardata_images/harris_sigs/manuel_m.gif" % settings.MEDIA_ROOT
    elif instructor == 'Yamunesh Rastogi':
        img = "%s/vardata_images/harris_sigs/yamunesh_r.gif" % settings.MEDIA_ROOT
    elif instructor == 'Kevin Shaw':
        img = "%s/vardata_images/harris_sigs/kevin_s.gif" % settings.MEDIA_ROOT
    elif instructor == 'Mark Trevena':
        img = "%s/vardata_images/harris_sigs/mark_t.gif" % settings.MEDIA_ROOT
    else:
        img = ''
    inst_line = "Instructor &#8212; %s" % instructor
    sig = []
    sig.append(Image(img, width=3*inch, height=0.75*inch))
    sig.append(Paragraph(inst_line, fonts['date']))

    c = canvas.Canvas(response, pagesize=pagesize, pageCompression=1)
    c.drawImage(bg_image, 0, 0, width=852, height=672, mask=None)
    f = Frame(0, 0, 11.833*inch, 9.333*inch, showBoundary=0, rightPadding=0, topPadding=4.57*inch)
    f.addFromList(name_line,c)
    f = Frame(0, 0, 11.833*inch, 9.333*inch, showBoundary=0, rightPadding=0, topPadding=5.47*inch)
    f.addFromList(course_line,c)
    f = Frame(0, 0, 11.833*inch, 9.333*inch, showBoundary=0, rightPadding=0, topPadding=6.42*inch)
    f.addFromList(date_line,c)
    f = Frame(552, 66, 3*inch, 1.18*inch, showBoundary=0, rightPadding=0, topPadding=0)
    f.addFromList(sig,c)


    # Close the PDF object cleanly
    c.showPage()
    c.save()

    return response
#}}}

# Digital Rapids
#{{{ digitalrapids_stylesheet
def digitalrapids_stylesheet():
    stylesheet = {}

    # Register all required fonts
    folder = settings.FONT_DIR # from settings.py
    registered = pdfmetrics.getRegisteredFontNames()

    afmFile = os.path.join(folder, 'Myriad-Roman.afm')
    pfbFile = os.path.join(folder, 'Myriad-Roman.pfb')
    faceName = 'Myriad-Roman'
    if faceName not in registered:
        justFace = pdfmetrics.EmbeddedType1Face(afmFile, pfbFile)
        pdfmetrics.registerTypeFace(justFace)
        justFont = pdfmetrics.Font(faceName, faceName, 'WinAnsiEncoding')
        pdfmetrics.registerFont(justFont)

    afmFile = os.path.join(folder, 'Myriad-Bold.afm')
    pfbFile = os.path.join(folder, 'Myriad-Bold.pfb')
    faceName = 'Myriad-Bold'
    if faceName not in registered:
        justFace = pdfmetrics.EmbeddedType1Face(afmFile, pfbFile)
        pdfmetrics.registerTypeFace(justFace)
        justFont = pdfmetrics.Font(faceName, faceName, 'WinAnsiEncoding')
        pdfmetrics.registerFont(justFont)

    afmFile = os.path.join(folder, 'Tahoma-Bold.afm')
    pfbFile = os.path.join(folder, 'Tahoma-Bold.pfb')
    faceName = 'Tahoma-Bold'
    if faceName not in registered:
        justFace = pdfmetrics.EmbeddedType1Face(afmFile, pfbFile)
        pdfmetrics.registerTypeFace(justFace)
        justFont = pdfmetrics.Font(faceName, faceName, 'WinAnsiEncoding')
        pdfmetrics.registerFont(justFont)

    afmFile = os.path.join(folder, 'Tahoma.afm')
    pfbFile = os.path.join(folder, 'Tahoma.pfb')
    faceName = 'Tahoma'
    if faceName not in registered:
        justFace = pdfmetrics.EmbeddedType1Face(afmFile, pfbFile)
        pdfmetrics.registerTypeFace(justFace)
        justFont = pdfmetrics.Font(faceName, faceName, 'WinAnsiEncoding')
        pdfmetrics.registerFont(justFont)

    p = ParagraphStyle('name', None)
    p.fontName = 'Tahoma-Bold'
    p.fontSize = 8.5
    p.leading = 10
    p.alignment = TA_LEFT
    p.textColor = HexColor(0x000000)
    stylesheet['name'] = p

    p = ParagraphStyle('title', None)
    p.fontName = 'Tahoma'
    p.fontSize = 8.5
    p.leading = 10
    p.alignment = TA_LEFT
    p.textColor = HexColor(0x000000)
    stylesheet['title'] = p

    p = ParagraphStyle('addr', None)
    p.fontName = 'Myriad-Roman'
    p.fontSize = 8.5
    p.leading = 10
    p.alignment = TA_LEFT
    p.textColor = HexColor(0xffffff)
    stylesheet['addr'] = p

    p = ParagraphStyle('url', None)
    p.fontName = 'Myriad-Bold'
    p.fontSize = 8.5
    p.leading = 10
    p.alignment = TA_LEFT
    p.textColor = HexColor(0xffffff)
    stylesheet['url'] = p

    p = ParagraphStyle('blank_line', None)
    p.spaceAfter = 10 # same as leading of paragraph
    stylesheet['blank_line'] = p

    return stylesheet
#}}}
#{{{ DrAsiaPacificBc_1up
def DrAsiaPacificBc_1up(request):
    # Create output filenames
    timestamp = str(time()).replace('.','')
    pdf_file = "%s/previews/%s.pdf" % (settings.MEDIA_ROOT, timestamp)
    img_file = "%s/previews/%s.gif" % (settings.MEDIA_ROOT, timestamp)

    # Set some document specifics
    pagesize = (inch*3.5, inch*2) # width, height. Measured at 72dpi, so this is 252x144
    bg_image = "%s/vardata_images/DrBc_bg_1up.tif" % settings.MEDIA_ROOT
    fonts = digitalrapids_stylesheet()

    # Get the info that the user entered. These fields should match what's in the model.
    form_data = escape(request.session.get('form_data', None))
    name = form_data['name']
    title1 = form_data['title1']
    title2 = form_data['title2']
    email = form_data['email']
    email_line = '%s@digitalrapids.com' % email
    mobile = form_data['mobile']
    mobile_line = 'M: +61 %s' % mobile

    # Format the lines and add them to the document
    nameblock = []
    if not title2:
        nameblock.append(Paragraph("", fonts['blank_line']))
    nameblock.append(Paragraph(name, fonts['name']))
    nameblock.append(Paragraph(title1, fonts['title']))
    if title2:
        nameblock.append(Paragraph(title2, fonts['title']))
    nameblock.append(Paragraph("", fonts['blank_line']))
    nameblock.append(Paragraph(email_line, fonts['title']))
    addrblock = []
    if not mobile:
        addrblock.append(Paragraph("", fonts['blank_line']))
    addrblock.append(Paragraph("16 Marie Dodd Crescent", fonts['addr']))
    addrblock.append(Paragraph("Blakehurst", fonts['addr']))
    addrblock.append(Paragraph("NSW 2221", fonts['addr']))
    addrblock.append(Paragraph("Australia", fonts['addr']))
    addrblock.append(Paragraph("", fonts['blank_line']))
    addrblock.append(Paragraph("Tel: +61 2 9546 1300", fonts['addr']))
    if mobile:
        addrblock.append(Paragraph(mobile_line, fonts['addr']))
    addrblock.append(Paragraph("Fax: +61 2 9594 1773", fonts['addr']))
    addrblock.append(Paragraph("", fonts['blank_line']))
    addrblock.append(Paragraph("www.digitalrapids.com", fonts['url']))

    c = canvas.Canvas(filename=pdf_file, pagesize=pagesize, pageCompression=1)
    c.drawImage(bg_image, 0, 0, width=252, height=144, mask=None)
    f = Frame(0, 0, 3.5*inch, 2*inch, showBoundary=0, leftPadding=0.19*inch, topPadding=1.18*inch)
    f.addFromList(nameblock,c)
    f = Frame(0, 0, 3.5*inch, 2*inch, showBoundary=0, leftPadding=2.1*inch, topPadding=0.485*inch)
    f.addFromList(addrblock,c)

    # Close the PDF object cleanly
    c.showPage()
    c.save()

    # Create a preview image
    command = 'convert -page 252x144 %s %s' % (pdf_file, img_file)
    os.system(command)

    # Set session variable so we can pass filename back to preview
    request.session['filename_prefix'] = timestamp

    return HttpResponseRedirect(reverse('orders:vardata_preview'))
#}}}
#{{{ DrAsiaPacificBc_print
def DrAsiaPacificBc_print(request, ordereditem_id):
    ordereditem = OrderedItem.objects.get(pk=ordereditem_id)

    # Create output filenames
    filename = "%s-%s.pdf" % (ordereditem.order.name, ordereditem_id)

    # Set some document specifics
    response = HttpResponse(mimetype='application/pdf')
    response['Content-Disposition'] = 'attachment; filename=%s' % filename # force save as dialog
    pagesize = (inch*17, inch*11) # width, height. Measured at 72dpi, so this is 1224x792
    bg_image = "%s/vardata_images/DrBc_bg_print.tif" % settings.MEDIA_ROOT
    fonts = digitalrapids_stylesheet()

    # Get the info stored in the DB. Refer to the model for the field names
    data = DrAsiaPacificBc.objects.get(ordereditem = ordereditem_id)
    name = cgi.escape(data.name)
    title1 = cgi.escape(data.title1)
    title2 = cgi.escape(data.title2)
    email = data.email
    email_line = '%s@digitalrapids.com' % email
    mobile = data.mobile
    mobile_line = 'M: +61 %s' % mobile

    # Format the lines and add them to the document
    nameblock = []
    if title2 == "":
        nameblock.append(Paragraph("", fonts['blank_line']))
    nameblock.append(Paragraph(name, fonts['name']))
    nameblock.append(Paragraph(title1, fonts['title']))
    if title2:
        nameblock.append(Paragraph(title2, fonts['title']))
    nameblock.append(Paragraph("", fonts['blank_line']))
    nameblock.append(Paragraph(email_line, fonts['title']))
    if title2 == "":
        nameblock.append(Paragraph("", fonts['blank_line']))

    addrblock = []
    if mobile == "":
        addrblock.append(Paragraph("", fonts['blank_line']))
    addrblock.append(Paragraph("16 Marie Dodd Crescent", fonts['addr']))
    addrblock.append(Paragraph("Blakehurst", fonts['addr']))
    addrblock.append(Paragraph("NSW 2221", fonts['addr']))
    addrblock.append(Paragraph("Australia", fonts['addr']))
    addrblock.append(Paragraph("", fonts['blank_line']))
    addrblock.append(Paragraph("Tel: +61 2 9546 1300", fonts['addr']))
    if mobile:
        addrblock.append(Paragraph(mobile_line, fonts['addr']))
    addrblock.append(Paragraph("Fax: +61 2 9594 1773", fonts['addr']))
    addrblock.append(Paragraph("", fonts['blank_line']))
    addrblock.append(Paragraph("www.digitalrapids.com", fonts['url']))
    if mobile == "":
        addrblock.append(Paragraph("", fonts['blank_line']))

    c = canvas.Canvas(response, pagesize=pagesize, pageCompression=1)
    c.drawImage(bg_image, 0, 0, width=1224, height=792, mask=None)

    # The addFromList method of the Frame object takes in a list, but it is
    # destructive in that it *removes* items from that list (so it can flow
    # everything into the frame until there is nothing left to add). See
    # reportlab/platypus/frames.py. Unfortunately for us this means we can't
    # merely put a copy of the same name or address block in multiple places on
    # the page, because after the first pass there's nothing left to put in the
    # second card. So we need to make a big list that includes the number of
    # cards we need (eg 16 copies of the same block of text). This also means
    # we can't make all the frames the size of the document, overlap them, and
    # adjust the left and top padding (as we did with the 1up pdf), because
    # then there would be plenty of room for the second card to flow into the
    # space for the first card. So we make the frames just big enough (actually
    # only vertical space should matter) to fit the number of lines per block,
    # and position the frames themselves from the *bottom corner*. Whew.

    # name blocks
    names = []
    names.extend(16*nameblock)
    # f = Frame(from_left, from_bottom, width, height)
    f = Frame(0.69*inch, 0.89*inch, 2.1*inch, 0.7*inch, showBoundary=0, topPadding=0,rightPadding=0,bottomPadding=0,leftPadding=0)
    f.addFromList(names,c)
    f = Frame(0.69*inch, 3.39*inch, 2.1*inch, 0.7*inch, showBoundary=0, topPadding=0,rightPadding=0,bottomPadding=0,leftPadding=0)
    f.addFromList(names,c)
    f = Frame(0.69*inch, 5.89*inch, 2.1*inch, 0.7*inch, showBoundary=0, topPadding=0,rightPadding=0,bottomPadding=0,leftPadding=0)
    f.addFromList(names,c)
    f = Frame(0.69*inch, 8.39*inch, 2.1*inch, 0.7*inch, showBoundary=0, topPadding=0,rightPadding=0,bottomPadding=0,leftPadding=0)
    f.addFromList(names,c)
    f = Frame(4.83*inch, 0.89*inch, 2.1*inch, 0.7*inch, showBoundary=0, topPadding=0,rightPadding=0,bottomPadding=0,leftPadding=0)
    f.addFromList(names,c)
    f = Frame(4.83*inch, 3.39*inch, 2.1*inch, 0.7*inch, showBoundary=0, topPadding=0,rightPadding=0,bottomPadding=0,leftPadding=0)
    f.addFromList(names,c)
    f = Frame(4.83*inch, 5.89*inch, 2.1*inch, 0.7*inch, showBoundary=0, topPadding=0,rightPadding=0,bottomPadding=0,leftPadding=0)
    f.addFromList(names,c)
    f = Frame(4.83*inch, 8.39*inch, 2.1*inch, 0.7*inch, showBoundary=0, topPadding=0,rightPadding=0,bottomPadding=0,leftPadding=0)
    f.addFromList(names,c)
    f = Frame(9.16*inch, 0.89*inch, 2.1*inch, 0.7*inch, showBoundary=0, topPadding=0,rightPadding=0,bottomPadding=0,leftPadding=0)
    f.addFromList(names,c)
    f = Frame(9.16*inch, 3.39*inch, 2.1*inch, 0.7*inch, showBoundary=0, topPadding=0,rightPadding=0,bottomPadding=0,leftPadding=0)
    f.addFromList(names,c)
    f = Frame(9.16*inch, 5.89*inch, 2.1*inch, 0.7*inch, showBoundary=0, topPadding=0,rightPadding=0,bottomPadding=0,leftPadding=0)
    f.addFromList(names,c)
    f = Frame(9.16*inch, 8.39*inch, 2.1*inch, 0.7*inch, showBoundary=0, topPadding=0,rightPadding=0,bottomPadding=0,leftPadding=0)
    f.addFromList(names,c)
    f = Frame(13.3*inch, 0.89*inch, 2.1*inch, 0.7*inch, showBoundary=0, topPadding=0,rightPadding=0,bottomPadding=0,leftPadding=0)
    f.addFromList(names,c)
    f = Frame(13.3*inch, 3.39*inch, 2.1*inch, 0.7*inch, showBoundary=0, topPadding=0,rightPadding=0,bottomPadding=0,leftPadding=0)
    f.addFromList(names,c)
    f = Frame(13.3*inch, 5.89*inch, 2.1*inch, 0.7*inch, showBoundary=0, topPadding=0,rightPadding=0,bottomPadding=0,leftPadding=0)
    f.addFromList(names,c)
    f = Frame(13.3*inch, 8.39*inch, 2.1*inch, 0.7*inch, showBoundary=0, topPadding=0,rightPadding=0,bottomPadding=0,leftPadding=0)
    f.addFromList(names,c)

    # address blocks
    addrs = []
    addrs.extend(16*addrblock)
    f = Frame(2.61*inch, 0.89*inch, 1.4*inch, 1.4*inch, showBoundary=0, topPadding=0,rightPadding=0,bottomPadding=0,leftPadding=0)
    f.addFromList(addrs,c)
    f = Frame(2.61*inch, 3.39*inch, 1.4*inch, 1.4*inch, showBoundary=0, topPadding=0,rightPadding=0,bottomPadding=0,leftPadding=0)
    f.addFromList(addrs,c)
    f = Frame(2.61*inch, 5.89*inch, 1.4*inch, 1.4*inch, showBoundary=0, topPadding=0,rightPadding=0,bottomPadding=0,leftPadding=0)
    f.addFromList(addrs,c)
    f = Frame(2.61*inch, 8.39*inch, 1.4*inch, 1.4*inch, showBoundary=0, topPadding=0,rightPadding=0,bottomPadding=0,leftPadding=0)
    f.addFromList(addrs,c)
    f = Frame(6.75*inch, 0.89*inch, 1.4*inch, 1.4*inch, showBoundary=0, topPadding=0,rightPadding=0,bottomPadding=0,leftPadding=0)
    f.addFromList(addrs,c)
    f = Frame(6.75*inch, 3.39*inch, 1.4*inch, 1.4*inch, showBoundary=0, topPadding=0,rightPadding=0,bottomPadding=0,leftPadding=0)
    f.addFromList(addrs,c)
    f = Frame(6.75*inch, 5.89*inch, 1.4*inch, 1.4*inch, showBoundary=0, topPadding=0,rightPadding=0,bottomPadding=0,leftPadding=0)
    f.addFromList(addrs,c)
    f = Frame(6.75*inch, 8.39*inch, 1.4*inch, 1.4*inch, showBoundary=0, topPadding=0,rightPadding=0,bottomPadding=0,leftPadding=0)
    f.addFromList(addrs,c)
    f = Frame(11.09*inch, 0.89*inch, 1.4*inch, 1.4*inch, showBoundary=0, topPadding=0,rightPadding=0,bottomPadding=0,leftPadding=0)
    f.addFromList(addrs,c)
    f = Frame(11.09*inch, 3.39*inch, 1.4*inch, 1.4*inch, showBoundary=0, topPadding=0,rightPadding=0,bottomPadding=0,leftPadding=0)
    f.addFromList(addrs,c)
    f = Frame(11.09*inch, 5.89*inch, 1.4*inch, 1.4*inch, showBoundary=0, topPadding=0,rightPadding=0,bottomPadding=0,leftPadding=0)
    f.addFromList(addrs,c)
    f = Frame(11.09*inch, 8.39*inch, 1.4*inch, 1.4*inch, showBoundary=0, topPadding=0,rightPadding=0,bottomPadding=0,leftPadding=0)
    f.addFromList(addrs,c)
    f = Frame(15.22*inch, 0.89*inch, 1.4*inch, 1.4*inch, showBoundary=0, topPadding=0,rightPadding=0,bottomPadding=0,leftPadding=0)
    f.addFromList(addrs,c)
    f = Frame(15.22*inch, 3.39*inch, 1.4*inch, 1.4*inch, showBoundary=0, topPadding=0,rightPadding=0,bottomPadding=0,leftPadding=0)
    f.addFromList(addrs,c)
    f = Frame(15.22*inch, 5.89*inch, 1.4*inch, 1.4*inch, showBoundary=0, topPadding=0,rightPadding=0,bottomPadding=0,leftPadding=0)
    f.addFromList(addrs,c)
    f = Frame(15.22*inch, 8.39*inch, 1.4*inch, 1.4*inch, showBoundary=0, topPadding=0,rightPadding=0,bottomPadding=0,leftPadding=0)
    f.addFromList(addrs,c)

    # Close the PDF object cleanly
    c.showPage()
    c.save()

    return response
#}}}
#{{{ DrMarkhamBc_1up
def DrMarkhamBc_1up(request):
    # Create output filenames
    timestamp = str(time()).replace('.','')
    pdf_file = "%s/previews/%s.pdf" % (settings.MEDIA_ROOT, timestamp)
    img_file = "%s/previews/%s.gif" % (settings.MEDIA_ROOT, timestamp)

    # Set some document specifics
    pagesize = (inch*3.5, inch*2) # width, height. Measured at 72dpi, so this is 252x144
    bg_image = "%s/vardata_images/DrBc_bg_1up.tif" % settings.MEDIA_ROOT
    fonts = digitalrapids_stylesheet()

    # Get the info that the user entered. These fields should match what's in the model.
    form_data = escape(request.session.get('form_data', None))
    name = form_data['name']
    title1 = form_data['title1']
    title2 = form_data['title2']
    email = form_data['email']
    email_line = '%s@digitalrapids.com' % email
    extension = form_data['extension']
    tel_line = "Tel: 905-946-9666 ext. %s" % extension
    cell = form_data['cell']
    if cell:
        cell_parts = phone_parts(form_data['cell'])
        cell_line = 'Cell: %s-%s-%s' % (cell_parts[0], cell_parts[1], cell_parts[2])

    # Format the lines and add them to the document
    nameblock = []
    if not title2:
        nameblock.append(Paragraph("", fonts['blank_line']))
    nameblock.append(Paragraph(name, fonts['name']))
    nameblock.append(Paragraph(title1, fonts['title']))
    if title2:
        nameblock.append(Paragraph(title2, fonts['title']))
    nameblock.append(Paragraph("", fonts['blank_line']))
    nameblock.append(Paragraph(email_line, fonts['title']))
    addrblock = []
    if not cell:
        addrblock.append(Paragraph("", fonts['blank_line']))
    addrblock.append(Paragraph("90 Allstate Parkway", fonts['addr']))
    addrblock.append(Paragraph("Suite 700", fonts['addr']))
    addrblock.append(Paragraph("Markham, Ontario", fonts['addr']))
    addrblock.append(Paragraph("L3R 6H3", fonts['addr']))
    addrblock.append(Paragraph("", fonts['blank_line']))
    addrblock.append(Paragraph(tel_line, fonts['addr']))
    if cell:
        addrblock.append(Paragraph(cell_line, fonts['addr']))
    addrblock.append(Paragraph("Fax: 416-352-0716", fonts['addr']))
    addrblock.append(Paragraph("", fonts['blank_line']))
    addrblock.append(Paragraph("www.digitalrapids.com", fonts['url']))

    c = canvas.Canvas(filename=pdf_file, pagesize=pagesize, pageCompression=1)
    c.drawImage(bg_image, 0, 0, width=252, height=144, mask=None)
    f = Frame(0, 0, 3.5*inch, 2*inch, showBoundary=0, leftPadding=0.19*inch, topPadding=1.18*inch)
    f.addFromList(nameblock,c)
    f = Frame(0, 0, 3.5*inch, 2*inch, showBoundary=0, leftPadding=2.1*inch, topPadding=0.485*inch)
    f.addFromList(addrblock,c)

    # Close the PDF object cleanly
    c.showPage()
    c.save()

    # Create a preview image
    command = 'convert -page 252x144 %s %s' % (pdf_file, img_file)
    os.system(command)

    # Set session variable so we can pass filename back to preview
    request.session['filename_prefix'] = timestamp

    return HttpResponseRedirect(reverse('orders:vardata_preview'))
#}}}
#{{{ DrMarkhamBc_print
def DrMarkhamBc_print(request, ordereditem_id):
    ordereditem = OrderedItem.objects.get(pk=ordereditem_id)

    # Create output filenames
    filename = "%s-%s.pdf" % (ordereditem.order.name, ordereditem_id)

    # Set some document specifics
    response = HttpResponse(mimetype='application/pdf')
    response['Content-Disposition'] = 'attachment; filename=%s' % filename # force save as dialog
    pagesize = (inch*17, inch*11) # width, height. Measured at 72dpi, so this is 1224x792
    bg_image = "%s/vardata_images/DrBc_bg_print.tif" % settings.MEDIA_ROOT
    fonts = digitalrapids_stylesheet()

    # Get the info stored in the DB. Refer to the model for the field names
    data = DrMarkhamBc.objects.get(ordereditem = ordereditem_id)
    name = cgi.escape(data.name)
    title1 = cgi.escape(data.title1)
    title2 = cgi.escape(data.title2)
    email = data.email
    email_line = '%s@digitalrapids.com' % email
    extension = data.extension
    tel_line = "Tel: 905-946-9666 ext. %s" % extension
    cell = data.cell
    if cell:
        cell_parts = phone_parts(data.cell)
        cell_line = 'Cell: %s-%s-%s' % (cell_parts[0], cell_parts[1], cell_parts[2])

    # Format the lines and add them to the document
    nameblock = []
    if title2 == "":
        nameblock.append(Paragraph("", fonts['blank_line']))
    nameblock.append(Paragraph(name, fonts['name']))
    nameblock.append(Paragraph(title1, fonts['title']))
    if title2:
        nameblock.append(Paragraph(title2, fonts['title']))
    nameblock.append(Paragraph("", fonts['blank_line']))
    nameblock.append(Paragraph(email_line, fonts['title']))
    if title2 == "":
        nameblock.append(Paragraph("", fonts['blank_line']))

    addrblock = []
    if cell == "":
        addrblock.append(Paragraph("", fonts['blank_line']))
    addrblock.append(Paragraph("90 Allstate Parkway", fonts['addr']))
    addrblock.append(Paragraph("Suite 700", fonts['addr']))
    addrblock.append(Paragraph("Markham, Ontario", fonts['addr']))
    addrblock.append(Paragraph("L3R 6H3", fonts['addr']))
    addrblock.append(Paragraph("", fonts['blank_line']))
    addrblock.append(Paragraph(tel_line, fonts['addr']))
    if cell:
        addrblock.append(Paragraph(cell_line, fonts['addr']))
    addrblock.append(Paragraph("Fax: 416-352-0716", fonts['addr']))
    addrblock.append(Paragraph("", fonts['blank_line']))
    addrblock.append(Paragraph("www.digitalrapids.com", fonts['url']))
    if cell == "":
        addrblock.append(Paragraph("", fonts['blank_line']))

    c = canvas.Canvas(response, pagesize=pagesize, pageCompression=1)
    c.drawImage(bg_image, 0, 0, width=1224, height=792, mask=None)

    # name blocks
    names = []
    names.extend(16*nameblock)
    # f = Frame(from_left, from_bottom, width, height)
    f = Frame(0.69*inch, 0.89*inch, 2.1*inch, 0.7*inch, showBoundary=0, topPadding=0,rightPadding=0,bottomPadding=0,leftPadding=0)
    f.addFromList(names,c)
    f = Frame(0.69*inch, 3.39*inch, 2.1*inch, 0.7*inch, showBoundary=0, topPadding=0,rightPadding=0,bottomPadding=0,leftPadding=0)
    f.addFromList(names,c)
    f = Frame(0.69*inch, 5.89*inch, 2.1*inch, 0.7*inch, showBoundary=0, topPadding=0,rightPadding=0,bottomPadding=0,leftPadding=0)
    f.addFromList(names,c)
    f = Frame(0.69*inch, 8.39*inch, 2.1*inch, 0.7*inch, showBoundary=0, topPadding=0,rightPadding=0,bottomPadding=0,leftPadding=0)
    f.addFromList(names,c)
    f = Frame(4.83*inch, 0.89*inch, 2.1*inch, 0.7*inch, showBoundary=0, topPadding=0,rightPadding=0,bottomPadding=0,leftPadding=0)
    f.addFromList(names,c)
    f = Frame(4.83*inch, 3.39*inch, 2.1*inch, 0.7*inch, showBoundary=0, topPadding=0,rightPadding=0,bottomPadding=0,leftPadding=0)
    f.addFromList(names,c)
    f = Frame(4.83*inch, 5.89*inch, 2.1*inch, 0.7*inch, showBoundary=0, topPadding=0,rightPadding=0,bottomPadding=0,leftPadding=0)
    f.addFromList(names,c)
    f = Frame(4.83*inch, 8.39*inch, 2.1*inch, 0.7*inch, showBoundary=0, topPadding=0,rightPadding=0,bottomPadding=0,leftPadding=0)
    f.addFromList(names,c)
    f = Frame(9.16*inch, 0.89*inch, 2.1*inch, 0.7*inch, showBoundary=0, topPadding=0,rightPadding=0,bottomPadding=0,leftPadding=0)
    f.addFromList(names,c)
    f = Frame(9.16*inch, 3.39*inch, 2.1*inch, 0.7*inch, showBoundary=0, topPadding=0,rightPadding=0,bottomPadding=0,leftPadding=0)
    f.addFromList(names,c)
    f = Frame(9.16*inch, 5.89*inch, 2.1*inch, 0.7*inch, showBoundary=0, topPadding=0,rightPadding=0,bottomPadding=0,leftPadding=0)
    f.addFromList(names,c)
    f = Frame(9.16*inch, 8.39*inch, 2.1*inch, 0.7*inch, showBoundary=0, topPadding=0,rightPadding=0,bottomPadding=0,leftPadding=0)
    f.addFromList(names,c)
    f = Frame(13.3*inch, 0.89*inch, 2.1*inch, 0.7*inch, showBoundary=0, topPadding=0,rightPadding=0,bottomPadding=0,leftPadding=0)
    f.addFromList(names,c)
    f = Frame(13.3*inch, 3.39*inch, 2.1*inch, 0.7*inch, showBoundary=0, topPadding=0,rightPadding=0,bottomPadding=0,leftPadding=0)
    f.addFromList(names,c)
    f = Frame(13.3*inch, 5.89*inch, 2.1*inch, 0.7*inch, showBoundary=0, topPadding=0,rightPadding=0,bottomPadding=0,leftPadding=0)
    f.addFromList(names,c)
    f = Frame(13.3*inch, 8.39*inch, 2.1*inch, 0.7*inch, showBoundary=0, topPadding=0,rightPadding=0,bottomPadding=0,leftPadding=0)
    f.addFromList(names,c)

    # address blocks
    addrs = []
    addrs.extend(16*addrblock)
    f = Frame(2.61*inch, 0.89*inch, 1.4*inch, 1.397*inch, showBoundary=0, topPadding=0,rightPadding=0,bottomPadding=0,leftPadding=0)
    f.addFromList(addrs,c)
    f = Frame(2.61*inch, 3.39*inch, 1.4*inch, 1.397*inch, showBoundary=0, topPadding=0,rightPadding=0,bottomPadding=0,leftPadding=0)
    f.addFromList(addrs,c)
    f = Frame(2.61*inch, 5.89*inch, 1.4*inch, 1.397*inch, showBoundary=0, topPadding=0,rightPadding=0,bottomPadding=0,leftPadding=0)
    f.addFromList(addrs,c)
    f = Frame(2.61*inch, 8.39*inch, 1.4*inch, 1.397*inch, showBoundary=0, topPadding=0,rightPadding=0,bottomPadding=0,leftPadding=0)
    f.addFromList(addrs,c)
    f = Frame(6.75*inch, 0.89*inch, 1.4*inch, 1.397*inch, showBoundary=0, topPadding=0,rightPadding=0,bottomPadding=0,leftPadding=0)
    f.addFromList(addrs,c)
    f = Frame(6.75*inch, 3.39*inch, 1.4*inch, 1.397*inch, showBoundary=0, topPadding=0,rightPadding=0,bottomPadding=0,leftPadding=0)
    f.addFromList(addrs,c)
    f = Frame(6.75*inch, 5.89*inch, 1.4*inch, 1.397*inch, showBoundary=0, topPadding=0,rightPadding=0,bottomPadding=0,leftPadding=0)
    f.addFromList(addrs,c)
    f = Frame(6.75*inch, 8.39*inch, 1.4*inch, 1.397*inch, showBoundary=0, topPadding=0,rightPadding=0,bottomPadding=0,leftPadding=0)
    f.addFromList(addrs,c)
    f = Frame(11.09*inch, 0.89*inch, 1.4*inch, 1.397*inch, showBoundary=0, topPadding=0,rightPadding=0,bottomPadding=0,leftPadding=0)
    f.addFromList(addrs,c)
    f = Frame(11.09*inch, 3.39*inch, 1.4*inch, 1.397*inch, showBoundary=0, topPadding=0,rightPadding=0,bottomPadding=0,leftPadding=0)
    f.addFromList(addrs,c)
    f = Frame(11.09*inch, 5.89*inch, 1.4*inch, 1.397*inch, showBoundary=0, topPadding=0,rightPadding=0,bottomPadding=0,leftPadding=0)
    f.addFromList(addrs,c)
    f = Frame(11.09*inch, 8.39*inch, 1.4*inch, 1.397*inch, showBoundary=0, topPadding=0,rightPadding=0,bottomPadding=0,leftPadding=0)
    f.addFromList(addrs,c)
    f = Frame(15.22*inch, 0.89*inch, 1.4*inch, 1.397*inch, showBoundary=0, topPadding=0,rightPadding=0,bottomPadding=0,leftPadding=0)
    f.addFromList(addrs,c)
    f = Frame(15.22*inch, 3.39*inch, 1.4*inch, 1.397*inch, showBoundary=0, topPadding=0,rightPadding=0,bottomPadding=0,leftPadding=0)
    f.addFromList(addrs,c)
    f = Frame(15.22*inch, 5.89*inch, 1.4*inch, 1.397*inch, showBoundary=0, topPadding=0,rightPadding=0,bottomPadding=0,leftPadding=0)
    f.addFromList(addrs,c)
    f = Frame(15.22*inch, 8.39*inch, 1.4*inch, 1.397*inch, showBoundary=0, topPadding=0,rightPadding=0,bottomPadding=0,leftPadding=0)
    f.addFromList(addrs,c)

    # Close the PDF object cleanly
    c.showPage()
    c.save()

    return response
#}}}
#{{{ DrUkBc_1up
def DrUkBc_1up(request):
    # Create output filenames
    timestamp = str(time()).replace('.','')
    pdf_file = "%s/previews/%s.pdf" % (settings.MEDIA_ROOT, timestamp)
    img_file = "%s/previews/%s.gif" % (settings.MEDIA_ROOT, timestamp)

    # Set some document specifics
    pagesize = (inch*3.5, inch*2) # width, height. Measured at 72dpi, so this is 252x144
    bg_image = "%s/vardata_images/DrBc_bg_1up.tif" % settings.MEDIA_ROOT
    fonts = digitalrapids_stylesheet()

    # Get the info that the user entered. These fields should match what's in the model.
    form_data = escape(request.session.get('form_data', None))
    name = form_data['name']
    title1 = form_data['title1']
    title2 = form_data['title2']
    email = form_data['email']
    email_line = '%s@digitalrapids.com' % email
    mobile = form_data['mobile']
    mobile_line = 'M: %s' % mobile

    # Format the lines and add them to the document
    nameblock = []
    if not title2:
        nameblock.append(Paragraph("", fonts['blank_line']))
    nameblock.append(Paragraph(name, fonts['name']))
    nameblock.append(Paragraph(title1, fonts['title']))
    if title2:
        nameblock.append(Paragraph(title2, fonts['title']))
    nameblock.append(Paragraph("", fonts['blank_line']))
    nameblock.append(Paragraph(email_line, fonts['title']))
    addrblock = []
    if not mobile:
        addrblock.append(Paragraph("", fonts['blank_line']))
    addrblock.append(Paragraph("Passfield Business Centre", fonts['addr']))
    addrblock.append(Paragraph("Lynchborough Road", fonts['addr']))
    addrblock.append(Paragraph("Passfield, Hampshire", fonts['addr']))
    addrblock.append(Paragraph("UK GU30 7SB", fonts['addr']))
    addrblock.append(Paragraph("", fonts['blank_line']))
    addrblock.append(Paragraph("Tel: +44 (0) 1428 751 012", fonts['addr']))
    if mobile:
        addrblock.append(Paragraph(mobile_line, fonts['addr']))
    addrblock.append(Paragraph("Fax: +44 (0) 1428 751 013", fonts['addr']))
    addrblock.append(Paragraph("", fonts['blank_line']))
    addrblock.append(Paragraph("www.digitalrapids.com", fonts['url']))

    c = canvas.Canvas(filename=pdf_file, pagesize=pagesize, pageCompression=1)
    c.drawImage(bg_image, 0, 0, width=252, height=144, mask=None)
    f = Frame(0, 0, 3.5*inch, 2*inch, showBoundary=0, leftPadding=0.19*inch, topPadding=1.18*inch)
    f.addFromList(nameblock,c)
    f = Frame(0, 0, 3.5*inch, 2*inch, showBoundary=0, leftPadding=2.1*inch, topPadding=0.485*inch)
    f.addFromList(addrblock,c)

    # Close the PDF object cleanly
    c.showPage()
    c.save()

    # Create a preview image
    command = 'convert -page 252x144 %s %s' % (pdf_file, img_file)
    os.system(command)

    # Set session variable so we can pass filename back to preview
    request.session['filename_prefix'] = timestamp

    return HttpResponseRedirect(reverse('orders:vardata_preview'))
#}}}
#{{{ DrUkBc_print
def DrUkBc_print(request, ordereditem_id):
    ordereditem = OrderedItem.objects.get(pk=ordereditem_id)

    # Create output filenames
    filename = "%s-%s.pdf" % (ordereditem.order.name, ordereditem_id)

    # Set some document specifics
    response = HttpResponse(mimetype='application/pdf')
    response['Content-Disposition'] = 'attachment; filename=%s' % filename # force save as dialog
    pagesize = (inch*17, inch*11) # width, height. Measured at 72dpi, so this is 1224x792
    bg_image = "%s/vardata_images/DrBc_bg_print.tif" % settings.MEDIA_ROOT
    fonts = digitalrapids_stylesheet()

    # Get the info stored in the DB. Refer to the model for the field names
    data = DrUkBc.objects.get(ordereditem = ordereditem_id)
    name = cgi.escape(data.name)
    title1 = cgi.escape(data.title1)
    title2 = cgi.escape(data.title2)
    email = data.email
    email_line = '%s@digitalrapids.com' % email
    mobile = data.mobile
    mobile_line = 'M: %s' % mobile

    # Format the lines and add them to the document
    nameblock = []
    if title2 == "":
        nameblock.append(Paragraph("", fonts['blank_line']))
    nameblock.append(Paragraph(name, fonts['name']))
    nameblock.append(Paragraph(title1, fonts['title']))
    if title2:
        nameblock.append(Paragraph(title2, fonts['title']))
    nameblock.append(Paragraph("", fonts['blank_line']))
    nameblock.append(Paragraph(email_line, fonts['title']))
    if title2 == "":
        nameblock.append(Paragraph("", fonts['blank_line']))

    addrblock = []
    if mobile == "":
        addrblock.append(Paragraph("", fonts['blank_line']))
    addrblock.append(Paragraph("Passfield Business Centre", fonts['addr']))
    addrblock.append(Paragraph("Lynchborough Road", fonts['addr']))
    addrblock.append(Paragraph("Passfield, Hampshire", fonts['addr']))
    addrblock.append(Paragraph("UK GU30 7SB", fonts['addr']))
    addrblock.append(Paragraph("", fonts['blank_line']))
    addrblock.append(Paragraph("Tel: +44 (0) 1428 751 012", fonts['addr']))
    if mobile:
        addrblock.append(Paragraph(mobile_line, fonts['addr']))
    addrblock.append(Paragraph("Fax: +44 (0) 1428 751 013", fonts['addr']))
    addrblock.append(Paragraph("", fonts['blank_line']))
    addrblock.append(Paragraph("www.digitalrapids.com", fonts['url']))
    if mobile == "":
        addrblock.append(Paragraph("", fonts['blank_line']))

    c = canvas.Canvas(response, pagesize=pagesize, pageCompression=1)
    c.drawImage(bg_image, 0, 0, width=1224, height=792, mask=None)

    # name blocks
    names = []
    names.extend(16*nameblock)
    # f = Frame(from_left, from_bottom, width, height)
    f = Frame(0.69*inch, 0.89*inch, 2.1*inch, 0.7*inch, showBoundary=0, topPadding=0,rightPadding=0,bottomPadding=0,leftPadding=0)
    f.addFromList(names,c)
    f = Frame(0.69*inch, 3.39*inch, 2.1*inch, 0.7*inch, showBoundary=0, topPadding=0,rightPadding=0,bottomPadding=0,leftPadding=0)
    f.addFromList(names,c)
    f = Frame(0.69*inch, 5.89*inch, 2.1*inch, 0.7*inch, showBoundary=0, topPadding=0,rightPadding=0,bottomPadding=0,leftPadding=0)
    f.addFromList(names,c)
    f = Frame(0.69*inch, 8.39*inch, 2.1*inch, 0.7*inch, showBoundary=0, topPadding=0,rightPadding=0,bottomPadding=0,leftPadding=0)
    f.addFromList(names,c)
    f = Frame(4.83*inch, 0.89*inch, 2.1*inch, 0.7*inch, showBoundary=0, topPadding=0,rightPadding=0,bottomPadding=0,leftPadding=0)
    f.addFromList(names,c)
    f = Frame(4.83*inch, 3.39*inch, 2.1*inch, 0.7*inch, showBoundary=0, topPadding=0,rightPadding=0,bottomPadding=0,leftPadding=0)
    f.addFromList(names,c)
    f = Frame(4.83*inch, 5.89*inch, 2.1*inch, 0.7*inch, showBoundary=0, topPadding=0,rightPadding=0,bottomPadding=0,leftPadding=0)
    f.addFromList(names,c)
    f = Frame(4.83*inch, 8.39*inch, 2.1*inch, 0.7*inch, showBoundary=0, topPadding=0,rightPadding=0,bottomPadding=0,leftPadding=0)
    f.addFromList(names,c)
    f = Frame(9.16*inch, 0.89*inch, 2.1*inch, 0.7*inch, showBoundary=0, topPadding=0,rightPadding=0,bottomPadding=0,leftPadding=0)
    f.addFromList(names,c)
    f = Frame(9.16*inch, 3.39*inch, 2.1*inch, 0.7*inch, showBoundary=0, topPadding=0,rightPadding=0,bottomPadding=0,leftPadding=0)
    f.addFromList(names,c)
    f = Frame(9.16*inch, 5.89*inch, 2.1*inch, 0.7*inch, showBoundary=0, topPadding=0,rightPadding=0,bottomPadding=0,leftPadding=0)
    f.addFromList(names,c)
    f = Frame(9.16*inch, 8.39*inch, 2.1*inch, 0.7*inch, showBoundary=0, topPadding=0,rightPadding=0,bottomPadding=0,leftPadding=0)
    f.addFromList(names,c)
    f = Frame(13.3*inch, 0.89*inch, 2.1*inch, 0.7*inch, showBoundary=0, topPadding=0,rightPadding=0,bottomPadding=0,leftPadding=0)
    f.addFromList(names,c)
    f = Frame(13.3*inch, 3.39*inch, 2.1*inch, 0.7*inch, showBoundary=0, topPadding=0,rightPadding=0,bottomPadding=0,leftPadding=0)
    f.addFromList(names,c)
    f = Frame(13.3*inch, 5.89*inch, 2.1*inch, 0.7*inch, showBoundary=0, topPadding=0,rightPadding=0,bottomPadding=0,leftPadding=0)
    f.addFromList(names,c)
    f = Frame(13.3*inch, 8.39*inch, 2.1*inch, 0.7*inch, showBoundary=0, topPadding=0,rightPadding=0,bottomPadding=0,leftPadding=0)
    f.addFromList(names,c)

    # address blocks
    addrs = []
    addrs.extend(16*addrblock)
    f = Frame(2.61*inch, 0.89*inch, 1.4*inch, 1.397*inch, showBoundary=0, topPadding=0,rightPadding=0,bottomPadding=0,leftPadding=0)
    f.addFromList(addrs,c)
    f = Frame(2.61*inch, 3.39*inch, 1.4*inch, 1.397*inch, showBoundary=0, topPadding=0,rightPadding=0,bottomPadding=0,leftPadding=0)
    f.addFromList(addrs,c)
    f = Frame(2.61*inch, 5.89*inch, 1.4*inch, 1.397*inch, showBoundary=0, topPadding=0,rightPadding=0,bottomPadding=0,leftPadding=0)
    f.addFromList(addrs,c)
    f = Frame(2.61*inch, 8.39*inch, 1.4*inch, 1.397*inch, showBoundary=0, topPadding=0,rightPadding=0,bottomPadding=0,leftPadding=0)
    f.addFromList(addrs,c)
    f = Frame(6.75*inch, 0.89*inch, 1.4*inch, 1.397*inch, showBoundary=0, topPadding=0,rightPadding=0,bottomPadding=0,leftPadding=0)
    f.addFromList(addrs,c)
    f = Frame(6.75*inch, 3.39*inch, 1.4*inch, 1.397*inch, showBoundary=0, topPadding=0,rightPadding=0,bottomPadding=0,leftPadding=0)
    f.addFromList(addrs,c)
    f = Frame(6.75*inch, 5.89*inch, 1.4*inch, 1.397*inch, showBoundary=0, topPadding=0,rightPadding=0,bottomPadding=0,leftPadding=0)
    f.addFromList(addrs,c)
    f = Frame(6.75*inch, 8.39*inch, 1.4*inch, 1.397*inch, showBoundary=0, topPadding=0,rightPadding=0,bottomPadding=0,leftPadding=0)
    f.addFromList(addrs,c)
    f = Frame(11.09*inch, 0.89*inch, 1.4*inch, 1.397*inch, showBoundary=0, topPadding=0,rightPadding=0,bottomPadding=0,leftPadding=0)
    f.addFromList(addrs,c)
    f = Frame(11.09*inch, 3.39*inch, 1.4*inch, 1.397*inch, showBoundary=0, topPadding=0,rightPadding=0,bottomPadding=0,leftPadding=0)
    f.addFromList(addrs,c)
    f = Frame(11.09*inch, 5.89*inch, 1.4*inch, 1.397*inch, showBoundary=0, topPadding=0,rightPadding=0,bottomPadding=0,leftPadding=0)
    f.addFromList(addrs,c)
    f = Frame(11.09*inch, 8.39*inch, 1.4*inch, 1.397*inch, showBoundary=0, topPadding=0,rightPadding=0,bottomPadding=0,leftPadding=0)
    f.addFromList(addrs,c)
    f = Frame(15.22*inch, 0.89*inch, 1.4*inch, 1.397*inch, showBoundary=0, topPadding=0,rightPadding=0,bottomPadding=0,leftPadding=0)
    f.addFromList(addrs,c)
    f = Frame(15.22*inch, 3.39*inch, 1.4*inch, 1.397*inch, showBoundary=0, topPadding=0,rightPadding=0,bottomPadding=0,leftPadding=0)
    f.addFromList(addrs,c)
    f = Frame(15.22*inch, 5.89*inch, 1.4*inch, 1.397*inch, showBoundary=0, topPadding=0,rightPadding=0,bottomPadding=0,leftPadding=0)
    f.addFromList(addrs,c)
    f = Frame(15.22*inch, 8.39*inch, 1.4*inch, 1.397*inch, showBoundary=0, topPadding=0,rightPadding=0,bottomPadding=0,leftPadding=0)
    f.addFromList(addrs,c)

    # Close the PDF object cleanly
    c.showPage()
    c.save()

    return response
#}}}
#{{{ DrRemoteBc_1up
def DrRemoteBc_1up(request):
    # Create output filenames
    timestamp = str(time()).replace('.','')
    pdf_file = "%s/previews/%s.pdf" % (settings.MEDIA_ROOT, timestamp)
    img_file = "%s/previews/%s.gif" % (settings.MEDIA_ROOT, timestamp)

    # Set some document specifics
    pagesize = (inch*3.5, inch*2) # width, height. Measured at 72dpi, so this is 252x144
    bg_image = "%s/vardata_images/DrBc_bg_1up.tif" % settings.MEDIA_ROOT
    fonts = digitalrapids_stylesheet()

    # Get the info that the user entered. These fields should match what's in the model.
    form_data = escape(request.session.get('form_data', None))
    name = form_data['name']
    title1 = form_data['title1']
    title2 = form_data['title2']
    email = form_data['email']
    email_line = '%s@digitalrapids.com' % email
    city = form_data['city']
    state = form_data['state']
    city_line = "%s, %s" % (city, state)
    tel_parts = phone_parts(form_data['tel'])
    tel_line = "Tel: %s-%s-%s" % (tel_parts[0], tel_parts[1], tel_parts[2])
    cell = form_data['cell']
    if cell:
        cell_parts = phone_parts(form_data['cell'])
        cell_line = 'Cell: %s-%s-%s' % (cell_parts[0], cell_parts[1], cell_parts[2])

    # Format the lines and add them to the document
    nameblock = []
    if not title2:
        nameblock.append(Paragraph("", fonts['blank_line']))
    nameblock.append(Paragraph(name, fonts['name']))
    nameblock.append(Paragraph(title1, fonts['title']))
    if title2:
        nameblock.append(Paragraph(title2, fonts['title']))
    nameblock.append(Paragraph("", fonts['blank_line']))
    nameblock.append(Paragraph(email_line, fonts['title']))
    addrblock = []
    if not cell:
        addrblock.append(Paragraph("", fonts['blank_line']))
    addrblock.append(Paragraph("Digital Rapids", fonts['addr']))
    addrblock.append(Paragraph(city_line, fonts['addr']))
    addrblock.append(Paragraph(tel_line, fonts['addr']))
    if cell:
        addrblock.append(Paragraph(cell_line, fonts['addr']))
    addrblock.append(Paragraph("", fonts['blank_line']))
    addrblock.append(Paragraph("Head Office", fonts['addr']))
    addrblock.append(Paragraph("90 Allstate Parkway", fonts['addr']))
    addrblock.append(Paragraph("Suite 700", fonts['addr']))
    addrblock.append(Paragraph("Markham, Ontario", fonts['addr']))
    addrblock.append(Paragraph("Canada L3R 6H3", fonts['addr']))
    addrblock.append(Paragraph("", fonts['blank_line']))
    addrblock.append(Paragraph("www.digitalrapids.com", fonts['url']))

    c = canvas.Canvas(filename=pdf_file, pagesize=pagesize, pageCompression=1)
    c.drawImage(bg_image, 0, 0, width=252, height=144, mask=None)
    f = Frame(0, 0, 3.5*inch, 2*inch, showBoundary=0, leftPadding=0.19*inch, topPadding=1.18*inch)
    f.addFromList(nameblock,c)
    f = Frame(0, 0, 3.5*inch, 2*inch, showBoundary=0, leftPadding=2.1*inch, topPadding=0.19*inch)
    f.addFromList(addrblock,c)

    # Close the PDF object cleanly
    c.showPage()
    c.save()

    # Create a preview image
    command = 'convert -page 252x144 %s %s' % (pdf_file, img_file)
    os.system(command)

    # Set session variable so we can pass filename back to preview
    request.session['filename_prefix'] = timestamp

    return HttpResponseRedirect(reverse('orders:vardata_preview'))
#}}}
#{{{ DrRemoteBc_print
def DrRemoteBc_print(request, ordereditem_id):
    ordereditem = OrderedItem.objects.get(pk=ordereditem_id)

    # Create output filenames
    filename = "%s-%s.pdf" % (ordereditem.order.name, ordereditem_id)

    # Set some document specifics
    response = HttpResponse(mimetype='application/pdf')
    response['Content-Disposition'] = 'attachment; filename=%s' % filename # force save as dialog
    pagesize = (inch*17, inch*11) # width, height. Measured at 72dpi, so this is 1224x792
    bg_image = "%s/vardata_images/DrBc_bg_print.tif" % settings.MEDIA_ROOT
    fonts = digitalrapids_stylesheet()

    # Get the info stored in the DB. Refer to the model for the field names
    data = DrRemoteBc.objects.get(ordereditem = ordereditem_id)
    name = cgi.escape(data.name)
    title1 = cgi.escape(data.title1)
    title2 = cgi.escape(data.title2)
    email = data.email
    email_line = '%s@digitalrapids.com' % email
    city = data.city
    state = data.state
    city_line = "%s, %s" % (city, state)
    tel_parts = phone_parts(data.tel)
    tel_line = "Tel: %s-%s-%s" % (tel_parts[0], tel_parts[1], tel_parts[2])
    cell = data.cell
    if cell:
        cell_parts = phone_parts(data.cell)
        cell_line = 'Cell: %s-%s-%s' % (cell_parts[0], cell_parts[1], cell_parts[2])

    # Format the lines and add them to the document
    nameblock = []
    if title2 == "":
        nameblock.append(Paragraph("", fonts['blank_line']))
    nameblock.append(Paragraph(name, fonts['name']))
    nameblock.append(Paragraph(title1, fonts['title']))
    if title2:
        nameblock.append(Paragraph(title2, fonts['title']))
    nameblock.append(Paragraph("", fonts['blank_line']))
    nameblock.append(Paragraph(email_line, fonts['title']))
    if title2 == "":
        nameblock.append(Paragraph("", fonts['blank_line']))

    addrblock = []
    if cell == "":
        addrblock.append(Paragraph("", fonts['blank_line']))
    addrblock.append(Paragraph("Digital Rapids", fonts['addr']))
    addrblock.append(Paragraph(city_line, fonts['addr']))
    addrblock.append(Paragraph(tel_line, fonts['addr']))
    if cell:
        addrblock.append(Paragraph(cell_line, fonts['addr']))
    addrblock.append(Paragraph("", fonts['blank_line']))
    addrblock.append(Paragraph("Head Office", fonts['addr']))
    addrblock.append(Paragraph("90 Allstate Parkway", fonts['addr']))
    addrblock.append(Paragraph("Suite 700", fonts['addr']))
    addrblock.append(Paragraph("Markham, Ontario", fonts['addr']))
    addrblock.append(Paragraph("Canada L3R 6H3", fonts['addr']))
    addrblock.append(Paragraph("", fonts['blank_line']))
    addrblock.append(Paragraph("www.digitalrapids.com", fonts['url']))
    if cell == "":
        addrblock.append(Paragraph("", fonts['blank_line']))

    c = canvas.Canvas(response, pagesize=pagesize, pageCompression=1)
    c.drawImage(bg_image, 0, 0, width=1224, height=792, mask=None)

    # name blocks
    names = []
    names.extend(16*nameblock)
    # f = Frame(from_left, from_bottom, width, height)
    f = Frame(0.69*inch, 0.89*inch, 2.1*inch, 0.7*inch, showBoundary=0, topPadding=0,rightPadding=0,bottomPadding=0,leftPadding=0)
    f.addFromList(names,c)
    f = Frame(0.69*inch, 3.39*inch, 2.1*inch, 0.7*inch, showBoundary=0, topPadding=0,rightPadding=0,bottomPadding=0,leftPadding=0)
    f.addFromList(names,c)
    f = Frame(0.69*inch, 5.89*inch, 2.1*inch, 0.7*inch, showBoundary=0, topPadding=0,rightPadding=0,bottomPadding=0,leftPadding=0)
    f.addFromList(names,c)
    f = Frame(0.69*inch, 8.39*inch, 2.1*inch, 0.7*inch, showBoundary=0, topPadding=0,rightPadding=0,bottomPadding=0,leftPadding=0)
    f.addFromList(names,c)
    f = Frame(4.83*inch, 0.89*inch, 2.1*inch, 0.7*inch, showBoundary=0, topPadding=0,rightPadding=0,bottomPadding=0,leftPadding=0)
    f.addFromList(names,c)
    f = Frame(4.83*inch, 3.39*inch, 2.1*inch, 0.7*inch, showBoundary=0, topPadding=0,rightPadding=0,bottomPadding=0,leftPadding=0)
    f.addFromList(names,c)
    f = Frame(4.83*inch, 5.89*inch, 2.1*inch, 0.7*inch, showBoundary=0, topPadding=0,rightPadding=0,bottomPadding=0,leftPadding=0)
    f.addFromList(names,c)
    f = Frame(4.83*inch, 8.39*inch, 2.1*inch, 0.7*inch, showBoundary=0, topPadding=0,rightPadding=0,bottomPadding=0,leftPadding=0)
    f.addFromList(names,c)
    f = Frame(9.16*inch, 0.89*inch, 2.1*inch, 0.7*inch, showBoundary=0, topPadding=0,rightPadding=0,bottomPadding=0,leftPadding=0)
    f.addFromList(names,c)
    f = Frame(9.16*inch, 3.39*inch, 2.1*inch, 0.7*inch, showBoundary=0, topPadding=0,rightPadding=0,bottomPadding=0,leftPadding=0)
    f.addFromList(names,c)
    f = Frame(9.16*inch, 5.89*inch, 2.1*inch, 0.7*inch, showBoundary=0, topPadding=0,rightPadding=0,bottomPadding=0,leftPadding=0)
    f.addFromList(names,c)
    f = Frame(9.16*inch, 8.39*inch, 2.1*inch, 0.7*inch, showBoundary=0, topPadding=0,rightPadding=0,bottomPadding=0,leftPadding=0)
    f.addFromList(names,c)
    f = Frame(13.3*inch, 0.89*inch, 2.1*inch, 0.7*inch, showBoundary=0, topPadding=0,rightPadding=0,bottomPadding=0,leftPadding=0)
    f.addFromList(names,c)
    f = Frame(13.3*inch, 3.39*inch, 2.1*inch, 0.7*inch, showBoundary=0, topPadding=0,rightPadding=0,bottomPadding=0,leftPadding=0)
    f.addFromList(names,c)
    f = Frame(13.3*inch, 5.89*inch, 2.1*inch, 0.7*inch, showBoundary=0, topPadding=0,rightPadding=0,bottomPadding=0,leftPadding=0)
    f.addFromList(names,c)
    f = Frame(13.3*inch, 8.39*inch, 2.1*inch, 0.7*inch, showBoundary=0, topPadding=0,rightPadding=0,bottomPadding=0,leftPadding=0)
    f.addFromList(names,c)

    # address blocks
    addrs = []
    addrs.extend(16*addrblock)
    f = Frame(2.61*inch, 0.89*inch, 1.4*inch, 1.673*inch, showBoundary=0, topPadding=0,rightPadding=0,bottomPadding=0,leftPadding=0)
    f.addFromList(addrs,c)
    f = Frame(2.61*inch, 3.39*inch, 1.4*inch, 1.673*inch, showBoundary=0, topPadding=0,rightPadding=0,bottomPadding=0,leftPadding=0)
    f.addFromList(addrs,c)
    f = Frame(2.61*inch, 5.89*inch, 1.4*inch, 1.673*inch, showBoundary=0, topPadding=0,rightPadding=0,bottomPadding=0,leftPadding=0)
    f.addFromList(addrs,c)
    f = Frame(2.61*inch, 8.39*inch, 1.4*inch, 1.673*inch, showBoundary=0, topPadding=0,rightPadding=0,bottomPadding=0,leftPadding=0)
    f.addFromList(addrs,c)
    f = Frame(6.75*inch, 0.89*inch, 1.4*inch, 1.673*inch, showBoundary=0, topPadding=0,rightPadding=0,bottomPadding=0,leftPadding=0)
    f.addFromList(addrs,c)
    f = Frame(6.75*inch, 3.39*inch, 1.4*inch, 1.673*inch, showBoundary=0, topPadding=0,rightPadding=0,bottomPadding=0,leftPadding=0)
    f.addFromList(addrs,c)
    f = Frame(6.75*inch, 5.89*inch, 1.4*inch, 1.673*inch, showBoundary=0, topPadding=0,rightPadding=0,bottomPadding=0,leftPadding=0)
    f.addFromList(addrs,c)
    f = Frame(6.75*inch, 8.39*inch, 1.4*inch, 1.673*inch, showBoundary=0, topPadding=0,rightPadding=0,bottomPadding=0,leftPadding=0)
    f.addFromList(addrs,c)
    f = Frame(11.09*inch, 0.89*inch, 1.4*inch, 1.673*inch, showBoundary=0, topPadding=0,rightPadding=0,bottomPadding=0,leftPadding=0)
    f.addFromList(addrs,c)
    f = Frame(11.09*inch, 3.39*inch, 1.4*inch, 1.673*inch, showBoundary=0, topPadding=0,rightPadding=0,bottomPadding=0,leftPadding=0)
    f.addFromList(addrs,c)
    f = Frame(11.09*inch, 5.89*inch, 1.4*inch, 1.673*inch, showBoundary=0, topPadding=0,rightPadding=0,bottomPadding=0,leftPadding=0)
    f.addFromList(addrs,c)
    f = Frame(11.09*inch, 8.39*inch, 1.4*inch, 1.673*inch, showBoundary=0, topPadding=0,rightPadding=0,bottomPadding=0,leftPadding=0)
    f.addFromList(addrs,c)
    f = Frame(15.22*inch, 0.89*inch, 1.4*inch, 1.673*inch, showBoundary=0, topPadding=0,rightPadding=0,bottomPadding=0,leftPadding=0)
    f.addFromList(addrs,c)
    f = Frame(15.22*inch, 3.39*inch, 1.4*inch, 1.673*inch, showBoundary=0, topPadding=0,rightPadding=0,bottomPadding=0,leftPadding=0)
    f.addFromList(addrs,c)
    f = Frame(15.22*inch, 5.89*inch, 1.4*inch, 1.673*inch, showBoundary=0, topPadding=0,rightPadding=0,bottomPadding=0,leftPadding=0)
    f.addFromList(addrs,c)
    f = Frame(15.22*inch, 8.39*inch, 1.4*inch, 1.673*inch, showBoundary=0, topPadding=0,rightPadding=0,bottomPadding=0,leftPadding=0)
    f.addFromList(addrs,c)

    # Close the PDF object cleanly
    c.showPage()
    c.save()

    return response
#}}}

# CaTECH
#{{{ catech_stylesheet
def catech_stylesheet():
    stylesheet = {}

    # Register all required fonts
    folder = settings.FONT_DIR # from settings.py
    registered = pdfmetrics.getRegisteredFontNames()

    afmFile = os.path.join(folder, 'TradeGothic-CondEighteen.afm')
    pfbFile = os.path.join(folder, 'TradeGothic-CondEighteen.pfb')
    faceName = 'TradeGothic-CondEighteen'
    if faceName not in registered:
        justFace = pdfmetrics.EmbeddedType1Face(afmFile, pfbFile)
        pdfmetrics.registerTypeFace(justFace)
        justFont = pdfmetrics.Font('TradeGothic-CondEighteen', faceName, 'WinAnsiEncoding')
        pdfmetrics.registerFont(justFont)

    afmFile = os.path.join(folder, 'TradeGothic-CondEighteenObl.afm')
    pfbFile = os.path.join(folder, 'TradeGothic-CondEighteenObl.pfb')
    faceName = 'TradeGothic-CondEighteenObl'
    if faceName not in registered:
        justFace = pdfmetrics.EmbeddedType1Face(afmFile, pfbFile)
        pdfmetrics.registerTypeFace(justFace)
        justFont = pdfmetrics.Font('TradeGothic-CondEighteenObl', faceName, 'WinAnsiEncoding')
        pdfmetrics.registerFont(justFont)

    afmFile = os.path.join(folder, 'TradeGothic-BoldCondTwenty.afm')
    pfbFile = os.path.join(folder, 'TradeGothic-BoldCondTwenty.pfb')
    faceName = 'TradeGothic-BoldCondTwenty'
    if faceName not in registered:
        justFace = pdfmetrics.EmbeddedType1Face(afmFile, pfbFile)
        pdfmetrics.registerTypeFace(justFace)
        justFont = pdfmetrics.Font('TradeGothic-BoldCondTwenty', faceName, 'WinAnsiEncoding')
        pdfmetrics.registerFont(justFont)

    p = ParagraphStyle('plain', None)
    p.fontName = 'TradeGothic-CondEighteen'
    p.fontSize = 8
    p.leading = 9
    p.textColor = HexColor(0x000000)
    stylesheet['plain'] = p

    p = ParagraphStyle('small', None)
    p.fontName = 'TradeGothic-CondEighteen'
    p.fontSize = 6
    p.leading = 9
    p.textColor = HexColor(0x000000)
    stylesheet['small'] = p

    p = ParagraphStyle('obl', None)
    p.fontName = 'TradeGothic-CondEighteenObl'
    p.fontSize = 7
    p.leading = 9
    p.textColor = HexColor(0x000000)
    stylesheet['obl'] = p

    p = ParagraphStyle('bold', None)
    p.fontName = 'TradeGothic-BoldCondTwenty'
    p.fontSize = 8
    p.leading = 9
    p.textColor = HexColor(0x000000)
    stylesheet['bold'] = p

    return stylesheet
#}}}
#{{{ CaTechTorontoBc_1up
def CaTechTorontoBc_1up(request):
    # Create output filenames
    timestamp = str(time()).replace('.','')
    pdf_file = "%s/previews/%s.pdf" % (settings.MEDIA_ROOT, timestamp)
    img_file = "%s/previews/%s.gif" % (settings.MEDIA_ROOT, timestamp)

    # Set some document specifics
    pagesize = (inch*3.5, inch*2) # width, height. Measured at 72dpi, so this is 252x144
    bg_image = "%s/vardata_images/CaTechTorontoBc_bg_1up.tif" % settings.MEDIA_ROOT
    fonts = catech_stylesheet()

    # Get the info that the user entered. These fields should match what's in the model.
    form_data = escape(request.session.get('form_data', None))
    name = form_data['name']
    initials = form_data['initials']
    title = form_data['title']
    email = form_data['email']
    email_line = '%s@catech-systems.com' % email
    fax = form_data['fax']
    fax_line = '<font size="6">FAX:</font><font color="white" size="2">________________</font>905 944 %s' % fax # spacing hack
    if form_data['cell'] != '':
        cell_parts = phone_parts(form_data['cell'])
        cell_label = form_data['cell_label']
        if cell_label == "CELL":
            spacer = '<font color="white" size="2">_____________..</font>'
        else:
            spacer = '<font color="white" size="2">________..</font>'
        cell_line = '<font size="6">%s:</font>%s%s %s %s' % (cell_label, spacer, cell_parts[0], cell_parts[1], cell_parts[2])
    else:
        cell_line = "&nbsp;"
    main_line = '<font size="6">MAIN:</font><font color="white" size="2">_____________</font>905 944 0000'

    # Format the lines and add them to the document
    nameblock = []
    if initials:
        initials = ", %s" % initials
    nameblock.append(Paragraph("%s<font size='6'>%s</font>" % (name, initials), fonts['bold']))
    nameblock.append(Paragraph(title, fonts['obl']))
    addrblock = []
    addrblock.append(Paragraph("CaTECH Systems Ltd.", fonts['bold']))
    addrblock.append(Paragraph("201 Whitehall Drive, Unit #4", fonts['plain']))
    addrblock.append(Paragraph("Markham, ON L3R 9Y3", fonts['plain']))
    addrblock.append(Paragraph("www.catech-systems.com", fonts['plain']))
    phoneblock = []
    phoneblock.append(Paragraph(cell_line, fonts['plain']))
    phoneblock.append(Paragraph(fax_line, fonts['plain']))
    phoneblock.append(Paragraph("<font size='6'>TOLL FREE:</font> 1 800 267 1919", fonts['plain']))
    cellblock = []
    cellblock.append(Paragraph(main_line, fonts['plain']))
    cellblock.append(Paragraph(email_line, fonts['plain']))

    c = canvas.Canvas(filename=pdf_file, pagesize=pagesize, pageCompression=1)
    c.drawImage(bg_image, 0, 0, width=252, height=144, mask=None)
    f = Frame(0, 0, 3.5*inch, 2*inch, showBoundary=0, leftPadding=0.41*inch, topPadding=1.51*inch)
    f.addFromList(nameblock,c)
    f = Frame(0, 0, 3.5*inch, 2*inch, showBoundary=0, leftPadding=1.79*inch, topPadding=0.23*inch)
    f.addFromList(addrblock,c)
    f = Frame(0, 0, 3.5*inch, 2*inch, showBoundary=0, leftPadding=1.79*inch, topPadding=0.82*inch)
    f.addFromList(phoneblock,c)
    f = Frame(0, 0, 3.5*inch, 2*inch, showBoundary=0, leftPadding=1.79*inch, topPadding=1.49*inch)
    f.addFromList(cellblock,c)

    # Close the PDF object cleanly
    c.showPage()
    c.save()

    # Create a preview image
    command = 'convert -page 252x144 %s %s' % (pdf_file, img_file)
    os.system(command)

    # Set session variable so we can pass filename back to preview
    request.session['filename_prefix'] = timestamp

    return HttpResponseRedirect(reverse('orders:vardata_preview'))
#}}}
#{{{ CaTechTorontoBc_print
def CaTechTorontoBc_print(request, ordereditem_id):
    ordereditem = OrderedItem.objects.get(pk=ordereditem_id)

    # Create output filenames
    filename = "%s-%s.pdf" % (ordereditem.order.name, ordereditem_id)

    # Set some document specifics
    response = HttpResponse(mimetype='application/pdf')
    response['Content-Disposition'] = 'attachment; filename=%s' % filename # force save as dialog
    pagesize = (inch*17, inch*11) # width, height. Measured at 72dpi, so this is 1224x792
    bg_image = "%s/vardata_images/CaTechTorontoBc_bg_print.tif" % settings.MEDIA_ROOT
    fonts = catech_stylesheet()

    # Get the info stored in the DB. Refer to the model for the field names
    data = CaTechTorontoBc.objects.get(ordereditem = ordereditem_id)
    name = cgi.escape(data.name)
    initials = cgi.escape(data.initials)
    title = cgi.escape(data.title)
    email = data.email
    email_line = '%s@catech-systems.com' % email
    fax = data.fax
    fax_line = '<font size="6">FAX:</font><font color="white" size="2">________________</font>905 944 %s' % fax # spacing hack
    if data.cell:
        cell_parts = phone_parts(data.cell)
        cell_label = data.cell_label
        if cell_label == "CELL":
            spacer = '<font color="white" size="2">_____________..</font>'
        else:
            spacer = '<font color="white" size="2">________..</font>'
        cell_line = '<font size="6">%s:</font>%s%s %s %s' % (cell_label, spacer, cell_parts[0], cell_parts[1], cell_parts[2])
    else:
        cell_line = "&nbsp;"
    main_line = '<font size="6">MAIN:</font><font color="white" size="2">_____________</font>905 944 0000'

    # Format the lines and add them to the document
    nameblock = []
    if initials:
        initials = ", %s" % initials
    nameblock.append(Paragraph("%s<font size='6'>%s</font>" % (name, initials), fonts['bold']))
    nameblock.append(Paragraph(title, fonts['obl']))
    addrblock = []
    addrblock.append(Paragraph("CaTECH Systems Ltd.", fonts['bold']))
    addrblock.append(Paragraph("201 Whitehall Drive, Unit #4", fonts['plain']))
    addrblock.append(Paragraph("Markham, ON L3R 9Y3", fonts['plain']))
    addrblock.append(Paragraph("www.catech-systems.com", fonts['plain']))
    phoneblock = []
    phoneblock.append(Paragraph(cell_line, fonts['plain']))
    phoneblock.append(Paragraph(fax_line, fonts['plain']))
    phoneblock.append(Paragraph("<font size='6'>TOLL FREE:</font> 1 800 267 1919", fonts['plain']))
    cellblock = []
    cellblock.append(Paragraph(main_line, fonts['plain']))
    cellblock.append(Paragraph(email_line, fonts['plain']))

    c = canvas.Canvas(response, pagesize=pagesize, pageCompression=1)
    c.drawImage(bg_image, 0, 0, width=1224, height=792, mask=None)

    # address block
    addrs = []
    addrs.extend(20*addrblock)
    # f = Frame(from_left, from_bottom, width, height)
    f = Frame(2.56*inch, 1.77*inch, 1.69*inch, 0.52*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(addrs,c)
    f = Frame(2.56*inch, 3.77*inch, 1.69*inch, 0.52*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(addrs,c)
    f = Frame(2.56*inch, 5.77*inch, 1.69*inch, 0.52*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(addrs,c)
    f = Frame(2.56*inch, 7.77*inch, 1.69*inch, 0.52*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(addrs,c)
    f = Frame(2.56*inch, 9.77*inch, 1.69*inch, 0.52*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(addrs,c)
    f = Frame(6.56*inch, 1.77*inch, 1.69*inch, 0.52*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(addrs,c)
    f = Frame(6.56*inch, 3.77*inch, 1.69*inch, 0.52*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(addrs,c)
    f = Frame(6.56*inch, 5.77*inch, 1.69*inch, 0.52*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(addrs,c)
    f = Frame(6.56*inch, 7.77*inch, 1.69*inch, 0.52*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(addrs,c)
    f = Frame(6.56*inch, 9.77*inch, 1.69*inch, 0.52*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(addrs,c)
    f = Frame(10.56*inch, 1.77*inch, 1.69*inch, 0.52*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(addrs,c)
    f = Frame(10.56*inch, 3.77*inch, 1.69*inch, 0.52*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(addrs,c)
    f = Frame(10.56*inch, 5.77*inch, 1.69*inch, 0.52*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(addrs,c)
    f = Frame(10.56*inch, 7.77*inch, 1.69*inch, 0.52*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(addrs,c)
    f = Frame(10.56*inch, 9.77*inch, 1.69*inch, 0.52*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(addrs,c)
    f = Frame(14.56*inch, 1.77*inch, 1.69*inch, 0.52*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(addrs,c)
    f = Frame(14.56*inch, 3.77*inch, 1.69*inch, 0.52*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(addrs,c)
    f = Frame(14.56*inch, 5.77*inch, 1.69*inch, 0.52*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(addrs,c)
    f = Frame(14.56*inch, 7.77*inch, 1.69*inch, 0.52*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(addrs,c)
    f = Frame(14.56*inch, 9.77*inch, 1.69*inch, 0.52*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(addrs,c)

    # phone block
    phones = []
    phones.extend(20*phoneblock)
    # f = Frame(from_left, from_bottom, width, height)
    f = Frame(2.56*inch, 1.32*inch, 1.69*inch, 0.38*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(phones,c)
    f = Frame(2.56*inch, 3.32*inch, 1.69*inch, 0.38*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(phones,c)
    f = Frame(2.56*inch, 5.32*inch, 1.69*inch, 0.38*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(phones,c)
    f = Frame(2.56*inch, 7.32*inch, 1.69*inch, 0.38*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(phones,c)
    f = Frame(2.56*inch, 9.32*inch, 1.69*inch, 0.38*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(phones,c)
    f = Frame(6.56*inch, 1.32*inch, 1.69*inch, 0.38*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(phones,c)
    f = Frame(6.56*inch, 3.32*inch, 1.69*inch, 0.38*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(phones,c)
    f = Frame(6.56*inch, 5.32*inch, 1.69*inch, 0.38*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(phones,c)
    f = Frame(6.56*inch, 7.32*inch, 1.69*inch, 0.38*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(phones,c)
    f = Frame(6.56*inch, 9.32*inch, 1.69*inch, 0.38*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(phones,c)
    f = Frame(10.56*inch, 1.32*inch, 1.69*inch, 0.38*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(phones,c)
    f = Frame(10.56*inch, 3.32*inch, 1.69*inch, 0.38*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(phones,c)
    f = Frame(10.56*inch, 5.32*inch, 1.69*inch, 0.38*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(phones,c)
    f = Frame(10.56*inch, 7.32*inch, 1.69*inch, 0.38*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(phones,c)
    f = Frame(10.56*inch, 9.32*inch, 1.69*inch, 0.38*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(phones,c)
    f = Frame(14.56*inch, 1.32*inch, 1.69*inch, 0.38*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(phones,c)
    f = Frame(14.56*inch, 3.32*inch, 1.69*inch, 0.38*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(phones,c)
    f = Frame(14.56*inch, 5.32*inch, 1.69*inch, 0.38*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(phones,c)
    f = Frame(14.56*inch, 7.32*inch, 1.69*inch, 0.38*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(phones,c)
    f = Frame(14.56*inch, 9.32*inch, 1.69*inch, 0.38*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(phones,c)

    # cell block
    cells = []
    cells.extend(20*cellblock)
    # f = Frame(from_left, from_bottom, width, height)
    f = Frame(2.56*inch, 0.76*inch, 1.69*inch, 0.27*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(cells,c)
    f = Frame(2.56*inch, 2.76*inch, 1.69*inch, 0.27*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(cells,c)
    f = Frame(2.56*inch, 4.76*inch, 1.69*inch, 0.27*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(cells,c)
    f = Frame(2.56*inch, 6.76*inch, 1.69*inch, 0.27*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(cells,c)
    f = Frame(2.56*inch, 8.76*inch, 1.69*inch, 0.27*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(cells,c)
    f = Frame(6.56*inch, 0.76*inch, 1.69*inch, 0.27*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(cells,c)
    f = Frame(6.56*inch, 2.76*inch, 1.69*inch, 0.27*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(cells,c)
    f = Frame(6.56*inch, 4.76*inch, 1.69*inch, 0.27*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(cells,c)
    f = Frame(6.56*inch, 6.76*inch, 1.69*inch, 0.27*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(cells,c)
    f = Frame(6.56*inch, 8.76*inch, 1.69*inch, 0.27*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(cells,c)
    f = Frame(10.56*inch, 0.76*inch, 1.69*inch, 0.27*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(cells,c)
    f = Frame(10.56*inch, 2.76*inch, 1.69*inch, 0.27*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(cells,c)
    f = Frame(10.56*inch, 4.76*inch, 1.69*inch, 0.27*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(cells,c)
    f = Frame(10.56*inch, 6.76*inch, 1.69*inch, 0.27*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(cells,c)
    f = Frame(10.56*inch, 8.76*inch, 1.69*inch, 0.27*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(cells,c)
    f = Frame(14.56*inch, 0.76*inch, 1.69*inch, 0.27*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(cells,c)
    f = Frame(14.56*inch, 2.76*inch, 1.69*inch, 0.27*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(cells,c)
    f = Frame(14.56*inch, 4.76*inch, 1.69*inch, 0.27*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(cells,c)
    f = Frame(14.56*inch, 6.76*inch, 1.69*inch, 0.27*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(cells,c)
    f = Frame(14.56*inch, 8.76*inch, 1.69*inch, 0.27*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(cells,c)

    # name block
    names = []
    names.extend(20*nameblock)
    # f = Frame(from_left, from_bottom, width, height)
    f = Frame(1.17*inch, 0.76*inch, 1.37*inch, 0.25*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(names,c)
    f = Frame(1.17*inch, 2.76*inch, 1.37*inch, 0.25*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(names,c)
    f = Frame(1.17*inch, 4.76*inch, 1.37*inch, 0.25*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(names,c)
    f = Frame(1.17*inch, 6.76*inch, 1.37*inch, 0.25*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(names,c)
    f = Frame(1.17*inch, 8.76*inch, 1.37*inch, 0.25*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(names,c)
    f = Frame(5.17*inch, 0.76*inch, 1.37*inch, 0.25*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(names,c)
    f = Frame(5.17*inch, 2.76*inch, 1.37*inch, 0.25*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(names,c)
    f = Frame(5.17*inch, 4.76*inch, 1.37*inch, 0.25*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(names,c)
    f = Frame(5.17*inch, 6.76*inch, 1.37*inch, 0.25*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(names,c)
    f = Frame(5.17*inch, 8.76*inch, 1.37*inch, 0.25*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(names,c)
    f = Frame(9.17*inch, 0.76*inch, 1.37*inch, 0.25*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(names,c)
    f = Frame(9.17*inch, 2.76*inch, 1.37*inch, 0.25*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(names,c)
    f = Frame(9.17*inch, 4.76*inch, 1.37*inch, 0.25*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(names,c)
    f = Frame(9.17*inch, 6.76*inch, 1.37*inch, 0.25*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(names,c)
    f = Frame(9.17*inch, 8.76*inch, 1.37*inch, 0.25*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(names,c)
    f = Frame(13.17*inch, 0.76*inch, 1.37*inch, 0.25*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(names,c)
    f = Frame(13.17*inch, 2.76*inch, 1.37*inch, 0.25*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(names,c)
    f = Frame(13.17*inch, 4.76*inch, 1.37*inch, 0.25*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(names,c)
    f = Frame(13.17*inch, 6.76*inch, 1.37*inch, 0.25*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(names,c)
    f = Frame(13.17*inch, 8.76*inch, 1.37*inch, 0.25*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(names,c)

    # Close the PDF object cleanly
    c.showPage()
    c.save()

    return response
#}}}
#{{{ CaTechMontrealBc_1up
def CaTechMontrealBc_1up(request):
    # Create output filenames
    timestamp = str(time()).replace('.','')
    pdf_file = "%s/previews/%s.pdf" % (settings.MEDIA_ROOT, timestamp)
    img_file = "%s/previews/%s.gif" % (settings.MEDIA_ROOT, timestamp)

    # Set some document specifics
    pagesize = (inch*3.5, inch*2) # width, height. Measured at 72dpi, so this is 252x144
    bg_image = "%s/vardata_images/CaTechMontrealBc_bg_1up.tif" % settings.MEDIA_ROOT
    fonts = catech_stylesheet()

    # Get the info that the user entered. These fields should match what's in the model.
    form_data = escape(request.session.get('form_data', None))
    name = form_data['name']
    initials = form_data['initials']
    title = form_data['title']
    ext = form_data['ext']
    email = form_data['email']
    email_line = '%s@catech-systems.com' % email
    if form_data['cell'] != "":
        cell_parts = phone_parts(form_data['cell'])
        cell_label = form_data['cell_label']
        if cell_label == "CELL":
            spacer = '<font color="white" size="2">___________________.</font>'
        else:
            spacer = '<font color="white" size="2">______________..</font>'
        cell_line = '<font size="6">%s:</font>%s(%s) %s %s' % (cell_label, spacer, cell_parts[0], cell_parts[1], cell_parts[2])
    else:
        cell_line = '&nbsp;'
    if ext:
        ext = "ext %s" % ext
    main_line = '<font size="6">BUREAU:</font><font color="white" size="3">________.</font>(450) 669 8866 %s' % ext

    # Format the lines and add them to the document
    nameblock = []
    if initials:
        initials = ", %s" % initials
    nameblock.append(Paragraph("%s<font size='6'>%s</font>" % (name, initials), fonts['bold']))
    nameblock.append(Paragraph(title, fonts['obl']))
    addrblock = []
    addrblock.append(Paragraph("CaTECH Systems Ltd.", fonts['bold']))
    addrblock.append(Paragraph("3114, ave. Francis-Hughes", fonts['plain']))
    addrblock.append(Paragraph("Laval (Qu\xc3\xa9bec) H7L 5A7", fonts['plain'])) # note unicode escape codes
    addrblock.append(Paragraph("www.catech-systems.com", fonts['plain']))
    phoneblock = []
    phoneblock.append(Paragraph(main_line, fonts['plain']))
    phoneblock.append(Paragraph("<font size='6'>T\xc3\x89L\xc3\x89COPIEUR:</font> (450) 669 5001", fonts['plain']))
    phoneblock.append(Paragraph('<font size="6">SANS FRAIS:</font><font color="white" size="3">___..</font>1 (866) 660 8866', fonts['plain']))
    cellblock = []
    cellblock.append(Paragraph(cell_line, fonts['plain']))
    cellblock.append(Paragraph(email_line, fonts['plain']))

    c = canvas.Canvas(filename=pdf_file, pagesize=pagesize, pageCompression=1)
    c.drawImage(bg_image, 0, 0, width=252, height=144, mask=None)
    f = Frame(0, 0, 3.5*inch, 2*inch, showBoundary=0, leftPadding=0.41*inch, topPadding=1.51*inch)
    f.addFromList(nameblock,c)
    f = Frame(0, 0, 3.5*inch, 2*inch, showBoundary=0, leftPadding=1.79*inch, topPadding=0.23*inch)
    f.addFromList(addrblock,c)
    f = Frame(0, 0, 3.5*inch, 2*inch, showBoundary=0, leftPadding=1.79*inch, topPadding=0.82*inch)
    f.addFromList(phoneblock,c)
    f = Frame(0, 0, 3.5*inch, 2*inch, showBoundary=0, leftPadding=1.79*inch, topPadding=1.49*inch)
    f.addFromList(cellblock,c)

    # Close the PDF object cleanly
    c.showPage()
    c.save()

    # Create a preview image
    command = 'convert -page 252x144 %s %s' % (pdf_file, img_file)
    os.system(command)

    # Set session variable so we can pass filename back to preview
    request.session['filename_prefix'] = timestamp

    return HttpResponseRedirect(reverse('orders:vardata_preview'))
#}}}
#{{{ CaTechMontrealBc_print
def CaTechMontrealBc_print(request, ordereditem_id):
    ordereditem = OrderedItem.objects.get(pk=ordereditem_id)

    # Create output filenames
    filename = "%s-%s.pdf" % (ordereditem.order.name, ordereditem_id)

    # Set some document specifics
    response = HttpResponse(mimetype='application/pdf')
    response['Content-Disposition'] = 'attachment; filename=%s' % filename # force save as dialog
    pagesize = (inch*17, inch*11) # width, height. Measured at 72dpi, so this is 1224x792
    bg_image = "%s/vardata_images/CaTechMontrealBc_bg_print.tif" % settings.MEDIA_ROOT
    fonts = catech_stylesheet()

    # Get the info stored in the DB. Refer to the model for the field names
    data = CaTechMontrealBc.objects.get(ordereditem = ordereditem_id)
    name = cgi.escape(data.name)
    initials = cgi.escape(data.initials)
    title = cgi.escape(data.title)
    ext = data.ext
    email = data.email
    email_line = '%s@catech-systems.com' % email
    if data.cell:
        cell_parts = phone_parts(data.cell)
        cell_label = data.cell_label
        if cell_label == "CELL":
            spacer = '<font color="white" size="2">___________________.</font>'
        else:
            spacer = '<font color="white" size="2">______________..</font>'
        cell_line = '<font size="6">%s:</font>%s(%s) %s %s' % (cell_label, spacer, cell_parts[0], cell_parts[1], cell_parts[2])
    else:
        cell_line = "&nbsp;"
    if ext:
        ext = "ext %s" % ext
    main_line = '<font size="6">BUREAU:</font><font color="white" size="3">________.</font>(450) 669 8866 %s' % ext

    # Format the lines and add them to the document
    nameblock = []
    if initials:
        initials = ", %s" % initials
    nameblock.append(Paragraph("%s<font size='6'>%s</font>" % (name, initials), fonts['bold']))
    nameblock.append(Paragraph(title, fonts['obl']))
    addrblock = []
    addrblock.append(Paragraph("CaTECH Systems Ltd.", fonts['bold']))
    addrblock.append(Paragraph("3114, ave. Francis-Hughes", fonts['plain']))
    addrblock.append(Paragraph("Laval (Qu\xc3\xa9bec) H7L 5A7", fonts['plain'])) # note unicode escape codes
    addrblock.append(Paragraph("www.catech-systems.com", fonts['plain']))
    phoneblock = []
    phoneblock.append(Paragraph(main_line, fonts['plain']))
    phoneblock.append(Paragraph("<font size='6'>T\xc3\x89L\xc3\x89COPIEUR:</font> (450) 669 5001", fonts['plain']))
    phoneblock.append(Paragraph('<font size="6">SANS FRAIS:</font><font color="white" size="3">___..</font>1 (866) 660 8866', fonts['plain']))
    cellblock = []
    cellblock.append(Paragraph(cell_line, fonts['plain']))
    cellblock.append(Paragraph(email_line, fonts['plain']))

    c = canvas.Canvas(response, pagesize=pagesize, pageCompression=1)
    c.drawImage(bg_image, 0, 0, width=1224, height=792, mask=None)

    # address block
    addrs = []
    addrs.extend(20*addrblock)
    # f = Frame(from_left, from_bottom, width, height)
    f = Frame(2.56*inch, 1.77*inch, 1.69*inch, 0.52*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(addrs,c)
    f = Frame(2.56*inch, 3.77*inch, 1.69*inch, 0.52*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(addrs,c)
    f = Frame(2.56*inch, 5.77*inch, 1.69*inch, 0.52*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(addrs,c)
    f = Frame(2.56*inch, 7.77*inch, 1.69*inch, 0.52*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(addrs,c)
    f = Frame(2.56*inch, 9.77*inch, 1.69*inch, 0.52*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(addrs,c)
    f = Frame(6.56*inch, 1.77*inch, 1.69*inch, 0.52*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(addrs,c)
    f = Frame(6.56*inch, 3.77*inch, 1.69*inch, 0.52*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(addrs,c)
    f = Frame(6.56*inch, 5.77*inch, 1.69*inch, 0.52*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(addrs,c)
    f = Frame(6.56*inch, 7.77*inch, 1.69*inch, 0.52*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(addrs,c)
    f = Frame(6.56*inch, 9.77*inch, 1.69*inch, 0.52*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(addrs,c)
    f = Frame(10.56*inch, 1.77*inch, 1.69*inch, 0.52*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(addrs,c)
    f = Frame(10.56*inch, 3.77*inch, 1.69*inch, 0.52*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(addrs,c)
    f = Frame(10.56*inch, 5.77*inch, 1.69*inch, 0.52*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(addrs,c)
    f = Frame(10.56*inch, 7.77*inch, 1.69*inch, 0.52*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(addrs,c)
    f = Frame(10.56*inch, 9.77*inch, 1.69*inch, 0.52*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(addrs,c)
    f = Frame(14.56*inch, 1.77*inch, 1.69*inch, 0.52*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(addrs,c)
    f = Frame(14.56*inch, 3.77*inch, 1.69*inch, 0.52*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(addrs,c)
    f = Frame(14.56*inch, 5.77*inch, 1.69*inch, 0.52*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(addrs,c)
    f = Frame(14.56*inch, 7.77*inch, 1.69*inch, 0.52*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(addrs,c)
    f = Frame(14.56*inch, 9.77*inch, 1.69*inch, 0.52*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(addrs,c)

    # phone block
    phones = []
    phones.extend(20*phoneblock)
    # f = Frame(from_left, from_bottom, width, height)
    f = Frame(2.56*inch, 1.32*inch, 1.69*inch, 0.38*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(phones,c)
    f = Frame(2.56*inch, 3.32*inch, 1.69*inch, 0.38*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(phones,c)
    f = Frame(2.56*inch, 5.32*inch, 1.69*inch, 0.38*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(phones,c)
    f = Frame(2.56*inch, 7.32*inch, 1.69*inch, 0.38*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(phones,c)
    f = Frame(2.56*inch, 9.32*inch, 1.69*inch, 0.38*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(phones,c)
    f = Frame(6.56*inch, 1.32*inch, 1.69*inch, 0.38*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(phones,c)
    f = Frame(6.56*inch, 3.32*inch, 1.69*inch, 0.38*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(phones,c)
    f = Frame(6.56*inch, 5.32*inch, 1.69*inch, 0.38*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(phones,c)
    f = Frame(6.56*inch, 7.32*inch, 1.69*inch, 0.38*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(phones,c)
    f = Frame(6.56*inch, 9.32*inch, 1.69*inch, 0.38*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(phones,c)
    f = Frame(10.56*inch, 1.32*inch, 1.69*inch, 0.38*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(phones,c)
    f = Frame(10.56*inch, 3.32*inch, 1.69*inch, 0.38*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(phones,c)
    f = Frame(10.56*inch, 5.32*inch, 1.69*inch, 0.38*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(phones,c)
    f = Frame(10.56*inch, 7.32*inch, 1.69*inch, 0.38*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(phones,c)
    f = Frame(10.56*inch, 9.32*inch, 1.69*inch, 0.38*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(phones,c)
    f = Frame(14.56*inch, 1.32*inch, 1.69*inch, 0.38*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(phones,c)
    f = Frame(14.56*inch, 3.32*inch, 1.69*inch, 0.38*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(phones,c)
    f = Frame(14.56*inch, 5.32*inch, 1.69*inch, 0.38*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(phones,c)
    f = Frame(14.56*inch, 7.32*inch, 1.69*inch, 0.38*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(phones,c)
    f = Frame(14.56*inch, 9.32*inch, 1.69*inch, 0.38*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(phones,c)

    # cell block
    cells = []
    cells.extend(20*cellblock)
    # f = Frame(from_left, from_bottom, width, height)
    f = Frame(2.56*inch, 0.76*inch, 1.69*inch, 0.27*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(cells,c)
    f = Frame(2.56*inch, 2.76*inch, 1.69*inch, 0.27*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(cells,c)
    f = Frame(2.56*inch, 4.76*inch, 1.69*inch, 0.27*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(cells,c)
    f = Frame(2.56*inch, 6.76*inch, 1.69*inch, 0.27*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(cells,c)
    f = Frame(2.56*inch, 8.76*inch, 1.69*inch, 0.27*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(cells,c)
    f = Frame(6.56*inch, 0.76*inch, 1.69*inch, 0.27*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(cells,c)
    f = Frame(6.56*inch, 2.76*inch, 1.69*inch, 0.27*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(cells,c)
    f = Frame(6.56*inch, 4.76*inch, 1.69*inch, 0.27*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(cells,c)
    f = Frame(6.56*inch, 6.76*inch, 1.69*inch, 0.27*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(cells,c)
    f = Frame(6.56*inch, 8.76*inch, 1.69*inch, 0.27*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(cells,c)
    f = Frame(10.56*inch, 0.76*inch, 1.69*inch, 0.27*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(cells,c)
    f = Frame(10.56*inch, 2.76*inch, 1.69*inch, 0.27*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(cells,c)
    f = Frame(10.56*inch, 4.76*inch, 1.69*inch, 0.27*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(cells,c)
    f = Frame(10.56*inch, 6.76*inch, 1.69*inch, 0.27*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(cells,c)
    f = Frame(10.56*inch, 8.76*inch, 1.69*inch, 0.27*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(cells,c)
    f = Frame(14.56*inch, 0.76*inch, 1.69*inch, 0.27*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(cells,c)
    f = Frame(14.56*inch, 2.76*inch, 1.69*inch, 0.27*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(cells,c)
    f = Frame(14.56*inch, 4.76*inch, 1.69*inch, 0.27*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(cells,c)
    f = Frame(14.56*inch, 6.76*inch, 1.69*inch, 0.27*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(cells,c)
    f = Frame(14.56*inch, 8.76*inch, 1.69*inch, 0.27*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(cells,c)

    # name block
    names = []
    names.extend(20*nameblock)
    # f = Frame(from_left, from_bottom, width, height)
    f = Frame(1.17*inch, 0.76*inch, 1.37*inch, 0.25*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(names,c)
    f = Frame(1.17*inch, 2.76*inch, 1.37*inch, 0.25*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(names,c)
    f = Frame(1.17*inch, 4.76*inch, 1.37*inch, 0.25*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(names,c)
    f = Frame(1.17*inch, 6.76*inch, 1.37*inch, 0.25*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(names,c)
    f = Frame(1.17*inch, 8.76*inch, 1.37*inch, 0.25*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(names,c)
    f = Frame(5.17*inch, 0.76*inch, 1.37*inch, 0.25*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(names,c)
    f = Frame(5.17*inch, 2.76*inch, 1.37*inch, 0.25*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(names,c)
    f = Frame(5.17*inch, 4.76*inch, 1.37*inch, 0.25*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(names,c)
    f = Frame(5.17*inch, 6.76*inch, 1.37*inch, 0.25*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(names,c)
    f = Frame(5.17*inch, 8.76*inch, 1.37*inch, 0.25*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(names,c)
    f = Frame(9.17*inch, 0.76*inch, 1.37*inch, 0.25*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(names,c)
    f = Frame(9.17*inch, 2.76*inch, 1.37*inch, 0.25*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(names,c)
    f = Frame(9.17*inch, 4.76*inch, 1.37*inch, 0.25*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(names,c)
    f = Frame(9.17*inch, 6.76*inch, 1.37*inch, 0.25*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(names,c)
    f = Frame(9.17*inch, 8.76*inch, 1.37*inch, 0.25*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(names,c)
    f = Frame(13.17*inch, 0.76*inch, 1.37*inch, 0.25*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(names,c)
    f = Frame(13.17*inch, 2.76*inch, 1.37*inch, 0.25*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(names,c)
    f = Frame(13.17*inch, 4.76*inch, 1.37*inch, 0.25*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(names,c)
    f = Frame(13.17*inch, 6.76*inch, 1.37*inch, 0.25*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(names,c)
    f = Frame(13.17*inch, 8.76*inch, 1.37*inch, 0.25*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(names,c)

    # Close the PDF object cleanly
    c.showPage()
    c.save()

    return response
#}}}
#{{{ CaTechOttawaBc_1up
def CaTechOttawaBc_1up(request):
    # Create output filenames
    timestamp = str(time()).replace('.','')
    pdf_file = "%s/previews/%s.pdf" % (settings.MEDIA_ROOT, timestamp)
    img_file = "%s/previews/%s.gif" % (settings.MEDIA_ROOT, timestamp)

    # Set some document specifics
    pagesize = (inch*3.5, inch*2) # width, height. Measured at 72dpi, so this is 252x144
    bg_image = "%s/vardata_images/CaTechTorontoBc_bg_1up.tif" % settings.MEDIA_ROOT
    fonts = catech_stylesheet()

    # Get the info that the user entered. These fields should match what's in the model.
    form_data = escape(request.session.get('form_data', None))
    name = form_data['name']
    initials = form_data['initials']
    title = form_data['title']
    ext = form_data['ext']
    email = form_data['email']
    email_line = '%s@catech-systems.com' % email
    if form_data['cell'] != '':
        cell_parts = phone_parts(form_data['cell'])
        cell_label = form_data['cell_label']
        if cell_label == "CELL":
            spacer = '<font color="white" size="2">_____________..</font>'
        else:
            spacer = '<font color="white" size="2">________..</font>'
        cell_line = '<font size="6">%s:</font>%s%s %s %s' % (cell_label, spacer, cell_parts[0], cell_parts[1], cell_parts[2])
    else:
        cell_line = "&nbsp;"
    if ext:
        ext = "ext %s" % ext
    main_line = '<font size="6">MAIN:</font><font color="white" size="2">_____________</font>613 521 6531 %s' % ext

    # Format the lines and add them to the document
    nameblock = []
    if initials:
        initials = ", %s" % initials
    nameblock.append(Paragraph("%s<font size='6'>%s</font>" % (name, initials), fonts['bold']))
    nameblock.append(Paragraph(title, fonts['obl']))
    addrblock = []
    addrblock.append(Paragraph("CaTECH Systems", fonts['bold']))
    addrblock.append(Paragraph("2465 Stevenage Drive, Unit #106", fonts['plain']))
    addrblock.append(Paragraph("Ottawa, ON K1G 3W2", fonts['plain']))
    addrblock.append(Paragraph("www.catech-systems.com", fonts['plain']))
    phoneblock = []
    phoneblock.append(Paragraph(main_line, fonts['plain']))
    phoneblock.append(Paragraph('<font size="6">FAX:</font><font color="white" size="2">________________</font>613 521 6533', fonts['plain'])) # spacing hack
    phoneblock.append(Paragraph("<font size='6'>TOLL FREE:</font> 1 866 935 6531", fonts['plain']))
    cellblock = []
    cellblock.append(Paragraph(cell_line, fonts['plain']))
    cellblock.append(Paragraph(email_line, fonts['plain']))

    c = canvas.Canvas(filename=pdf_file, pagesize=pagesize, pageCompression=1)
    c.drawImage(bg_image, 0, 0, width=252, height=144, mask=None)
    f = Frame(0, 0, 3.5*inch, 2*inch, showBoundary=0, leftPadding=0.41*inch, topPadding=1.51*inch)
    f.addFromList(nameblock,c)
    f = Frame(0, 0, 3.5*inch, 2*inch, showBoundary=0, leftPadding=1.79*inch, topPadding=0.23*inch)
    f.addFromList(addrblock,c)
    f = Frame(0, 0, 3.5*inch, 2*inch, showBoundary=0, leftPadding=1.79*inch, topPadding=0.82*inch)
    f.addFromList(phoneblock,c)
    f = Frame(0, 0, 3.5*inch, 2*inch, showBoundary=0, leftPadding=1.79*inch, topPadding=1.49*inch)
    f.addFromList(cellblock,c)

    # Close the PDF object cleanly
    c.showPage()
    c.save()

    # Create a preview image
    command = 'convert -page 252x144 %s %s' % (pdf_file, img_file)
    os.system(command)

    # Set session variable so we can pass filename back to preview
    request.session['filename_prefix'] = timestamp

    return HttpResponseRedirect(reverse('orders:vardata_preview'))
#}}}
#{{{ CaTechOttawaBc_print
def CaTechOttawaBc_print(request, ordereditem_id):
    ordereditem = OrderedItem.objects.get(pk=ordereditem_id)

    # Create output filenames
    filename = "%s-%s.pdf" % (ordereditem.order.name, ordereditem_id)

    # Set some document specifics
    response = HttpResponse(mimetype='application/pdf')
    response['Content-Disposition'] = 'attachment; filename=%s' % filename # force save as dialog
    pagesize = (inch*17, inch*11) # width, height. Measured at 72dpi, so this is 1224x792
    bg_image = "%s/vardata_images/CaTechTorontoBc_bg_print.tif" % settings.MEDIA_ROOT
    fonts = catech_stylesheet()

    # Get the info stored in the DB. Refer to the model for the field names
    data = CaTechOttawaBc.objects.get(ordereditem = ordereditem_id)
    name = cgi.escape(data.name)
    initials = cgi.escape(data.initials)
    title = cgi.escape(data.title)
    ext = data.ext
    email = data.email
    email_line = '%s@catech-systems.com' % email
    if data.cell:
        cell_parts = phone_parts(data.cell)
        cell_label = data.cell_label
        if cell_label == "CELL":
            spacer = '<font color="white" size="2">_____________..</font>'
        else:
            spacer = '<font color="white" size="2">________..</font>'
        cell_line = '<font size="6">%s:</font>%s%s %s %s' % (cell_label, spacer, cell_parts[0], cell_parts[1], cell_parts[2])
    else:
        cell_line = "&nbsp;"
    if ext:
        ext = "ext %s" % ext
    main_line = '<font size="6">MAIN:</font><font color="white" size="2">_____________</font>613 521 6531 %s' % ext

    # Format the lines and add them to the document
    nameblock = []
    if initials:
        initials = ", %s" % initials
    nameblock.append(Paragraph("%s<font size='6'>%s</font>" % (name, initials), fonts['bold']))
    nameblock.append(Paragraph(title, fonts['obl']))
    addrblock = []
    addrblock.append(Paragraph("CaTECH Systems", fonts['bold']))
    addrblock.append(Paragraph("2465 Stevenage Drive, Unit #106", fonts['plain']))
    addrblock.append(Paragraph("Ottawa, ON K1G 3W2", fonts['plain']))
    addrblock.append(Paragraph("www.catech-systems.com", fonts['plain']))
    phoneblock = []
    phoneblock.append(Paragraph(main_line, fonts['plain']))
    phoneblock.append(Paragraph('<font size="6">FAX:</font><font color="white" size="2">________________</font>613 521 6533', fonts['plain'])) # spacing hack
    phoneblock.append(Paragraph("<font size='6'>TOLL FREE:</font> 1 800 267 1919", fonts['plain']))
    cellblock = []
    cellblock.append(Paragraph(cell_line, fonts['plain']))
    cellblock.append(Paragraph(email_line, fonts['plain']))

    c = canvas.Canvas(response, pagesize=pagesize, pageCompression=1)
    c.drawImage(bg_image, 0, 0, width=1224, height=792, mask=None)

    # address block
    addrs = []
    addrs.extend(20*addrblock)
    # f = Frame(from_left, from_bottom, width, height)
    f = Frame(2.56*inch, 1.77*inch, 1.69*inch, 0.52*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(addrs,c)
    f = Frame(2.56*inch, 3.77*inch, 1.69*inch, 0.52*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(addrs,c)
    f = Frame(2.56*inch, 5.77*inch, 1.69*inch, 0.52*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(addrs,c)
    f = Frame(2.56*inch, 7.77*inch, 1.69*inch, 0.52*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(addrs,c)
    f = Frame(2.56*inch, 9.77*inch, 1.69*inch, 0.52*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(addrs,c)
    f = Frame(6.56*inch, 1.77*inch, 1.69*inch, 0.52*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(addrs,c)
    f = Frame(6.56*inch, 3.77*inch, 1.69*inch, 0.52*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(addrs,c)
    f = Frame(6.56*inch, 5.77*inch, 1.69*inch, 0.52*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(addrs,c)
    f = Frame(6.56*inch, 7.77*inch, 1.69*inch, 0.52*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(addrs,c)
    f = Frame(6.56*inch, 9.77*inch, 1.69*inch, 0.52*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(addrs,c)
    f = Frame(10.56*inch, 1.77*inch, 1.69*inch, 0.52*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(addrs,c)
    f = Frame(10.56*inch, 3.77*inch, 1.69*inch, 0.52*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(addrs,c)
    f = Frame(10.56*inch, 5.77*inch, 1.69*inch, 0.52*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(addrs,c)
    f = Frame(10.56*inch, 7.77*inch, 1.69*inch, 0.52*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(addrs,c)
    f = Frame(10.56*inch, 9.77*inch, 1.69*inch, 0.52*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(addrs,c)
    f = Frame(14.56*inch, 1.77*inch, 1.69*inch, 0.52*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(addrs,c)
    f = Frame(14.56*inch, 3.77*inch, 1.69*inch, 0.52*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(addrs,c)
    f = Frame(14.56*inch, 5.77*inch, 1.69*inch, 0.52*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(addrs,c)
    f = Frame(14.56*inch, 7.77*inch, 1.69*inch, 0.52*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(addrs,c)
    f = Frame(14.56*inch, 9.77*inch, 1.69*inch, 0.52*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(addrs,c)

    # phone block
    phones = []
    phones.extend(20*phoneblock)
    # f = Frame(from_left, from_bottom, width, height)
    f = Frame(2.56*inch, 1.32*inch, 1.69*inch, 0.38*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(phones,c)
    f = Frame(2.56*inch, 3.32*inch, 1.69*inch, 0.38*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(phones,c)
    f = Frame(2.56*inch, 5.32*inch, 1.69*inch, 0.38*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(phones,c)
    f = Frame(2.56*inch, 7.32*inch, 1.69*inch, 0.38*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(phones,c)
    f = Frame(2.56*inch, 9.32*inch, 1.69*inch, 0.38*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(phones,c)
    f = Frame(6.56*inch, 1.32*inch, 1.69*inch, 0.38*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(phones,c)
    f = Frame(6.56*inch, 3.32*inch, 1.69*inch, 0.38*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(phones,c)
    f = Frame(6.56*inch, 5.32*inch, 1.69*inch, 0.38*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(phones,c)
    f = Frame(6.56*inch, 7.32*inch, 1.69*inch, 0.38*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(phones,c)
    f = Frame(6.56*inch, 9.32*inch, 1.69*inch, 0.38*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(phones,c)
    f = Frame(10.56*inch, 1.32*inch, 1.69*inch, 0.38*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(phones,c)
    f = Frame(10.56*inch, 3.32*inch, 1.69*inch, 0.38*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(phones,c)
    f = Frame(10.56*inch, 5.32*inch, 1.69*inch, 0.38*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(phones,c)
    f = Frame(10.56*inch, 7.32*inch, 1.69*inch, 0.38*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(phones,c)
    f = Frame(10.56*inch, 9.32*inch, 1.69*inch, 0.38*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(phones,c)
    f = Frame(14.56*inch, 1.32*inch, 1.69*inch, 0.38*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(phones,c)
    f = Frame(14.56*inch, 3.32*inch, 1.69*inch, 0.38*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(phones,c)
    f = Frame(14.56*inch, 5.32*inch, 1.69*inch, 0.38*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(phones,c)
    f = Frame(14.56*inch, 7.32*inch, 1.69*inch, 0.38*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(phones,c)
    f = Frame(14.56*inch, 9.32*inch, 1.69*inch, 0.38*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(phones,c)

    # cell block
    cells = []
    cells.extend(20*cellblock)
    # f = Frame(from_left, from_bottom, width, height)
    f = Frame(2.56*inch, 0.76*inch, 1.69*inch, 0.27*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(cells,c)
    f = Frame(2.56*inch, 2.76*inch, 1.69*inch, 0.27*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(cells,c)
    f = Frame(2.56*inch, 4.76*inch, 1.69*inch, 0.27*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(cells,c)
    f = Frame(2.56*inch, 6.76*inch, 1.69*inch, 0.27*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(cells,c)
    f = Frame(2.56*inch, 8.76*inch, 1.69*inch, 0.27*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(cells,c)
    f = Frame(6.56*inch, 0.76*inch, 1.69*inch, 0.27*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(cells,c)
    f = Frame(6.56*inch, 2.76*inch, 1.69*inch, 0.27*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(cells,c)
    f = Frame(6.56*inch, 4.76*inch, 1.69*inch, 0.27*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(cells,c)
    f = Frame(6.56*inch, 6.76*inch, 1.69*inch, 0.27*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(cells,c)
    f = Frame(6.56*inch, 8.76*inch, 1.69*inch, 0.27*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(cells,c)
    f = Frame(10.56*inch, 0.76*inch, 1.69*inch, 0.27*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(cells,c)
    f = Frame(10.56*inch, 2.76*inch, 1.69*inch, 0.27*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(cells,c)
    f = Frame(10.56*inch, 4.76*inch, 1.69*inch, 0.27*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(cells,c)
    f = Frame(10.56*inch, 6.76*inch, 1.69*inch, 0.27*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(cells,c)
    f = Frame(10.56*inch, 8.76*inch, 1.69*inch, 0.27*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(cells,c)
    f = Frame(14.56*inch, 0.76*inch, 1.69*inch, 0.27*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(cells,c)
    f = Frame(14.56*inch, 2.76*inch, 1.69*inch, 0.27*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(cells,c)
    f = Frame(14.56*inch, 4.76*inch, 1.69*inch, 0.27*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(cells,c)
    f = Frame(14.56*inch, 6.76*inch, 1.69*inch, 0.27*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(cells,c)
    f = Frame(14.56*inch, 8.76*inch, 1.69*inch, 0.27*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(cells,c)

    # name block
    names = []
    names.extend(20*nameblock)
    # f = Frame(from_left, from_bottom, width, height)
    f = Frame(1.17*inch, 0.76*inch, 1.37*inch, 0.25*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(names,c)
    f = Frame(1.17*inch, 2.76*inch, 1.37*inch, 0.25*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(names,c)
    f = Frame(1.17*inch, 4.76*inch, 1.37*inch, 0.25*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(names,c)
    f = Frame(1.17*inch, 6.76*inch, 1.37*inch, 0.25*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(names,c)
    f = Frame(1.17*inch, 8.76*inch, 1.37*inch, 0.25*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(names,c)
    f = Frame(5.17*inch, 0.76*inch, 1.37*inch, 0.25*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(names,c)
    f = Frame(5.17*inch, 2.76*inch, 1.37*inch, 0.25*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(names,c)
    f = Frame(5.17*inch, 4.76*inch, 1.37*inch, 0.25*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(names,c)
    f = Frame(5.17*inch, 6.76*inch, 1.37*inch, 0.25*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(names,c)
    f = Frame(5.17*inch, 8.76*inch, 1.37*inch, 0.25*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(names,c)
    f = Frame(9.17*inch, 0.76*inch, 1.37*inch, 0.25*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(names,c)
    f = Frame(9.17*inch, 2.76*inch, 1.37*inch, 0.25*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(names,c)
    f = Frame(9.17*inch, 4.76*inch, 1.37*inch, 0.25*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(names,c)
    f = Frame(9.17*inch, 6.76*inch, 1.37*inch, 0.25*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(names,c)
    f = Frame(9.17*inch, 8.76*inch, 1.37*inch, 0.25*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(names,c)
    f = Frame(13.17*inch, 0.76*inch, 1.37*inch, 0.25*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(names,c)
    f = Frame(13.17*inch, 2.76*inch, 1.37*inch, 0.25*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(names,c)
    f = Frame(13.17*inch, 4.76*inch, 1.37*inch, 0.25*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(names,c)
    f = Frame(13.17*inch, 6.76*inch, 1.37*inch, 0.25*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(names,c)
    f = Frame(13.17*inch, 8.76*inch, 1.37*inch, 0.25*inch, showBoundary=0, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f.addFromList(names,c)

    # Close the PDF object cleanly
    c.showPage()
    c.save()

    return response
#}}}

# Ross D & Sons
#{{{ ross_stylesheet
def ross_stylesheet():
    stylesheet = {}

    # Register all required fonts
    folder = settings.FONT_DIR # from settings.py
    registered = pdfmetrics.getRegisteredFontNames()

    afmFile = os.path.join(folder, 'TimesNewRomanPSMT.afm')
    pfbFile = os.path.join(folder, 'TimesNewRomanPSMT.pfb')
    faceName = 'TimesNewRomanPSMT'
    if faceName not in registered:
        justFace = pdfmetrics.EmbeddedType1Face(afmFile, pfbFile)
        pdfmetrics.registerTypeFace(justFace)
        justFont = pdfmetrics.Font('TimesNewRomanPSMT', faceName, 'WinAnsiEncoding')
        pdfmetrics.registerFont(justFont)

    afmFile = os.path.join(folder, 'TimesNewRomanPS-ItalicMT.afm')
    pfbFile = os.path.join(folder, 'TimesNewRomanPS-ItalicMT.pfb')
    faceName = 'TimesNewRomanPS-ItalicMT'
    if faceName not in registered:
        justFace = pdfmetrics.EmbeddedType1Face(afmFile, pfbFile)
        pdfmetrics.registerTypeFace(justFace)
        justFont = pdfmetrics.Font('TimesNewRomanPS-ItalicMT', faceName, 'WinAnsiEncoding')
        pdfmetrics.registerFont(justFont)

    p = ParagraphStyle('plain', None)
    p.fontName = 'TimesNewRomanPSMT'
    p.fontSize = 13
    p.leading = 13.5
    p.alignment = TA_CENTER
    p.textColor = HexColor(0xEED723)
    stylesheet['plain'] = p

    p = ParagraphStyle('plain-italic', None)
    p.fontName = 'TimesNewRomanPS-ItalicMT'
    p.fontSize = 9
    p.leading = 11
    p.alignment = TA_CENTER
    p.textColor = HexColor(0xEED723)
    stylesheet['plain-italic'] = p

    return stylesheet
#}}}
#{{{ RossBc_1up
def RossBc_1up(request):
    # Get the info that the user entered. These fields should match what's in the model.
    form_data = escape(request.session.get('form_data', None))

    # Set some document specifics
    timestamp = str(time()).replace('.','')
    pdf_file = "%s/previews/%s.pdf" % (settings.MEDIA_ROOT, timestamp)
    img_file = "%s/previews/%s.gif" % (settings.MEDIA_ROOT, timestamp)
    pagesize = (inch*3.5, inch*2) # width, height. Measured at 72dpi, so this is 252x144
    bg_image = "%s/vardata_images/RossBc_bg_1up.tif" % settings.MEDIA_ROOT
    fonts = ross_stylesheet()

    # Format the lines and add them to the document
    building_block = []
    building_block.append(Paragraph(form_data['building_name'], fonts['plain']))
    building_block.append(Paragraph("<font size=11>%s</font>" % form_data['street_address'], fonts['plain']))
    building_block.append(Paragraph("<font size=11>%s, %s</font>" % (form_data['city'], form_data['province']), fonts['plain']))
    name_block = []
    name_block.append(Paragraph(form_data['name'], fonts['plain']))
    name_block.append(Paragraph(form_data['job_title'], fonts['plain-italic']))
    name_block.append(Paragraph("<font size=11>%s</font>" % form_data['direct_number'], fonts['plain']))

    c = canvas.Canvas(filename=pdf_file, pagesize=pagesize, pageCompression=1)
    c.drawImage(bg_image, 0, 0, width=252, height=144, mask=None)

    # f = Frame(left, bottom, width, height)
    # note that both the bottom coord and the height will affect vertical positioning
    # add showBoundary=1 to see container
    f = Frame(0, 1.2*inch, 3.5*inch, 0.8*inch)
    f.addFromList(building_block,c)
    f = Frame(0, 0.57*inch, 3.5*inch, 0.8*inch)
    f.addFromList(name_block,c)

    # Close the PDF object cleanly
    c.showPage()
    c.save()

    # Create a preview image
    command = 'convert -page 252x144 %s %s' % (pdf_file, img_file)
    os.system(command)

    # Set session variable so we can pass filename back to preview
    request.session['filename_prefix'] = timestamp

    return HttpResponseRedirect(reverse('orders:vardata_preview'))
#}}}
#{{{ RossBc_print
def RossBc_print(request, ordereditem_id):
    ordereditem = OrderedItem.objects.get(pk=ordereditem_id)
    data = RossBc.objects.get(ordereditem = ordereditem_id)

    # Set some document specifics
    filename = "%s-%s.pdf" % (ordereditem.order.name, ordereditem_id)
    response = HttpResponse(mimetype='application/pdf')
    response['Content-Disposition'] = 'attachment; filename=%s' % filename # force save as dialog
    pagesize = (inch*17, inch*11) # width, height. Measured at 72dpi, so this is 1224x792
    bg_image = "%s/vardata_images/RossBc_bg_print.tif" % settings.MEDIA_ROOT
    fonts = ross_stylesheet()

    # Measurements of page
    left_margin = 0.75*inch  # distance from edge of page to leftmost cropmark
    bottom_margin = 0.5*inch # distance from edge of page to bottommost cropmark
    horiz_offset = 4*inch    # distance between the start of one piece & the next (ie left side to left side)
    vert_offset = 2*inch     # same but from top to top
    num_cols = 4             # number of columns of pieces
    num_rows = 5             # number of rows of pieces
    total_pieces = num_cols * num_rows

    # Format the lines and add them to the document
    building_block, name_block = [], []
    buildings, names = [], []
    building_block.append(Paragraph(cgi.escape(data.building_name), fonts['plain']))
    building_block.append(Paragraph("<font size=11>%s</font>" % cgi.escape(data.street_address), fonts['plain']))
    building_block.append(Paragraph("<font size=11>%s, %s</font>" % (cgi.escape(data.city), cgi.escape(data.province)), fonts['plain']))
    buildings.extend(total_pieces*building_block)
    name_block.append(Paragraph(cgi.escape(data.name), fonts['plain']))
    name_block.append(Paragraph(cgi.escape(data.job_title), fonts['plain-italic']))
    name_block.append(Paragraph("<font size=11>%s</font>" % data.direct_number, fonts['plain']))
    names.extend(total_pieces*name_block)

    # Loop through rows & columns and draw all the pieces
    c = canvas.Canvas(response, pagesize=pagesize, pageCompression=1)
    c.drawImage(bg_image, 0, 0, width=1224, height=792, mask=None)
    for row in range(num_rows):
        for col in range(num_cols):
            f = Frame(left_margin+(col*horiz_offset), (1.2*inch)+(row*vert_offset)+bottom_margin, 3.5*inch, 0.8*inch)
            f.addFromList(buildings,c)
            f = Frame(left_margin+(col*horiz_offset), (0.57*inch)+(row*vert_offset)+bottom_margin, 3.5*inch, 0.8*inch)
            f.addFromList(names,c)

    # Close the PDF object cleanly
    c.showPage()
    c.save()
    return response
#}}}

# Trillium College
#{{{ trillium_stylesheet
def trillium_stylesheet():
    stylesheet = {}

    # Register all required fonts
    folder = settings.FONT_DIR # from settings.py
    registered = pdfmetrics.getRegisteredFontNames()

    afmFile = os.path.join(folder, 'Myriad-Bold.afm')
    pfbFile = os.path.join(folder, 'Myriad-Bold.pfb')
    faceName = 'Myriad-Bold'
    if faceName not in registered:
        justFace = pdfmetrics.EmbeddedType1Face(afmFile, pfbFile)
        pdfmetrics.registerTypeFace(justFace)
        justFont = pdfmetrics.Font(faceName, faceName, 'WinAnsiEncoding')
        pdfmetrics.registerFont(justFont)

    afmFile = os.path.join(folder, 'MyriadPro-CondIt.afm')
    pfbFile = os.path.join(folder, 'MyriadPro-CondIt.pfb')
    faceName = 'MyriadPro-CondIt'
    if faceName not in registered:
        justFace = pdfmetrics.EmbeddedType1Face(afmFile, pfbFile)
        pdfmetrics.registerTypeFace(justFace)
        justFont = pdfmetrics.Font(faceName, faceName, 'WinAnsiEncoding')
        pdfmetrics.registerFont(justFont)

    afmFile = os.path.join(folder, 'MyriadPro-BoldCond.afm')
    pfbFile = os.path.join(folder, 'MyriadPro-BoldCond.pfb')
    faceName = 'MyriadPro-BoldCond'
    if faceName not in registered:
        justFace = pdfmetrics.EmbeddedType1Face(afmFile, pfbFile)
        pdfmetrics.registerTypeFace(justFace)
        justFont = pdfmetrics.Font(faceName, faceName, 'WinAnsiEncoding')
        pdfmetrics.registerFont(justFont)

    afmFile = os.path.join(folder, 'MyriadPro-SemiboldCondIt.afm')
    pfbFile = os.path.join(folder, 'MyriadPro-SemiboldCondIt.pfb')
    faceName = 'MyriadPro-SemiboldCondIt'
    if faceName not in registered:
        justFace = pdfmetrics.EmbeddedType1Face(afmFile, pfbFile)
        pdfmetrics.registerTypeFace(justFace)
        justFont = pdfmetrics.Font(faceName, faceName, 'WinAnsiEncoding')
        pdfmetrics.registerFont(justFont)

    p = ParagraphStyle('bold', None)
    p.fontName = 'Myriad-Bold'
    p.fontSize = 10
    p.leading = 10
    p.alignment = TA_LEFT
    p.textColor = HexColor(0x000000)
    stylesheet['name'] = p

    p = ParagraphStyle('bold', None)
    p.fontName = 'Myriad-Bold'
    p.fontSize = 10
    p.leading = 10
    p.alignment = TA_RIGHT
    p.textColor = HexColor(0x000000)
    stylesheet['phone'] = p

    p = ParagraphStyle('italic', None)
    p.fontName = 'MyriadPro-SemiboldCondIt'
    p.fontSize = 9
    p.leading = 9
    p.alignment = TA_LEFT
    p.textColor = HexColor(0x000000)
    stylesheet['title'] = p

    p = ParagraphStyle('italic', None)
    p.fontName = 'MyriadPro-CondIt'
    p.fontSize = 10
    p.leading = 10
    p.alignment = TA_RIGHT
    p.textColor = HexColor(0x000000)
    stylesheet['email'] = p

    p = ParagraphStyle('italic', None)
    p.fontName = 'MyriadPro-BoldCond'
    p.fontSize = 10
    p.leading = 10
    p.alignment = TA_RIGHT
    p.textColor = HexColor(0xffffff)
    stylesheet['address'] = p

    return stylesheet
#}}}
#{{{ TrilliumBc_render
def TrilliumBc_render(canvas, data, left_coord, bottom_coord):
    """
    Draws a single Trillium business card onto `canvas` (content Frames start at
    `left_coord` and `bottom_coord`) with the `data` provided, which represents
    either the data the user entered into the form (when creating a preview) or
    the database record (when creating a printready file).
    """
    fonts = trillium_stylesheet()

    card_type = data['card_type']
    campus = data['campus']

    if card_type.startswith('Individual'):
        name_block = []
        name_block.append(Paragraph(data['name'], fonts['name']))
        if card_type == 'Individual Admission Representative Card':
            name_block.append(Paragraph('Admission Representative', fonts['title']))
        else:
            name_block.append(Paragraph(data['title'], fonts['title']))

    if campus == 'Kingston':
        addr1 = '797 Princess Street'
        addr2 = 'Kingston, ON K7L 1G1'
        tel = '613-531-5138'
    elif campus == 'Oshawa':
        addr1 = '419 King Street W., Oshawa Centre'
        addr2 = 'Oshawa, ON L1J 2K5'
        tel = '905-723-1163'
    elif campus == 'Corporate':
        addr1 = '111 Simcoe St. N.'
        addr2 = 'Oshawa, ON L1G 4S4'
        tel = '905-448-4130'
    elif campus == 'Ottawa':
        addr1 = '2525 Carling Avenue, Lincoln Fields Mall'
        addr2 = 'Ottawa, ON K2B 7Z2'
        tel = '613-829-9059'
    elif campus == 'Peterborough':
        addr1 = '<font size="9">360 George Street N., Peterborough Square</font>'
        addr2 = '<font size="9">Peterborough, ON K9H 7E7</font>'
        tel = '705-742-5565'
    elif campus == 'St. Catharines':
        addr1 = '60 James Street, 2nd Floor'
        addr2 = 'St. Catharines, Ontario L2R 7E7'
        tel = '289-438-1918'
    elif campus == 'Toronto-Yonge':
        addr1 = '869 Yonge Street'
        addr2 = 'Toronto, ON M4W 2H2'
        tel = '416-907-2571'
    elif campus == 'Burlington':
        addr1 = '760 Brant Street, Burlington Square'
        addr2 = 'Burlington, ON L7R 4B7'
        tel = '905-632-3200'
    elif campus == 'Toronto-Church':
        addr1 = '557 Church Street, Main Floor'
        addr2 = 'Toronto, ON M4Y 2E2'
        tel = '416-907-2570'
    elif campus == 'Kitchener':
        addr1 = '1356 Weber Street East'
        addr2 = 'Kitchener, ON N2A 1C4'
        tel = '519-804-2463'
    else:
        street_addr, tel = "", ""

    if card_type.startswith('Individual'): # individual Admission Representative, individual campus personnel
        tel_line = '%s <font size="9">ext. %s</font>' % (tel, data['ext'])
        email_line = data["email"] + "@trilliumcollege.ca"
    else: # campus generic
        tel_line = "1.888.982.0575"
        email_line = "admissions@trilliumcollege.ca"

    contact_block = []
    contact_block.append(Paragraph(tel_line, fonts['phone']))
    contact_block.append(Paragraph(email_line, fonts['email']))

    address_block = []
    address_block.append(Paragraph(addr1, fonts['address']))
    address_block.append(Paragraph(addr2, fonts['address']))

    # Add above content blocks to Frames
    # f = Frame(left, bottom, width of container, height of container)
    # It should be safe to have the frames be the entire dimensions of the
    # finished piece. If not, note that both the bottom coord and the height
    # of the frame will affect vertical positioning (add showBoundary=1 to see
    # the container).
    if card_type.startswith('Individual'):
        f = Frame(left_coord, bottom_coord, 3.5*inch, 2*inch, leftPadding=0.13*inch, topPadding=1.03*inch)
        f.addFromList(name_block,canvas)

    f = Frame(left_coord, bottom_coord, 3.5*inch, 2*inch, rightPadding=0.13*inch, topPadding=1.03*inch)
    f.addFromList(contact_block,canvas)

    f = Frame(left_coord, bottom_coord, 3.5*inch, 2*inch, rightPadding=0.13*inch, topPadding=1.63*inch)
    f.addFromList(address_block,canvas)
#}}}
#{{{ TrilliumBc_1up
def TrilliumBc_1up(request):
    # Get the info that the user entered. These fields should match what's in the model.
    form_data = escape(request.session.get('form_data', None))

    # Set some document specifics
    timestamp = str(time()).replace('.','')
    pdf_file = "%s/previews/%s.pdf" % (settings.MEDIA_ROOT, timestamp)
    img_file = "%s/previews/%s.gif" % (settings.MEDIA_ROOT, timestamp)
    pagesize = (inch*3.5, inch*2) # width, height. Measured at 72dpi, so this is 252x144
    bg_image = "%s/vardata_images/TrilliumBc_bg_1up.tif" % settings.MEDIA_ROOT

    # Create the canvas
    c = canvas.Canvas(filename=pdf_file, pagesize=pagesize, pageCompression=1)
    c.drawImage(bg_image, 0, 0, width=252, height=144, mask=None)

    # Draw the actual content
    TrilliumBc_render(c, form_data, 0, 0)

    # Close the PDF object cleanly
    c.showPage()
    c.save()

    # Create a preview image
    command = 'convert -page 252x144 %s %s' % (pdf_file, img_file)
    os.system(command)

    # Set session variable so we can pass filename back to preview
    request.session['filename_prefix'] = timestamp

    return HttpResponseRedirect(reverse('orders:vardata_preview'))
#}}}
#{{{ TrilliumBc_print
def TrilliumBc_print(request, ordereditem_id):
    ordereditem = OrderedItem.objects.get(pk=ordereditem_id)
    data = TrilliumBc.objects.get(ordereditem = ordereditem_id)
    data = escape(data.__dict__)

    # Set some document specifics
    filename = "%s-%s.pdf" % (ordereditem.order.name, ordereditem_id)
    response = HttpResponse(mimetype='application/pdf')
    response['Content-Disposition'] = 'attachment; filename=%s' % filename # force save as dialog
    pagesize = (inch*17, inch*11) # width, height. Measured at 72dpi, so this is 1224x792
    bg_image = "%s/vardata_images/TrilliumBc_bg_print.tif" % settings.MEDIA_ROOT
    fonts = trillium_stylesheet()

    # Measurements of page
    left_margin = 0.75*inch   # distance from edge of page to leftmost cropmark
    bottom_margin = 0.75*inch # distance from edge of page to bottommost cropmark
    horiz_offset = 4*inch     # distance between the start of one piece & the next (ie left side to left side)
    vert_offset = 2.5*inch    # same but from top to top
    num_cols = 4              # number of columns of pieces
    num_rows = 5              # number of rows of pieces

    # Create the canvas
    c = canvas.Canvas(response, pagesize=pagesize, pageCompression=1)
    c.drawImage(bg_image, 0, 0, width=1224, height=792, mask=None)

    # Draw the actual content
    for row in range(num_rows):
        for col in range(num_cols):
            TrilliumBc_render(c, data, left_margin+(col*horiz_offset), (row*vert_offset)+bottom_margin)

    # Close the PDF object cleanly
    c.showPage()
    if data['card_type'] == 'Individual Admission Representative Card':
        back_image = "%s/vardata_images/TrilliumBc_backappts_bg_print.tif" % settings.MEDIA_ROOT
        c.drawImage(back_image, 0, 0, width=1224, height=792, mask=None)
    if data['card_type'] == 'Campus Generic Blank Card':
        back_image = "%s/vardata_images/TrilliumBc_backoffer_bg_print.tif" % settings.MEDIA_ROOT
        c.drawImage(back_image, 0, 0, width=1224, height=792, mask=None)
    c.save()

    return response
#}}}

# Kafko
#{{{ kafko_stylesheet
def kafko_stylesheet():
    stylesheet = {}

    # Register all required fonts
    folder = settings.FONT_DIR # from settings.py
    registered = pdfmetrics.getRegisteredFontNames()

    afmFile = os.path.join(folder, 'GillSans.afm')
    pfbFile = os.path.join(folder, 'GillSans.pfb')
    faceName = 'GillSans'
    if faceName not in registered:
        justFace = pdfmetrics.EmbeddedType1Face(afmFile, pfbFile)
        pdfmetrics.registerTypeFace(justFace)
        justFont = pdfmetrics.Font('GillSans', faceName, 'WinAnsiEncoding')
        pdfmetrics.registerFont(justFont)

    afmFile = os.path.join(folder, 'GillSans-Light.afm')
    pfbFile = os.path.join(folder, 'GillSans-Light.pfb')
    faceName = 'GillSans-Light'
    if faceName not in registered:
        justFace = pdfmetrics.EmbeddedType1Face(afmFile, pfbFile)
        pdfmetrics.registerTypeFace(justFace)
        justFont = pdfmetrics.Font('GillSans-Light', faceName, 'WinAnsiEncoding')
        pdfmetrics.registerFont(justFont)

    afmFile = os.path.join(folder, 'GillSans-Bold.afm')
    pfbFile = os.path.join(folder, 'GillSans-Bold.pfb')
    faceName = 'GillSans-Bold'
    if faceName not in registered:
        justFace = pdfmetrics.EmbeddedType1Face(afmFile, pfbFile)
        pdfmetrics.registerTypeFace(justFace)
        justFont = pdfmetrics.Font('GillSans-Bold', faceName, 'WinAnsiEncoding')
        pdfmetrics.registerFont(justFont)

    p = ParagraphStyle('light', None)
    p.fontName = 'GillSans-Light'
    p.fontSize = 7
    p.leading = 8.5
    p.textColor = HexColor(0x000000)
    p.alignment = TA_LEFT
    stylesheet['light'] = p

    p = ParagraphStyle('light', None)
    p.fontName = 'GillSans-Light'
    p.fontSize = 7
    p.leading = 8.5
    p.textColor = HexColor(0x000000)
    p.alignment = TA_RIGHT
    stylesheet['light-name'] = p

    p = ParagraphStyle('bold', None)
    p.fontName = 'GillSans-Bold'
    p.fontSize = 7
    p.leading = 8.5
    p.alignment = TA_LEFT
    p.textColor = HexColor(0x000000)
    stylesheet['bold'] = p

    p = ParagraphStyle('bold', None)
    p.fontName = 'GillSans-Bold'
    p.fontSize = 7
    p.leading = 8.5
    p.alignment = TA_RIGHT
    p.textColor = HexColor(0x000000)
    stylesheet['bold-name'] = p

    p = ParagraphStyle('spacer', None)
    p.spaceAfter = 6
    stylesheet['spacer'] = p

    return stylesheet
#}}}
#{{{ KafkoEnglishCanadaBc_render
def KafkoEnglishCanadaBc_render(canvas, data, left_coord, bottom_coord):
    """
    Draws a single KafkoEnglishCanada business card onto `canvas` (content Frames start at
    `left_coord` and `bottom_coord`) with the `data` provided, which represents
    either the data the user entered into the form (when creating a preview) or
    the database record (when creating a printready file).
    """
    fonts = kafko_stylesheet()

    address_block = []
    location = 'Ontario Branch'
    addr1 = '1231 Kamato Road'
    addr2 = 'Mississauga, ON L4W 2M2'
    address_block.append(Paragraph(location, fonts['bold']))
    address_block.append(Paragraph(addr1, fonts['light']))
    address_block.append(Paragraph(addr2, fonts['light']))
    address_block.append(Paragraph("", fonts['spacer']))
    address_block.append(Paragraph("Customer Service", fonts['light']))
    address_block.append(Paragraph('<font name="GillSans" color="0xef4723">T</font><font color="white" size="2">__</font>1.866.995.2356', fonts['light']))
    address_block.append(Paragraph('<font name="GillSans" color="0xef4723">F</font><font color="white" size="2">___</font>1.888.228.2217', fonts['light']))

    name_block = []
    name_block.append(Paragraph(data['name'], fonts['bold-name']))
    name_block.append(Paragraph(data['title'], fonts['light-name']))

    nums_block = []
    tel = '<font name="GillSans" color="0xef4723">T</font><font color="white" size="2">__..</font>905.624.3000 x %s' % data['ext']
    nums_block.append(Paragraph(tel, fonts['light']))
    if data['fax']:
        fax = phone_parts(data['fax'])
        fax_line = '<font name="GillSans" color="0xef4723">F</font><font color="white" size="2">___..</font>%s.%s.%s' % (fax[0], fax[1], fax[2])
        nums_block.append(Paragraph(fax_line, fonts['light']))
    if data['cell']:
        cell = phone_parts(data['cell'])
        cell_line = '<font name="GillSans" color="0xef4723">C</font><font color="white" size="2">__</font>%s.%s.%s' % (cell[0], cell[1], cell[2])
        nums_block.append(Paragraph(cell_line, fonts['light']))
    email = '<font name="GillSans" color="0xef4723">E</font><font color="white" size="2">___.</font>%s@kafkomfg.com' % data['email']
    nums_block.append(Paragraph(email, fonts['light']))

    # Add above content blocks to Frames
    # f = Frame(left, bottom, width of container, height of container)
    # It should be safe to have the frames be the entire dimensions of the
    # finished piece. If not, note that both the bottom coord and the height
    # of the frame will affect vertical positioning (add showBoundary=1 to see
    # the container).
    f = Frame(left_coord, bottom_coord, 3.5*inch, 2*inch, leftPadding=0.25*inch, topPadding=0.84*inch)
    f.addFromList(address_block,canvas)
    f = Frame(left_coord, bottom_coord, 3.5*inch, 2*inch, rightPadding=0.25*inch, topPadding=0.73*inch)
    f.addFromList(name_block,canvas)
    f = Frame(left_coord, bottom_coord, 3.5*inch, 2*inch, leftPadding=1.94*inch, topPadding=1.15*inch)
    f.addFromList(nums_block,canvas)
#}}}
#{{{ KafkoEnglishCanadaBc_1up
def KafkoEnglishCanadaBc_1up(request):
    # Get the info that the user entered. These fields should match what's in the model.
    form_data = escape(request.session.get('form_data', None))

    # Set some document specifics
    timestamp = str(time()).replace('.','')
    pdf_file = "%s/previews/%s.pdf" % (settings.MEDIA_ROOT, timestamp)
    img_file = "%s/previews/%s.gif" % (settings.MEDIA_ROOT, timestamp)
    pagesize = (inch*3.5, inch*2) # width, height. Measured at 72dpi, so this is 252x144
    bg_image = "%s/vardata_images/KafkoEnglishCanadaBc_bg_1up.tif" % settings.MEDIA_ROOT

    # Create the canvas
    c = canvas.Canvas(filename=pdf_file, pagesize=pagesize, pageCompression=1)
    c.drawImage(bg_image, 0, 0, width=252, height=144, mask=None)

    # Draw the actual content
    KafkoEnglishCanadaBc_render(c, form_data, 0, 0)

    # Close the PDF object cleanly
    c.showPage()
    c.save()

    # Create a preview image
    command = 'convert -page 252x144 %s %s' % (pdf_file, img_file)
    os.system(command)

    # Set session variable so we can pass filename back to preview
    request.session['filename_prefix'] = timestamp

    return HttpResponseRedirect(reverse('orders:vardata_preview'))
#}}}
#{{{ KafkoEnglishCanadaBc_print
def KafkoEnglishCanadaBc_print(request, ordereditem_id):
    ordereditem = OrderedItem.objects.get(pk=ordereditem_id)
    data = KafkoEnglishCanadaBc.objects.get(ordereditem = ordereditem_id)
    data = escape(data.__dict__)

    # Set some document specifics
    filename = "%s-%s.pdf" % (ordereditem.order.name, ordereditem_id)
    response = HttpResponse(mimetype='application/pdf')
    response['Content-Disposition'] = 'attachment; filename=%s' % filename # force save as dialog
    pagesize = (inch*17, inch*11) # width, height. Measured at 72dpi, so this is 1224x792
    bg_image = "%s/vardata_images/KafkoEnglishCanadaBc_bg_print.tif" % settings.MEDIA_ROOT
    fonts = trillium_stylesheet()

    # Measurements of page
    left_margin = 0.75*inch   # distance from edge of page to leftmost cropmark
    bottom_margin = 0.75*inch # distance from edge of page to bottommost cropmark
    horiz_offset = 4*inch     # distance between the start of one piece & the next (ie left side to left side)
    vert_offset = 2.5*inch    # same but from top to top
    num_cols = 4              # number of columns of pieces
    num_rows = 5              # number of rows of pieces

    # Create the canvas
    c = canvas.Canvas(response, pagesize=pagesize, pageCompression=1)
    c.drawImage(bg_image, 0, 0, width=1224, height=792, mask=None)

    # Draw the actual content
    for row in range(num_rows):
        for col in range(num_cols):
            KafkoEnglishCanadaBc_render(c, data, left_margin+(col*horiz_offset), (row*vert_offset)+bottom_margin)

    # Close the PDF object cleanly
    c.showPage()
    c.save()
    return response
#}}}
#{{{ KafkoFrenchCanadaBc_render
def KafkoFrenchCanadaBc_render(canvas, data, left_coord, bottom_coord):
    """
    Draws a single KafkoFrenchCanada business card onto `canvas` (content Frames start at
    `left_coord` and `bottom_coord`) with the `data` provided, which represents
    either the data the user entered into the form (when creating a preview) or
    the database record (when creating a printready file).
    """
    fonts = kafko_stylesheet()

    address_block = []
    addr1 = '3645, boul. des Enterprises'
    addr2 = 'Terrebonne, Qu\xc3\xa9bec'
    addr3 = 'J6X 4J9'
    address_block.append(Paragraph(addr1, fonts['light']))
    address_block.append(Paragraph(addr2, fonts['light']))
    address_block.append(Paragraph(addr3, fonts['light']))
    address_block.append(Paragraph("", fonts['spacer']))
    address_block.append(Paragraph("Service \xc3\xa0 la client\xc3\xa8le /", fonts['light']))
    address_block.append(Paragraph("Customer Service", fonts['light']))
    address_block.append(Paragraph('<font name="GillSans" color="0xef4723">T</font> 1.800.516.1204', fonts['light']))

    name_block = []
    name_block.append(Paragraph(data['name'], fonts['bold-name']))
    name_block.append(Paragraph(data['title_fr'], fonts['light-name']))
    name_block.append(Paragraph(data['title_en'], fonts['light-name']))

    nums_block = []
    tel = '<font name="GillSans" color="0xef4723">T</font><font color="white" size="2">__..</font>905.624.3000 x %s' % data['ext']
    nums_block.append(Paragraph(tel, fonts['light']))
    fax_line = '<font name="GillSans" color="0xef4723">F</font><font color="white" size="2">___..</font>450.968.2313 / 1.888.923.2313'
    nums_block.append(Paragraph(fax_line, fonts['light']))
    email = '<font name="GillSans" color="0xef4723">E</font><font color="white" size="2">___.</font>%s@kafkomfg.com' % data['email']
    nums_block.append(Paragraph(email, fonts['light']))

    # Add above content blocks to Frames
    # f = Frame(left, bottom, width of container, height of container)
    # It should be safe to have the frames be the entire dimensions of the
    # finished piece. If not, note that both the bottom coord and the height
    # of the frame will affect vertical positioning (add showBoundary=1 to see
    # the container).
    f = Frame(left_coord, bottom_coord, 3.5*inch, 2*inch, leftPadding=0.25*inch, topPadding=0.84*inch)
    f.addFromList(address_block,canvas)
    f = Frame(left_coord, bottom_coord, 3.5*inch, 2*inch, rightPadding=0.25*inch, topPadding=0.73*inch)
    f.addFromList(name_block,canvas)
    f = Frame(left_coord, bottom_coord, 3.5*inch, 2*inch, leftPadding=1.94*inch, topPadding=1.15*inch)
    f.addFromList(nums_block,canvas)
#}}}
#{{{ KafkoFrenchCanadaBc_1up
def KafkoFrenchCanadaBc_1up(request):
    # Get the info that the user entered. These fields should match what's in the model.
    form_data = escape(request.session.get('form_data', None))

    # Set some document specifics
    timestamp = str(time()).replace('.','')
    pdf_file = "%s/previews/%s.pdf" % (settings.MEDIA_ROOT, timestamp)
    img_file = "%s/previews/%s.gif" % (settings.MEDIA_ROOT, timestamp)
    pagesize = (inch*3.5, inch*2) # width, height. Measured at 72dpi, so this is 252x144
    bg_image = "%s/vardata_images/KafkoFrenchCanadaBc_bg_1up.tif" % settings.MEDIA_ROOT

    # Create the canvas
    c = canvas.Canvas(filename=pdf_file, pagesize=pagesize, pageCompression=1)
    c.drawImage(bg_image, 0, 0, width=252, height=144, mask=None)

    # Draw the actual content
    KafkoFrenchCanadaBc_render(c, form_data, 0, 0)

    # Close the PDF object cleanly
    c.showPage()
    c.save()

    # Create a preview image
    command = 'convert -page 252x144 %s %s' % (pdf_file, img_file)
    os.system(command)

    # Set session variable so we can pass filename back to preview
    request.session['filename_prefix'] = timestamp

    return HttpResponseRedirect(reverse('orders:vardata_preview'))
#}}}
#{{{ KafkoFrenchCanadaBc_print
def KafkoFrenchCanadaBc_print(request, ordereditem_id):
    ordereditem = OrderedItem.objects.get(pk=ordereditem_id)
    data = KafkoFrenchCanadaBc.objects.get(ordereditem = ordereditem_id)
    data = escape(data.__dict__)

    # Set some document specifics
    filename = "%s-%s.pdf" % (ordereditem.order.name, ordereditem_id)
    response = HttpResponse(mimetype='application/pdf')
    response['Content-Disposition'] = 'attachment; filename=%s' % filename # force save as dialog
    pagesize = (inch*17, inch*11) # width, height. Measured at 72dpi, so this is 1224x792
    bg_image = "%s/vardata_images/KafkoFrenchCanadaBc_bg_print.tif" % settings.MEDIA_ROOT
    fonts = trillium_stylesheet()

    # Measurements of page
    left_margin = 0.75*inch   # distance from edge of page to leftmost cropmark
    bottom_margin = 0.75*inch # distance from edge of page to bottommost cropmark
    horiz_offset = 4*inch     # distance between the start of one piece & the next (ie left side to left side)
    vert_offset = 2.5*inch    # same but from top to top
    num_cols = 4              # number of columns of pieces
    num_rows = 5              # number of rows of pieces

    # Create the canvas
    c = canvas.Canvas(response, pagesize=pagesize, pageCompression=1)
    c.drawImage(bg_image, 0, 0, width=1224, height=792, mask=None)

    # Draw the actual content
    for row in range(num_rows):
        for col in range(num_cols):
            KafkoFrenchCanadaBc_render(c, data, left_margin+(col*horiz_offset), (row*vert_offset)+bottom_margin)

    # Close the PDF object cleanly
    c.showPage()
    c.save()
    return response
#}}}
#{{{ KafkoUsBc_render
def KafkoUsBc_render(canvas, data, left_coord, bottom_coord):
    """
    Draws a single KafkoUs business card onto `canvas` (content Frames start at
    `left_coord` and `bottom_coord`) with the `data` provided, which represents
    either the data the user entered into the form (when creating a preview) or
    the database record (when creating a printready file).
    """
    fonts = kafko_stylesheet()

    address_block = []
    # Sacramento, CA
    if data['location'] == 'farwest':
        address_block.append(Paragraph('Farwest Branch', fonts['bold']))
        address_block.append(Paragraph('9611 Oates Drive, Suite C', fonts['light']))
        address_block.append(Paragraph('Sacramento, CA 95827', fonts['light']))
        tel = '916.363.8595'
        cs_tel = '1.800.222.4644'
        cs_fax = '1.916.363.8593'
    # Decatur, GA
    elif data['location'] == 'southeast':
        address_block.append(Paragraph('Southeast Branch', fonts['bold']))
        address_block.append(Paragraph('5393 Truman Drive', fonts['light']))
        address_block.append(Paragraph('Decatur, GA, 30035', fonts['light']))
        tel = '770.987.3316'
        cs_tel = '1.800.545.7030'
        cs_fax = '1.888.331.3382'
    # Whitmore Lake, MI
    elif data['location'] == 'midwest-mi':
        address_block.append(Paragraph('Midwest Branch', fonts['bold']))
        address_block.append(Paragraph('9293 M-36', fonts['light']))
        address_block.append(Paragraph('Whitmore Lake, MI 48189', fonts['light']))
        tel = '734.449.8377'
        cs_tel = '1.888.485.7280'
        cs_fax = '1.800.788.7665'
    # Fort Wayne, IN
    elif data['location'] == 'midwest-in':
        address_block.append(Paragraph('Midwest Branch', fonts['bold']))
        address_block.append(Paragraph('6930 Gettysburg Pike', fonts['light']))
        address_block.append(Paragraph('Fort Wayne, IN 46804', fonts['light']))
        tel = '260.459.4100'
        cs_tel = '1.888.485.7280'
        cs_fax = '1.800.788.7665'
    # Latham, NY
    elif data['location'] == 'northeast':
        address_block.append(Paragraph('Northeast Branch', fonts['bold']))
        address_block.append(Paragraph('787 Watervliet Shaker Rd', fonts['light']))
        address_block.append(Paragraph('Latham, NY 12110', fonts['light']))
        tel = '609.587.5800'
        cs_tel = '1.800.878.0801'
        cs_fax = '1.800.520.3091'

    address_block.append(Paragraph("", fonts['spacer']))
    address_block.append(Paragraph("Customer Service", fonts['light']))
    address_block.append(Paragraph('<font name="GillSans" color="0xef4723">T</font><font color="white" size="2">__</font>%s' % cs_tel, fonts['light']))
    address_block.append(Paragraph('<font name="GillSans" color="0xef4723">F</font><font color="white" size="2">___</font>%s' % cs_fax, fonts['light']))

    name_block = []
    name_block.append(Paragraph(data['name'], fonts['bold-name']))
    name_block.append(Paragraph(data['title'], fonts['light-name']))

    nums_block = []
    tel_line = '<font name="GillSans" color="0xef4723">T</font><font color="white" size="2">__..</font>%s x %s' % (tel, data['ext'])
    nums_block.append(Paragraph(tel_line, fonts['light']))
    if data['fax']:
        fax = phone_parts(data['fax'])
        fax_line = '<font name="GillSans" color="0xef4723">F</font><font color="white" size="2">___..</font>%s.%s.%s' % (fax[0], fax[1], fax[2])
        nums_block.append(Paragraph(fax_line, fonts['light']))
    if data['cell']:
        cell = phone_parts(data['cell'])
        cell_line = '<font name="GillSans" color="0xef4723">C</font><font color="white" size="2">__</font>%s.%s.%s' % (cell[0], cell[1], cell[2])
        nums_block.append(Paragraph(cell_line, fonts['light']))
    email = '<font name="GillSans" color="0xef4723">E</font><font color="white" size="2">___.</font>%s@kafkomfg.com' % data['email']
    nums_block.append(Paragraph(email, fonts['light']))

    # Add above content blocks to Frames
    # f = Frame(left, bottom, width of container, height of container)
    # It should be safe to have the frames be the entire dimensions of the
    # finished piece. If not, note that both the bottom coord and the height
    # of the frame will affect vertical positioning (add showBoundary=1 to see
    # the container).
    f = Frame(left_coord, bottom_coord, 3.5*inch, 2*inch, leftPadding=0.25*inch, topPadding=0.84*inch)
    f.addFromList(address_block,canvas)
    f = Frame(left_coord, bottom_coord, 3.5*inch, 2*inch, rightPadding=0.25*inch, topPadding=0.73*inch)
    f.addFromList(name_block,canvas)
    f = Frame(left_coord, bottom_coord, 3.5*inch, 2*inch, leftPadding=1.94*inch, topPadding=1.15*inch)
    f.addFromList(nums_block,canvas)
#}}}
#{{{ KafkoUsBc_1up
def KafkoUsBc_1up(request):
    # Get the info that the user entered. These fields should match what's in the model.
    form_data = escape(request.session.get('form_data', None))

    # Set some document specifics
    timestamp = str(time()).replace('.','')
    pdf_file = "%s/previews/%s.pdf" % (settings.MEDIA_ROOT, timestamp)
    img_file = "%s/previews/%s.gif" % (settings.MEDIA_ROOT, timestamp)
    pagesize = (inch*3.5, inch*2) # width, height. Measured at 72dpi, so this is 252x144
    bg_image = "%s/vardata_images/KafkoEnglishCanadaBc_bg_1up.tif" % settings.MEDIA_ROOT

    # Create the canvas
    c = canvas.Canvas(filename=pdf_file, pagesize=pagesize, pageCompression=1)
    c.drawImage(bg_image, 0, 0, width=252, height=144, mask=None)

    # Draw the actual content
    KafkoUsBc_render(c, form_data, 0, 0)

    # Close the PDF object cleanly
    c.showPage()
    c.save()

    # Create a preview image
    command = 'convert -page 252x144 %s %s' % (pdf_file, img_file)
    os.system(command)

    # Set session variable so we can pass filename back to preview
    request.session['filename_prefix'] = timestamp

    return HttpResponseRedirect(reverse('orders:vardata_preview'))
#}}}
#{{{ KafkoUsBc_print
def KafkoUsBc_print(request, ordereditem_id):
    ordereditem = OrderedItem.objects.get(pk=ordereditem_id)
    data = KafkoUsBc.objects.get(ordereditem = ordereditem_id)
    data = escape(data.__dict__)

    # Set some document specifics
    filename = "%s-%s.pdf" % (ordereditem.order.name, ordereditem_id)
    response = HttpResponse(mimetype='application/pdf')
    response['Content-Disposition'] = 'attachment; filename=%s' % filename # force save as dialog
    pagesize = (inch*17, inch*11) # width, height. Measured at 72dpi, so this is 1224x792
    bg_image = "%s/vardata_images/KafkoEnglishCanadaBc_bg_print.tif" % settings.MEDIA_ROOT
    fonts = trillium_stylesheet()

    # Measurements of page
    left_margin = 0.75*inch   # distance from edge of page to leftmost cropmark
    bottom_margin = 0.75*inch # distance from edge of page to bottommost cropmark
    horiz_offset = 4*inch     # distance between the start of one piece & the next (ie left side to left side)
    vert_offset = 2.5*inch    # same but from top to top
    num_cols = 4              # number of columns of pieces
    num_rows = 5              # number of rows of pieces

    # Create the canvas
    c = canvas.Canvas(response, pagesize=pagesize, pageCompression=1)
    c.drawImage(bg_image, 0, 0, width=1224, height=792, mask=None)

    # Draw the actual content
    for row in range(num_rows):
        for col in range(num_cols):
            KafkoUsBc_render(c, data, left_margin+(col*horiz_offset), (row*vert_offset)+bottom_margin)

    # Close the PDF object cleanly
    c.showPage()
    c.save()
    return response
#}}}

# Algonquin
#{{{ algonquin_stylesheet
def algonquin_stylesheet():
    stylesheet = {}

    # Register all required fonts
    folder = settings.FONT_DIR # from settings.py
    registered = pdfmetrics.getRegisteredFontNames()

    afmFile = os.path.join(folder, 'Times-Bold.afm')
    pfbFile = os.path.join(folder, 'Times-Bold.pfb')
    faceName = 'Times-Bold'
    if faceName not in registered:
        justFace = pdfmetrics.EmbeddedType1Face(afmFile, pfbFile)
        pdfmetrics.registerTypeFace(justFace)
        justFont = pdfmetrics.Font('Times-Bold', faceName, 'WinAnsiEncoding')
        pdfmetrics.registerFont(justFont)

    afmFile = os.path.join(folder, 'Times-Italic.afm')
    pfbFile = os.path.join(folder, 'Times-Italic.pfb')
    faceName = 'Times-Italic'
    if faceName not in registered:
        justFace = pdfmetrics.EmbeddedType1Face(afmFile, pfbFile)
        pdfmetrics.registerTypeFace(justFace)
        justFont = pdfmetrics.Font('Times-Italic', faceName, 'WinAnsiEncoding')
        pdfmetrics.registerFont(justFont)

    afmFile = os.path.join(folder, 'ArialNarrow.afm')
    pfbFile = os.path.join(folder, 'ArialNarrow.pfb')
    faceName = 'ArialNarrow'
    if faceName not in registered:
        justFace = pdfmetrics.EmbeddedType1Face(afmFile, pfbFile)
        pdfmetrics.registerTypeFace(justFace)
        justFont = pdfmetrics.Font('ArialNarrow', faceName, 'WinAnsiEncoding')
        pdfmetrics.registerFont(justFont)

    p = ParagraphStyle('times-bold', None)
    p.fontName = 'Times-Bold'
    p.fontSize = 9
    p.leading = 10.5
    p.alignment = TA_LEFT
    p.textColor = HexColor(0x000000)
    stylesheet['times-bold'] = p

    p = ParagraphStyle('times-italic', None)
    p.fontName = 'Times-Italic'
    p.fontSize = 6.5
    p.leading = 9
    p.alignment = TA_LEFT
    p.textColor = HexColor(0x000000)
    stylesheet['times-italic'] = p

    p = ParagraphStyle('arial', None)
    p.fontName = 'ArialNarrow'
    p.fontSize = 7
    p.leading = 9
    p.alignment = TA_RIGHT
    p.textColor = HexColor(0x000000)
    stylesheet['arial'] = p

    return stylesheet
#}}}
#{{{ AlgonquinBc_render
def AlgonquinBc_render(canvas, data, left_coord, bottom_coord, location):
    """
    Draws a single Algonquin business card onto `canvas` (content Frames start at
    `left_coord` and `bottom_coord`) with the `data` provided, which represents
    either the data the user entered into the form (when creating a preview) or
    the database record (when creating a printready file).
    """
    fonts = algonquin_stylesheet()

    address_block = []
    if location == 'Mississauga':
        address_block.append(Paragraph('3025 Hurontario St., #600', fonts['arial']))
        address_block.append(Paragraph('Mississauga, Ontario, L5A 2H1', fonts['arial']))
        address_block.append(Paragraph('Phone: 905.361.2380', fonts['arial']))
        address_block.append(Paragraph('Fax: 905.361.0603', fonts['arial']))
    elif location == 'Ottawa':
        address_block.append(Paragraph('1830 Bank Street', fonts['arial']))
        address_block.append(Paragraph('Ottawa, Ontario, K1V 7Y6', fonts['arial']))
        address_block.append(Paragraph('Phone: 613.722.7811', fonts['arial']))
        address_block.append(Paragraph('Fax: 613.722.4494', fonts['arial']))

    email_line = '%s@algonquinacademy.com' % data['email']
    address_block.append(Paragraph(email_line, fonts['arial']))
    address_block.append(Paragraph('www.algonquinacademy.com', fonts['arial']))

    name_block = []
    name_block.append(Paragraph(data['name'], fonts['times-bold']))
    name_block.append(Paragraph(data['title'], fonts['times-italic']))

    # Add above content blocks to Frames
    # f = Frame(left, bottom, width of container, height of container)
    # It should be safe to have the frames be the entire dimensions of the
    # finished piece. If not, note that both the bottom coord and the height
    # of the frame will affect vertical positioning (add showBoundary=1 to see
    # the container).
    f = Frame(left_coord, bottom_coord, 3.5*inch, 2*inch, rightPadding=0.2*inch, topPadding=1.12*inch)
    f.addFromList(address_block,canvas)
    f = Frame(left_coord, bottom_coord, 3.5*inch, 2*inch, leftPadding=0.2*inch, topPadding=0.77*inch)
    f.addFromList(name_block,canvas)
#}}}
#{{{ AlgonquinMississaugaBc_1up
def AlgonquinMississaugaBc_1up(request):
    # Get the info that the user entered. These fields should match what's in the model.
    form_data = escape(request.session.get('form_data', None))

    # Set some document specifics
    timestamp = str(time()).replace('.','')
    pdf_file = "%s/previews/%s.pdf" % (settings.MEDIA_ROOT, timestamp)
    img_file = "%s/previews/%s.gif" % (settings.MEDIA_ROOT, timestamp)
    pagesize = (inch*3.5, inch*2) # width, height. Measured at 72dpi, so this is 252x144
    bg_image = "%s/vardata_images/AlgonquinBc_bg_1up.tif" % settings.MEDIA_ROOT

    # Create the canvas
    c = canvas.Canvas(filename=pdf_file, pagesize=pagesize, pageCompression=1)
    c.drawImage(bg_image, 0, 0, width=252, height=144, mask=None)

    # Draw the actual content
    AlgonquinBc_render(c, form_data, 0, 0, 'Mississauga')

    # Close the PDF object cleanly
    c.showPage()
    c.save()

    # Create a preview image
    command = 'convert -page 252x144 %s %s' % (pdf_file, img_file)
    os.system(command)

    # Set session variable so we can pass filename back to preview
    request.session['filename_prefix'] = timestamp

    return HttpResponseRedirect(reverse('orders:vardata_preview'))
#}}}
#{{{ AlgonquinMississaugaBc_print
def AlgonquinMississaugaBc_print(request, ordereditem_id):
    ordereditem = OrderedItem.objects.get(pk=ordereditem_id)
    data = AlgonquinMississaugaBc.objects.get(ordereditem = ordereditem_id)
    data = escape(data.__dict__)

    # Set some document specifics
    filename = "%s-%s.pdf" % (ordereditem.order.name, ordereditem_id)
    response = HttpResponse(mimetype='application/pdf')
    response['Content-Disposition'] = 'attachment; filename=%s' % filename # force save as dialog
    pagesize = (inch*17, inch*11) # width, height. Measured at 72dpi, so this is 1224x792
    bg_image = "%s/vardata_images/AlgonquinBc_bg_print.tif" % settings.MEDIA_ROOT
    fonts = trillium_stylesheet()

    # Measurements of page
    left_margin = 0.75*inch   # distance from edge of page to leftmost cropmark
    bottom_margin = 0.75*inch # distance from edge of page to bottommost cropmark
    horiz_offset = 4*inch     # distance between the start of one piece & the next (ie left side to left side)
    vert_offset = 2.5*inch    # same but from top to top
    num_cols = 4              # number of columns of pieces
    num_rows = 5              # number of rows of pieces

    # Create the canvas
    c = canvas.Canvas(response, pagesize=pagesize, pageCompression=1)
    c.drawImage(bg_image, 0, 0, width=1224, height=792, mask=None)

    # Draw the actual content
    for row in range(num_rows):
        for col in range(num_cols):
            AlgonquinBc_render(c, data, left_margin+(col*horiz_offset), (row*vert_offset)+bottom_margin, 'Mississauga')

    # Close the PDF object cleanly
    c.showPage()
    c.save()
    return response
#}}}
#{{{ AlgonquinOttawaBc_1up
def AlgonquinOttawaBc_1up(request):
    # Get the info that the user entered. These fields should match what's in the model.
    form_data = escape(request.session.get('form_data', None))

    # Set some document specifics
    timestamp = str(time()).replace('.','')
    pdf_file = "%s/previews/%s.pdf" % (settings.MEDIA_ROOT, timestamp)
    img_file = "%s/previews/%s.gif" % (settings.MEDIA_ROOT, timestamp)
    pagesize = (inch*3.5, inch*2) # width, height. Measured at 72dpi, so this is 252x144
    bg_image = "%s/vardata_images/AlgonquinBc_bg_1up.tif" % settings.MEDIA_ROOT

    # Create the canvas
    c = canvas.Canvas(filename=pdf_file, pagesize=pagesize, pageCompression=1)
    c.drawImage(bg_image, 0, 0, width=252, height=144, mask=None)

    # Draw the actual content
    AlgonquinBc_render(c, form_data, 0, 0, 'Ottawa')

    # Close the PDF object cleanly
    c.showPage()
    c.save()

    # Create a preview image
    command = 'convert -page 252x144 %s %s' % (pdf_file, img_file)
    os.system(command)

    # Set session variable so we can pass filename back to preview
    request.session['filename_prefix'] = timestamp

    return HttpResponseRedirect(reverse('orders:vardata_preview'))
#}}}
#{{{ AlgonquinOttawaBc_print
def AlgonquinOttawaBc_print(request, ordereditem_id):
    ordereditem = OrderedItem.objects.get(pk=ordereditem_id)
    data = AlgonquinOttawaBc.objects.get(ordereditem = ordereditem_id)
    data = escape(data.__dict__)

    # Set some document specifics
    filename = "%s-%s.pdf" % (ordereditem.order.name, ordereditem_id)
    response = HttpResponse(mimetype='application/pdf')
    response['Content-Disposition'] = 'attachment; filename=%s' % filename # force save as dialog
    pagesize = (inch*17, inch*11) # width, height. Measured at 72dpi, so this is 1224x792
    bg_image = "%s/vardata_images/AlgonquinBc_bg_print.tif" % settings.MEDIA_ROOT
    fonts = trillium_stylesheet()

    # Measurements of page
    left_margin = 0.75*inch   # distance from edge of page to leftmost cropmark
    bottom_margin = 0.75*inch # distance from edge of page to bottommost cropmark
    horiz_offset = 4*inch     # distance between the start of one piece & the next (ie left side to left side)
    vert_offset = 2.5*inch    # same but from top to top
    num_cols = 4              # number of columns of pieces
    num_rows = 5              # number of rows of pieces

    # Create the canvas
    c = canvas.Canvas(response, pagesize=pagesize, pageCompression=1)
    c.drawImage(bg_image, 0, 0, width=1224, height=792, mask=None)

    # Draw the actual content
    for row in range(num_rows):
        for col in range(num_cols):
            AlgonquinBc_render(c, data, left_margin+(col*horiz_offset), (row*vert_offset)+bottom_margin, 'Ottawa')

    # Close the PDF object cleanly
    c.showPage()
    c.save()
    return response
#}}}

# Superior Energy
#{{{ superior_stylesheet
def superior_stylesheet():
    stylesheet = {}

    # Register all required fonts
    folder = settings.FONT_DIR # from settings.py
    registered = pdfmetrics.getRegisteredFontNames()

    afmFile = os.path.join(folder, 'Myriad-Roman.afm')
    pfbFile = os.path.join(folder, 'Myriad-Roman.pfb')
    faceName = 'Myriad-Roman'
    if faceName not in registered:
        justFace = pdfmetrics.EmbeddedType1Face(afmFile, pfbFile)
        pdfmetrics.registerTypeFace(justFace)
        justFont = pdfmetrics.Font('Myriad-Roman', faceName, 'WinAnsiEncoding')
        pdfmetrics.registerFont(justFont)

    afmFile = os.path.join(folder, 'Myriad-Bold.afm')
    pfbFile = os.path.join(folder, 'Myriad-Bold.pfb')
    faceName = 'Myriad-Bold'
    if faceName not in registered:
        justFace = pdfmetrics.EmbeddedType1Face(afmFile, pfbFile)
        pdfmetrics.registerTypeFace(justFace)
        justFont = pdfmetrics.Font(faceName, faceName, 'WinAnsiEncoding')
        pdfmetrics.registerFont(justFont)

    p = ParagraphStyle('bold', None)
    p.fontName = 'Myriad-Bold'
    p.fontSize = 10.5
    p.leading = 11
    p.alignment = TA_CENTER
    p.textColor = HexColor(0x000000)
    stylesheet['bold'] = p

    p = ParagraphStyle('title', None)
    p.fontName = 'Myriad-Roman'
    p.fontSize = 8
    p.leading = 9
    p.alignment = TA_CENTER
    p.textColor = HexColor(0x000000)
    stylesheet['title'] = p

    p = ParagraphStyle('roman', None)
    p.fontName = 'Myriad-Roman'
    p.fontSize = 7
    p.leading = 8
    p.alignment = TA_LEFT
    p.textColor = HexColor(0x000000)
    stylesheet['roman'] = p

    p = ParagraphStyle('spacer', None)
    p.spaceAfter = 9
    stylesheet['spacer'] = p

    return stylesheet
#}}}
#{{{ SuperiorEnergyBc_render
def SuperiorEnergyBc_render(canvas, data, left_coord, bottom_coord):
    """
    Draws a single Superior Energy business card onto `canvas` (content Frames start at
    `left_coord` and `bottom_coord`) with the `data` provided, which represents
    either the data the user entered into the form (when creating a preview) or
    the database record (when creating a printready file)
    """
    fonts = superior_stylesheet()

    name_block = []
    name_block.append(Paragraph(data['name'], fonts['bold']))
    name_block.append(Paragraph(data['title'], fonts['title']))

    address_block = []
    address_block.append(Paragraph('6860 Century Avenue', fonts['roman']))
    address_block.append(Paragraph('East Tower, Suite 3000', fonts['roman']))
    address_block.append(Paragraph('Mississauga, ON  L5N 2W5', fonts['roman']))
    address_block.append(Paragraph('www.superiorenergy.ca', fonts['roman']))

    direct = phone_parts(data['direct'])
    cell = phone_parts(data['cell'])
    fax = phone_parts(data['fax'])
    direct_line = 'Direct: <font color="white" size="1">.</font>%s-%s-%s' % (direct[0], direct[1], direct[2])
    cell_line = 'Cell: <font color="white" size="2">______..</font>%s-%s-%s' % (cell[0], cell[1], cell[2])
    fax_line = 'Fax: <font color="white" size="2">_______..</font>%s-%s-%s' % (fax[0], fax[1], fax[2])
    email_line = "%s@superiorenergy.ca" % data['email']
    contact_block = []
    contact_block.append(Paragraph(direct_line, fonts['roman']))
    contact_block.append(Paragraph(cell_line, fonts['roman']))
    contact_block.append(Paragraph(fax_line, fonts['roman']))
    contact_block.append(Paragraph(email_line, fonts['roman']))

    # Add above content blocks to Frames
    # f = Frame(left, bottom, width of container, height of container)
    # It should be safe to have the frames be the entire dimensions of the
    # finished piece. If not, note that both the bottom coord and the height
    # of the frame will affect vertical positioning (add showBoundary=1 to see
    # the container).
    f = Frame(left_coord, bottom_coord, 3.5*inch, 2*inch, rightPadding=0, topPadding=0.98*inch)
    f.addFromList(name_block,canvas)
    f = Frame(left_coord, bottom_coord, 3.5*inch, 2*inch, leftPadding=0.17*inch, topPadding=1.42*inch)
    f.addFromList(address_block,canvas)
    f = Frame(left_coord, bottom_coord, 3.5*inch, 2*inch, leftPadding=2.12*inch, topPadding=1.42*inch)
    f.addFromList(contact_block,canvas)
#}}}
#{{{ SuperiorEnergyBc_1up
def SuperiorEnergyBc_1up(request):
    # Get the info that the user entered. These fields should match what's in the model.
    form_data = escape(request.session.get('form_data', None))

    # Set some document specifics
    timestamp = str(time()).replace('.','')
    pdf_file = "%s/previews/%s.pdf" % (settings.MEDIA_ROOT, timestamp)
    img_file = "%s/previews/%s.gif" % (settings.MEDIA_ROOT, timestamp)
    pagesize = (inch*3.5, inch*2) # width, height. Measured at 72dpi, so this is 252x144
    bg_image = "%s/vardata_images/SuperiorEnergyBc_bg_1up.tif" % settings.MEDIA_ROOT

    # Create the canvas
    c = canvas.Canvas(filename=pdf_file, pagesize=pagesize, pageCompression=1)
    c.drawImage(bg_image, 0, 0, width=252, height=144, mask=None)

    # Draw the actual content
    SuperiorEnergyBc_render(c, form_data, 0, 0)

    # Close the PDF object cleanly
    c.showPage()
    c.save()

    # Create a preview image
    command = 'convert -page 252x144 %s %s' % (pdf_file, img_file)
    os.system(command)

    # Set session variable so we can pass filename back to preview
    request.session['filename_prefix'] = timestamp

    return HttpResponseRedirect(reverse('orders:vardata_preview'))
#}}}
#{{{ SuperiorEnergyBc_print
def SuperiorEnergyBc_print(request, ordereditem_id):
    ordereditem = OrderedItem.objects.get(pk=ordereditem_id)
    data = SuperiorEnergyBc.objects.get(ordereditem = ordereditem_id)
    data = escape(data.__dict__)

    # Set some document specifics
    filename = "%s-%s.pdf" % (ordereditem.order.name, ordereditem_id)
    response = HttpResponse(mimetype='application/pdf')
    response['Content-Disposition'] = 'attachment; filename=%s' % filename # force save as dialog
    pagesize = (inch*17, inch*11) # width, height. Measured at 72dpi, so this is 1224x792
    bg_image = "%s/vardata_images/SuperiorEnergyBc_bg_print.tif" % settings.MEDIA_ROOT

    # Measurements of page
    left_margin = 0.75*inch   # distance from edge of page to leftmost cropmark
    bottom_margin = 0.75*inch # distance from edge of page to bottommost cropmark
    horiz_offset = 4*inch     # distance between the start of one piece & the next (ie left side to left side)
    vert_offset = 2.5*inch    # same but from top to top
    num_cols = 4              # number of columns of pieces
    num_rows = 5              # number of rows of pieces

    # Create the canvas
    c = canvas.Canvas(response, pagesize=pagesize, pageCompression=1)
    c.drawImage(bg_image, 0, 0, width=1224, height=792, mask=None)

    # Draw the actual content
    for row in range(num_rows):
        for col in range(num_cols):
            SuperiorEnergyBc_render(c, data, left_margin+(col*horiz_offset), (row*vert_offset)+bottom_margin)

    # Close the PDF object cleanly
    c.showPage()
    c.save()
    return response
#}}}

#{{{ superior_agent_stylesheet
def superior_agent_stylesheet():
    stylesheet = {}

    # Register all required fonts
    folder = settings.FONT_DIR # from settings.py
    registered = pdfmetrics.getRegisteredFontNames()

    afmFile = os.path.join(folder, 'Myriad-Roman.afm')
    pfbFile = os.path.join(folder, 'Myriad-Roman.pfb')
    faceName = 'Myriad-Roman'
    if faceName not in registered:
        justFace = pdfmetrics.EmbeddedType1Face(afmFile, pfbFile)
        pdfmetrics.registerTypeFace(justFace)
        justFont = pdfmetrics.Font('Myriad-Roman', faceName, 'WinAnsiEncoding')
        pdfmetrics.registerFont(justFont)

    afmFile = os.path.join(folder, 'Myriad-Bold.afm')
    pfbFile = os.path.join(folder, 'Myriad-Bold.pfb')
    faceName = 'Myriad-Bold'
    if faceName not in registered:
        justFace = pdfmetrics.EmbeddedType1Face(afmFile, pfbFile)
        pdfmetrics.registerTypeFace(justFace)
        justFont = pdfmetrics.Font(faceName, faceName, 'WinAnsiEncoding')
        pdfmetrics.registerFont(justFont)

    p = ParagraphStyle('bold', None)
    p.fontName = 'Myriad-Bold'
    p.fontSize = 11.5
    p.leading = 8.5
    p.alignment = TA_LEFT
    p.textColor = HexColor(0x004990)
    stylesheet['bold'] = p

    p = ParagraphStyle('bold-title', None)
    p.fontName = 'Myriad-Bold'
    p.fontSize = 11.5
    p.leading = 11.5
    p.alignment = TA_LEFT
    p.textColor = HexColor(0x004990)
    stylesheet['bold-title'] = p

    p = ParagraphStyle('roman', None)
    p.fontName = 'Myriad-Roman'
    p.fontSize = 8
    p.leading = 8.5
    p.alignment = TA_LEFT
    p.textColor = HexColor(0x004990)
    stylesheet['roman'] = p

    p = ParagraphStyle('roman-noleading', None)
    p.fontName = 'Myriad-Roman'
    p.fontSize = 7
    p.leading = 0
    p.alignment = TA_LEFT
    p.textColor = HexColor(0x004990)
    stylesheet['roman-noleading'] = p

    p = ParagraphStyle('spacer', None)
    p.spaceAfter = 8
    stylesheet['spacer'] = p

    p = ParagraphStyle('tiny-spacer', None)
    p.spaceAfter = 2.3
    stylesheet['tiny-spacer'] = p

    return stylesheet
#}}}
#{{{ SuperiorEnergyAgentBc_render
def SuperiorEnergyAgentBc_render(canvas, data, left_coord, bottom_coord):
    """
    Draws a single Superior Energy business card onto `canvas` (content Frames start at
    `left_coord` and `bottom_coord`) with the `data` provided, which represents
    either the data the user entered into the form (when creating a preview) or
    the database record (when creating a printready file)
    """
    fonts = superior_agent_stylesheet()

    name_block = []
    name_block.append(Paragraph(data['name'], fonts['bold-title']))
    name_block.append(Paragraph('<font size="7">%s</font>' % data['title'], fonts['roman']))

    email_block = []
    email_line = "<font size='7'>%s</font>" % data['email']
    email_block.append(Paragraph(email_line, fonts['roman']))

    contact_block, num_text_block = [], []
    direct = phone_parts(data['direct'])
    direct_line = '<font size="8">%s-%s-%s</font>' % (direct[0], direct[1], direct[2])
    contact_block.append(Paragraph(direct_line, fonts['bold']))
    num_text_block.append(Paragraph('<font size="7">direct</font>', fonts['roman']))
    if data['cell']:
        cell = phone_parts(data['cell'])
        cell_line = '%s-%s-%s' % (cell[0], cell[1], cell[2])
        contact_block.append(Paragraph(cell_line, fonts['roman']))
        num_text_block.append(Paragraph('<font size="7">cell</font>', fonts['roman']))
    if data['fax']:
        fax = phone_parts(data['fax'])
        fax_line = '%s-%s-%s' % (fax[0], fax[1], fax[2])
        contact_block.append(Paragraph(fax_line, fonts['roman']))
        num_text_block.append(Paragraph('<font size="7">fax</font>', fonts['roman']))
    if not data['cell'] and not data['fax']:
        contact_block.append(Paragraph('<font color="white">.</font>', fonts['roman']))
    else:
        contact_block.append(Paragraph('', fonts['tiny-spacer']))
    contact_block.append(Paragraph('<font size="7.5">www.superiorenergy.ca</font>', fonts['bold']))

    address_block = []
    address_block.append(Paragraph('6860 Century Avenue, Suite 3000', fonts['roman-noleading']))
    address_block.append(Paragraph('', fonts['spacer']))
    address_block.append(Paragraph('Mississauga, ON  L5N 2W5', fonts['roman-noleading']))

    # Add above content blocks to Frames
    # f = Frame(left, bottom, width of container, height of container)
    # It should be safe to have the frames be the entire dimensions of the
    # finished piece. If not, note that both the bottom coord and the height
    # of the frame will affect vertical positioning (add showBoundary=1 to see
    # the container).
    f = Frame(left_coord, bottom_coord, 3.5*inch, 2*inch, leftPadding=1.63*inch, topPadding=0.71*inch)
    f.addFromList(name_block,canvas)
    f = Frame(left_coord, bottom_coord, 3.5*inch, 2*inch, leftPadding=1.63*inch, topPadding=1.03*inch)
    f.addFromList(email_block,canvas)
    f = Frame(left_coord, bottom_coord, 3.5*inch, 2*inch, leftPadding=1.63*inch, topPadding=1.20*inch)
    f.addFromList(contact_block,canvas)
    f = Frame(left_coord, bottom_coord, 3.5*inch, 2*inch, leftPadding=2.36*inch, topPadding=1.21*inch)
    f.addFromList(num_text_block,canvas)
    f = Frame(left_coord, bottom_coord, 3.5*inch, 2*inch, leftPadding=0.9*inch, topPadding=1.73*inch)
    f.addFromList(address_block,canvas)
#}}}
#{{{ SuperiorEnergyAgentBc_1up
def SuperiorEnergyAgentBc_1up(request):
    # Get the info that the user entered. These fields should match what's in the model.
    form_data = escape(request.session.get('form_data', None))

    # Set some document specifics
    timestamp = str(time()).replace('.','')
    pdf_file = "%s/previews/%s.pdf" % (settings.MEDIA_ROOT, timestamp)
    img_file = "%s/previews/%s.gif" % (settings.MEDIA_ROOT, timestamp)
    pagesize = (inch*3.5, inch*2) # width, height. Measured at 72dpi, so this is 252x144
    bg_image = "%s/vardata_images/SuperiorAgentBc_bg_1up.tif" % settings.MEDIA_ROOT

    # Create the canvas
    c = canvas.Canvas(filename=pdf_file, pagesize=pagesize, pageCompression=1)
    c.drawImage(bg_image, 0, 0, width=252, height=144, mask=None)

    # Draw the actual content
    SuperiorEnergyAgentBc_render(c, form_data, 0, 0)

    # Close the PDF object cleanly
    c.showPage()
    c.save()

    # Create a preview image
    command = 'convert -page 252x144 %s %s' % (pdf_file, img_file)
    os.system(command)

    # Set session variable so we can pass filename back to preview
    request.session['filename_prefix'] = timestamp

    return HttpResponseRedirect(reverse('orders:vardata_preview'))
#}}}
#{{{ SuperiorEnergyAgentBc_print
def SuperiorEnergyAgentBc_print(request, ordereditem_id):
    ordereditem = OrderedItem.objects.get(pk=ordereditem_id)
    data = SuperiorEnergyAgentBc.objects.get(ordereditem = ordereditem_id)
    data = escape(data.__dict__)

    # Set some document specifics
    filename = "%s-%s.pdf" % (ordereditem.order.name, ordereditem_id)
    response = HttpResponse(mimetype='application/pdf')
    response['Content-Disposition'] = 'attachment; filename=%s' % filename # force save as dialog
    pagesize = (inch*17, inch*11) # width, height. Measured at 72dpi, so this is 1224x792
    bg_image = "%s/vardata_images/SuperiorAgentBc_bg_print.tif" % settings.MEDIA_ROOT

    # Measurements of page
    left_margin = 0.75*inch   # distance from edge of page to leftmost cropmark
    bottom_margin = 0.75*inch # distance from edge of page to bottommost cropmark
    horiz_offset = 4*inch     # distance between the start of one piece & the next (ie left side to left side)
    vert_offset = 2.5*inch    # same but from top to top
    num_cols = 4              # number of columns of pieces
    num_rows = 5              # number of rows of pieces

    # Create the canvas
    c = canvas.Canvas(response, pagesize=pagesize, pageCompression=1)
    c.drawImage(bg_image, 0, 0, width=1224, height=792, mask=None)

    # Draw the actual content
    for row in range(num_rows):
        for col in range(num_cols):
            SuperiorEnergyAgentBc_render(c, data, left_margin+(col*horiz_offset), (row*vert_offset)+bottom_margin)

    # Close the PDF object cleanly
    c.showPage()
    c.save()
    return response
#}}}

def generic_1up(request, renderer, pagesize, styles):
    form_data = escape(request.session.get('form_data', None))

    timestamp = str(time()).replace('.', '')
    pdf_file = '%s/previews/%s.pdf' % (settings.MEDIA_ROOT, timestamp)
    img_file = '%s/previews/%s.gif' % (settings.MEDIA_ROOT, timestamp)

    c = canvas.Canvas(pdf_file, pagesize, pageCompression=1)

    if styles and hasattr(styles, '__call__'):
        styles = styles()

    renderer(c, form_data, 0, 0, styles)

    c.showPage()
    c.save()

    os.system('convert -page %dx%d %s %s' % (pagesize[0], pagesize[1], pdf_file, img_file))

    request.session['filename_prefix'] = timestamp

    return HttpResponseRedirect(reverse('orders:vardata_preview'))


def hash_square(c, top, left, bottom, right, noTop=False, noLeft=False, noRight=False, noBottom=False):
    width = right - left
    height = bottom - top

    lines = []

    if not noTop:
        lines.append([left + (width * 0.15), top, left + (width * 0.85), top])

    if not noBottom:
        lines.append([left + (width * 0.15), bottom, left + (width * 0.85), bottom])

    if not noLeft:
        lines.append([left, top + (height * 0.15), left, top + (height * 0.85)])

    if not noRight:
        lines.append([right, top + (height * 0.15), right, top + (height * 0.85)])

    if lines:
        c.lines(lines)

def generic_grid_printer(c, data, renderer, pagesize, margins, counts, size, styles, rotate=None, postprocess=None, hashes=True, half_inch=None, min_val=0.5):
    if rotate is not None:
        c.setPageRotation(rotate)

    margin_x = margins[0]
    margin_y = margins[1]
    if half_inch is None:
        half_inch = 0.5 * inch

    for i in range(0, counts[1] + 1):
        bottom_coord = (margin_y + i * (size[1] + min_val)) * inch
        for j in range(0, counts[0] + 1):
            if i < counts[1] and j < counts[0]:
                renderer(c, data, (margin_x + j * (size[0] + min_val)) * inch, bottom_coord, styles)

            if hashes:
                right = (j * (size[0] + min_val) + margin_x) * inch
                hash_square(c, bottom_coord - half_inch, right - half_inch, bottom_coord, right, i==0, j==0, j==counts[0], i==counts[1])

    if postprocess is not None:
        postprocess(c, data, pagesize, margins, counts, size, styles, rotate)
    c.save()

    return c

def generic_grid_print(request, ordereditem_id, model, renderer, pagesize, margins, counts, size, styles, rotate=None, postprocess=None, hashes=True, half_inch=None, min_val=0.5):
    ordereditem = OrderedItem.objects.get(pk=ordereditem_id)
    data = model.objects.get(ordereditem=ordereditem_id).__dict__
    #data = escape(model.objects.get(ordereditem=ordereditem_id).__dict__)

    response = HttpResponse(mimetype='application/pdf')
    response['Content-Disposition'] = 'attachment; filename=%s-%s.pdf' % (ordereditem.order.name, ordereditem_id)

    if styles and hasattr(styles, '__call__'):
        styles = styles()

    c = canvas.Canvas(response, pagesize=pagesize, pageCompression=1)

    generic_grid_printer(c, data, renderer, pagesize, margins, counts, size, styles, rotate, postprocess, hashes, half_inch, min_val)

    return response

def stylesheet(func):
    style = func() if hasattr(func, '__call__') else func

    for name, attrs in style.iteritems():
        if isinstance(attrs, dict):
            if 'parent' in attrs:
                parent = style[attrs['parent']]
                del attrs['parent']
            else:
                parent = None

            style[name] = ParagraphStyle(name, parent, **attrs)

    folder = os.path.join(os.path.dirname(__file__), '..', 'fonts')
    registered = pdfmetrics.getRegisteredFontNames()

    for faceName in set([p.fontName for p in style.values() if p and hasattr(p, 'fontName')]):
        if faceName in registered:
            continue

        afmFile = os.path.join(folder, faceName + '.afm')
        pfbFile = os.path.join(folder, faceName + '.pfb')

        justFace = pdfmetrics.EmbeddedType1Face(afmFile, pfbFile)
        pdfmetrics.registerTypeFace(justFace)
        justFont = pdfmetrics.Font(faceName, faceName, 'WinAnsiEncoding')
        pdfmetrics.registerFont(justFont)

    return style

def vardata_image(name):
    return "%s/vardata_images/%s" % (settings.MEDIA_ROOT, name)

rexall_styles = stylesheet({
        'name': {
            'fontName': 'MyriadPro-Semibold',
            'fontSize': 13,
            'alignment': TA_RIGHT,
            'textColor': HexColor(0x6d6f71)
        },

        'title': {
            'fontName': 'MyriadPro-It',
            'fontSize': 9,
            'leading': 20,
            'alignment': TA_RIGHT,
            'textColor': HexColor(0x6d6f71)
        },

        'contact': {
            'fontName': 'Myriad-Roman',
            'fontSize': 9,
            'alignment': TA_RIGHT,
            'textColor': HexColor(0x6d6f71)
        },

        'address': {
            'fontName': 'Myriad-Roman',
            'fontSize': 9,
            'alignment': TA_LEFT,
            'textColor': HexColor(0x6d6f71)
        }
    })

def RexallBc_renderer(c, data, left, bottom, stylesheet):
    c.drawImage("%s/vardata_images/RexallBc.tiff" % settings.MEDIA_ROOT, left, bottom, width=252, height=144, mask=None)

    Frame(left, bottom, 3.5*inch, 1.75*inch, showBoundary=0, rightPadding=0.162*inch, topPadding=0).addFromList([
        Paragraph(data['name'], stylesheet['name'])
    ], c)

    Frame(left, bottom, 3.5*inch, 1.75*inch, showBoundary=0, rightPadding=0.162*inch, topPadding=0.20*inch).addFromList([
        Paragraph(data['title'], stylesheet['title'])
    ], c)

    Frame(left, bottom, 3.5*inch, 1.75*inch, showBoundary=0, topPadding=0.85*inch, leftPadding=0.13*inch).addFromList([
        Paragraph(text, stylesheet['address'])
        for text in [data['address'], data['city'] + ', ' + data['province'], data['zip']]
    ], c)

    Frame(left, bottom, 3.5*inch, 1.75*inch, showBoundary=0, topPadding=0.85*inch, rightPadding=0.162*inch).addFromList([
        Paragraph(text, stylesheet['contact'])
        for text in ['Tel. (905) 567-8910 ext. %s' % data['ext'], 'Fax (905) 789-1011', 'rexall.ca']
    ], c)

def RexallBc_print(request, ordereditem_id):
    return generic_grid_print(request, ordereditem_id,
            model=RexallBc,
            renderer=RexallBc_renderer,
            pagesize=(17 * inch, 11 * inch),
            margins=(0.75, 0.75),
            counts=(4, 4),
            size=(3.5, 2.0),
            styles=rexall_styles)

def RexallBc_1up(request):
    return generic_1up(request,
            renderer=RexallBc_renderer,
            pagesize=(inch*3.5, inch*2.0),
            styles=rexall_styles)

e10e_styles = stylesheet({
    'default': {
        'fontName': 'MetaPlusMedium-Caps',
        'fontSize': 6,
        'leading': 14,
        'alignment': TA_CENTER,
        'textColor': HexColor(0x007bc3)
    },
    })

def EverestN10Envelope_renderer(c, data, left, bottom, stylesheet):
    c.drawImage(vardata_image('Everest #10 env template.tif'), left, bottom, width=684, height=306)

    Frame(left + 23, bottom + 128, 100, 100, showBoundary=0).addFromList([
        Paragraph(data['campus_location'].upper(), stylesheet['default']),
        Paragraph(', '.join((data['address_1'], data['address_2'])), stylesheet['default']),
        Paragraph('%s, %s %s' % (data['city'], data['province'], data['postal_code']), stylesheet['default']),
    ], c)

def EverestN10Envelope_1up(request):
    return generic_1up(request,
            renderer=EverestN10Envelope_renderer,
            pagesize=(684, 306),
            styles=e10e_styles)
def EverestN10Envelope_print(request, ordereditem_id):
    return generic_grid_print(request, ordereditem_id,
            model=EverestN10Envelope,
            renderer=EverestN10Envelope_renderer,
            pagesize=(17 * inch, 11 * inch),
            margins=(0.75, 0.75),
            counts=(1, 2),
            size=(9.5, 4.25),
            styles=e10e_styles)

def Everest10x13Envelope_renderer(c, data, left, bottom, stylesheet):
    c.drawImage(vardata_image('Everest 10x13 env template.tif'), left, bottom, width=936, height=720, mask=None)

    Frame(left + 22.6, bottom + 544, 100, 100, showBoundary=0).addFromList([
        Paragraph(data['campus_location'].upper(), stylesheet['default']),
        Paragraph(', '.join((data['address_1'], data['address_2'])), stylesheet['default']),
        Paragraph('%s, %s %s' % (data['city'], data['province'], data['postal_code']), stylesheet['default']),
    ], c)
def Everest10x13Envelope_1up(request):
    return generic_1up(request,
            renderer=Everest10x13Envelope_renderer,
            pagesize=(936, 720),
            styles=e10e_styles)
def Everest10x13Envelope_print(request, ordereditem_id):
     return generic_grid_print(request, ordereditem_id,
            model=Everest10x13Envelope,
            renderer=Everest10x13Envelope_renderer,
            pagesize=(17 * inch, 11 * inch),
            margins=(0.75, 0.47),
            counts=(1, 1),
            size=(13, 10),
            styles=e10e_styles)

def Everest9x12Envelope_renderer(c, data, left, bottom, stylesheet):
    c.drawImage(vardata_image('Everest 6x9 env template.tif'), left, bottom, width=864, height=648)

    Frame(left + 22.8, bottom + 474, 100, 100, showBoundary=0).addFromList([
        Paragraph(data['campus_location'].upper(), stylesheet['default']),
        Paragraph(', '.join((data['address_1'], data['address_2'])), stylesheet['default']),
        Paragraph('%s, %s %s' % (data['city'], data['province'], data['postal_code']), stylesheet['default']),
    ], c)
def Everest9x12Envelope_1up(request):
    return generic_1up(request,
            renderer=Everest9x12Envelope_renderer,
            pagesize=(864, 648),
            styles=e10e_styles)
def Everest9x12Envelope_print(request, ordereditem_id):
     return generic_grid_print(request, ordereditem_id,
            model=Everest9x12Envelope,
            renderer=Everest9x12Envelope_renderer,
            pagesize=(17 * inch, 11 * inch),
            margins=(0.75, 0.75),
            counts=(1, 1),
            size=(12, 9),
            styles=e10e_styles)

def Everest6x9Envelope_renderer(c, data, left, bottom, stylesheet):
    c.drawImage(vardata_image('Everest 9x12 env template.tif'), left, bottom, width=936, height=720)

    Frame(left + 54, bottom + 495, 100, 100, showBoundary=0).addFromList([
        Paragraph(data['campus_location'].upper(), stylesheet['default']),
        Paragraph(', '.join((data['address_1'], data['address_2'])), stylesheet['default']),
        Paragraph('%s, %s %s' % (data['city'], data['province'], data['postal_code']), stylesheet['default']),
    ], c)
def Everest6x9Envelope_1up(request):
    return generic_1up(request,
            renderer=Everest6x9Envelope_renderer,
            pagesize=(936, 720),
            styles=e10e_styles)
def Everest6x9Envelope_print(request, ordereditem_id):
     return generic_grid_print(request, ordereditem_id,
            model=Everest6x9Envelope,
            renderer=Everest6x9Envelope_renderer,
            pagesize=(17 * inch, 11 * inch),
            margins=(0.75, 0.75),
            counts=(1, 1),
            size=(13, 10),
            styles=e10e_styles)

letterhead_style = stylesheet({
    'default': {
        'fontName': 'MetaPlus-Medium',
        'fontSize': 6,
        'alignment': TA_CENTER,
        'textColor': HexColor(0x007bc3)
    },

    'italic': {
        'fontName': 'SimonciniGaramondStd-Italic',
        'fontSize': 6,
        'alignment': TA_CENTER,
        'textColor': HexColor(0x007bc3)
    }
    })

def EverestSampleLetterhead_renderer(c, data, left, bottom, stylesheet):
    address = ', '.join((data['address_1'], data['address_2']))

    Frame(10.73 + left, bottom + 590.68, 140, 100, showBoundary=0).addFromList([
        Paragraph(data['campus_location'].upper(), stylesheet['default']),
        Paragraph(address, stylesheet['default']),
        Paragraph('%s, %s %s' % (data['city'], data['province'], data['postal_code']), stylesheet['default']),

        Paragraph('<font name="SimonciniGaramondStd-Italic">tel</font> %s <font name="SimonciniGaramondStd-Italic">fax</font> %s' % (data['phone'], data['fax']), stylesheet['default']),

        Paragraph('www.cdicollege.com', stylesheet['default']),
    ], c)

def EverestSampleLetterhead_1up(request):
    return generic_1up(request,
            renderer=EverestSampleLetterhead_renderer,
            pagesize=(612, 792),
            styles=letterhead_style)
def EverestSampleLetterhead_print(request, ordereditem_id):
     return generic_grid_print(request, ordereditem_id,
            model=EverestSampleLetterhead,
            renderer=EverestSampleLetterhead_renderer,
            pagesize=(17 * inch, 11 * inch),
            margins=(0.75, 0.75),
            counts=(1, 1),
            size=(8.5, 11),
            styles=letterhead_style,
            rotate=90)

everestbc_styles = stylesheet({
    'name': {
        'fontName': 'MetaPlusMedium-Caps',
        'fontSize': 8.5,
        'leading': 10,
        'alignment': TA_LEFT,
        'textColor': HexColor(0x0081c1)
    },

    'title': {
        'fontName': 'AGaramondPro-Italic',
        'fontSize': 8,
        'leading': 9,
        'alignment': TA_LEFT,
        'textColor': HexColor(0x007bc3)
    },

    'contacts': {
        'fontName': 'MetaPlus-Medium',
        'fontSize': 8,
        'leading': 14,
        'alignment': TA_LEFT,
        'textColor': HexColor(0x0081c1)
    },

    'address': {
        'fontName': 'MetaPlusNormal-Roman',
        'fontSize': 6,
        'leading': 8,
        'alignment': TA_CENTER,
        'textColor': HexColor(0x0081c1)
    }
})

def EverestBC_renderer(c, data, left, bottom, stylesheet):
    c.setFillColor('white')
    c.rect(left, bottom, width=252, height=144, fill=True, stroke=False)

    escaped = {k: v for k, v in data.iteritems()}

    lines = [
        Paragraph(escaped['name'].upper(), stylesheet['name']),
        Paragraph(escaped['title_1'], stylesheet['title']),
        Paragraph('%s<br/><br/>' % escaped['title_2'], stylesheet['title']),
    ]

    if escaped.get('phone'):
        line = '<font name="AGaramondPro-Italic">phone</font> &nbsp; ' + escaped['phone']

        if escaped['phone_ext']:
            line += ' &nbsp; <font name="MetaPlusNormal-Roman">ext. %s</font>' % escaped['phone_ext']

        lines.append(Paragraph(line, stylesheet['contacts']))

    if escaped.get('mobile'):
        lines.append(Paragraph('<font name="AGaramondPro-Italic">mobile</font> &nbsp; %s' % escaped['mobile'], stylesheet['contacts']))

    if escaped.get('email'):
        lines.append(Paragraph('<font name="AGaramondPro-Italic">email</font> &nbsp; %s' % escaped['email'], stylesheet['contacts']))

    Frame(left + 105, bottom + 40, 137, 91, showBoundary=0).addFromList(lines, c)

    address1 = ''
    if 'campus' in escaped and escaped['campus']:
        address1 += '<font name="MetaPlus-Medium">%s</font>, ' % escaped['campus']

    address1 += '%s &bull; %s' % (
        escaped['address_1'],
        escaped['address_2']
    )

    address2 = []
    if escaped.get('telephone'):
        address2.append('<font name="AGaramondPro-Italic">tel</font> %s' % escaped['telephone'])

    if escaped.get('fax'):
        address2.append('<font name="AGaramondPro-Italic">fax</font> %s' % escaped['fax'])

    if address2:
        address2.append('&bull;');

    address2.append('<font name="MetaPlus-Medium">www.everest.ca</font>')

    Frame(left, bottom, 252, 35).addFromList([
        Paragraph(address1, stylesheet['address']),
        Paragraph(' '.join(address2) , stylesheet['address'])
    ], c)

def EverestBC_1up(request):
    return generic_1up(request,
            renderer=EverestBC_renderer,
            pagesize=(252, 180),
            styles=everestbc_styles)

def EverestBC_print(request, ordereditem_id):
    return generic_grid_print(request, ordereditem_id,
            model=EverestBC,
            renderer=EverestBC_renderer,
            pagesize=(17 * inch, 11 * inch),
            margins=(0.75, 0.75),
            counts=(4, 4),
            size=(3.5, 2.0),
            styles=everestbc_styles)

trilliumbcd_styles = stylesheet({
    'name': {
        'fontName': 'FrutigerLTStd-Bold',
        'fontSize': 9,
        'alignment': TA_RIGHT
    },

    'title': {
        'fontName': 'FrutigerLTStd-Roman',
        'fontSize': 8,
        'alignment': TA_RIGHT
    },

    'contacts': {
        'fontName': 'FrutigerLTStd-Roman',
        'fontSize': 7.5,
        'leading': 9,
        'alignment': TA_LEFT
    }
})

def TrilliumDoubleBC_renderer(c, escaped, left, bottom, stylesheet):
    c.drawImage(vardata_image('tc_bc_grid.tif'), left, bottom, width=270, height=162)

    no_padding = {
        'topPadding': 0,
        'leftPadding': 0,
        'rightPadding': 0,
        'bottomPadding': 0,
        'showBoundary': 0
    }

    Frame(left + 40, bottom + 105, 195, 30, **no_padding).addFromList([
        Paragraph(escaped['name'], stylesheet['name']),
        Paragraph(escaped['title'], stylesheet['title'])
    ], c)

    lst = []
    for i in ['address_1', 'address_2', 'address_3']:
        t = escaped.get(i)
        if t:
            lst.append(Paragraph(t, stylesheet['contacts']))

    Frame(left + 38, bottom + 20, 90, 32, **no_padding).addFromList(lst, c)

    lst = []

    for p, i in [('P: ', 'phone'), ('F: ', 'fax'), ('', 'email')]:
        t = escaped.get(i)
        if t:
            lst.append(Paragraph('%s%s' % (p, t), stylesheet['contacts']))

    Frame(left + 130, bottom + 20, 120, 32, **no_padding).addFromList(lst, c)

def TrilliumDoubleBC_renderer_grid(ordereditem_id):
    no_padding = {
        'topPadding': 0,
        'leftPadding': 0,
        'rightPadding': 0,
        'bottomPadding': 0,
        'showBoundary': 0
    }

    ordereditem = OrderedItem.objects.get(pk=ordereditem_id)
    escaped = TrilliumDoubleBC.objects.get(ordereditem=ordereditem_id).__dict__

    #escaped = {
        #'name': 'Carol Larocque',
        #'title': 'Medical Esthetics Instructor',
        #'address_1': '557 Church Street',
        #'address_2': 'Toronto, ON',
        #'address_3': 'M4Y 2E2',
        #'phone': '416.907.2570 ext. 400',
        #'fax': '289.222.2520',
        #'email': 'carol.larocque@trilliumcollege.ca'
    #}

    packet = StringIO()
    c = canvas.Canvas(packet, pagesize=(294,186))

    Frame(40, 125, 195, 30, **no_padding).addFromList([
        Paragraph(escaped['name'], trilliumbcd_styles['name']),
        Paragraph(escaped['title'], trilliumbcd_styles['title'])
    ], c)

    lst = []
    for i in ['address_1', 'address_2', 'address_3']:
        t = escaped.get(i)
        if t:
            lst.append(Paragraph(t, trilliumbcd_styles['contacts']))

    Frame(43, 25, 90, 32, **no_padding).addFromList(lst, c)

    lst = []

    for p, i in [('P: ', 'phone'), ('F: ', 'fax'), ('', 'email')]:
        t = escaped.get(i)
        if t:
            lst.append(Paragraph('%s%s' % (p, t), trilliumbcd_styles['contacts']))

    Frame(133, 25, 120, 32, **no_padding).addFromList(lst, c)
    c.save()

    packet.seek(0)
    result = merge_pdfs(
        PdfFileReader(open(vardata_image('tc_bc_blank.pdf'), 'rb')),
        PdfFileReader(packet)
    )

    response = HttpResponse(mimetype='application/pdf')
    response['Content-Disposition'] = 'attachment; filename=%s-%s.pdf' % (ordereditem.order.name, ordereditem_id)
    result.write(response)
    return response


def TrilliumDoubleBC_1up(request):
    return generic_1up(request,
                       renderer=TrilliumDoubleBC_renderer,
                       pagesize=(270, 162),
                       styles=trilliumbcd_styles)

def TrilliumDoubleBC_print(request, ordereditem_id):
    return TrilliumDoubleBC_renderer_grid(ordereditem_id)


###
# CaTech
###

#{{{ catech_stylesheet
def catech_new_stylesheet():
    stylesheet = {}

    # Register all required fonts
    folder = settings.FONT_DIR # from settings.py
    registered = pdfmetrics.getRegisteredFontNames()

    fonts = {
        'Swis721 BT Roman': 'tt0003m_.ttf',
        'Swis721 BT Bold': 'tt0005m_.ttf',
        'Swiss721BT BT Bold Italic': 'tt0006c_.ttf',
        'Swis721 Hv BT Heavy': 'tt0102m_.ttf',
    }

    for fn, ff in fonts.iteritems():
        if fn not in registered:
            pdfmetrics.registerFont(TTFont(fn, os.path.join(folder, ff)))

    p = ParagraphStyle('bold', None)
    p.fontName = 'Swis721 BT Bold'
    p.fontSize = 9
    p.leading = 11
    p.alignment = TA_LEFT
    p.textColor = HexColor(0xfffefe)

    stylesheet['name'] = p

    p = ParagraphStyle('roman', None)
    p.fontName = 'Swis721 BT Roman'
    p.fontSize = 6.8
    p.leading = 8
    p.spaceAfter = 2
    p.alignment = TA_LEFT
    p.textColor = HexColor(0xfffefe)

    stylesheet['title'] = p

    p = ParagraphStyle('roman2', None)
    p.fontName = 'Swis721 BT Roman'
    p.fontSize = 6.8
    p.leading = 8
    p.alignment = TA_LEFT
    p.textColor = HexColor(0xfffefe)

    stylesheet['direct_phone'] = p
    stylesheet['email'] = p

    p = ParagraphStyle('bold2', None)
    p.fontName = 'Swis721 BT Bold'
    p.fontSize = 7
    p.leading = 8
    p.alignment = TA_LEFT
    p.textColor = HexColor(0xffffff)
    stylesheet['company'] = p

    p = ParagraphStyle('roman3', None)
    p.fontName = 'Swis721 BT Roman'
    p.fontSize = 7
    p.leading = 8
    p.alignment = TA_LEFT
    p.textColor = HexColor(0xffffff)
    stylesheet['address'] = p

    p = ParagraphStyle('bold2', None)
    p.fontName = 'Swis721 Hv BT Heavy'
    p.fontSize = 6.5
    p.leading = 7
    p.alignment = TA_LEFT
    p.textColor = HexColor(0xffffff)
    stylesheet['website'] = p

    return stylesheet
#}}}


def catech_address(fonts, variant):
    res = [
        Paragraph('<font name="Swiss721BT BT Bold Italic">Ca</font><font name="Swis721 BT Bold">TECH Systems Ltd.</font>',
                  fonts['address'])
    ]

    if variant == 1:
        parts = [
            '201 Whitehall Drive, Unit 4',
            'Markham, ON L3R 9Y3',
            'MAIN 905 944 0000',
            'FAX 905 944 4844',
            'TOLL FREE 1 800 267 1919',
        ]
    elif variant == 2:
        parts = [
            '11830 160 Street NW',
            'Edmonton, AB T5V 1C9',
            'MAIN 780 413 7550',
            'FAX 800 398 2936',
            'TOLL FREE 1 800 267 1919',
        ]
    elif variant == 3:
        parts = [
            '3605 29th Street NE, Unit 400',
            'Calgary, AB T1Y 5W4',
            'MAIN 403 291 6119',
            'FAX 800 267 1919',
            'TOLL FREE 1 800 267 1919',
        ]
    elif variant == 4:
        parts = [
            '375 avenue Sainte Croix',
            'Saint-Laurent, PQ H4N 2L3',
            'TÉL 450 669 8866',
            'TÉLÉCOPIE 800 398 2936',
            'SANS FRAIS 1 800 267 1919',
        ]
    elif variant == 5:
        parts = [
            '91 Golden Drive, Unit 17',
            'Coquitlam, BC V3K 6R2',
            'MAIN 604 343 4664',
            'FAX 800 398 2936',
            'TOLL FREE 1 800 267 1919',
        ]
    elif variant == 6:
        parts = [
            '2465 Stevenage Drive, Unit 106',
            'Ottawa, ON K1G 3W2',
            'MAIN 613 903 4085',
            'FAX 800 398 2936',
            'TOLL FREE 1 800 267 1919',
        ]
    else:
        raise RuntimeError('unknown variant: %r' % variant)
    
    res.extend([
        Paragraph(p, fonts['address'])
        for p in parts
    ])

    return res


#{{{ catech_bc_render
def catech_bc_render(canvas, data, left_coord, bottom_coord):
    """
    Draws a single CaTech business card onto `canvas` (content Frames start at
    `left_coord` and `bottom_coord`) with the `data` provided, which represents
    either the data the user entered into the form (when creating a preview) or
    the database record (when creating a printready file).
    """
    fonts = catech_new_stylesheet()

    #bg_image = "%s/vardata_images/catech-bg.png" % settings.MEDIA_ROOT
    bg_image = "%s/vardata_images/CaTECH business card BG ONLY.tif" % settings.MEDIA_ROOT
    logo = "%s/vardata_images/catech-logo.svg" % settings.MEDIA_ROOT

    contact_block = []
    for k in 'name title direct_phone email'.split():
        if k == 'direct_phone':
            v = 'DIRECT ' + data[k]
        elif k == 'email':
            v = data[k] + '@catech-systems.com'
        else:
            v = data[k]
        contact_block.append(Paragraph(v, fonts[k]))

    canvas.drawImage(bg_image, left_coord, bottom_coord, width=270, height=162, mask=None)

    f = Frame(left_coord, bottom_coord, 3.75*inch, 2.25*inch,
              leftPadding=.37*inch, rightPadding=0.13*inch, topPadding=1.40*inch, bottomPadding=0)
    f.addFromList(contact_block, canvas)

    address_block = catech_address(fonts, data['template'])
    f = Frame(left_coord, bottom_coord, 3.75*inch, 2.25*inch,
              leftPadding=2.08*inch, topPadding=1.1*inch, rightPadding=0.13*inch, bottomPadding=0)
    f.addFromList(address_block, canvas)

    f = Frame(left_coord, bottom_coord, 3.75*inch, 2.25*inch,
              leftPadding=2.08*inch, topPadding=1.8*inch, rightPadding=0.13*inch, bottomPadding=0)
    f.addFromList([Paragraph('www.catech-systems.com', fonts['website'])], canvas)

#}}}

#{{{ catech_1up
def CaTechBc_1up(request):
    # Get the info that the user entered. These fields should match what's in the model.
    data = escape(request.session.get('form_data', None))

    # Set some document specifics
    timestamp = str(time()).replace('.','')
    pdf_file = "%s/previews/%s.pdf" % (settings.MEDIA_ROOT, timestamp)
    img_file = "%s/previews/%s.gif" % (settings.MEDIA_ROOT, timestamp)

    _catech_bc_1up(pdf_file, data)

    # Create a preview image
    command = 'convert -page 270x162 %s %s' % (pdf_file, img_file)
    os.system(command)

    # Set session variable so we can pass filename back to preview
    request.session['filename_prefix'] = timestamp

    return HttpResponseRedirect(reverse('orders:vardata_preview'))
#}}}

def _catech_bc_1up(pdf_file, data):

    pagesize = (inch*3.75, inch*2.25) # width, height. Measured at 72dpi, so this is 252x144

    # Create the canvas
    c = canvas.Canvas(filename=pdf_file, pagesize=pagesize, pageCompression=1)

    # Draw the actual content
    catech_bc_render(c, data, 0, 0)

    # Close the PDF object cleanly
    c.showPage()
    c.save()

    return c


#{{{ catech_bc_print
def CaTechBc_print(request, ordereditem_id):
    ordereditem = OrderedItem.objects.get(pk=ordereditem_id)
    data = CaTechBc.objects.get(ordereditem = ordereditem_id)
    data = escape(data.__dict__)

    # Set some document specifics
    filename = "%s-%s.pdf" % (ordereditem.order.name, ordereditem_id)
    response = HttpResponse(mimetype='application/pdf')
    response['Content-Disposition'] = 'attachment; filename=%s' % filename # force save as dialog

    _catech_bc_1up(response, data)

    return response
#}}}

