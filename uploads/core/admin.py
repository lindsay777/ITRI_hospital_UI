from django.contrib import admin

from uploads.core.models import Document, PATIENT, FRAX, LVA, APSPINE, DUALFEMUR, COMBINATION
# 以register的方式 將建立的資料模型向admin註冊
admin.site.register(Document)
admin.site.register(PATIENT)
admin.site.register(FRAX)
admin.site.register(LVA)
admin.site.register(APSPINE)
admin.site.register(DUALFEMUR)
admin.site.register(COMBINATION)

# Register your models here.
