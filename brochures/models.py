from __future__ import unicode_literals

from django.db import models

class Brochure(models.Model):
    """
    This is a model for all existing brochures
    """
    name = models.CharField(max_length=200)
    title = models.CharField(max_length=200)
    description = models.TextField(max_length=1000)
    template = models.CharField(max_length=250)
    preview_image = models.CharField(max_length=250, default="img/brochure.jpg")
    num_of_images = models.PositiveSmallIntegerField(default=0)
    num_of_textfields = models.PositiveSmallIntegerField(default=0)
    feature_prop = models.CharField(max_length=128, default="Single Property")

    def __str__(self):
        return self.name

class PersonalInfo(models.Model):
    """
    Model describes step in brochure ordering
    """
    first_name = models.CharField(max_length=200)
    middle_name = models.CharField(max_length=200, blank=True)
    last_name = models.CharField(max_length=200)
    title = models.CharField(max_length=200, blank=True)
    email = models.EmailField(max_length=50, blank=True)
    website = models.CharField(max_length=200, blank=True)
    phone1 = models.CharField(max_length=50, blank=True)
    phone2 = models.CharField(max_length=50, blank=True)

    smart_search = models.CharField(max_length=50, blank=True)
    def __str__(self):
        return self.first_name