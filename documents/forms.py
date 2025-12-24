# documents/forms.py
from django import forms
from .models import Document

class DocumentForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ['full_name', 'identifier', 'channel', 'request_type', 'department', 'status', 'comment', 'file']
        
        widgets = {
            'full_name': forms.TextInput(attrs={'placeholder': 'ПІБ клієнта', 'class': 'form-input'}),
            'identifier': forms.TextInput(attrs={'placeholder': 'ІПН, телефон тощо', 'class': 'form-input'}),
            'channel': forms.Select(attrs={'class': 'form-select'}),
            'request_type': forms.Select(attrs={'class': 'form-select'}),
            'department': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'comment': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Опис проблеми', 'class': 'form-input'}),
            'file': forms.FileInput(attrs={'class': 'form-file'}),
        }