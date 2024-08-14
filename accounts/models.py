from django.db import models
from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.utils import timezone

# Create your models here.
from django.forms import DateTimeField
from datetime import  date

# import random
# import os
# import requests


class UserManager(BaseUserManager):
    """docstring fos UserManager"""

    def create_user(self, email, password=None, is_staff=False, is_active=True, is_verified=False, is_admin=False,
                    is_provider=False, verified_code=""):
        if not email:
            raise ValueError('Email is required')

        if not password:
            raise ValueError('password is required')

        user_obj = self.model(
            email=email
        )
        user_obj.set_password(password)
        user_obj.admin = is_admin
        user_obj.staff = is_staff
        user_obj.active = is_active
        user_obj.isverified = is_verified
        user_obj.isprovider = is_provider
        user_obj.verifiedcode = verified_code
        user_obj.save(using=self._db)

        return user_obj

    def create_staffuser(self, email, password=None):
        user = self.create_user(
            email,
            password=password,
            is_admin=False,
            is_staff=True,
            is_provider=False,
            is_active=True,
            is_verified=False,
            verifiedcode="",
        )
        return user

    def create_superuser(self, email, password=None):
        user = self.create_user(
            email,
            password=password,
            is_admin=True,
            is_staff=True,
            is_provider=False,
            is_active=True,
            is_verified=True,

        )
        return user


