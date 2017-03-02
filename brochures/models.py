from __future__ import unicode_literals

from django.db import models


class BrochureTemplate(models.Model):
    """
    Model describes personal info step in brochure ordering
    """
    file = models.FileField(upload_to='templates/pdf')
    name = models.CharField(max_length=200)
    def __str__(self):
        return self.name

    def getName(self):
        return self.file.file.name


class BrochurePreviewImage(models.Model):
    """
    Model presents preview images for brochure
    """
    name = models.CharField(max_length=200, default="Preview Image")
    preview_img = models.FileField(upload_to='brochure_images', default="img/brochure.jpg")
    def __str__(self):
        return self.name

class Brochure(models.Model):
    """
    This is a model for all existing brochures
    """
    name = models.CharField(max_length=200)
    title = models.CharField(max_length=200)
    description = models.TextField(max_length=1000)
    template = models.ForeignKey(BrochureTemplate, default=1)
    preview_image = models.FileField(upload_to='brochure_images', default="img/brochure.jpg")
    preview_images = models.ManyToManyField(BrochurePreviewImage, blank=True)
    num_of_images = models.PositiveSmallIntegerField(default=0)
    num_of_textfields = models.PositiveSmallIntegerField(default=0)
    feature_prop = models.CharField(max_length=128, default="Single Property")

    def __str__(self):
        return self.name


class PersonalInfo(models.Model):
    """
    Model describes personal info step in brochure ordering
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

class PropertyInfo(models.Model):
    """
    Model describes property info step in brochure ordering
    """
    property_address1 = models.CharField(max_length=200, blank=True)
    property_address2 = models.CharField(max_length=200, blank=True)
    property_city = models.CharField(max_length=100, blank=True)
    property_state = models.CharField(max_length=100, blank=True)
    property_code = models.CharField(max_length=50, blank=True)
    property_price = models.CharField(max_length=50, blank=True)

