from django import forms
from django.contrib.auth.forms import ReadOnlyPasswordHashField, UserCreationForm
from .models import User, PatientProfile
from django.utils import timezone
from distutils.util import strtobool


class LoginForm(forms.Form):
    email = forms.EmailField(label='Email')
    password = forms.CharField(widget=forms.PasswordInput)


class VerificationUser(forms.Form):
    verify_code = forms.CharField(label='')


class RegisterationFrom(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    password2 = forms.CharField(label='Confirm Password', widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ('email',)

    def clean_email(self):
        email = self.cleaned_data.get('email')
        qs = User.objects.filter(email=email)
        if qs.exists():
            raise forms.ValidationError('Email is already taken')

        return email

    def clean_password2(self):
        passsword1 = self.cleaned_data.get('password1')
        passsword2 = self.cleaned_data.get('password2')

        if passsword1 and passsword2 and passsword1 != passsword2:
            raise forms.ValidationError("Password don't match")
        return passsword2

    def save(self, commit=True):
        user = super(RegisterationFrom, self).save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        user.active = True
        if commit:
            user.save()
            return user


class UserAdminChangeForm(forms.ModelForm):
    """A form for updating users. Includes all the fields on
    the user, but replaces the password field with admin's
    password hash display field.
    """
    password = ReadOnlyPasswordHashField()

    class Meta:
        model = User
        fields = ('email', 'password', 'active', 'admin', 'isprovider')

    def clean_password(self):
        # Regardless of what the user provides, return the initial value.
        # This is done here, rather than on the field, because the
        # field does not have access to the initial value
        return self.initial["password"]


class UserAdminCreationForm(forms.ModelForm):
    """A form for creating new users. Includes all the required
    fields, plus a repeated password."""
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Password confirmation', widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ('email',)

    def clean_password2(self):
        # Check that the two password entries match
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords don't match")
        return password2

    def save(self, commit=True):
        # Save the provided password in hashed format
        user = super(UserAdminCreationForm, self).save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


class UserRegisterationForm(forms.ModelForm):
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput, min_length=8, max_length=200)
    password2 = forms.CharField(label='Password confirmation', widget=forms.PasswordInput, min_length=8, max_length=200)
    first_name = forms.CharField(label='First Name')
    email = forms.CharField(label='Email')
    #password1.widget.attrs['placeholder'] = "Password"
    #password2.widget.attrs['placeholder'] = "Password Confirmation"
    #email.widget.attrs['placeholder'] = "Email"




    class Meta:
        model = User
        fields = ('email', 'isprovider')

    def clean_password2(self):
        # Check that the two password entries match
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        first_name = self.cleaned_data.get('first_name')

        if "&" in password1:
            raise forms.ValidationError("Don't Use (&) Sign.")
        return password1

        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords don't match")
        return password2

        # if first_name == None:
        #     raise forms.ValidationError("First name required.")
        # return first_name

    def save(self, commit=True):
        # Save the provided password in hashed format
        user = super(UserRegisterationForm, self).save(commit=False)
        user.set_password(self.cleaned_data["password1"])

        if commit:
            user.save()
        return user


class PatientRegisterationForm(forms.ModelForm):
    class Meta:
        model = PatientProfile
        fields = ['patient_user', 'first_name', 'last_name', 'contact_no', 'primary_care_office_name',
                  'primary_care_doctor_name', 'doctor_ref_number', ]
