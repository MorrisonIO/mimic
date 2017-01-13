from django.db import models
from django.forms import ModelForm
from products.models import Product
from orders.models import OrderedItem


PROVINCE_CHOICES = (
    ('ON', 'Ontario'),
    ('QC', 'Quebec'),
    ('BC', 'British Columbia'),
    ('AB', 'Alberta'),
    ('MB', 'Manitoba'),
    ('SK', 'Saskatchewan'),
    ('NS', 'Nova Scotia'),
    ('NB', 'New Brunswick'),
    ('NL', 'Newfoundland and Laborador'),
    ('PE', 'Prince Edward Island'),
    ('NT', 'Northwest Territories'),
    ('YT', 'Yukon'),
    ('NU', 'Nunavut'),
)

TRILLIUM_CARD_TYPE_CHOICES = (
    ('Campus Generic Blank Card', 'SBC-GCA Campus Generic Blank Card'),
    ('Individual Admission Representative Card', 'SBC-INDV-RC Individual Admission Representative Card'),
    ('Individual Campus Personnel', 'SBC-INDV-CA Individual Campus Personnel'),
)
TRILLIUM_CAMPUS_CHOICES = (
    ('Burlington', 'Burlington'),
    ('Corporate', 'Corporate'),
    ('Kingston', 'Kingston'),
    ('Kitchener', 'Kitchener'),
    ('Oshawa', 'Oshawa'),
    ('Ottawa', 'Ottawa'),
    ('Peterborough', 'Peterborough'),
    ('St. Catharines', 'St. Catharines'),
    ('Toronto-Church', 'Toronto-Church'),
    ('Toronto-Yonge', 'Toronto-Yonge'),
)

KAFKO_US_CHOICES = (
    ('farwest', 'Farwest Branch -- Sacramento, CA'),
    ('midwest-mi', 'Midwest Branch -- Whitmore Lake, MI'),
    ('midwest-in', 'Midwest Branch -- Fort Wayne, IN'),
    ('northeast', 'Northeast Branch -- Latham, NY'),
    ('southeast', 'Southeast Branch -- Decatur, GA'),
)



class MimicBc(models.Model):
    """
    Mimic business cards
    """
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField(max_length=50)
    cell = models.CharField(max_length=50)
    extension = models.CharField(max_length=5, blank=True)
    ordereditem = models.ForeignKey(OrderedItem)
    product = models.ForeignKey(Product)

    def __unicode__(self):
        return u'First name: %s\nLast name: %s\nEmail: %s\nCell: %s\nExtension: %s' \
                % (self.first_name, self.last_name, self.email, self.cell, self.extension)

    def as_list(self):
        return (
            ('First name', self.first_name),
            ('Last name', self.last_name),
            ('Email', self.email),
            ('Cell', self.cell),
            ('Extension', self.extension)
            )


class MimicBcForm(ModelForm):
    class Meta:
        model = MimicBc
        exclude = (
            'ordereditem',
            'product'
        )


class TlaBc(models.Model):
    """
    TLA business cards
    """
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    title = models.CharField(max_length=50)
    # we are programmatically adding the domain, so we don't want to validate against an EmailField
    email = models.CharField(help_text="@tlacorp.com", max_length=50)
    cell = models.CharField(help_text='Include area code. Will be automatically formatted to <em>(nnn) nnn-nnnn</em>.', max_length=50)
    ordereditem = models.ForeignKey(OrderedItem)
    product = models.ForeignKey(Product)

    def __unicode__(self):
        return u'First name: %s\nLast name: %s\nTitle: %s\nEmail: %s\nCell: %s\n' \
                % (self.first_name, self.last_name, self.title, self.email, self.cell)

    def as_list(self):
        return (
            ('First name', self.first_name),
            ('Last name', self.last_name),
            ('Title', self.title),
            ('Email', self.email),
            ('Cell', self.cell)
            )


class TlaBcForm(ModelForm):
    class Meta:
        model = TlaBc
        exclude = (
            'ordereditem',
            'product',
        )


