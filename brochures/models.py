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

    def __str__(self):
        return self.name