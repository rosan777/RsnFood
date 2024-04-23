from django import forms
from .models import Restaurant


class RestaurantForm(forms.ModelForm):
    """Form for the image model"""

    class Meta:
        model = Restaurant
        fields = ("name", "image")