class HarrisCertificate(models.Model):
    """
    Harris training certificates
    """
    INSTRUCTORS = (
        ('Robert Amoroso', 'Robert Amoroso'),
        ('David Armstrong', 'David Armstrong'),
        ('Jay Burdsal', 'Jay Burdsal'),
        ('GC', 'GC'),  #### TODO ####
        ('Connie C Gordon', 'Connie C Gordon'),
        ('Geoff Howells', 'Geoff Howells'),
        ('Harry Johnson', 'Harry Johnson'),
        ('David LaFleche', 'David LaFleche'),
        ('Manuel Minut', 'Manuel Minut'),
        ('Yamunesh Rastogi', 'Yamunesh Rastogi'),
        ('Kevin Shaw', 'Kevin Shaw'),
        ('Mark Trevena', 'Mark Trevena'),
    )
    name = models.CharField(max_length=200)
    course = models.CharField(max_length=500)
    #    date = models.DateField() # don't use DateField for now,
    # as there's no nice way of giving text hints to users so that makes validation annoying
    date = models.CharField(max_length=200)
    instructor = models.CharField(max_length=200, choices=INSTRUCTORS)
    ordereditem = models.ForeignKey(OrderedItem)
    product = models.ForeignKey(Product)

    def __unicode__(self):
        return u'Name: %s\nCourse: %s\nDate: %s\nInstructor: %s' \
                % (self.name, self.course, self.date, self.instructor)

    def as_list(self):
        return (
            ('Name', self.name),
            ('Course', self.course),
            ('Date', self.date),
            ('Instructor', self.instructor)
            )


class HarrisCertificateForm(ModelForm):
    class Meta:
        model = HarrisCertificate
        exclude = (
            'ordereditem',
            'product'
        )


class DrAsiaPacificBc(models.Model):
    """
    Digital Rapids Asia Pacific business cards
    """
    name = models.CharField(max_length=50)
    title1 = models.CharField("Title 1", max_length=50)
    title2 = models.CharField("Title 2", max_length=50, blank=True, null=True)
    email = models.CharField(help_text="@digitalrapids.com", max_length=50)
    mobile = models.CharField(help_text='Country code +61 will be automatically added', max_length=50, blank=True, null=True)
    ordereditem = models.ForeignKey(OrderedItem)
    product = models.ForeignKey(Product)

    def __unicode__(self):
        return u'Name: %s\nTitle1: %s\nTitle2: %s\nEmail: %s@digitalrapids.com\nMobile: %s' \
                % (self.name, self.title1, self.title2, self.email, self.mobile)

    def as_list(self):
        return (
            ('Name', self.name),
            ('Title 1', self.title1),
            ('Title 2', self.title2),
            ('Email', '%s@digitalrapids.com' % self.email),
            ('Mobile', self.mobile)
            )


class DrAsiaPacificBcForm(ModelForm):
    class Meta:
        model = DrAsiaPacificBc
        exclude = (
            'ordereditem',
            'product'
        )


class DrMarkhamBc(models.Model):
    """
    Digital Rapids Markham business cards
    """
    name = models.CharField(max_length=50)
    title1 = models.CharField("Title 1", max_length=50)
    title2 = models.CharField("Title 2", max_length=50, blank=True, null=True)
    email = models.CharField(help_text="@digitalrapids.com", max_length=50)
    extension = models.CharField(max_length=10)
    cell = models.CharField(help_text='Include area code. Will be automatically formatted to <em>(nnn) nnn-nnnn</em>.', max_length=50, blank=True, null=True)
    ordereditem = models.ForeignKey(OrderedItem)
    product = models.ForeignKey(Product)

    def __unicode__(self):
        return u'Name: %s\nTitle1: %s\nTitle2: %s\nEmail: %s@digitalrapids.com\nExtension: %s\nCell: %s' \
                % (self.name, self.title1, self.title2, self.email, self.extension, self.cell)

    def as_list(self):
        return (
            ('Name', self.name),
            ('Title 1', self.title1),
            ('Title 2', self.title2),
            ('Email', '%s@digitalrapids.com' % self.email),
            ('Extension', self.extension),
            ('Cell', self.cell)
            )


class DrMarkhamBcForm(ModelForm):
    class Meta:
        model = DrMarkhamBc
        exclude = (
            'ordereditem',
            'product'
        )


