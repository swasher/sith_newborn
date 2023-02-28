# coding: utf-8

from .models import Image
from .models import SpareType
from .models import Computer
from django import forms
from .widgets import AdminCloudinaryWidget


class ImageForm(forms.ModelForm):

    class Meta:
        model = Image
        fields = ['picture']
        widgets = {
            'picture': AdminCloudinaryWidget(),
        }


class RenameForm(forms.Form):
    sparetype = forms.ModelChoiceField(label='Компонент',
                                       queryset=SpareType.objects.all().order_by('name_verbose'),
                                       widget=forms.Select(attrs={'class': 'form-control'}))
    old_key = forms.CharField(label='Старое название',
                              max_length=30,
                              widget=forms.TextInput(attrs={'class': 'form-control'}))
    new_key = forms.CharField(label='Новое название',
                              max_length=30,
                              widget=forms.TextInput(attrs={'class': 'form-control'}))


class ComputerForm(forms.ModelForm):
    class Meta:
        model = Computer
        fields = ['name']

    name = forms.CharField(max_length=50, required=False)