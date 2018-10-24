from __future__ import unicode_literals

from django.db import models

class Document(models.Model):
    description = models.CharField(max_length=255, blank=True)
    document = models.FileField(upload_to='documents/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

class PATIENT(models.Model):
    pid = models.CharField(max_length=50, null=True)
    pub_date = models.CharField(max_length=22,null=True)
    name = models.CharField(max_length=50,null=True)
    sex = models.CharField(max_length=1,null=True)
    age = models.CharField(max_length=3,null=True)
    mp = models.CharField(max_length=3,null=True)

    def __unicode__(self):
        return self.pid

class FRAX(models.Model):
    pid = models.CharField(max_length=50, null=True)
    scantype = models.CharField(max_length=15,null=True)
    majorFracture = models.CharField(max_length=5,null=True)
    hipFracture = models.CharField(max_length=5,null=True)

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