class DrUkBc(models.Model):
    """
    Digital Rapids UK business cards
    """
    name = models.CharField(max_length=50)
    title1 = models.CharField("Title 1", max_length=50)
    title2 = models.CharField("Title 2", max_length=50, blank=True, null=True)
    email = models.CharField(help_text="@digitalrapids.com", max_length=50)
    mobile = models.CharField(max_length=50, blank=True, null=True)
    ordereditem = models.ForeignKey(OrderedItem)
    product = models.ForeignKey(Product)

    def __unicode__(self):
        return u'Name: %s\nTitle1: %s\nTitle2: %s\nEmail: %s@digitalrapids.com\nMobile: %s'\
                % (self.name, self.title1, self.title2, self.email, self.mobile)

    def as_list(self):
        return (
            ('Name', self.name),
            ('Title 1', self.title1),
            ('Title 2', self.title2),
            ('Email', '%s@digitalrapids.com' % self.email),
            ('Mobile', self.mobile)
            )


class DrUkBcForm(ModelForm):
    class Meta:
        model = DrUkBc
        exclude = (
            'ordereditem',
            'product'
        )


class DrRemoteBc(models.Model):
    """
    Digital Rapids Remote business cards
    """
    name = models.CharField(max_length=50)
    title1 = models.CharField("Title 1", max_length=50)
    title2 = models.CharField("Title 2", max_length=50, blank=True, null=True)
    email = models.CharField(help_text="@digitalrapids.com", max_length=50)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    tel = models.CharField(help_text='Include area code. Will be automatically formatted to <em>(nnn) nnn-nnnn</em>.', max_length=50)
    cell = models.CharField(help_text='Include area code. Will be automatically formatted to <em>(nnn) nnn-nnnn</em>.', max_length=50, blank=True, null=True)
    ordereditem = models.ForeignKey(OrderedItem)
    product = models.ForeignKey(Product)

    def __unicode__(self):
        return u'Name: %s\nTitle1: %s\nTitle2: %s\nEmail: %s@digitalrapids.com\nCity: %s\nState: %s\nTel: %s\nCell: %s'\
                % (self.name, self.title1, self.title2, self.email, self.city, self.state, self.tel, self.cell)

    def as_list(self):
        return (
            ('Name', self.name),
            ('Title 1', self.title1),
            ('Title 2', self.title2),
            ('Email', '%s@digitalrapids.com' % self.email),
            ('City', self.city),
            ('State', self.state),
            ('Tel', self.tel),
            ('Cell', self.cell)
            )


class DrRemoteBcForm(ModelForm):
    class Meta:
        model = DrRemoteBc
        exclude = (
            'ordereditem',
            'product'
        )


CATECH_LABEL_CHOICES = (
    ('CELL', 'CELL'),
    ('DIRECT', 'DIRECT'),
)


class CaTechTorontoBc(models.Model):
    """
    CaTECH business cards - Toronto
    """
    name = models.CharField(max_length=50)
    initials = models.CharField(max_length=50, blank=True, help_text="Use for degrees, credentials, etc.")
    title = models.CharField(max_length=50)
    email = models.CharField(help_text="@catech-systems.com", max_length=50)
    cell = models.CharField(help_text='Will be automatically formatted.', 
                            max_length=50, blank=True)
    cell_label = models.CharField(help_text="Used to label cell number", 
                                  max_length=50, choices=CATECH_LABEL_CHOICES, default='CELL', blank=True)
    fax = models.CharField(max_length=4, help_text="Enter only the last 4 digits. The area code and first three digits will be automatically added.")
    ordereditem = models.ForeignKey(OrderedItem)
    product = models.ForeignKey(Product)

    def __unicode__(self):
        return u'Name: %s\nTitle: %s\nEmail: %s\nCell: %s\nFax: %s' \
                % (self.name, self.title, self.email, self.cell, self.fax)

    def as_list(self):
        return (('Name', self.name), ('Title', self.title), ('Email', '%s@catech-systems.com' % self.email), ('Cell', self.cell), ('Fax', self.fax))

