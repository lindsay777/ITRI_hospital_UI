from django.conf.urls import url
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static

from uploads.core import views

# 把url 跟views串起來!!
urlpatterns = [
    url(r'^$', views.home, name='home'),
    url(r'^uploads/simple/$', views.simple_upload, name='simple_upload'),
    url(r'^uploads/uploadDCM/$', views.upload_dcm, name='upload_dcm'),
    url(r'^uploads/uploadZIP/$', views.upload_zip, name='upload_zip'),
    url(r'^uploads/form/$', views.model_form_upload, name='model_form_upload'),
    # url(r'^uploads/form/$', views.manage_dcm, name='manage_dcm'),
    # url(r'^uploads/form/$', views.manage_zip, name='manage_zip'),
    url(r'^admin/', admin.site.urls),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
