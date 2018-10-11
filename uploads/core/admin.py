from django.contrib import admin

from uploads.core.models import Document, PATIENT, FRAX, LVA, APSPINE, DUALFEMUR, COMBINATION
admin.site.register(Document)
admin.site.register(PATIENT)
admin.site.register(FRAX)
admin.site.register(LVA)
admin.site.register(APSPINE)
admin.site.register(DUALFEMUR)
admin.site.register(COMBINATION)