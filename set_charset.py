import sys
# from settings import SITE_ROOT

sys.path.append('/Users/mac/Documents/workspace/projects/mimicprint_1.9/mimicprint')  
import os  
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mimicprint.settings")  
from django.db import connection
 
cursor = connection.cursor()
tables = connection.introspection.table_names()

for table in tables:  
   print "Fixing table: %s" %table
   sql = "ALTER TABLE %s CONVERT TO CHARACTER SET utf8;" %(table)
   try:
       cursor.execute(sql)
   except Exception as ex:
       print('\n*********************', ex, '************************\n')
       print(ex)
       continue
   print "Table %s set to utf8"%table

print "DONE!"