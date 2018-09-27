from django import forms

from uploads.core.models import Document

# 創造一個依照model的form，會繼承欄位description document
class DocumentForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ('description', 'document', )

class nameForm(forms.Form):
    rename=forms.CharField()

class File(forms.Form):
    pid = forms.CharField(max_length=20)
    name = forms.CharField(max_length=20)
    sex = forms.CharField()
    age = forms.IntegerField()
    mp = forms.IntegerField()
    scanType = forms.CharField(max_length=10)
    fracture = forms.IntegerField()
    tscore = forms.CharField()
    zscore = forms.CharField()
    region = forms.CharField()
    lva = forms.CharField()
    apspine = forms.CharField()
    dualfemur = forms.CharField()
    combination = forms.CharField()