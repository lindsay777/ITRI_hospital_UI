from django import forms

from uploads.core.models import Document

# 創造一個依照model的form，會繼承欄位description document
class DocumentForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ('description', 'document', )
