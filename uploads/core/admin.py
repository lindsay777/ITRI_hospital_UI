from django.contrib import admin

from uploads.core.models import Document
# 以register的方式 將建立的資料模型向admin註冊
admin.site.register(Document)

# Register your models here.
