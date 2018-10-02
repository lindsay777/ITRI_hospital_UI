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
    pid = models.CharField(max_length=50, null=True)
    filename = models.CharField(max_length=50,null=True)
    #pub_date = models.DateTimeField('date published')
    #name = models.CharField(max_length=50)
    sex = models.CharField(max_length=1,null=True)
    age = models.CharField(null=True)
    mp = models.CharField(null=True)
    scantype = models.CharField(max_length=15,null=True)
    fracture = models.CharField(null=True)
    tscore = models.CharField(null=True)
    zscore = models.CharField(null=True)
    region = models.CharField(null=True)
    lva = models.CharField(null=True)
    apspine = models.CharField(null=True)
    dualfemur = models.CharField(null=True)
    combination = models.CharField(null=True)


    def __unicode__(self):
        return self.filename