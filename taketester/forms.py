from django import forms
from django.utils import timezone
from .models import Guest_User


class GuestUserForm(forms.ModelForm):
    class Meta:
        model = Guest_User
        fields = [
            'first_name',
            'last_name',
            'email',
            'phone',


        ]