class User(AbstractBaseUser):
    email = models.CharField(max_length=100, unique=True)
    username = models.CharField(max_length=100)
    passwordstr = models.CharField(max_length=100, default="")
    first_login = models.BooleanField(default=False)
    active = models.BooleanField(default=True)
    active_patient = models.BooleanField(default=True)
    staff = models.BooleanField(default=False)
    role_id = models.IntegerField(default=False)
    isprovider = models.BooleanField(default=False)
    isverified = models.BooleanField(default=False)
    package = models.IntegerField(default=False)
    verifiedcode = models.CharField(max_length=30, default="")
    user_agent = models.CharField(max_length=50, default="")
    admin = models.BooleanField(default=False)
    timestamp = DateTimeField()
    document_id = models.CharField(max_length=250, default="")
    signing_link_1 = models.URLField(blank=True, null=True)
    signing_link_2 = models.URLField(blank=True, null=True)
    invite_id = models.CharField(max_length=250, default="")
    status = models.CharField(max_length=100)
    access_token = models.CharField(max_length=255, null=True, blank=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        return self.email

    def get_full_name(self):
        if self.username:
            return self.username
        else:
            return self.email

    def get_user_packageno(self):
        return self.packageno

    def get_user_name(self):
        return self.username

    def get_user_password(self):
        return self.password

    def get_user_paswordstr(self):
        return self.passwordstr

    def get_short_name(self):
        if self.username:
            return self.username
        else:
            return self.email

    def has_perm(self, perm, obj=None):
        return True

    def has_module_perms(self, app_label):
        return True

    @property
    def is_staff(self):
        return self.staff

    @property
    def is_provider(self):
        return self.isprovider
    @property
    def is_role_id(self):
        return self.role_id

    @property
    def is_verified(self):
        return self.is_verified

    @property
    def is_admin(self):
        return self.admin

    @property
    def is_active(self):
        return self.active


# Provider Model

class Provider(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    contact_no = models.CharField(max_length=20)
    license_state = models.CharField(max_length=20)
    type_of_practice = models.CharField(max_length=50)
    timestamp = models.DateTimeField(default=timezone.now)
    practice_name = models.CharField(max_length=50)
    practice_phone_number = models.CharField(max_length=20)
    practice_address = models.CharField(max_length=200)
    driving_license_front_img = models.ImageField(default='/media/default.png', upload_to='user_pics')
    driving_license_back_img = models.ImageField(default='/media/default.png', upload_to='user_pics')
    provider_image = models.ImageField(default='/media/patient.png', upload_to='user_pics')
    medical_license_image = models.ImageField(default='/media/default.png', upload_to='user_pics')
    fax_no = models.CharField(max_length=20)
    primary_care_office_name = models.CharField(max_length=100)
    primary_care_doctor_name = models.CharField(max_length=100)
    primary_care_doctor_id = models.CharField(max_length=50, null=True)
    provider_ref = models.CharField(max_length=50)
    total_patients = models.IntegerField(default=0)
    subscription_status = models.CharField(max_length=100, null=True)
    #new fields
    provider_type = models.CharField(max_length=100, null=False)
    package_type = models.CharField(max_length=250, null=False)
    flag = models.CharField(max_length=50, null=False)
    subscription_type = models.CharField(default="package",max_length=100,null=False)
    coupon_code = models.CharField(max_length=100,null=True)

    class Meta:
        db_table = "providers"
    def __str__(self):
        return self.first_name

# Provider Model

class PatientProfile(models.Model):
    patient_user = models.OneToOneField(User, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    dob = models.DateField(null=True, blank=True)
    contact_no = models.CharField(max_length=20)
    license_state = models.CharField(max_length=20)
    type_of_practice = models.CharField(max_length=50)
    timestamp = models.DateTimeField(default=timezone.now)
    practice_name = models.CharField(max_length=50)
    practice_phone_number = models.CharField(max_length=20)
    practice_address = models.CharField(max_length=200)
    driving_license_front_img = models.ImageField(default='/media/default.png', upload_to='user_pics')
    driving_license_back_img = models.ImageField(default='/media/default.png', upload_to='user_pics')
    provider_image = models.ImageField(default='/media/default.png', upload_to='user_pics')
    fax_no = models.CharField(max_length=20)
    primary_care_office_name = models.CharField(max_length=100)
    primary_care_doctor_name = models.CharField(max_length=100)
    doctor_ref_number = models.CharField(max_length=100)


    def __str__(self):
        return self.first_name


# Patient Model

class Patient(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE,primary_key=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    dob = models.DateField(null=True, blank=True)
    contact_no = models.CharField(max_length=20)
    driving_license_front_img = models.ImageField(default='/media/default.png', upload_to='user_pics')
    driving_license_back_img = models.ImageField(default='/media/default.png', upload_to='user_pics')
    timestamp = models.DateTimeField(default=timezone.now)
    package_no = models.CharField(max_length=100)

    class Meta:
        db_table = "patients"

    def __str__(self):
        return self.last_name


# Refferel Patient Model

class RefPatient(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE,primary_key=True)
    #provider = models.OneToOneField(User,on_delete=models.CASCADE)
    provider_id = models.CharField(max_length=50)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    dob = models.DateField(null=True, blank=True)
    contact_no = models.CharField(max_length=20)
    driving_license_front_img = models.ImageField(default='/media/default.png', upload_to='user_pics')
    driving_license_back_img = models.ImageField(default='/media/default.png', upload_to='user_pics')
    timestamp = models.DateTimeField(default=timezone.now)
    package_no = models.CharField(max_length=100)

    class Meta:
        db_table = "ref_patients"

    def __str__(self):
        return self.last_name



class PatientPaymentDetails(models.Model):
    patient_user = models.OneToOneField(User, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    card_no = models.CharField(max_length=30)
    card_expiry = models.CharField(max_length=30)
    card_cvv = models.CharField(max_length=5)
    card_address = models.CharField(max_length=200)
    card_city = models.CharField(max_length=20)
    card_state = models.CharField(max_length=20)
    card_zip_code = models.CharField(max_length=20)

    def __str__(self):
        return self.first_name

class Provider_Verification(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    user_position = models.IntegerField(max_length=5)

    class Meta:
        db_table = "provider_verification"

class Provider_type(models.Model):
    name = models.CharField(max_length=50)

    class Meta:
        db_table = "provider_type"

############################################## MA MODELS #######################################
class Invitation(models.Model):
    PROVIDER = 'provider'
    MAA = 'MA'
    INVITED_TYPE_CHOICES = [
        (PROVIDER, 'Provider'),
        (MAA, 'MA'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    invited_to = models.EmailField(max_length=60)
    invited_type = models.CharField(max_length=10,choices=INVITED_TYPE_CHOICES)
    date = models.DateField(default=date.today, blank=True)
    invitation_accept = models.BooleanField(default=False)
    class Meta:
        db_table = "invitation"
    def str(self):
        return self.invited_email

class Add_provider(models.Model):
    mid = models.CharField(max_length=10, null=False)
    pid = models.CharField(max_length=10,null=False)
    date = models.DateField(default=date.today, blank=True)
    status = models.BooleanField(default=True)

    class Meta:
        db_table = "ma_record"

    def str(self):
        return self.mid

# class AccessToken(models.Model):
#     token = models.CharField(max_length=255)
#     created_at = models.DateTimeField(auto_now_add=True)
#
#     def __str__(self):
#         return self.token