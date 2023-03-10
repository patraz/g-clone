from django import forms
from .models import Product
from django.core.exceptions import ValidationError

import re

def validate_english_chars(value):
    pattern = re.compile('[^a-zA-Z0-9_]')
    if pattern.search(value):
        raise ValidationError('Only English characters are allowed')

def minimal_price(value):
    if value < 200:
        raise ValidationError('Price have to be minimum 200')

class ProductModelForm(forms.ModelForm):
    name = forms.CharField(validators=[validate_english_chars])
    description = forms.CharField(validators=[validate_english_chars])
    slug = forms.CharField(validators=[validate_english_chars])
    price = forms.IntegerField(validators=[minimal_price])
    class Meta:
        model = Product
        fields = (
            'name',
            'description',
            'cover',
            'slug',
            'content_url',
            'content_file',
            'price',
            'active'
        )