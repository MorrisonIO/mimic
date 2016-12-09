#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import os
import re

os.environ['DJANGO_SETTINGS_MODULE'] = 'mimicprint.settings'

MY_DIR = os.path.dirname(os.path.realpath(__file__))

sys.path.append(os.path.realpath(MY_DIR + '/../..'))

from mimicprint import settings
from django.core.management import setup_environ
from mimicprint.products.models import Product
from datetime import datetime
from jinja2 import Environment, Template, FileSystemLoader

PRODUCTS_IMPORT = (
	'EVE-BCARD-100', 'EVE-BCARD-250', 'EVE-BCARD-500', 'EVE-CAT-ON-1013',
	'EVE-NON-PCC', 'EVE-SCF–2NCR-250', 'EVE-SCF–2NCR-500', 'EVE-SCF–2NCR-1000',
	'EVE-SCF–3NCR-250', 'EVE-SCF–3NCR-500', 'EVE-SCF-3NCR-1000', 'EVE-CGRC',
	'EVE-CLING-500', 'EVE-CLING-1000', 'E-CT-0000-NAT', 'E-DP-0000-NAT',
	'E-DH-0000-NAT', 'E-TR-0000-NAT', 'E-TR-CVUE-001', 'E-MKT5041',
	'EVE-10ENV-1000', 'EVE-10ENV-1500', 'EVE-10ENV-2000', 'EVE-10ENV-3000',
	'EVE-10WINENV-1000', 'EVE-10WINENV-1500', 'EVE-10WINENV-2000', 'EVE-10WINENV-3000',
	'EVE-10X13-500', 'EVE-10X13-1000', 'EVE-9X12-500', 'EVE-9X12-1000',
	'EVE-6X9-1000', 'EVE-LH-1000', 'EVE-LH-1500', 'EVE-LH-2000',
	'EVE-LH-3000', 'EVE-NC', 'EVE-OFF-RECPT', 'EVE-MSGT-RECPT',
	'CUMELGV1-0', 'CYYELGV1-0', 'FQMELGV1-0', 'HEEELGV1-0',
	'ICCELGV1-0', 'IZ2ELGV1-0', 'LAMELGV1-0', 'LSSELGV1-0',
	'QQLELGV1-0', 'ALGMLTV1-0', 'AFFELGV1-0', 'AOCELGV1-0',
	'AOCELGV1-2', 'AOJELGV1-0', 'AOJELGV1-3', 'AP6ELGV1-3',
	'ASTELGV1-0', 'BFCELGV1-0', 'CCOELGV1-0', 'CESESMV1-1',
	'CFKELGV1-0', 'CMOELGV1-0', 'CPDELGV1-0', 'CSCT Booklet',
	'CSCT-AM', 'CTPE1', 'CT082012', 'CTV4-0 2010-04-07',
	'CTP-v2012-Book 1', 'CTP-v2012-Book 2', 'CU1ESWv1-0', 'CYHELGv1-0',
	'DAXELGV1-0', 'Dbaelgv1-0', 'DBCELGV1-6', 'DBDELGV1-0',
	'DWEELGV1-0', 'DWEELGV2-0', 'EOSESWV1-1', 'EXCELGV1-3',
	'FTMELGv1-0', 'GFFELGV1-0', 'HEMELGv1-0', 'HEMESRv1-0',
	'HDUELGV2-0', 'HUSELGV1-0', 'ICLELGv1-0', 'ICNELGV1-1',
	'INCELGV1-9', 'INNELGV1-0', 'IPGELGV1-0', 'IZPELGv1-0',
	'JSPELGV1-0', 'LAAESWV2-0', 'LMBELGv1-0', 'LPDELGv1-0',
	'LSAELGv1-0', 'LXCELGV1-0', 'LXCELGV1-1', 'MLASRM1V3-0',
	'MLASRM2V3-0', 'MLATv1-0', 'NEPELGV-1-1', 'NWEELGV1-0',
	'OOCELGV1-1', 'OOCELGV1-2', 'OOCELGV1-3', 'OOJELGV1-0',
	'OOJELGv1-2', 'OPCELGV1-2', 'OPCELGv1-4', 'OPJELGV1-2 ',
	'PINELGV1-0', 'PSFELGV1-0', 'PSKELGV1-1', 'PLDELGV2-0',
	'PRFELGV1-5', 'PRFELGV1-6', 'PTCELGV1-0', 'PTCELGV1-1',
	'PTPELGV1-0', 'QLMELGv1-0', 'SD1ELGV1-3', 'SD2ELGV1-2',
	'SD3ELGV1-0', 'SPCELGV1-1', 'UNSELGv1-0', 'WAAELGv5-0',
	'WADECGV4-2', 'WADELGV5-1', 'WADELGv6-0', 'WAFECGV3-1',
	'WAFELGV4-0', 'WAFELGV5-0', 'WDMELGV1-5', 'WDSELGV1-2',
	'WGPECGV3-1', 'WGPELGV4-0', 'WIFELGV2-4', 'WISELGV1-2',
	'WNIELGV1-4', 'WPBELGV2-2', 'WPDELGV1-3', 'WPMELGV1-3',
	'WPNELGV1-5', 'WSBELGV1-5', 'WSRELGV1-3', 'XPPELGv1-2',
	'MLATPEv1-0', 'CTPAMV8-13', 'CTPECGV8-13', 'CTPETTV8-13',
        'CTPILBV8-13', "PARASTUNDBK", 'CMMLATP-02-14', 'SHMLATP-03-14',
	'MLATPPIOB-03-14','MLATPSPI-03-14', 'CMMLATP-03-14',
	'EVE-NON-PCC-250', 'EVE-NON-PCC-500', 'EVE-CONG-100',
	'EVE-CONG-500', 'EVE-CONG-1000', 'ISWP-2014'
)

def cifq(x):
	return '"%s"' % unicode(x).replace('"', '""')

def strftime(v, format):
	return v.strftime(format)

def product_url(v):
	return "http://mimicprint2.com/oos"

CLEANER = re.compile(r'^[\s-]+')

def clear_name(p):
	pname = p.name
	if pname.startswith(p.part_number):
		pname = CLEANER.sub('', pname[len(p.part_number):])
	return pname.strip()

def main():
	setup_environ(settings)
	products = []
	for i in PRODUCTS_IMPORT:
		t = Product.objects.filter(part_number=i)
		if not t:
			print >>sys.stderr, "missing: ", i
		else:
			last = None
			for x in t:
				if not x.price:
					print >>sys.stderr, "price is none: ", i
				else:
					last = x

			if last is not None:
				products.append(last)

	env = Environment(autoescape=False, loader=FileSystemLoader(MY_DIR, 'utf-8'), trim_blocks=True)
	env.filters['cifq'] = cifq
	env.filters['strftime'] = strftime
	env.filters['product_url'] = product_url
	env.filters['clear_name'] = clear_name
	print env.get_template('template.cif').render(products=products, now=datetime.now()).encode('utf-8')

if __name__ == "__main__":
	main()
