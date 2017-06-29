Mimicprint. A print republic
==========

Instalation
-----------
Mimicprint requires Python 2.7.x to run.
You need to install the following system libs and python packages:

System libs:
```
cairo-2
pango
pygtk
```

Packages:
```
pytz
CairoSVG
```

Quick start
-----------
**Local running:**
...
Restore DB dump and run server:
```shell
$ mysql -u %mysql_user% -p %mysql_password% mimic_original < path/to/mysql/dump.sql
$ python manage.py runserver
```
Open brower at localhost:8000


**Server running:**
You need configure server. You may use this [document](https://docs.google.com/document/d/1T2dokP4TJhqIz8xRXzJKzfodfzfR4TAKAHIYW6dP48U/edit?usp=sharing) 
