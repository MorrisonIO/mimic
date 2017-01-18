import os
from reportlab.pdfbase import pdfmetrics, pdfdoc

for afm in os.listdir('.'):
    if not afm.endswith('.afm'):
        continue

    title = afm[:-4]
    pfb = title + '.pfb'

    if not os.path.exists(pfb):
        print "%s doesn't exist!" % pfb
        continue

    face = pdfmetrics.EmbeddedType1Face(afm, pfb)
    if face.name != title:
        os.rename(afm, face.name + '.afm')
        os.rename(pfb, face.name + '.pfb')