class CaTechTorontoBcForm(ModelForm):
    class Meta:
        model = CaTechTorontoBc
        exclude = (
            'ordereditem',
            'product'
        )

class CaTechMontrealBc(models.Model):
    """
    CaTECH business cards - Montreal
    """
    name = models.CharField(max_length=50)
    initials = models.CharField(max_length=50, blank=True, help_text="Use for degrees, credentials, etc.")
    title = models.CharField(max_length=50)
    ext = models.CharField("Extension", max_length=50, blank=True)
    email = models.CharField(help_text="@catech-systems.com", max_length=50)
    cell = models.CharField(help_text='Will be automatically formatted.', max_length=50, blank=True)
    cell_label = models.CharField(help_text="Used to label cell number", max_length=50, choices=CATECH_LABEL_CHOICES, default='CELL', blank=True)
    ordereditem = models.ForeignKey(OrderedItem)
    product = models.ForeignKey(Product)

    def __unicode__(self):
        return u'Name: %s\nTitle: %s\nExt: %s\nEmail: %s\nCell: %s' % (self.name, self.title, self.ext, self.email, self.cell)

    def as_list(self):
        return (('Name', self.name), ('Title', self.title), ('Ext', self.ext), ('Email', '%s@catech-systems.com' % self.email), ('Cell', self.cell))

class CaTechMontrealBcForm(ModelForm):
    class Meta:
        model = CaTechMontrealBc
        exclude = (
            'ordereditem',
            'product'
        )

class CaTechOttawaBc(models.Model):
    """
    CaTECH business cards - Ottawa
    """
    name = models.CharField(max_length=50)
    initials = models.CharField(max_length=50, blank=True, help_text="Use for degrees, credentials, etc.")
    title = models.CharField(max_length=50)
    ext = models.CharField("Extension", max_length=50, blank=True)
    email = models.CharField(help_text="@catech-systems.com", max_length=50)
    cell = models.CharField(help_text='Will be automatically formatted.', max_length=50, blank=True)
    cell_label = models.CharField(help_text="Used to label cell number", max_length=50, choices=CATECH_LABEL_CHOICES, default='CELL', blank=True)
    ordereditem = models.ForeignKey(OrderedItem)
    product = models.ForeignKey(Product)

    def __unicode__(self):
        return u'Name: %s\nTitle: %s\nExt: %s\nEmail: %s\nCell: %s' % (self.name, self.title, self.ext, self.email, self.cell)

    def as_list(self):
        return (('Name', self.name), ('Title', self.title), ('Ext', self.ext), ('Email', '%s@catech-systems.com' % self.email), ('Cell', self.cell))

class CaTechOttawaBcForm(ModelForm):
    class Meta:
        model = CaTechOttawaBc
        exclude = (
            'ordereditem',
            'product'
        )

CATECH_BC_TEMPLATE_CHOICES = (
    (1, 'Markham'),
    (2, 'Edmonton'),
    (3, 'Calgary'),
    (4, 'Saint-Laurent'),
    (5, 'Coquitlam'),
    (6, 'Ottawa'),
)

class CaTechBc(models.Model):
    """
    CaTECH business cards - new
    """
    name = models.CharField(max_length=50)
    title = models.CharField(max_length=50)
    direct_phone = models.CharField("Direct phone", max_length=50)
    email = models.CharField(help_text="@catech-systems.com", max_length=50)
    ordereditem = models.ForeignKey(OrderedItem)
    product = models.ForeignKey(Product)
    template = models.IntegerField('Template', choices=CATECH_BC_TEMPLATE_CHOICES)

    def __unicode__(self):
        return u'Name: %s\nTitle: %s\nDirect phone: %s\nEmail: %s' % (self.name, self.title, self.direct_phone, self.email)

    def as_list(self):
        return (('Name', self.name), ('Title', self.title), ('Direct Phone', self.ext), ('Email', '%s@catech-systems.com' % self.email))

class CaTechBcForm(ModelForm):
    class Meta:
        model = CaTechBc
        exclude = (
            'ordereditem',
            'product'
        )


