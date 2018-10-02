from django.conf.urls import url
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static

from uploads.core import views

# 把url 跟views串起來!!
urlpatterns = [
    url(r'^$', views.home, name='home'),
    url(r'^uploads/form/$', views.model_form_upload, name='model_form_upload'),
    url(r'^uploads/uploadDCM/$', views.upload_dcm, name='upload_dcm'),
    url(r'^uploads/uploadDCM/$', views.upload_dcm, name='upload_dcm'),
    url(r'^uploads/uploadZIP/$', views.upload_zip, name='upload_zip'),
    url(r'^uploads/uploadMultiZIP/$', views.upload_multi_zip, name='upload_multi_zip'),
    url(r'^uploads/showZIP/$', views.show_zip, name='show_zip'),
    url(r'^uploads/manageDCM/$', views.manage_dcm, name='manage_dcm'),
    url(r'^uploads/showDCM/$', views.show_dcm, name='show_dcm'),
    url(r'^uploads/rename/$', views.rename, name='rename'),
    url(r'^uploads/remove/$', views.remove, name='remove'),
    url(r'^uploads/download/$', views.download, name='download'),
    url(r'^uploads/manageZIP/$', views.manage_zip, name='manage_zip'),
    url(r'^uploads/manageShowZIP/$', views.manage_show_zip, name='manage_show_zip'),
    url(r'^uploads/checkAPSpine/$', views.check_apspine, name='check_apspine'),
    url(r'^uploads/report/$', views.report, name='report'),
    url(r'^uploads/uploadDB/$', views.upload_to_db, name='upload_to_db'),
    url(r'^admin/', admin.site.urls),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
