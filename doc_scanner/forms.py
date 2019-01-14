from django import forms
from .models import Source


class SourceRemoteForm(forms.ModelForm):
    remote_password = forms.CharField(widget=forms.PasswordInput())

    class Meta:
        model = Source
        fields = ['remote_systemIP', 'remote_username', 'remote_password']