class RossBc(models.Model):
    """
    Ross D & Sons business cards
    """
    building_name = models.CharField(max_length=255)
    street_address = models.CharField(max_length=255)
    city = models.CharField(max_length=255)
    province = models.CharField(max_length=30, choices=PROVINCE_CHOICES)
    name = models.CharField(max_length=255)
    job_title = models.CharField(max_length=255)
    direct_number = models.CharField(max_length=255)
    ordereditem = models.ForeignKey(OrderedItem)
    product = models.ForeignKey(Product)

    def __unicode__(self):
        return u'Building name: %s\nStreet address: %s\nCity: %s\nProvince: %s\nName: %s\nJob title: %s\nDirect number: %s' % (self.building_name, self.street_address, self.city, self.province, self.name, self.job_title, self.direct_number)

    def as_list(self):
        return (('Building name', self.building), ('Street address', self.street_address), ('City', self.city), ('Province', self.province), ('Name', self.name), ('Job title', self.job_title), ('Direct number', self.direct_number))

class RossBcForm(ModelForm):
    class Meta:
        model = RossBc
        exclude = (
            'ordereditem',
            'product',
        )


class TrilliumBc(models.Model):
    """
    Trillium College business cards
    """
    card_type = models.CharField(max_length=255, choices=TRILLIUM_CARD_TYPE_CHOICES)
    campus = models.CharField(max_length=255, choices=TRILLIUM_CAMPUS_CHOICES)
    name = models.CharField(max_length=50, blank=True, help_text='Will not appear on Campus Generic Blank Card.')
    title = models.CharField(max_length=50, blank=True, help_text='Will not appear on Campus Generic Blank Card or Individual Admission Representative Card.')
    email = models.CharField(help_text="Enter your name for your email only as @trilliumcollege.ca will appear automatically. Will not appear on Campus Generic Blank Card.", max_length=50, blank=True)
    ext = models.CharField("Extension", help_text='Will not appear on Campus Generic Blank Card.', max_length=50, blank=True)
    ordereditem = models.ForeignKey(OrderedItem)
    product = models.ForeignKey(Product)

    def __unicode__(self):
        return u'Name: %s\nTitle: %s\nEmail: %s\nExt: %s\nCampus: %s' % (self.name, self.title, self.email, self.ext, self.campus)

    def as_list(self):
        return (('Name', self.name), ('Title', self.title), ('Email', self.email), ('Ext', self.ext), ('Campus', self.campus))

class TrilliumBcForm(ModelForm):
    class Meta:
        model = TrilliumBc
        exclude = (
            'ordereditem',
            'product',
        )


class KafkoEnglishCanadaBc(models.Model):
    """
    Business cards for Kafko Canada in English.
    """
    name = models.CharField(max_length=255)
    title = models.CharField(max_length=255)
    ext = models.CharField("Extension", max_length=50)
    fax = models.CharField(help_text='Will be automatically formatted.', max_length=50, blank=True)
    cell = models.CharField(help_text='Will be automatically formatted.', max_length=50, blank=True)
    email = models.CharField(help_text="@kafkomfg.com", max_length=100)
    ordereditem = models.ForeignKey(OrderedItem)
    product = models.ForeignKey(Product)

    def __unicode__(self):
        return u'Name: %s\nTitle: %s\nExt: %s\nFax: %s\nCell: %s\nEmail: %s' % (self.name, self.title, self.ext, self.fax, self.cell, self.email)

    def as_list(self):
        return (('Name', self.name), ('Title', self.title), ('Ext', self.ext), ('Fax', self.fax), ('Cell', self.cell), ('Email', self.email))

class KafkoEnglishCanadaBcForm(ModelForm):
    class Meta:
        model = KafkoEnglishCanadaBc
        exclude = (
            'ordereditem',
            'product',
        )


