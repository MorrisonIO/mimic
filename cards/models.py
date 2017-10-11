from __future__ import unicode_literals

from django.db import models
from orgs.models import Org


class CardTemplate(models.Model):
    """
    Model describes personal info step in card ordering
    """
    file = models.FileField(upload_to='templates/pdf')
    name = models.CharField(max_length=200, default="template")
    def __str__(self):
        return self.name

    def getName(self):
        return self.file.file.name


class CardPreviewImage(models.Model):
    """
    Model presents preview images for card
    """
    name = models.CharField(max_length=200, default="Preview Image")
    preview_img = models.FileField(upload_to='card_images', default="img/card.jpg")
    def __str__(self):
        return self.name


class CardSelectTextFields(models.Model):
    """
    Text fields for fixed names
    """
    # Textfields = (
    #     "Full Name",
    #     "Street Name",
    #     "City",
    #     "Position",
    #     "Province",
    #     "Postal Code",
    #     "Office Phone",
    #     "Cell Phone",
    #     "Toll-Free Phone",
    #     "Fax",
    #     "E-mail"
    # )

    name = models.CharField(max_length=200, default="")
    # preview_img = models.FileField(upload_to='card_images', default="img/card.jpg")

    def __str__(self):
        return self.name


class Card(models.Model):
    """
    This is a model for all existing card
    """
    org = models.ForeignKey(Org, null=True)
    name = models.CharField(max_length=200)
    title = models.CharField(max_length=200)
    description = models.TextField(max_length=1000)
    template = models.ForeignKey(CardTemplate, default=1)
    preview_image = models.FileField(upload_to='card_images', default="img/card.jpg")
    preview_images = models.ManyToManyField(CardPreviewImage, blank=True)
    num_of_images = models.PositiveSmallIntegerField(default=0)
    textfields = models.ManyToManyField(CardSelectTextFields, blank=True)
    feature_prop = models.CharField(max_length=128, default="Single Property")

    def __str__(self):
        return self.name


class PersonalInfo(models.Model):
    """
    Model describes personal info step in card ordering
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
    Model describes property info step in card ordering
    """
    property_address1 = models.CharField(max_length=200, blank=True)
    property_address2 = models.CharField(max_length=200, blank=True)
    property_city = models.CharField(max_length=100, blank=True)
    property_state = models.CharField(max_length=100, blank=True)
    property_code = models.CharField(max_length=50, blank=True)
    property_price = models.CharField(max_length=50, blank=True)
