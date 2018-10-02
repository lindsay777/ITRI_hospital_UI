from __future__ import unicode_literals

from django.db import models

# 建立model
class Document(models.Model):
    description = models.CharField(max_length=255, blank=True)
    document = models.FileField(upload_to='documents/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

def get_upload_file_name(instance, filename):
    return "core/%s" %filename

class File(models.Model):
    #filepath = models.FileField(upload_to='files/', null=True, verbose_name="")
    filename = models.CharField(max_length=50)
    # pub_date = models.DateTimeField('date published')
    # pid = models.CharField(max_length=50)
    # name = models.CharField(max_length=50)
    # sex = models.CharField(max_length=5)
    # age = models.IntegerField()
    # mp = models.IntegerField()

    def __unicode__(self):
        return self.filename