class KafkoFrenchCanadaBc(models.Model):
    """
    Business cards for Kafko Canada in French.
    """
    name = models.CharField(max_length=255)
    title_fr = models.CharField("Title (French)", max_length=255)
    title_en = models.CharField("Title (English)", max_length=255)
    ext = models.CharField("Extension", max_length=50)
    email = models.CharField(help_text="@kafkomfg.com", max_length=100)
    ordereditem = models.ForeignKey(OrderedItem)
    product = models.ForeignKey(Product)

    def __unicode__(self):
        return u'Name: %s\nTitle (French): %s\nTitle (English):\nExt: %s\nFax: %s\nCell: %s\nEmail: %s' % (self.name, self.title_fr, self.title_en, self.ext, self.fax, self.cell, self.email)

    def as_list(self):
        return (('Name', self.name), ('Title (French)', self.title_fr), ('Title (English)', self.title_en), ('Ext', self.ext), ('Fax', self.fax), ('Cell', self.cell), ('Email', self.email))

class KafkoFrenchCanadaBcForm(ModelForm):
    class Meta:
        model = KafkoFrenchCanadaBc
        exclude = (
            'ordereditem',
            'product',
        )


class KafkoUsBc(models.Model):
    """
    Business cards for Kafko US in English.
    """
    location = models.CharField(max_length=255, choices=KAFKO_US_CHOICES)
    name = models.CharField(max_length=255)
    title = models.CharField(max_length=255)
    ext = models.CharField("Extension", max_length=50)
    fax = models.CharField(help_text='Will be automatically formatted.', max_length=50, blank=True)
    cell = models.CharField(help_text='Will be automatically formatted.', max_length=50, blank=True)
    email = models.CharField(help_text="@kafkomfg.com", max_length=100)
    ordereditem = models.ForeignKey(OrderedItem)
    product = models.ForeignKey(Product)

    def __unicode__(self):
        return u'Location: %s\nName: %s\nTitle: %s\nExt: %s\nFax: %s\nCell: %s\nEmail: %s' % (self.location, self.name, self.title, self.ext, self.fax, self.cell, self.email)

    def as_list(self):
        return (('Location', self.location), ('Name', self.name), ('Title', self.title), ('Ext', self.ext), ('Fax', self.fax), ('Cell', self.cell), ('Email', self.email))

class KafkoUsBcForm(ModelForm):
    class Meta:
        model = KafkoUsBc
        exclude = (
            'ordereditem',
            'product',
        )


class AlgonquinMississaugaBc(models.Model):
    """
    Business cards for Algonquin Mississauga.
    """
    name = models.CharField(max_length=255)
    title = models.CharField(max_length=255)
    email = models.CharField(help_text="@algonquinacademy.com", max_length=100)
    ordereditem = models.ForeignKey(OrderedItem)
    product = models.ForeignKey(Product)

    def __unicode__(self):
        return u'Name: %s\nTitle: %s\nEmail: %s' % (self.name, self.title, self.email)

    def as_list(self):
        return (('Name', self.name), ('Title', self.title), ('Email', self.email))

class AlgonquinMississaugaBcForm(ModelForm):
    class Meta:
        model = AlgonquinMississaugaBc
        exclude = (
            'ordereditem',
            'product',
        )


class AlgonquinOttawaBc(models.Model):
    """
    Business cards for Algonquin Ottawa.
    """
    name = models.CharField(max_length=255)
    title = models.CharField(max_length=255)
    email = models.CharField(help_text="@algonquinacademy.com", max_length=100)
    ordereditem = models.ForeignKey(OrderedItem)
    product = models.ForeignKey(Product)

    def __unicode__(self):
        return u'Name: %s\nTitle: %s\nEmail: %s' % (self.name, self.title, self.email)

    def as_list(self):
        return (('Name', self.name), ('Title', self.title), ('Email', self.email))

class AlgonquinOttawaBcForm(ModelForm):
    class Meta:
        model = AlgonquinOttawaBc
        exclude = (
            'ordereditem',
            'product',
        )


class SuperiorEnergyBc(models.Model):
    """
    Business cards for Superior Energy.
    """
    name = models.CharField(max_length=255)
    title = models.CharField(max_length=255)
    direct = models.CharField(help_text='Will be automatically formatted.', max_length=50)
    cell = models.CharField(help_text='Will be automatically formatted.', max_length=50)
    fax = models.CharField(help_text='Will be automatically formatted.', max_length=50)
    email = models.CharField(help_text="@superiorenergy.ca", max_length=100)
    ordereditem = models.ForeignKey(OrderedItem)
    product = models.ForeignKey(Product)

    def __unicode__(self):
        return u'Name: %s\nTitle: %s\nDirect: %s\nCell: %s\nFax: %s\nEmail: %s' % (self.name, self.title, self.direct, self.cell, self.fax, self.email)

    def as_list(self):
        return (('Name', self.name), ('Title', self.title), ('Direct', self.direct), ('Cell', self.cell), ('Fax', self.fax), ('Email', self.email))

