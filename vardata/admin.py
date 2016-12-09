from django.contrib import admin
from models import *

class MimicBcAdmin(admin.ModelAdmin):
    raw_id_fields = ('ordereditem', 'product')

class TlaBcAdmin(admin.ModelAdmin):
    raw_id_fields = ('ordereditem', 'product')

class HarrisCertificateAdmin(admin.ModelAdmin):
    raw_id_fields = ('ordereditem', 'product')

class DrAsiaPacificBcAdmin(admin.ModelAdmin):
    raw_id_fields = ('ordereditem', 'product')

class DrUkBcAdmin(admin.ModelAdmin):
    raw_id_fields = ('ordereditem', 'product')

class DrRemoteBcAdmin(admin.ModelAdmin):
    raw_id_fields = ('ordereditem', 'product')

class CaTechTorontoBcAdmin(admin.ModelAdmin):
    raw_id_fields = ('ordereditem', 'product')

class CaTechMontrealBcAdmin(admin.ModelAdmin):
    raw_id_fields = ('ordereditem', 'product')

class CaTechOttawaBcAdmin(admin.ModelAdmin):
    raw_id_fields = ('ordereditem', 'product')

class CaTechBcAdmin(admin.ModelAdmin):
    raw_id_fields = ('ordereditem', 'product')

class RossBcAdmin(admin.ModelAdmin):
    raw_id_fields = ('ordereditem', 'product')

class TrilliumBcAdmin(admin.ModelAdmin):
    raw_id_fields = ('ordereditem', 'product')

class KafkoEnglishCanadaBcAdmin(admin.ModelAdmin):
    raw_id_fields = ('ordereditem', 'product')

class KafkoFrenchCanadaBcAdmin(admin.ModelAdmin):
    raw_id_fields = ('ordereditem', 'product')

class KafkoUsBcAdmin(admin.ModelAdmin):
    raw_id_fields = ('ordereditem', 'product')

class AlgonquinMississaugaBcAdmin(admin.ModelAdmin):
    raw_id_fields = ('ordereditem', 'product')

class AlgonquinOttawaBcAdmin(admin.ModelAdmin):
    raw_id_fields = ('ordereditem', 'product')

class SuperiorEnergyBcAdmin(admin.ModelAdmin):
    raw_id_fields = ('ordereditem', 'product')

class SuperiorEnergyAgentBcAdmin(admin.ModelAdmin):
    raw_id_fields = ('ordereditem', 'product')

class RexallBcAdmin(admin.ModelAdmin):
    raw_id_fields = ('ordereditem', 'product')

class EverestN10EnvelopeAdmin(admin.ModelAdmin):
    raw_id_fields = ('ordereditem', 'product')

class Everest10x13EnvelopeAdmin(admin.ModelAdmin):
    raw_id_fields = ('ordereditem', 'product')

class Everest9x12EnvelopeAdmin(admin.ModelAdmin):
    raw_id_fields = ('ordereditem', 'product')

class Everest6x9EnvelopeAdmin(admin.ModelAdmin):
    raw_id_fields = ('ordereditem', 'product')

class EverestSampleLetterheadAdmin(admin.ModelAdmin):
    raw_id_fields = ('ordereditem', 'product')

admin.site.register(MimicBc, MimicBcAdmin)
admin.site.register(TlaBc, TlaBcAdmin)
admin.site.register(HarrisCertificate, HarrisCertificateAdmin)
admin.site.register(DrAsiaPacificBc, DrAsiaPacificBcAdmin)
admin.site.register(DrUkBc, DrUkBcAdmin)
admin.site.register(DrRemoteBc, DrRemoteBcAdmin)
admin.site.register(CaTechTorontoBc, CaTechTorontoBcAdmin)
admin.site.register(CaTechMontrealBc, CaTechMontrealBcAdmin)
admin.site.register(CaTechOttawaBc, CaTechOttawaBcAdmin)
admin.site.register(CaTechBc, CaTechBcAdmin)
admin.site.register(RossBc, RossBcAdmin)
admin.site.register(TrilliumBc, TrilliumBcAdmin)
admin.site.register(KafkoEnglishCanadaBc, KafkoEnglishCanadaBcAdmin)
admin.site.register(KafkoFrenchCanadaBc, KafkoFrenchCanadaBcAdmin)
admin.site.register(KafkoUsBc, KafkoUsBcAdmin)
admin.site.register(AlgonquinMississaugaBc, AlgonquinMississaugaBcAdmin)
admin.site.register(AlgonquinOttawaBc, AlgonquinOttawaBcAdmin)
admin.site.register(SuperiorEnergyBc, SuperiorEnergyBcAdmin)
admin.site.register(SuperiorEnergyAgentBc, SuperiorEnergyAgentBcAdmin)
admin.site.register(RexallBc, RexallBcAdmin)
admin.site.register(EverestN10Envelope, EverestN10EnvelopeAdmin)
admin.site.register(Everest10x13Envelope, Everest10x13EnvelopeAdmin)
admin.site.register(Everest9x12Envelope, Everest9x12EnvelopeAdmin)
admin.site.register(Everest6x9Envelope, Everest6x9EnvelopeAdmin)
admin.site.register(EverestSampleLetterhead, EverestSampleLetterheadAdmin)
