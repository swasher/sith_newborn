# coding: utf-8

from .models import Image
from django import forms
from .widgets import AdminCloudinaryWidget


class ImageForm(forms.ModelForm):

    class Meta:
        model = Image
        fields = ['picture']
        widgets = {
            'picture': AdminCloudinaryWidget(),
        }