class SuperiorEnergyBcForm(ModelForm):
    class Meta:
        model = SuperiorEnergyBc
        exclude = (
            'ordereditem',
            'product',
        )


class SuperiorEnergyAgentBc(models.Model):
    """
    Agent business cards for Superior Energy.
    """
    name = models.CharField(max_length=255)
    title = models.CharField(max_length=255)
    email = models.CharField(max_length=100)
    direct = models.CharField(help_text='Will be automatically formatted.', max_length=50)
    cell = models.CharField(help_text='Will be automatically formatted.', max_length=50, blank=True)
    fax = models.CharField(help_text='Will be automatically formatted.', max_length=50, blank=True)
    ordereditem = models.ForeignKey(OrderedItem)
    product = models.ForeignKey(Product)

    def __unicode__(self):
        return u'Name: %s\nTitle: %s\nEmail: %s\nDirect: %s\nCell: %s\nFax: %s' % (self.name, self.title, self.email, self.direct, self.cell, self.fax)

    def as_list(self):
        return (('Name', self.name), ('Title', self.title), ('Email', self.email), ('Direct', self.direct), ('Cell', self.cell), ('Fax', self.fax))

class SuperiorEnergyAgentBcForm(ModelForm):
    class Meta:
        model = SuperiorEnergyAgentBc
        exclude = (
            'ordereditem',
            'product',
        )


class RexallBc(models.Model):
    """
    Rexall business card.
    """
    name = models.CharField(max_length=60)
    title = models.CharField(max_length=90)
    ext = models.CharField(max_length=12)
    address = models.CharField(max_length=50)
    city = models.CharField(max_length=25)
    province = models.CharField(max_length=30, choices=[(x[1], x[1]) for x in PROVINCE_CHOICES])
    zip = models.CharField(max_length=30)

    ordereditem = models.ForeignKey(OrderedItem)
    product = models.ForeignKey(Product)

    def __unicode__(self):
        return u'Name: %s\nTitle: %s\nExt: %s\nAddress: %s\nCity: %s\nProvince: %s\nZip: %s\n'\
                % (self.name, self.title, self.ext, self.address, self.city, self.province, self.zip)

    def as_list(self):
        return (
            ('Name', self.name),
            ('Title', self.title),
            ('Ext', self.ext),
            ('Address', self.address),
            ('City', self.city),
            ('Province', self.province),
            ('Zip', self.zip)
        )

class RexallBcForm(ModelForm):
    class Meta:
        model = RexallBc
        exclude = (
            'ordereditem',
            'product'
        )

class EverestEnvelopeCommon(models.Model):
    campus_location = models.CharField(max_length=60)
    address_1 = models.CharField(max_length=60)
    address_2 = models.CharField(max_length=60)
    city = models.CharField(max_length=30)
    province = models.CharField(max_length=2, choices=PROVINCE_CHOICES)
    postal_code = models.CharField(max_length=40)

    ordereditem = models.ForeignKey(OrderedItem)
    product = models.ForeignKey(Product)

    def __unicode__(self):
        return "\n".join(["%s: %s" % f for f in self.as_list])

    def as_list(self):
        return (
            ('Location', self.campus_location),
            ('Address 1', self.address_1),
            ('Address 2', self.address_2),
            ('City', self.city),
            ('Province', self.province),
            ('Postal code', self.postal_code)
        )

    class Meta:
        abstract = True

class EverestN10Envelope(EverestEnvelopeCommon):
    class Meta(EverestEnvelopeCommon.Meta):
        db_table = 'vardata_everest_n10_env'

class EverestN10EnvelopeForm(ModelForm):
    class Meta:
     model = EverestN10Envelope
     exclude = ('ordereditem', 'product')


