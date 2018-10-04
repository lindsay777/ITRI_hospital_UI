from __future__ import unicode_literals

from django.db import models

# 建立model
class Document(models.Model):
    description = models.CharField(max_length=255, blank=True)
    document = models.FileField(upload_to='documents/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

class PATIENT(models.Model):
    pid = models.CharField(max_length=50, null=True)
    filename = models.CharField(max_length=50,null=True)
    #pub_date = models.DateTimeField('date published')
    name = models.CharField(max_length=50)
    sex = models.CharField(max_length=1,null=True)
    age = models.CharField(max_length=5,null=True)
    mp = models.CharField(max_length=5,null=True)

    def __unicode__(self):
        return self.pid

class FRAX(models.Model):
    pid = models.CharField(max_length=50, null=True)
    scantype = models.CharField(max_length=15,null=True)
    fracture = models.CharField(max_length=5,null=True)

class LVA(models.Model):
    pid = models.CharField(max_length=50, null=True)
    scantype = models.CharField(max_length=15,null=True)
    lva = models.CharField(max_length=50,null=True)

class APSPINE(models.Model):
    pid = models.CharField(max_length=50, null=True)
    scantype = models.CharField(max_length=15,null=True)
    tscore = models.CharField(max_length=30,null=True)
    zscore = models.CharField(max_length=30,null=True)
    region = models.CharField(max_length=30,null=True)
    apspine = models.CharField(max_length=100,null=True)

class DUALFEMUR(models.Model):
    pid = models.CharField(max_length=50, null=True)
    scantype = models.CharField(max_length=15,null=True)
    tscore = models.CharField(max_length=30,null=True)
    zscore = models.CharField(max_length=30,null=True)
    region = models.CharField(max_length=30,null=True)
    dualfemur = models.CharField(max_length=100,null=True)

class COMBINATION(models.Model):
    pid = models.CharField(max_length=50, null=True)
    scantype = models.CharField(max_length=15,null=True)
    tscore = models.CharField(max_length=30,null=True)
    zscore = models.CharField(max_length=30,null=True)
    region = models.CharField(max_length=30,null=True)
    lva = models.CharField(max_length=50,null=True)
    apspine = models.CharField(max_length=100,null=True)
    dualfemur = models.CharField(max_length=100,null=True)
    combination = models.CharField(max_length=100,null=True)
    t7 = models.CharField(max_length=5,null=True)