class Everest10x13Envelope(EverestEnvelopeCommon):
    class Meta(EverestEnvelopeCommon.Meta):
        db_table = 'vardata_everest_10x13_env'

class Everest10x13EnvelopeForm(ModelForm):
    class Meta:
        model = Everest10x13Envelope
        exclude = ('ordereditem', 'product')


class Everest9x12Envelope(EverestEnvelopeCommon):
    class Meta(EverestEnvelopeCommon.Meta):
        db_table = 'vardata_everest_9x12_env'

class Everest9x12EnvelopeForm(ModelForm):
    class Meta:
        model = Everest9x12Envelope
        exclude = ('ordereditem', 'product')


class Everest6x9Envelope(EverestEnvelopeCommon):
    class Meta(EverestEnvelopeCommon.Meta):
        db_table = 'vardata_everest_6x9_env'

class Everest6x9EnvelopeForm(ModelForm):
    class Meta:
        model = Everest6x9Envelope
        exclude = ('ordereditem', 'product')


class EverestSampleLetterhead(EverestEnvelopeCommon):
    phone = models.CharField(max_length=30)
    fax = models.CharField(max_length=30)

    class Meta(EverestEnvelopeCommon.Meta):
        db_table = 'vardata_everest_letterhead'

class EverestSampleLetterheadForm(ModelForm):
    class Meta:
        model = EverestSampleLetterhead
        exclude = ('ordereditem', 'product')

class EverestBC(models.Model):
    """
    Everest business card.
    """
    name = models.CharField(max_length=60)
    title_1 = models.CharField(max_length=90)
    title_2 = models.CharField(max_length=90, blank=True)

    phone = models.CharField(max_length=60, blank=True)
    phone_ext = models.CharField(max_length=6, blank=True)

    mobile = models.CharField(max_length=60, blank=True)
    email = models.CharField(max_length=50)

    campus = models.CharField(max_length=20, blank=True)
    address_1 = models.CharField(max_length=40)
    address_2 = models.CharField(max_length=40)

    ordereditem = models.ForeignKey(OrderedItem)
    product = models.ForeignKey(Product)

    telephone = models.CharField(max_length=60, blank=True, verbose_name='Address phone')

    fax = models.CharField(max_length = 60, blank=True, verbose_name='Address fax')

    def __unicode__(self):
        return unicode("\n".join(["%s: %s" % f for f in self.as_list()]))

    def as_list(self):
        return (
            ('Name', self.name),
            ('Title 1', self.title_1),
            ('Title 2', self.title_2),
            ('Phone', self.phone),
            ('Phone ext', self.phone_ext),
            ('Mobile', self.mobile),
            ('Email', self.email),
            ('Campus', self.campus),
            ('Address 1', self.address_1),
            ('Address 2', self.address_2),
            ('Telephone', self.telephone),
            ('Fax', self.fax),
        )

class EverestBCForm(ModelForm):
    class Meta:
        model = EverestBC
        exclude = (
            'ordereditem',
            'product'
        )


class TrilliumDoubleBC(models.Model):
    """
    Trillium two-sided business card
    """
    name = models.CharField(max_length=60)
    title = models.CharField(max_length=60)

    address_1 = models.CharField(max_length=60)
    address_2 = models.CharField(max_length=60, blank=True)
    address_3 = models.CharField(max_length=60, blank=True)

    phone = models.CharField(max_length=60)
    fax = models.CharField(max_length=60, blank=True)
    email = models.CharField(max_length=60, blank=True)

    ordereditem = models.ForeignKey(OrderedItem)
    product = models.ForeignKey(Product)

    def __unicode__(self):
        return unicode("\n".join(["%s: %s" % f for f in self.as_list()]))

    def as_list(self):
        return (
            ('Name', self.name),
            ('Title', self.title),
            ('Address 1', self.address_1),
            ('Address 2', self.address_2),
            ('Address 3', self.address_3),
            ('Phone', self.phone),
            ('Fax', self.fax),
            ('Email', self.email),
        )

class TrilliumDoubleBCForm(ModelForm):
    class Meta:
        model = TrilliumDoubleBC
        exclude = (
            'ordereditem',
            'product'
        )
