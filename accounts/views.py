import traceback

from django.shortcuts import render, redirect, reverse
from rest_framework.views import APIView
from django.contrib.auth.decorators import login_required
from rest_framework import permissions, status, generics
from rest_framework.permissions import AllowAny
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.http import HttpResponse, HttpResponseRedirect
from django.core.paginator import Paginator
import os
from cogni.settings import BASE_DIR
from rest_framework.views import exception_handler
from rest_framework.response import Response
from urllib.request import urlretrieve
from cogni.views import email_records
from payments.views import isPaymentSuccess
from .models import User as U, PatientPaymentDetails, Add_provider, Invitation, Patient, RefPatient, Provider, \
    Provider_Verification, Provider_type
from .serializer import LoginSerializer, RefpatientSerializer, CreateUserSerializer, LoginFormSerializer, \
    PasswordChangeSerializer, \
    LoginFormProviderSerializer, SignupProviderSerializer, ProviderTypeSerializer, UserDetailSerializer, \
    ProviderRegSerializer
from django.shortcuts import get_object_or_404
import json
from rest_framework.exceptions import APIException
from django.contrib.auth import update_session_auth_hash
from .forms import UserRegisterationForm, PatientRegisterationForm, LoginForm, VerificationUser
from knox.views import LoginView as KnoxLoginView
from knox.auth import TokenAuthentication

from django.contrib.auth import login, authenticate
from django.contrib.auth.hashers import make_password
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages, auth
from django.views.generic import CreateView, FormView

from django.contrib.auth import get_user_model
from backend.models import StripeCustomer
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.files.storage import FileSystemStorage
from django.utils.crypto import get_random_string

from random import choice
from string import ascii_lowercase
from dashboard.models import ProviderCard

from django import template
from django.conf import settings
from django.core.mail import send_mail
from django.template import loader
from django.views.generic import TemplateView
from django.shortcuts import render
from django.contrib import messages
import datetime
from datetime import timedelta
import re
from dashboard.models import SleepDiary
from django.http import JsonResponse
import cogni
import requests
from django.contrib.auth.decorators import login_required
from payments.models import Coupon

User = get_user_model()

MESSAGE_TAGS = {
    messages.ERROR: 'danger',
}


# def home(request):
# 	return render(request, 'home.html', {})


class ValidateEmail(APIView):

    def post(self, request, *args, **kwargs):
        email_id = request.data.get('id_email')
        if email_id:
            email = email_id
            user = User.objects.filter(email__iexact=email)

            if user.exists():
                return Response({
                    'success': True,
                    'message': 'Email is aleady exists'
                })
            else:
                return Response({
                    'success': False,
                    'message': 'Email not found'
                })

        else:

            return Response({
                'success': False,
                'message': 'Email is not given in post request'

            })


class RegisterPatient(APIView):

    def post(self, request, *args, **kwargs):
        json_arry_request = request.data.get('patient_modal')
        # json_array = json.loads(json_arry_request)

        return Response({
            'status': True,
            'message': json_arry_request
        })


class LoginAPI(KnoxLoginView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request, format=None):
        serializer = LoginSerializer(data=request.data)

        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        login(request, user)

        return super().post(request, format=None)


class RegisterUser(APIView):

    def post(self, request, *args, **kwargs):
        email = request.data.get('email', False)
        password = request.data.get('password', False)

        password = make_password(password)
        if email and password:
            temp_data = {
                "email": email,
                "password": password,
            }

            serializer = CreateUserSerializer(data=temp_data)
            serializer.is_valid(raise_exception=True)
            user = serializer.save()

            return Response({
                'status': True,
                'message': 'Account created'
            })

        else:
            return Response({
                'status': False,
                'message': 'Both email and password not set.'
            })


# class RegisterView(CreateView):	

# 	form_class = UserRegisterationForm
# 	template_name = 'registration/patient_referral_registration.html'
# 	success_url = '/accounts/login/'

# 	def form_valid(self):

# 		email = form.cleaned_data.get('email')
# 		password = form.cleaned_data.get('password')
# 		first_name = form.cleaned_data.get('first_name')

# 		return super(RegisterView, self).form_invalid()


def UpdateUser(request):
    try:
        if request.user.is_authenticated:
            if request.method == 'POST':
                messages.error(request, "Data  is not Updated.")
                return redirect('/dashboard/')

            else:
                messages.success(request, "Data update successfully.")
                return redirect('/dashboard/')
        else:
            return redirect('/accounts/login/', {})
    except Exception as e:
        print(e)
        return redirect('/')


def LoginPatient(request):
    try:
        if request.user.is_authenticated:
            return redirect('/dashboard/')
        # print(request.POST)
        if request.method == 'POST':
            form = LoginForm(request.POST)
            context = {
                'form': form,
                'base_url': cogni.settings.BASE_URL
            }

            if form.is_valid():
                email = request.POST['email']
                password = request.POST['password']
                user = authenticate(email=email, password=password)

                if user:

                    new_user_patient = User.objects.get(id=user.id)
                    print("active patient", new_user_patient.active_patient)

                    if not new_user_patient.active_patient:
                        messages.error(request, "You account has been block by provider, contact your provider!")
                        return redirect('/accounts/login/', context)

                    if user.is_admin:
                        messages.error(request, "Patient Login required.")
                        return redirect('/home_page/', context)

                    if user.is_provider:
                        messages.error(request, "Patient Login required.")
                        return redirect('/accounts/login/', context)

                    if not user.isverified:
                        messages.error(request, "Please verify your account ")
                        return redirect('/accounts/login/', context)

                    if user.is_active:
                        login(request, user)
                        # messages.success(request, "Patient Login in successfully.")
                        return redirect('/dashboard/', context)

                    else:

                        return redirect('/accounts/login/', {'form': form, 'base_url': cogni.settings.BASE_URL})


                else:
                    form = LoginForm()
                    messages.error(request, "Invalid email or password. Try again. ")
                    return redirect('/accounts/login/', {'form': form, 'base_url': cogni.settings.BASE_URL})

        else:
            form = LoginForm()
        return render(request, 'registration/login.html', {'form': form, 'base_url': cogni.settings.BASE_URL})
    except Exception as e:
        print(e)
        return redirect('/')


def pro_logout(request):
    auth.logout(request)
    return redirect('/accounts/provider_login')


def LoginProvider(request):
    try:
        if request.user.is_authenticated:
            return redirect('/dashboard/')

        if request.method == 'POST':

            form = LoginForm(request.POST)
            context = {
                'form': form,
                'base_url': cogni.settings.BASE_URL
            }

            if form.is_valid():
                email = request.POST['email']
                password = request.POST['password']
                user = authenticate(email=email, password=password)

                if user:
                    user_step = Provider_Verification.objects.get(user_id=user.id)
                    user_code = user_step.user_position
                    # if user.is_admin:
                    #     messages.error(request, "Provider Login required.")
                    #     return redirect('/accounts/provider_login/', context)
                    #
                    if not user.isverified and user_code > 1:
                        show_verify_message = request.session.get('show_verify_message', True)
                        context = {'show_verify_message': show_verify_message}
                        return redirect('/accounts/provider_verification/', context)

                    if user.is_provider:
                        login(request, user)
                        user_step = Provider_Verification.objects.get(user_id=user.id)
                        user_code = user_step.user_position
                        print("user codeeeeeeeeeeeeeee", user_code)
                        if user_code == 1:
                            # url = "/payments/" + str(user.id)
                            return redirect(f'/accounts/baa_signature/{user.id}')
                            # return redirect(url)
                        if user_code == 2:
                            return redirect('/accounts/provider_registration')
                        # if StripeCustomer.objects.filter(user_id=user.id).exists():
                        #    return redirect('/dashboard/')
                        if user_code == 3:
                            return redirect('/dashboard/')
                        if user_code == 4 or user_code == 5:
                            return redirect('/dashboard/')
                            # return redirect('/dashboard/provider_subscription/')
                    else:
                        messages.error(request, "Provider Login required.")
                        return redirect('/accounts/provider_login/', context)
                else:
                    messages.error(request, "Invalid email or password. Try again. ")
                    return redirect('/accounts/provider_login/', {'form': form, 'base_url': cogni.settings.BASE_URL})

        else:
            form = LoginForm()
            return render(request, 'registration/provider_login.html',
                          {'form': form, 'base_url': cogni.settings.BASE_URL})

    except Exception as e:
        print(e)
        return redirect('/')


def daterange(date1, date2):
    for n in range(int((date2 - date1).days) + 1):
        yield date1 + timedelta(n)


def UserRegterForm(request):
    try:
        if request.user.id is not None:
            return redirect('/dashboard/')
        if request.method == 'POST':
            package = 0
            form = UserRegisterationForm(request.POST or None)
            request.session['allform'] = request.POST
            context = {
                'form': form
            }
            check_valid = True
            invalid_format = "Invalid format"

            refNm = request.POST.get('doctor_ref_number')
            try:
                Provider.objects.get(provider_ref=refNm)
                verifiedrefid = None
                package = 1
            except Provider.DoesNotExist:
                print("Provider with reference {} does not exist.".format(refNm))

            password1 = request.POST.get('password1')
            password2 = request.POST.get('password2')
            pass_match = re.compile("^(?=.*[a-z])(?=.*[A-Z])(?=.*[0-9])(?=.*[!@#$%^&*_=+-]).{8,15}$")

            # if not pass_match.match(password1) or password1 != password2:

            if password1 != password2:
                check_valid = False
                if password1 != password2:
                    invalid_format = "Password didn't Match"

            if not check_valid or verifiedrefid is not None:
                context = {
                    'form': form,
                    'error': invalid_format,
                    'verifiedRefId': verifiedrefid,
                }

                return render(request, 'registration/patient_referral_registration.html', context)

            if form.is_valid():
                filepath = os.path.join(BASE_DIR, 'media')
                unique_id_patient_pic = ''.join(choice(ascii_lowercase) for i in range(8))
                i1 = request.POST.get('driving_license_front_img')
                ii1 = request.POST.get('front_image')
                if i1 != '':
                    myfile = request.FILES['driving_license_front_img']
                    fs = FileSystemStorage()
                    filename = fs.save(myfile.name, myfile)
                    uploaded_file_url_front = filename
                if ii1 != '':
                    print("Yes in ii1")
                    img_name_ii1 = str(unique_id_patient_pic) + 'front_licesnse.jpg'
                    full_path = filepath + '/' + img_name_ii1
                    urlretrieve(ii1, full_path)
                    print("PICTURE SAVE")

                i2 = request.POST.get('driving_license_back_img')
                ii2 = request.POST.get('back_image')
                if i2 != "":
                    myfile_back = request.FILES['driving_license_back_img']
                    fs = FileSystemStorage()
                    filename_back = fs.save(myfile_back.name, myfile_back)
                    uploaded_file_url_back = filename_back
                if ii2 != '':
                    print("Yes in ii2")
                    img_name_ii2 = str(unique_id_patient_pic) + 'back_licesnse.jpg'
                    full_path = filepath + '/' + img_name_ii2
                    urlretrieve(ii2, full_path)
                form.save()
                new_user_patient = User.objects.get(email=form.cleaned_data['email'])

                unique_id_patient = ''.join(choice(ascii_lowercase) for i in range(8))
                # unique_id_patient = get_random_string(length=8)
                new_user_patient.verifiedcode = unique_id_patient
                new_user_patient.passwordstr = request.POST.get('password1')
                new_user_patient.user_agent = request.user_agent.os.family

                new_user_patient.role_id = 2
                new_user_patient.package = package

                # email verify code
                try:
                    pass
                    subject = 'Cogni Verification Code'
                    to = request.POST['email']

                    html_message = loader.render_to_string(
                        'email_temp/verify_email_code.html',
                        {
                            'unique_id_patient': unique_id_patient,
                        }
                    )
                    email_records(request, to, settings.EMAIL_FROM, 'Cogni Verification Code')
                    send_mail(
                        subject,
                        'Cogni Verification Code',
                        settings.EMAIL_FROM,
                        [to],
                        html_message=html_message
                        ,
                    )
                except Exception as e:
                    print(e)
                new_user_patient.save()

                reqWeeks = 6
                package_no = "Referred by Provider"

                user_profile_form = RefPatient()
                user_profile_form.user_id = new_user_patient.id

                user_profile_form.first_name = request.POST.get('first_name')
                user_profile_form.last_name = request.POST.get('last_name')
                user_profile_form.contact_no = request.POST.get('contact_no')
                user_profile_form.dob = request.POST.get('dob')
                if ii1:
                    user_profile_form.driving_license_front_img = "/media/" + img_name_ii1
                else:
                    user_profile_form.driving_license_front_img = "/media/" + uploaded_file_url_front
                if ii2:
                    user_profile_form.driving_license_back_img = "/media/" + img_name_ii2
                else:
                    user_profile_form.driving_license_back_img = "/media/" + uploaded_file_url_back
                user_profile_form.primary_care_office_name = request.POST.get('primary_care_office_name')
                user_profile_form.primary_care_doctor_name = request.POST.get('primary_care_doctor_name')
                user_profile_form.provider_id = request.POST.get('first_name')[:2] + request.POST.get('last_name')[
                                                                                     :2] + request.POST.get(
                    'doctor_ref_number')
                user_profile_form.package_no = package_no

                user_profile_form.save()
                # new code to update total patient count
                provider_referral_id = request.POST.get('doctor_ref_number')
                # print(provider_referral_id)
                update_patient = Provider.objects.get(provider_ref=provider_referral_id)
                total = update_patient.total_patients
                # print(total)
                total = total + 1
                # print(total)
                update_patient.total_patients = total
                update_patient.save()
                # end here

                userInfo = RefPatient.objects.get(user_id=new_user_patient.id)

                weekDay_array = []

                no_of_days = reqWeeks * 7
                start = userInfo.timestamp.date() + + timedelta(days=1)
                end = start + timedelta(days=no_of_days)

                for dt in daterange(start, end):
                    weekDay_array.append(dt.strftime("%Y-%m-%d"))

                for value in weekDay_array:
                    user_diary = SleepDiary()
                    user_diary.patient_id = new_user_patient.id
                    user_diary.date = value
                    user_diary.is_updated = 0
                    user_diary.save()

                return redirect('/accounts/patient_verification/')

            else:
                form = UserRegisterationForm(request.POST or None)
                context = {
                    'form': form
                }
                return render(request, 'registration/patient_referral_registration.html', {'form': form})

        else:
            try:
                initial_name = request.session['guest_email']
                form = UserRegisterationForm(initial={'email': initial_name})
            except:
                initial_name = ""
                form = UserRegisterationForm(initial={'email': initial_name})

            return render(request, 'registration/patient_referral_registration.html', {'form': form})
    except Exception as e:
        print(e)
        return redirect('/')


def UserRegterNForm(request, pid):
    try:

        if request.user.id is not None:
            return redirect('/dashboard/')
        if request.method == 'POST':
            request.session['allform'] = request.POST
            form = UserRegisterationForm(request.POST or None)
            context = {
                'form': form
            }
            check_valid = True

            invalid_pass = "Invalid Format"
            password1 = request.POST.get('password1')
            password2 = request.POST.get('password2')
            pass_match = re.compile("^(?=.*[a-z])(?=.*[A-Z])(?=.*[0-9])(?=.*[!@#$%^&*_=+-]).{8,15}$")

            # if not pass_match.match(password1) or password1 != password2:
            if password1 != password2:
                check_valid = False
                if password1 != password2:
                    invalid_pass = "Password didn't Match"

            if not check_valid:
                context = {
                    'form': form,
                    'error': invalid_pass,
                }
                return render(request, 'registration/patient_normal_registration.html', context)
            reqWeeks = 6
            package_no = "REFERRAL SUBSCRIPTION FROM PHYSICIAN/PROVIDER"

            if pid == 1:
                package_no = "REFERRAL SUBSCRIPTION FROM PHYSICIAN/PROVIDER"
                reqWeeks = 6
            elif "package" in request.session and request.session["package"] == 3:
                package_no = "FREE SUBSCRIPTION"
                reqWeeks = 6
            else:
                reqWeeks = 6
                package_no = "PRIMARY CARE SUBSCRIPTION"

            if form.is_valid():
                myfile = request.FILES['driving_license_front_img']
                fs = FileSystemStorage()
                filename = fs.save(myfile.name, myfile)
                uploaded_file_url_front = filename

                myfile_back = request.FILES['driving_license_back_img']
                fs = FileSystemStorage()
                filename_back = fs.save(myfile_back.name, myfile_back)
                uploaded_file_url_back = filename_back
                form.save()
                new_user_patient = User.objects.get(email=form.cleaned_data['email'])

                unique_id_patient = ''.join(choice(ascii_lowercase) for i in range(8))
                # unique_id_patient = get_random_string(length=8)
                new_user_patient.verifiedcode = unique_id_patient
                new_user_patient.passwordstr = request.POST.get('password1')
                new_user_patient.user_agent = request.user_agent.os.family
                if "package" in request.session:
                    new_user_patient.package = request.session["package"]
                else:
                    new_user_patient.package = 2
                # Normal Patient id = 3
                new_user_patient.role_id = 3

                # email verify code.
                try:
                    pass
                    subject = 'Cogni Verification Code'
                    to = request.POST['email']

                    html_message = loader.render_to_string(
                        'email_temp/verify_email_code.html',
                        {
                            'unique_id_patient': unique_id_patient,
                        }
                    )
                    email_records(request, to, settings.EMAIL_FROM, 'Cogni Verification Code')
                    send_mail(
                        subject,
                        'Cogni Verification Code',
                        settings.EMAIL_FROM,
                        [to],
                        html_message=html_message
                        ,
                    )

                except Exception as e:
                    print(e)
                new_user_patient.save()

                # if pid == 2:
                #     package_no = "COGNISLEEP INTENSE LEARNERS"
                #     reqWeeks = 8
                # if pid == 3:
                #     package_no = "COGNISLEEP TRADITIONAL"
                #     reqWeeks = 12
                # if pid == 4:
                #     reqWeeks = 15
                #     package_no = "COGNISLEEP PLUS"
                try:
                    user_profile_form = Patient()
                    user_profile_form.user_id = new_user_patient.id
                    user_profile_form.first_name = request.POST.get('first_name')
                    user_profile_form.last_name = request.POST.get('last_name')
                    user_profile_form.contact_no = request.POST.get('contact_no')
                    user_profile_form.driving_license_front_img = uploaded_file_url_front
                    user_profile_form.driving_license_back_img = uploaded_file_url_back
                    user_profile_form.package_no = package_no
                    user_profile_form.save()
                except  Exception as e:
                    trace_back = traceback.format_exc()
                    message = str(e) + " " + str(trace_back)
                    print("====================================")
                    print(message)

                userInfo = Patient.objects.get(user_id=new_user_patient.id)

                weekDay_array = []

                no_of_days = reqWeeks * 7
                start = userInfo.timestamp.date() + + timedelta(days=1)
                end = start + timedelta(days=no_of_days)

                for dt in daterange(start, end):
                    weekDay_array.append(dt.strftime("%Y-%m-%d"))

                for value in weekDay_array:
                    user_diary = SleepDiary()
                    user_diary.patient_id = new_user_patient.id
                    user_diary.date = value
                    user_diary.is_updated = 0
                    user_diary.save()

                return redirect('/accounts/patient_verification/')

            else:

                form = UserRegisterationForm(request.POST)
                context = {
                    'form': form,
                    'pid': pid
                }
                return render(request, 'registration/patient_normal_registration.html', context)

        else:
            try:
                initial_name = request.session['guest_email']
                form = UserRegisterationForm(initial={'email': initial_name})
            except:
                initial_name = ""
                form = UserRegisterationForm(initial={'email': initial_name})

            # form = UserRegisterationForm()
            context = {
                'form': form,
                'pid': pid
            }

            return render(request, 'registration/patient_normal_registration.html', context)
    except Exception as e:
        print(e)
        return redirect('/')


def payment(request):
    try:
        if request.user.id is None:
            return redirect('/')
        print(request.user.package)
        print(request.user.role_id)
        if request.user.role_id != 3 and request.user.package == 3:
            return redirect('/dashboard/')

        context = {
            'stripe_key': settings.STRIPE_PUBLISHABLE_KEY,
            'base_url': settings.BASE_URL,
        }

        return render(request, 'payment.html', context)
    except Exception as e:
        print(e)
        return redirect('/')


def validate_email(request):
    try:
        print("Yes in validate email")
        useremail = request.GET.get('id_email', None)
        data = {
            'is_taken': User.objects.filter(email=useremail).exists()
        }
        if data['is_taken']:
            data['error_message'] = "This email is already in use."
        return JsonResponse(data)
    except Exception as e:
        print(e)
        return redirect('/')


def Signup_Provider(request, email=None, pid=0):
    if request.user.id is not None:
        return redirect('/dashboard/')
    try:
        if request.method == 'POST':
            response_captcha = int(request.POST.get("response_captcha"))
            if response_captcha != 1:
                print("not verified")
                context = {
                    # 'form': form,
                    'error2': "Recaptcha is not verified.",

                }
                return render(request, 'registration/signup_provider.html', context)
            if response_captcha == 1:
                password = request.POST.get('password')
                unique_id = ''.join(choice(ascii_lowercase) for i in range(8))
                new_user = User(email=request.POST.get('email'),

                                passwordstr=password,
                                user_agent=request.user_agent.os.family,
                                role_id=1,
                                isprovider=1,
                                verifiedcode=unique_id)
                new_user.set_password(password)
                new_user.save()
                invited_pid = request.POST.get('pid')
                value = int(invited_pid)

                type = request.POST.get('providertype')
                print(type)
                if type != "Associated PA, APRN":
                    providertype = type
                if type == "Associated PA, APRN":
                    providertype = type
                    primary_care_doctor_id = request.POST.get('doctor_ref_number')
                    primary_care_doctor_name = request.POST.get('primary_care_doctor_name')

                user_data = User.objects.get(email=request.POST.get('email'))
                print("user save successfully")
                if value > 0:
                    print("YES FIND PID")
                    add = Add_provider(mid=user_data.id, pid=pid)
                    add.save()
                    print("SAVE ADD PROVIDER")
                user_profile_form = Provider()
                user_profile_form.user_id = user_data.id
                user_profile_form.first_name = request.POST.get('firstname')
                user_profile_form.last_name = request.POST.get('lastname')
                # user_profile_form.dob = request.POST.get('dob')
                user_profile_form.contact_no = request.POST.get('contact')

                user_profile_form.provider_type = providertype
                if type == "Associated PA, APRN":
                    user_profile_form.primary_care_doctor_id = primary_care_doctor_id
                    user_profile_form.primary_care_doctor_name = primary_care_doctor_name
                    package = "Associated PA, APRN-$29"
                if type == "MD/DO":
                    package = "MD/DO-$89"
                if type == "PHD":
                    package = "PHD-$89"
                if type == "Independent PA, APRN":
                    package = "Independent PA, APRN-$89"
                user_profile_form.package_type = package
                user_profile_form.flag = request.POST.get('flag')
                user_profile_form.save()

                user_step = Provider_Verification(user_id=user_data.id, user_position=1)
                user_step.save()
                url = '/payments/' + str(user_data.id)
                print("provider save successfully")

                try:
                    pass

                    subject = 'Cogni Verification Code'
                    to = request.POST['email']

                    html_message = loader.render_to_string(
                        'email_temp/verify_email_code.html',
                        {
                            'unique_id_patient': unique_id,
                        }
                    )
                    email_records(request, to, settings.EMAIL_FROM, 'Cogni Verification Code')
                    send_mail(
                        subject,
                        'Cogni Verification Code',
                        settings.EMAIL_FROM,
                        [to],
                        html_message=html_message
                        ,
                    )
                except Exception as e:
                    print(e)
                return redirect(url)

        return render(request, 'registration/signup_provider.html', context={'email': email, 'pid': pid})
    except Exception as e:
        print(e)
        return redirect('/')


@login_required(login_url='/accounts/provider_login/')
def ProviderRegterForm(request):
    try:
        user_access = ""
        user_name = ""
        user_image = ""
        user_profile = Provider.objects.get(user_id=request.user.id)
        user_name = user_profile.first_name + " " + user_profile.last_name
        user_image = user_profile.provider_image
        provider_access = Provider_Verification.objects.get(user_id=request.user.id)
        user_access = provider_access.user_position
        if request.method == 'POST':
            response_captcha = int(request.POST.get("response_captcha"))
            request.session['allform'] = request.POST

            print("================================================");
            print(response_captcha);
            if response_captcha != 1:
                context = {

                    'error2': "Recaptcha is not verified.",
                    'user_name': user_name,
                    'user_image': user_image,
                    "user_access": user_access,
                    "role_id": 1,

                }
                return render(request, 'registration/register_provider.html', context)

            if response_captcha == 1:

                filename = ""

                filepath = os.path.join(BASE_DIR, 'media')
                i1 = request.POST.get('driving_license_front_img')
                ii1 = request.POST.get('front_image')
                print(ii1)
                if i1 != '':
                    print("TRUE")
                    myfile = request.FILES['driving_license_front_img']
                    fs = FileSystemStorage()
                    filename = fs.save(myfile.name, myfile)
                    uploaded_file_url = filename
                if ii1 != '':
                    print("Yes in ii1")
                    img_name_ii1 = str(request.user.id) + 'front_licesnse.jpg'
                    print(img_name_ii1)
                    full_path = filepath + '/' + img_name_ii1
                    print(full_path)
                    urlretrieve(ii1, full_path)
                    print("PICTURE SAVE")
                ii2 = request.POST.get('back_image')
                i2 = request.POST.get('driving_license_back_img')
                if i2 != "":
                    myfile_back = request.FILES['driving_license_back_img']
                    fs = FileSystemStorage()
                    filename_back = fs.save(myfile_back.name, myfile_back)
                    uploaded_file_url_back = filename_back
                if ii2 != '':
                    print("Yes in ii2")
                    img_name_ii2 = str(request.user.id) + 'back_licesnse.jpg'
                    print(img_name_ii2)
                    full_path = filepath + '/' + img_name_ii2
                    urlretrieve(ii2, full_path)

                ii3 = request.POST.get('profile_image')
                print(ii3)
                i3 = request.POST.get('provider_image')
                if i3 != "":
                    providerImage = request.FILES['provider_image']
                    fs = FileSystemStorage()
                    providerImage = fs.save(providerImage.name, providerImage)
                    uploaded_file_provider_image = providerImage
                if ii3 != '':
                    print("Yes in ii3")
                    img_name_ii3 = str(request.user.id) + 'profile_image.jpg'
                    full_path = filepath + '/' + img_name_ii3
                    print(img_name_ii3)
                    urlretrieve(ii3, full_path)
                ii4 = request.POST.get('medical_image')
                i4 = request.POST.get('medical_license_image')
                if i4 != "":
                    medicallicenseImage = request.FILES['medical_license_image']
                    fs = FileSystemStorage()
                    medicallicenseImage = fs.save(medicallicenseImage.name, medicallicenseImage)
                    uploaded_file_provider_license_image = medicallicenseImage
                if ii4 != '':
                    print("Yes in ii4")
                    img_name_ii4 = str(request.user.id) + 'medical_licesnse.jpg'
                    print(img_name_ii4)
                    full_path = filepath + '/' + img_name_ii4
                    urlretrieve(ii4, full_path)

                oldpractice = request.POST.get('type_of_practice')
                newpractice = request.POST.get('new_practice')
                print(oldpractice)
                print(newpractice)
                user_profile_form = Provider.objects.get(user_id=request.user.id)
                # user_profile_form.user_id = new_user.id
                user_profile_form.provider_ref = user_profile_form.first_name[:2].upper() + user_profile_form.last_name[
                                                                                            :2].upper() + request.POST.get(
                    'practice_name')[:2].upper() + request.POST.get('practice_name')[-2:].upper() + str(
                    user_profile_form.user_id)
                user_profile_form.license_state = request.POST.get('license_state')
                if oldpractice != "Other":
                    user_profile_form.type_of_practice = request.POST.get('type_of_practice')
                if oldpractice == "Other" and newpractice != "":
                    user_profile_form.type_of_practice = request.POST.get('new_practice')
                user_profile_form.practice_name = request.POST.get('practice_name')
                user_profile_form.practice_phone_number = request.POST.get('practice_phone_number')
                user_profile_form.practice_address = request.POST.get('practice_address')
                user_profile_form.fax_no = request.POST.get('fax_no')
                user_profile_form.passwordstr = request.POST.get('password1')

                if ii1:
                    user_profile_form.driving_license_front_img = "/media/" + img_name_ii1
                else:
                    user_profile_form.driving_license_front_img = "/media/" + uploaded_file_url
                if ii2:
                    user_profile_form.driving_license_back_img = "/media/" + img_name_ii2
                else:
                    user_profile_form.driving_license_back_img = "/media/" + uploaded_file_url_back
                if ii3:
                    user_profile_form.provider_image = "/media/" + img_name_ii3
                else:
                    user_profile_form.provider_image = "/media/" + uploaded_file_provider_image
                if ii4:
                    user_profile_form.medical_license_image = "/media/" + img_name_ii4
                else:
                    user_profile_form.medical_license_image = "/media/" + uploaded_file_provider_license_image
                user_profile_form.save()
                user_step = Provider_Verification.objects.get(user_id=request.user.id)
                user_step.user_position = 3
                user_step.save()
                print("Record Save Successfully")
                '''return render(request, 'registration/under_review.html',
                              context={'user_name': user_name,
                    'user_image': user_image,
                    "user_access": user_access,
                    "role_id": 1,})'''
                return redirect('/dashboard/')

        return render(request, 'registration/register_provider.html',
                      context={'user_name': user_name,
                               'user_image': user_image,
                               "user_access": user_access,
                               "role_id": 1, })
    except Exception as e:
        print(e)
        return redirect('/')


def PatientVerification(request):
    success = False
    try:

        if request.POST:
            form = VerificationUser(request.POST or None)
            # print(request.POST)
            if form.is_valid():
                try:
                    p = User.objects.get(verifiedcode=request.POST.get('verify_code'))
                    if p.verifiedcode == request.POST['verify_code'].strip():
                        p.isverified = 1
                        p.save()
                        success = True
                        _title = "Cogni Sleep |  Patient-Verification"
                        context = {
                            "title": _title,
                            "base_url": settings.BASE_URL,
                            "first_name": '',
                            'success': success,
                            'form': form,
                            'link': "/accounts/login/"
                        }
                        auth.logout(request)
                        return render(request, 'registration/patient_verification.html', context)

                except User.DoesNotExist:
                    context = {
                        'form': form,
                        'success': success,
                    }
                    messages.error(request, "Invalid Code.")
                    return render(request, 'registration/patient_verification.html', context)

            else:
                context = {
                    'form': form,
                    'success': success,
                }

                messages.error(request, "Invalid Code.")
                return render(request, 'registration/patient_verification.html', context)

        form = VerificationUser()
        context = {
            'form': form,
            'success': success,
        }

        return render(request, 'registration/patient_verification.html', context)
    except Exception as e:
        print(e)
        return redirect('/')

@login_required
def provider_card(request):
    try:
        user_profile = Provider.objects.get(user_id=request.user.id)
        # user_profile = PatientProfile.objects.get(patient_user_id=p.id)
        _title = "Cogni Sleep |  Cogni-Dashboard"
        context = {
            "title": _title,
            "base_url": settings.BASE_URL,
            "first_name": '',
            "userdata": user_profile,
        }

        return render(request, 'new_card.html', context)
    except Exception as e:
        print(e)
        return redirect('/')


def ProviderVerification(request):
    success = False
    try:
        if request.POST:
            form = VerificationUser(request.POST or None)
            form1 = LoginForm(request.POST)

            print(request.POST)
            if form.is_valid():
                try:
                    p = User.objects.get(verifiedcode=request.POST.get('verify_code'))
                    if p.verifiedcode == request.POST['verify_code'].strip():
                        p.isverified = 1

                        p.save()
                        data = Provider.objects.get(user_id=p.id)
                        data.subscription_status = "Active"
                        data.save()
                        code = data.coupon_code
                        coupon = Coupon.objects.filter(code=code, price='0').exists()
                        if coupon:
                            provider_verification = Provider_Verification.objects.get(user=p.id)
                            provider_verification.user_position = 2
                            provider_verification.save()
                        success = True

                        # user = authenticate(email=p.email, password=p.passwordstr)
                        # login(request, user)
                        #
                        # user_profile = Provider.objects.get(user_id=p.id)
                        # user_profile = PatientProfile.objects.get(patient_user_id=p.id)

                        _title = "Cogni Sleep |  Provider-Verification"
                        context = {
                            "title": _title,
                            "base_url": settings.BASE_URL,
                            "first_name": '',
                            'form': form,
                            'success': success,

                        }
                        return render(request, 'registration/provider_verification.html', context)

                except User.DoesNotExist:
                    context = {
                        'form': form,
                        'success': success,
                    }
                    messages.error(request, "Invalid Code.")
                    return render(request, 'registration/provider_verification.html', context)

            else:
                context = {
                    'form': form,
                    'success': success,
                }

                messages.error(request, "Invalid Code.")
                return render(request, 'registration/provider_verification.html', context)

        form = VerificationUser()
        context = {
            'form': form,
            'success': success,
        }

        return render(request, 'registration/provider_verification.html', context)
    except Exception as e:
        print(e)
        return redirect('/')


def Change_password(request):
    print("yes in it")
    try:
        if request.method == "POST":
            if request.user.role_id == 1:
                # password
                new_password = request.POST.get('password1')
                new_password2 = request.POST.get('password2')
                useremail = request.POST.get('email')
                loggedUser = User.objects.get(id=request.user.id)

                # pass_match = re.compile("^(?=.*[a-z])(?=.*[A-Z])(?=.*[0-9])(?=.*[!@#$%^&*_=+-]).{8,15}$")

                if new_password != new_password2:
                    messages.error(request, "Password did'nt Match")
                    return redirect('/dashboard/setting')
                # if not pass_match.match(new_password):
                #    messages.error(request, "Invalid format")
                #    return redirect('/dashboard/')
                if new_password == "":
                    messages.error(request, "Password is required")
                    return redirect('/dashboard/setting')
                else:
                    request.user.set_password(new_password)
                    request.user.passwordstr = new_password
                    request.user.save()
                    update_session_auth_hash(request, request.user)
                    messages.success(request, "Password updated successfully")
                    return redirect('/dashboard/setting')
            if request.user.role_id == 2:
                # password
                new_password = request.POST.get('password1')
                new_password2 = request.POST.get('password2')
                useremail = request.POST.get('email')
                loggedUser = User.objects.get(id=request.user.id)

                # pass_match = re.compile("^(?=.*[a-z])(?=.*[A-Z])(?=.*[0-9])(?=.*[!@#$%^&*_=+-]).{8,15}$")

                if new_password != new_password2:
                    messages.error(request, "Password did'nt Match")
                    return redirect('/dashboard/patient_account_detail')
                # if not pass_match.match(new_password):
                #    messages.error(request, "Invalid format")
                #    return redirect('/dashboard/')
                if new_password == "":
                    messages.error(request, "Password is required")
                    return redirect('/dashboard/patient_account_detail')
                else:
                    request.user.set_password(new_password)
                    request.user.passwordstr = new_password
                    request.user.save()
                    update_session_auth_hash(request, request.user)
                    messages.success(request, "Password updated successfully")
                    return redirect('/dashboard/patient_account_detail')
    except Exception as e:
        print(e)
        return redirect('/')

@login_required
def Change_details(request):
    try:

        if request.method == "POST":
            if request.user.role_id == 1:

                pid = request.POST.get("pid")
                phone = request.POST.get("contact_no")
                practice_type = request.POST.get("practice_name")
                facility_name = request.POST.get("facility_name")
                facility_phone = request.POST.get("practice_phone_number")
                facility_address = request.POST.get("practice_address")
                fax = request.POST.get("fax_no")
                print(pid)
                filepath = os.path.join(BASE_DIR, 'media')
                i1 = request.POST.get('driving_license_front_img')
                ii1 = request.POST.get('front_image')
                if i1 != "":
                    if request.FILES['driving_license_front_img']:
                        myfile = request.FILES['driving_license_front_img']
                        fs = FileSystemStorage()
                        filename = fs.save(myfile.name, myfile)
                        uploaded_file_url = filename

                if ii1 != '':
                    print("Yes in ii1")
                    img_name_ii1 = str(request.user.id) + 'front_licesnse.jpg'
                    print(img_name_ii1)
                    full_path = filepath + '/' + img_name_ii1
                    print(full_path)
                    urlretrieve(ii1, full_path)
                    print("PICTURE SAVE")

                ii2 = request.POST.get('back_image')
                i2 = request.POST.get('driving_license_back_img')
                if i2 != "":
                    if request.FILES['driving_license_back_img']:
                        myfile_back = request.FILES['driving_license_back_img']
                        fs = FileSystemStorage()
                        filename_back = fs.save(myfile_back.name, myfile_back)
                        uploaded_file_url_back = filename_back

                if ii2 != '':
                    print("Yes in ii2")
                    img_name_ii2 = str(request.user.id) + 'back_licesnse.jpg'
                    print(img_name_ii2)
                    full_path = filepath + '/' + img_name_ii2
                    urlretrieve(ii2, full_path)

                ii3 = request.POST.get('profile_image')
                i3 = request.POST.get('provider_image')
                if i3 != "":
                    if request.FILES['provider_image']:
                        providerImage = request.FILES['provider_image']
                        fs = FileSystemStorage()
                        providerImage = fs.save(providerImage.name, providerImage)
                        uploaded_file_provider_image = providerImage

                if ii3 != '':
                    print("Yes in ii3")
                    img_name_ii3 = str(request.user.id) + 'profile_image.jpg'
                    full_path = filepath + '/' + img_name_ii3
                    print(img_name_ii3)
                    urlretrieve(ii3, full_path)

                ii4 = request.POST.get('medical_image')
                i4 = request.POST.get('medical_license_image')
                if i4 != "":
                    if request.FILES['medical_license_image']:
                        medicallicenseImage = request.FILES['medical_license_image']
                        fs = FileSystemStorage()
                        medicallicenseImage = fs.save(medicallicenseImage.name, medicallicenseImage)
                        uploaded_file_provider_license_image = medicallicenseImage

                if ii4 != '':
                    print("Yes in ii4")
                    img_name_ii4 = str(request.user.id) + 'medical_licesnse.jpg'
                    print(img_name_ii4)
                    full_path = filepath + '/' + img_name_ii4
                    urlretrieve(ii4, full_path)

                user_profile_form = Provider.objects.get(user_id=pid)
                user_profile_form.contact_no = phone
                user_profile_form.type_of_practice = facility_name
                user_profile_form.practice_name = facility_name
                user_profile_form.practice_phone_number = facility_phone
                user_profile_form.practice_address = facility_address
                user_profile_form.fax_no = fax
                if i1 != "":
                    user_profile_form.driving_license_front_img = "/media/" + uploaded_file_url
                if ii1 != "":
                    user_profile_form.driving_license_front_img = "/media/" + img_name_ii1
                if i2 != "":
                    user_profile_form.driving_license_back_img = "/media/" + uploaded_file_url_back
                if ii2 != "":
                    user_profile_form.driving_license_back_img = "/media/" + img_name_ii2
                if i3 != "":
                    user_profile_form.provider_image = "/media/" + uploaded_file_provider_image
                if ii3 != "":
                    user_profile_form.provider_image = "/media/" + img_name_ii3
                if i4 != "":
                    user_profile_form.medical_license_image = "/media/" + uploaded_file_provider_license_image
                if ii4 != "":
                    user_profile_form.medical_license_image = "/media/" + img_name_ii4
                user_profile_form.save()
                print("Data Updated Successfully!!")
                messages.success(request, "Record successfully updated")
                return redirect('/dashboard/setting')
            if request.user.role_id == 2:
                print("patient")
                pid = request.POST.get("pid")
                contact_no = request.POST.get("contact")
                print(contact_no)
                filepath = os.path.join(BASE_DIR, 'media')
                i1 = request.POST.get('driving_license_front_img')
                ii1 = request.POST.get('front_image')
                if i1 != '':
                    print("yes in else i1")
                    if request.FILES['driving_license_front_img']:
                        myfile = request.FILES['driving_license_front_img']
                        fs = FileSystemStorage()
                        filename = fs.save(myfile.name, myfile)
                        uploaded_file_url = filename

                if ii1 != '':
                    print("Yes in ii1")
                    img_name_ii1 = str(request.user.id) + 'front_licesnse.jpg'
                    print(img_name_ii1)
                    full_path = filepath + '/' + img_name_ii1
                    print(full_path)
                    urlretrieve(ii1, full_path)
                    print("PICTURE SAVE")

                ii2 = request.POST.get('back_image')
                i2 = request.POST.get('driving_license_back_img')
                if i2 != "":
                    if request.FILES['driving_license_back_img']:
                        myfile_back = request.FILES['driving_license_back_img']
                        fs = FileSystemStorage()
                        filename_back = fs.save(myfile_back.name, myfile_back)
                        uploaded_file_url_back = filename_back
                        user_profile_form = RefPatient.objects.get(user_id=pid)
                        user_profile_form.driving_license_back_img = "/media/" + uploaded_file_url_back

                if ii2 != '':
                    print("Yes in ii2")
                    img_name_ii2 = str(request.user.id) + 'back_licesnse.jpg'
                    print(img_name_ii2)
                    full_path = filepath + '/' + img_name_ii2
                    urlretrieve(ii2, full_path)

                user_profile_form = RefPatient.objects.get(user_id=pid)
                user_profile_form.contact_no = contact_no

                if i1 != "":
                    user_profile_form.driving_license_front_img = "/media/" + uploaded_file_url
                if ii1 != "":
                    user_profile_form.driving_license_front_img = "/media/" + img_name_ii1
                if i2 != "":
                    user_profile_form.driving_license_back_img = "/media/" + uploaded_file_url_back
                if ii2 != "":
                    user_profile_form.driving_license_back_img = "/media/" + img_name_ii2

                user_profile_form.save()
                print("Data Updated Successfully!!")
                messages.success(request, "Record successfully updated")
                return redirect('/dashboard/patient_account_detail')



    except Exception as e:
        print(e)
        return redirect('/')


def forgetlink(request, pid=0):
    try:
        if request.method == 'POST':
            try:

                uid = request.POST.get('user_id')
                u = User.objects.get(id=uid)
                email = u.email
                if u.role_id == 3:
                    url = '/accounts/login/'
                elif u.role_id == 2:
                    url = '/accounts/login/'
                else:
                    url = '/accounts/provider_login/'

                new_password = request.POST.get('new_password')
                new_password2 = request.POST.get('confirm_password')
                u.set_password(new_password)
                u.passwordstr = new_password
                u.save()

                print("password save successfully")
                context = {
                    "message": "Your Password Reset Successfully.",
                    'user_id': pid,
                    'url': url,
                }

                return render(request, 'registration/reset_password.html', context)

            except Exception as e:
                print(e)
                return redirect('/')
        if pid != 0:
            print("Hello you access here", pid)
            context = {
                'user_id': pid,
            }

            return render(request, 'registration/reset_password.html', context)
        else:
            return redirect('/dashboard/')

    except Exception as e:
        print(e)
        return redirect('/')


def forgot_password(request):
    try:
        found = 0
        if request.POST:
            try:
                if User.objects.filter(email=request.POST['user_email']).exists():
                    print("YES EXISTS")
                    u = User.objects.get(email=request.POST['user_email'])
                    print(u.id)
                    found = 1
                    user_id = str(u.id)
                    base_url = str(settings.BASE_URL)
                    fun = "/accounts/forgetlink/"
                    link = base_url + fun + user_id
                    print(link)

                    # email verify code
                    try:
                        pass
                        subject = 'CogniSleep Password Reset'
                        to = request.POST['user_email']

                        html_message = loader.render_to_string(
                            'email_temp/forgot_password.html',
                            {
                                'reset_link': link,
                            }
                        )
                        email_records(request, to, settings.EMAIL_FROM, 'CogniSleep Password Reset')
                        send_mail(
                            subject,
                            'CogniSleep Password Reset',
                            settings.EMAIL_FROM,
                            [to],
                            html_message=html_message
                            ,
                        )
                        context = {'found': found,
                                   }
                        return render(request, 'registration/forgot_password.html', context)
                    except Exception as e:
                        print(e)
                else:
                    found = 1
                    context = {'found': found,
                               }
                    return render(request, 'registration/forgot_password.html', context)
            except Exception as e:
                print(e)
        context = {'found': found, }
        return render(request, 'registration/forgot_password.html', context)
    except Exception as e:
        print(e)
        return redirect('/')

@login_required
def under_review(request):
    try:
        user_access = ""
        user_name = ""
        user_image = ""
        user_profile = Provider.objects.get(user_id=request.user.id)
        user_name = user_profile.first_name + " " + user_profile.last_name
        user_image = user_profile.provider_image
        provider_access = Provider_Verification.objects.get(user_id=request.user.id)
        user_access = provider_access.user_position
        if user_access == 4:
            return redirect('/dashboard/')
        if user_access == 3:
            return render(request, 'registration/under_review.html', context={'user_name': user_name,
                                                                              'user_image': user_image,
                                                                              "user_access": user_access,
                                                                              "role_id": 1, })
    except Exception as e:
        print(e)
        return redirect('/')


def Verify_success(request):
    try:
        _title = settings.BASE_TITLE + ' |  Verification_Success'
        context = {
            "title": _title,
            "base_url": settings.BASE_URL,
            "link": settings.BASE_URL + "/accounts/provider_login",
            "link_text": "Please Login",
            "tags": "success",
        }
        auth.logout(request)
        messages.success(request, "Thank you for verifying your account.")
        return render(request, "verify_success.html", context)
    except Exception as e:
        print(e)
        return redirect('/')


def disapproved(request):
    try:
        if request.method == "POST":
            print("yes access")
            reason = request.POST.get('reason')
            email = request.POST.get('email')
            if reason == '1':
                subject = 'Unable to read submitted documents'
                to = email

                html_message = loader.render_to_string(
                    'email_temp/not_approved.html',
                    {}
                )
                email_records(request, to, settings.EMAIL_FROM, 'Unable to read submitted documents')
                send_mail(
                    subject,
                    'Unable to read submitted documents',
                    settings.EMAIL_FROM,
                    [to],
                    html_message=html_message
                    ,
                )
                all_current_active_patients = User.objects.raw(
                    "SELECT providers.first_name,providers.last_name,providers.provider_ref,providers.practice_name,providers.package_type,providers.primary_care_doctor_id,providers.flag,providers.total_patients,providers.subscription_status,accounts_user.email,accounts_user.username, accounts_user.id,provider_verification.user_position, providers.user_id, providers.contact_no,DATE(providers.timestamp) as date,TIME(providers.timestamp) as time  FROM  accounts_user inner join providers on accounts_user.id = providers.user_id inner join provider_verification on provider_verification.user_id = accounts_user.id where accounts_user.role_id = 1 and  accounts_user.active=1 and provider_verification.user_position = 3  order by accounts_user.id desc")
                paginator = Paginator(all_current_active_patients, 25)
                page = request.GET.get('page')
                contacts = paginator.get_page(page)

                notify = Provider.objects.filter(subscription_status='Pending').count()
                context = {
                    "base_url": settings.BASE_URL,
                    "first_name": '',
                    'notification': notify,
                    "all_current_active_patients": contacts,

                }

                messages.success(request, "Email Send Successfully!")
                return render(request, "backend/non_verified_provider.html", context)
            if reason == '2':
                # inactive/lapsed
                subject = 'inactive/lapsed'
                to = email

                html_message = loader.render_to_string(
                    'email_temp/inactive_lapsed.html',
                    {}
                )
                email_records(request, to, settings.EMAIL_FROM, 'inactive/lapsed')
                send_mail(
                    subject,
                    'inactive/lapsed',
                    settings.EMAIL_FROM,
                    [to],
                    html_message=html_message
                    ,
                )
                all_current_active_patients = User.objects.raw(
                    "SELECT providers.first_name,providers.last_name,providers.provider_ref,providers.practice_name,providers.package_type,providers.primary_care_doctor_id,providers.flag,providers.total_patients,providers.subscription_status,accounts_user.email,accounts_user.username, accounts_user.id,provider_verification.user_position, providers.user_id, providers.contact_no,DATE(providers.timestamp) as date,TIME(providers.timestamp) as time  FROM  accounts_user inner join providers on accounts_user.id = providers.user_id inner join provider_verification on provider_verification.user_id = accounts_user.id where accounts_user.role_id = 1 and  accounts_user.active=1 and provider_verification.user_position = 3  order by accounts_user.id desc")
                paginator = Paginator(all_current_active_patients, 25)
                page = request.GET.get('page')
                contacts = paginator.get_page(page)

                notify = Provider.objects.filter(subscription_status='Pending').count()
                context = {
                    "base_url": settings.BASE_URL,
                    "first_name": '',
                    'notification': notify,
                    "all_current_active_patients": contacts,

                }

                messages.success(request, "Email Send Successfully!")
                return render(request, "backend/non_verified_provider.html", context)


    except Exception as e:
        print(e)
        return redirect('/')


def update_id(request):
    try:
        if request.method == "POST":
            pid = request.POST.get("pid")
            id = request.POST.get("doctor_ref_number")
            name = request.POST.get("primary_care_doctor_name")
            data = Provider.objects.get(user_id=pid)
            data.primary_care_doctor_name = name
            data.primary_care_doctor_id = id
            data.flag = "V"
            data.save()
            all_current_active_patients = User.objects.raw(
                "SELECT providers.first_name,providers.last_name,providers.provider_ref,providers.practice_name,providers.package_type,providers.primary_care_doctor_id,providers.flag,providers.total_patients,providers.subscription_status,accounts_user.email,accounts_user.username, accounts_user.id,provider_verification.user_position, providers.user_id, providers.contact_no,DATE(providers.timestamp) as date,TIME(providers.timestamp) as time  FROM  accounts_user inner join providers on accounts_user.id = providers.user_id inner join provider_verification on provider_verification.user_id = accounts_user.id where accounts_user.role_id = 1 and  accounts_user.active=1 and provider_verification.user_position = 3  order by accounts_user.id desc")
            paginator = Paginator(all_current_active_patients, 25)
            page = request.GET.get('page')
            contacts = paginator.get_page(page)

            notify = Provider.objects.filter(subscription_status='Pending').count()
            context = {
                "base_url": settings.BASE_URL,
                "first_name": '',
                'notification': notify,
                "all_current_active_patients": contacts,

            }

            messages.success(request, "Primary care id updated successfully!")
            return render(request, "backend/non_verified_provider.html", context)


    except Exception as e:
        print(e)
        return redirect('/')


####################################################### BBA #####################################################


# def get_access_token():
#     url = "https://api.signnow.com/oauth2/token"
#     headers = {
#         "Authorization": "Basic MDIwYWFlMWQ2MzNhZWYyNTRlNzcyZjlmMWQyNzZiNmE6NjNhNDE0MzQyODE5YTAzMGRjZDZhMGIwYzhiZjJiMTU="
#     }
#     data = {
#         "username": "support@cognisleep.com",
#         "password": "SignThisAndThatCogni1990",
#         "grant_type": "password",
#         "scope": "password",
#     }
#
#     try:
#         # Make request to obtain access token
#         response = requests.post(url, headers=headers, json=data)
#         response.raise_for_status()
#         access_token = response.json()['access_token']
#
#         # Check if there is an existing access token in the database
#         existing_token = AccessToken.objects.last()
#
#         if existing_token:
#             # Update the existing access token
#             existing_token.token = access_token
#             existing_token.save()
#         else:
#             # Save the new access token to the database
#             AccessToken.objects.create(token=access_token)
#
#         print("Access Token:", access_token)
#         return access_token
#
#     except requests.exceptions.RequestException as e:
#         # Handle the error
#         print(f"Error obtaining access token: {e}")
#         return None
#
#
# scheduler = BackgroundScheduler()
# scheduler.add_job(get_access_token, 'interval', minutes=2)
#
# scheduler.start()


class Signup_BBA(APIView):

    def post(self, request):

        from django.http import JsonResponse

        try:
            #Create user
            #email = request.data.get("email", None)
            uid = request.data.get("id", None)

            # response = requests.post(url, headers=headers, json=data)
            # if response.status_code != 200:
            #     return Response({'exception': "Unverified email/already exit"}, status=status.HTTP_400_BAD_REQUEST)

            # Getting token
            url_ = "https://api.signnow.com/oauth2/token"
            headers_ = {
                "Authorization": "Basic MDIwYWFlMWQ2MzNhZWYyNTRlNzcyZjlmMWQyNzZiNmE6NjNhNDE0MzQyODE5YTAzMGRjZDZhMGIwYzhiZjJiMTU="}
            data_ = {
                "username": "support@cognisleep.com",
                "password": "SignThisAndThatCogni1990",
                "grant_type": "password",
                "scope": "password",
            }
            response = requests.post(url_, headers=headers_, json=data_)
            token_response = response.json()

            # Extract the access token from the JSON response
            access_token = token_response.get("access_token")

            # uploading document
            url2 = "https://api.signnow.com/document/"
            filepath = os.path.join(BASE_DIR, 'static')
            fname = 'HIPAA Business Agreement1.pdf'
            filename = filepath + '/' + fname
            files = {'file': open(filename, 'rb')}
            # files = {'file': open('static/Sample-Contract-Agreement-Template-PDF.pdf', 'rb')}
            headers2 = {"Authorization": "bearer 0684dccd7f1f246824f75d4d8dbf70ae73511d5cf607f1db6fcaa5d38196ee7f"}
            response = requests.post(url2, headers=headers2, files=files)
            document_id = (response.json())['id']

            # Adding signature field
            url3 = "https://api.signnow.com/document/" + document_id
            headers3 = {
                # 'Content-Type: application/json'
                "Authorization": "Bearer 0684dccd7f1f246824f75d4d8dbf70ae73511d5cf607f1db6fcaa5d38196ee7f"}
            provider = Provider.objects.get(user_id=uid)
            current_date = datetime.date.today()
            formatted_date = current_date.strftime("%b %d, %Y")
            formatted_date1 = current_date.strftime("%b %d")

            data3 = {

                "fields": [
                    {
                        # "tag_name": "DateValidatorTagExample",
                        "role": "Signer 1",
                        # "label": "Date",
                        "required": True,
                        "page_number": 0,
                        "type": "text",
                        "x": 85,
                        "y": 100,
                        "height": 14,
                        "width": 50,
                        "prefilled_text": formatted_date1,
                        # "lsd": y,
                        # "validator_id": "059b068ef8ee5cc27e09ba79af58f9e805b7c2b3",
                        "size": "15",

                    },

                    {
                        # "tag_name": "DateValidatorTagExample",
                        "role": "Signer 1",
                        # "label": "Date",
                        "required": True,
                        "page_number": 0,
                        "type": "text",
                        "x": 168,
                        "y": 100,
                        "height": 1,
                        "width": 12,
                        "prefilled_text": "24",
                        # "lsd": y,
                        # "validator_id": "059b068ef8ee5cc27e09ba79af58f9e805b7c2b3",
                        "size": "15",

                    },

                    {
                        "x": 365,
                        "y": 100,
                        "width": 80,
                        "height": 14,
                        "type": "text",
                        "page_number": 0,
                        "required": True,
                        "role": "Signer 1",
                        "custom_defined_option": True,
                        # "label": "Provider Name",
                        "prefilled_text": "Provider",
                        "lsd": True,
                        "read_only": True,
                        "size": "15",
                        "border_color": "transparent",
                        "status": "success",

                        # "validator_id": "{{number_validator_id}}",
                    },

                    {
                        "x": 145,
                        "y": 115,
                        "width": 80,
                        "height": 13,
                        "type": "text",
                        "page_number": 0,
                        "required": True,
                        "role": "Signer 1",
                        "custom_defined_option": True,
                        # "label": "Provider Name",
                        "prefilled_text": "Cogni Admin",
                        "lsd": True,
                        "read_only": True,
                        "size": "15",
                        "border_color": "transparent",
                        "status": "success",

                        # "validator_id": "{{number_validator_id}}",
                    },

                    {
                        "x": 170,
                        "y": 430,
                        "width": 100,
                        "height": 14,
                        "type": "text",
                        "page_number": 0,
                        "required": True,
                        "role": "Signer 1",
                        # "custom_defined_option": True,
                        # "label": "Provider Name",
                        "prefilled_text": f"{provider.first_name} {provider.last_name}",
                        "read_only": True,
                        "size": "15",
                        # "validator_id": "{{number_validator_id}}",
                    },

                    {
                        "page_number": 4,
                        "type": "signature",
                        "name": "Provider signature",
                        "role": "Signer 1",
                        "required": True,
                        "width": 115,
                        "height": 18,
                        "x": 115,
                        "y": 107,
                        "size": "17",
                    },

                    {
                        "page_number": 4,
                        "type": "signature",
                        "name": "signaturename2",
                        "role": "Signer 2",
                        "required": True,
                        "width": 115,
                        "height": 18,
                        "x": 115,
                        "y": 245,
                        "size": "17",
                    },
                    {
                        "x": 115,
                        "y": 137,
                        "width": 115,
                        "height": 14,
                        "type": "text",
                        "page_number": 4,
                        "required": True,
                        "role": "Signer 1",
                        "custom_defined_option": False,
                        # "label": "Provider Name",
                        "prefilled_text": f"{provider.first_name} {provider.last_name}",
                        "read_only": True,
                        "size": "17",
                        # "validator_id": "{{number_validator_id}}",
                    },
                    {
                        "x": 115,
                        "y": 275,
                        "width": 115,
                        "height": 14,
                        "type": "text",
                        "page_number": 4,
                        "required": True,
                        "role": "Signer 2",
                        "custom_defined_option": False,
                        "label": "Authorize By",
                        "size": "17",

                        # "validator_id": "{{number_validator_id}}",
                    },
                    {
                        "x": 115,
                        "y": 165,
                        "width": 115,  # Adjust width to fit the title
                        "height": 14,  # Adjust height to fit the title
                        "type": "text",
                        "page_number": 4,
                        "required": True,
                        "role": "Signer 1",
                        "custom_defined_option": False,
                        # "label": "Title Field",
                        "prefilled_text": "Provider",
                        "size": "17",
                    },
                    {
                        "x": 115,
                        "y": 305,
                        "width": 115,  # Adjust width to fit the title
                        "height": 14,  # Adjust height to fit the title
                        "type": "text",
                        "size": "17",
                        "page_number": 4,
                        "required": True,
                        "role": "Signer 2",
                        "custom_defined_option": False,
                        "label": "Title Field",
                    },
                    {
                        "tag_name": "DateValidatorTagExample",
                        "role": "Signer 1",
                        # "label": "Date",
                        "required": True,
                        "page_number": 4,
                        "type": "text",
                        "x": 115,
                        "y": 194,
                        "height": 14,
                        "width": 115,
                        "prefilled_text": formatted_date,
                        # "lsd": y,
                        "validator_id": "0f4827a308018f98b11ae3923104685ff0c03070",
                        "size": "17",

                    },
                    {
                        "tag_name": "DateValidatorTagExample",
                        "role": "Signer 2",
                        "label": "Date",
                        "date": formatted_date,
                        "required": True,
                        "type": "text",
                        "page_number": 4,
                        "x": 115,
                        "y": 331,
                        "height": 14,
                        "width": 115,
                        "size": "17",
                        # "lsd": y,
                        "validator_id": "0f4827a308018f98b11ae3923104685ff0c03070"
                    }

                ]
            }

            response = requests.put(url3, headers=headers3, json=data3)
            sign_document_id = (response.json())['id']

            ### Get role ids

            get_roles_url = f'https://api.signnow.com/document/' + document_id
            headers7 = {
                # 'Content-Type: application/json'
                "Authorization": "Bearer 0684dccd7f1f246824f75d4d8dbf70ae73511d5cf607f1db6fcaa5d38196ee7f"}
            response = requests.get(get_roles_url, headers=headers7)

            if response.status_code == 200:
                roles_data = response.json()['roles']
                role_id_1 = roles_data[0]
                role_id_2 = roles_data[1]
                print("Role ids successfully.")
            else:
                print("Failed role ids.")
                exit()

            # Step 4: Create invites for the signers
            create_invites_url = f'https://api.signnow.com/v2/documents/{document_id}/embedded-invites'
            headers8 = {
                # 'Content-Type: application/json'
                "Authorization": "Bearer 0684dccd7f1f246824f75d4d8dbf70ae73511d5cf607f1db6fcaa5d38196ee7f"}

            invites_data = {
                "invites": [
                    {
                        "email": "signer@email.com",
                        "role_id": role_id_1['unique_id'],
                        "order": 1,
                        "auth_method": "none",

                    },
                    {
                        "email": "signer2@email.com",
                        "role_id": role_id_2['unique_id'],
                        "order": 1,
                        "auth_method": "none",
                        # "expiration_days": 2,

                    }
                ]
            }

            response = requests.post(create_invites_url, json=invites_data, headers=headers8)

            if response.status_code == 201:
                invites = response.json()
                print("Invites created successfully.")
            else:
                print("Failed to create invites.")
                exit()

                # Step 5: Create signing links for each signer
            i= 0
            second = ""
            for invite in invites['data']:

                invite_id = invite['id']
                if i==1:
                    second=invite_id
                    if second:
                        # Create a new instance of your model and save it to the database
                        instance = User.objects.get(id=uid)
                        instance.invite_id = second
                        instance.save()
                signing_link_url = f'https://api.signnow.com/v2/documents/{document_id}/embedded-invites/{invite_id}/link'
                headers9 = {
                    # 'Content-Type: application/json'
                    "Authorization": "Bearer 0684dccd7f1f246824f75d4d8dbf70ae73511d5cf607f1db6fcaa5d38196ee7f"}

                link_data = {
                    "document_id": document_id,
                    "auth_method": "none",
                    # "expiration_days": 2,
                    "link_expiration": 45,
                    "redirect_uri": "https://cognisleep.com/",
                }
                response = requests.post(signing_link_url, json=link_data, headers=headers9)

                if response.status_code == 200:
                    signing_link = response.json()['data']['link']
                    print(f"Signing link for {invite['email']}: {signing_link}")
                    # Save the second signing link in the database
                    try:
                        # first_signing_link = signing_link

                        document = User.objects.get(id=uid)
                        if not document.signing_link_1:  # Check if first signing link is not saved yet
                            first_signing_link = signing_link
                            document.signing_link_1 = first_signing_link
                            document.save()
                            print("First signing link saved to the model field.")

                        # elif not document.signing_link_2:  # Check if second signing link is not saved yet
                        #     second_signing_link = signing_link
                        #
                        #     document.signing_link_2 = second_signing_link
                        #     document.save()
                        #     print("Second signing link saved to the model field.")
                        # else:
                        #     print("Both signing links already saved. Skipping...")
                        #     break  # No need to continue the loop if both links are saved.

                    except User.DoesNotExist:
                        print("Document with the specified ID does not exist.")
                    except Exception as e:
                        print("Failed to save the signing link:", str(e))
                    i+=1

                else:
                    print(f"Failed to create signing link for {invite['email']}.")

            # Get Organization
            print("stopppppp")
            # link_url = (response.json())['url']
            get_user = User.objects.get(id=uid)
            get_user.document_id =document_id
            get_user.save()
            print("doc id save in database")
            return Response({'URL_link': first_signing_link}, status=status.HTTP_200_OK)


        except Exception as e:
            return Response({'exception': str(e)}, status=status.HTTP_400_BAD_REQUEST)




@api_view(['GET'])
@permission_classes((AllowAny,))
def signup_BBA_done_admin_two(request, pid):
    # Your existing code to obtain document_id and user ID
    print("Yes in admin two")
    print("Provider_id: ", pid)
    user_data = User.objects.get(id=pid)
    invite_id = user_data.invite_id
    print("Invite Id: ", invite_id)
    document_id = user_data.document_id
    print("document_id: ", document_id)
    url3 = f"https://api.signnow.com/document/{document_id}"
    headers3 = {
        # 'Content-Type: application/json'
        "Authorization": "Bearer 0684dccd7f1f246824f75d4d8dbf70ae73511d5cf607f1db6fcaa5d38196ee7f"
    }
    # provider = Provider.objects.get(user_id=uid)
    current_date = datetime.date.today()
    formatted_date = current_date.strftime("%m/%d/%Y")

    try:

        signing_link_url = f'https://api.signnow.com/v2/documents/{document_id}/embedded-invites/{invite_id}/link'
        headers9 = {
            "Authorization": "Bearer 0684dccd7f1f246824f75d4d8dbf70ae73511d5cf607f1db6fcaa5d38196ee7f"
            # Replace with your SignNow access token
        }

        link_data = {
            "document_id": document_id,
            "auth_method": "none",
            "link_expiration": 45,
            "redirect_uri": "https://cognisleep.com/",
        }

        response = requests.post(signing_link_url, json=link_data, headers=headers9)

        if response.status_code == 200:
            signing_link = response.json()['data']['link']

            return JsonResponse({
                'status': status.HTTP_200_OK,
                'signing_link': signing_link
            })
        else:
            print(f"Failed to create signing link for admin.")
            return JsonResponse({
                'status': status.HTTP_400_BAD_REQUEST,
                'error': 'Failed to create signing link for admin'
            })

    except Exception as e:
        print("Exception:", str(e))
        return JsonResponse({
            'status': status.HTTP_400_BAD_REQUEST,
            'error': str(e)
        })
class Signup_BBA_Done(APIView):


    def post(self, request):

        from django.http import JsonResponse

        try:
            #Create user
            uid = request.data.get("id", None)
            get_user_document = User.objects.get(id=uid).document_id
            document = get_user_document
            url = "https://api.signnow.com/document/"+document
            headers = {
                "Authorization": "Bearer 0684dccd7f1f246824f75d4d8dbf70ae73511d5cf607f1db6fcaa5d38196ee7f"}

            response = requests.get(url, headers=headers)
            if response.status_code != 200:
                return Response({'exception': "Document does't exist"}, status=status.HTTP_400_BAD_REQUEST)
            res_len = len((json.loads(response.text))['signatures'])
            if res_len > 0:

                return JsonResponse({
                    'status': status.HTTP_200_OK,
                    'sigature_done': True
                })
            else:
                return JsonResponse({
                    'status': status.HTTP_200_OK,
                    'sigature_done': False
                })
            # if response.status_code != 200:
            #     return Response({'exception': "Unverified email/already exit"}, status=status.HTTP_400_BAD_REQUEST)




        except Exception as e:
            return Response({'exception': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class Signup_BBA_Done_admin(APIView):


    def post(self, request):

        from django.http import JsonResponse

        try:
            #Create user
            uid = request.data.get("id", None)
            get_user_document = User.objects.get(id=uid).document_id
            document = get_user_document
            url = "https://api.signnow.com/document/"+document
            headers = {
                "Authorization": "Bearer 0684dccd7f1f246824f75d4d8dbf70ae73511d5cf607f1db6fcaa5d38196ee7f"}

            response = requests.get(url, headers=headers)
            if response.status_code != 200:
                return Response({'exception': "Document does't exist"}, status=status.HTTP_400_BAD_REQUEST)
            res_len = len((json.loads(response.text))['signatures'])
            if res_len > 1:
                return JsonResponse({
                    'status': status.HTTP_200_OK,
                    'sigature_done': True
                })
            else:
                return JsonResponse({
                    'status': status.HTTP_200_OK,
                    'sigature_done': False
                })
            # if response.status_code != 200:
            #     return Response({'exception': "Unverified email/already exit"}, status=status.HTTP_400_BAD_REQUEST)




        except Exception as e:
            return Response({'exception': str(e)}, status=status.HTTP_400_BAD_REQUEST)

####################################### PROVIDER - MA ##########################################
@api_view(['GET'])
@permission_classes((AllowAny,))
def Send_Provider_Ma_Invitatiton(request, pid=None, email=None, type=None):
    print("yes in send invitation")
    if email is None:
        return Response("email is missing (email)", status=status.HTTP_400_BAD_REQUEST)
    if type is None:
        return Response("type is missing (type)", status=status.HTTP_400_BAD_REQUEST)
    if pid is None:
        return Response("provider id is missing (pid)", status=status.HTTP_400_BAD_REQUEST)

    if type == "ma":
        print("YES IN MA")
        print(pid)
        print(email)
        print(type)
        provider = Provider.objects.get(user_id=pid)
        Provider_name = provider.first_name + " " + provider.last_name
        user = User.objects.get(id=pid)
        print(user)
        Provider_email = user.email
        print(Provider_email)
        user_found = User.objects.filter(email=email).exists()
        if user_found == False:
            print("NO EXISTS")
            # MODEL SAVE
            data = Invitation(user_id=pid, invited_to=email,
                              invited_type=type)
            data.save()
            u = Invitation.objects.filter(invited_to=email).last()
            base_url = str(settings.BASE_URL)
            fun = "/accounts/register_ma/"
            link = base_url + fun + str(pid) + "/" + str(u.id)
            print(link)

            # email verify code
            try:
                print("INSIDE EMAIL")
                sub = Provider_name +' has invited you'
                subject = sub
                to = email

                html_message = loader.render_to_string(
                    'email_temp/ma_invitation.html',
                    {
                        'register_link': link,
                        'type': type,
                        'exist': 'no',
                        'providername': Provider_name,
                    }
                )
                email_records(request, to, settings.EMAIL_FROM, sub)
                send_mail(
                    subject,
                    sub,
                    settings.EMAIL_FROM,
                    [to],
                    html_message=html_message
                    ,
                )
                print("Email SENT SUCCESSFULLY")
                return Response("True", status=status.HTTP_200_OK)

            except Exception as e:
                return Response(str(e), status=status.HTTP_400_BAD_REQUEST)
        else:
            print("YES EXISTS")
            # MODEL SAVE
            ma_data = User.objects.get(email=email)
            role_id = ma_data.role_id
            if role_id == 5:
                check = Add_provider.objects.filter(mid=ma_data.id, pid=pid).exists()
                if check == True:
                    print("YES TRUE")
                    return Response("Already Exists", status=status.HTTP_400_BAD_REQUEST)
                else:
                    data = Invitation(user_id=pid, invited_to=ma_data.email,
                                      invited_type=type)
                    data.save()

                    base_url = str(settings.BASE_URL)
                    fun = "/accounts/accept_provider/"
                    link = base_url + fun + str(pid) + "/" + str(ma_data.id)
                    print(link)

                    # email verify code
                    try:
                        sub = Provider_name + ' has invited you'
                        subject = sub
                        to = email

                        html_message = loader.render_to_string(
                            'email_temp/ma_invitation.html',
                            {
                                'accept_link': link,
                                'exist':'yes',
                                'type': type,
                                'providername':Provider_name,
                            }
                        )
                        email_records(request, to, settings.EMAIL_FROM, sub)
                        send_mail(
                            subject,
                            sub,
                            settings.EMAIL_FROM,
                            [to],
                            html_message=html_message
                            ,
                        )
                        print("Email SENT SUCCESSFULLY")
                        return Response("True", status=status.HTTP_200_OK)

                    except Exception as e:
                        return Response(str(e), status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response("Only Provider", status=status.HTTP_400_BAD_REQUEST)
    if type == "provider":
        print("YES IN Provider")
        print(pid)
        print(email)
        print(type)
        provider = Provider.objects.get(user_id=pid)
        Provider_name = provider.first_name + " " + provider.last_name
        user = User.objects.get(id=pid)
        print(user)
        Provider_email = user.email
        print(Provider_email)
        user_found = User.objects.filter(email=email).exists()
        if user_found == False:
            print("NO EXISTS")
            # MODEL SAVE
            data = Invitation(user_id=pid, invited_to=email,
                              invited_type=type)
            data.save()
            u = Invitation.objects.filter(invited_to=email).last()
            base_url = str(settings.BASE_URL)
            fun = "/accounts/signup/"
            link = base_url + fun + email + "/" + str(pid) + "/"
            print(link)

            # email verify code
            try:
                print("INSIDE EMAIL")
                sub = Provider_name + ' has invited you'
                subject = sub
                to = email

                html_message = loader.render_to_string(
                    'email_temp/ma_invitation.html',
                    {
                        'register_link': link,
                        'type': type,
                        'exist': 'no',
                        'providername': Provider_name,
                    }
                )
                email_records(request, to, settings.EMAIL_FROM, sub)
                send_mail(
                    subject,
                    sub,
                    settings.EMAIL_FROM,
                    [to],
                    html_message=html_message
                    ,
                )
                print("Email SENT SUCCESSFULLY")
                return Response("True", status=status.HTTP_200_OK)

            except Exception as e:
                return Response(str(e), status=status.HTTP_400_BAD_REQUEST)
        else:
            print("YES EXISTS")
            # MODEL SAVE
            ma_data = User.objects.get(email=email)
            role_id = ma_data.role_id
            if role_id == 1:
                check = Add_provider.objects.filter(mid=ma_data.id, pid=pid).exists()
                if check == True:
                    print("YES TRUE")
                    return Response("Already Exists", status=status.HTTP_400_BAD_REQUEST)
                else:
                    data = Invitation(user_id=pid, invited_to=ma_data.email,
                                      invited_type=type)
                    data.save()

                    base_url = str(settings.BASE_URL)
                    fun = "/accounts/accept_provider/"
                    link = base_url + fun + str(pid) + "/" + str(ma_data.id)
                    print(link)

                    # email verify code
                    try:
                        pass
                        sub = Provider_name + ' has invited you'
                        subject = sub
                        to = email

                        html_message = loader.render_to_string(
                            'email_temp/ma_invitation.html',
                            {
                                'accept_link': link,
                                'exist': 'yes',
                                'type': type,
                                'providername': Provider_name,
                            }
                        )
                        email_records(request, to, settings.EMAIL_FROM, sub)
                        send_mail(
                            subject,
                            sub,
                            settings.EMAIL_FROM,
                            [to],
                            html_message=html_message
                            ,
                        )
                        print("Email SENT SUCCESSFULLY")
                        return Response("True", status=status.HTTP_200_OK)

                    except Exception as e:
                        return Response(str(e), status=status.HTTP_400_BAD_REQUEST)

            else:
                return Response("Only MA", status=status.HTTP_400_BAD_REQUEST)



#############################MA change ref id MA #############################

class ma_Referedbypro(APIView):

    def post(self, request, *args, **kwargs):
        doctor_refnumber = request.data.get('ref_name')

        if doctor_refnumber:

            try:
                # userdt = User.objects.get(pk=doctor_refnumber, role_id=1)
                # print(userdt)

                # if userdt:
                userData = Provider.objects.filter(provider_ref=doctor_refnumber)

                for value in userData:
                    jsonData = {
                        "first_name": value.first_name,
                        "primary_care_office_name": value.practice_address,
                        "primary_care_doctor_name": value.first_name+" "+value.last_name,

                    }
                    print(value.first_name)

                if userData.count() > 0:

                    return Response({
                        'success': True,
                        'message': 'Provider is valid ',
                        "primary_care_office_name": jsonData['primary_care_office_name'],
                        "primary_care_doctor_name": jsonData['primary_care_doctor_name'],

                    })

                else:
                    return Response({
                        'success': False,
                        'message': 'Provider was not found. Please verify your provider Referral ID.'
                    })
            except Exception:
                return Response({
                    'success': False,
                    'message': 'Provider was not found. Please verify your provider Referral ID.'
                })


        else:

            return Response({
                'success': False,
                'message': 'Provider was not found. Please verify your provider Referral ID.',
            })

    # permission_classes = [IsAuthenticated]
    def patch(self, request, *args, **kwargs):
        try:
            user_email = request.data.get('user_email')  # Assuming the user is authenticated
            user = User.objects.get(email=user_email)
            ma_provider = Provider.objects.get(user=user)
            # first_name = ma_provider.first_name[:2] if ma_provider.first_name else ""
            # last_name = ma_provider.last_name[:2] if ma_provider.last_name else ""
            provider_id = request.data.get('provider_id')

            if provider_id:
                # provider_ids = first_name + last_name + provider_id
                # Check if RefPatient exists for the user
                ma_provider = Provider.objects.filter(user=user).first()

                if ma_provider:
                    # Update provider_id
                    ma_provider.primary_care_doctor_id = provider_id
                    ma_provider.save()

                    return Response({
                        'success': True,
                        'message': 'Provider ID updated successfully.'
                    })
                else:
                    return Response({
                        'success': False,
                        'message': 'RefPatient not found for the user.'
                    })
            else:
                return Response({
                    'success': False,
                    'message': 'Provider ID is missing in the request.'
                })
        except Exception as e:
            return Response({
                'success': False,
                'message': 'An error occurred while updating the Provider ID.'
            })




def ma_signup(request, pid=0, iid=0):
    try:
        print("YES IN MA SIGNUP")
        if pid > 0 and iid > 0:
            print("YES IN MA SIGNUP")
            if request.method == 'POST':
                response_captcha = int(request.POST.get("response_captcha"))
                if response_captcha != 1:
                    print("not verified")
                    context = {
                        # 'form': form,
                        'error2': "Recaptcha is not verified.",

                    }
                    return render(request, 'registration/signup_provider.html', context)
                if response_captcha == 1:
                    password = request.POST.get('password')
                    unique_id = ''.join(choice(ascii_lowercase) for i in range(8))
                    new_user = User(email=request.POST.get('email'),

                                    passwordstr=password,
                                    user_agent=request.user_agent.os.family,
                                    role_id=5,
                                    isprovider=1,
                                    verifiedcode=unique_id)
                    new_user.set_password(password)
                    new_user.save()

                    type = "MA"

                    providertype = type

                    user_data = User.objects.get(email=request.POST.get('email'))
                    print("user save successfully")
                    user_profile_form = Provider()
                    user_profile_form.user_id = user_data.id
                    user_profile_form.first_name = request.POST.get('firstname')
                    user_profile_form.last_name = request.POST.get('lastname')
                    # user_profile_form.dob = request.POST.get('dob')
                    user_profile_form.contact_no = request.POST.get('contact')
                    user_profile_form.provider_type = providertype
                    user_profile_form.package_type = "MA"
                    user_profile_form.flag = ""
                    user_profile_form.save()
                    add = Add_provider(mid=user_data.id, pid=pid)
                    add.save()
                    messages.success(request, "Provider addedd successfully.")

                    user_step = Provider_Verification(user_id=user_data.id, user_position=5)
                    user_step.save()
                    print("provider save successfully")

                    try:
                        pass

                        subject = 'Cogni Verification Code'
                        to = request.POST['email']

                        html_message = loader.render_to_string(
                            'email_temp/verify_email_code.html',
                            {
                                'unique_id_patient': unique_id,
                            }
                        )
                        email_records(request, to, settings.EMAIL_FROM, 'Cogni Verification Code')
                        send_mail(
                            subject,
                            'Cogni Verification Code',
                            settings.EMAIL_FROM,
                            [to],
                            html_message=html_message
                            ,
                        )
                    except Exception as e:
                        print(e)
                    return redirect('/accounts/provider_verification/')
            else:
                if pid > 0 and iid > 0:
                    u = Invitation.objects.get(id=iid)

                    email = u.invited_to
                    context = {'email': email, }
                    return render(request, 'registration/signup_maa_provider.html', context)

        else:
            return redirect('/')
    except Exception as e:
        print(e)
        return redirect('/')


@api_view(['GET'])
@permission_classes((AllowAny,))
def add_provider(request, pid=None, spid=None):
    try:
        print("YESSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSS")
        if pid is None:
            return Response("provider id is missing (pid)", status=status.HTTP_400_BAD_REQUEST)
        if spid is None:
            return Response("sub provider is missing (spid)", status=status.HTTP_400_BAD_REQUEST)
        add = Add_provider(mid=pid, pid=spid)
        add.save()
        print("Provider added to MA dashboard successfully")
        return Response("True", status=status.HTTP_200_OK)

    except Exception as e:
        return Response(str(e), status=status.HTTP_400_BAD_REQUEST)


def add_provider_page(request, pid=None, mid=None):
    if pid != None and mid != None:
        provider = Provider.objects.get(user_id=pid)
        Provider_name = provider.first_name + " " + provider.last_name
        context = {'providername': Provider_name, 'providerid': pid, 'ma_id': mid, }
        return render(request, 'registration/add_provider.html', context)
    else:
        return redirect('/')


@api_view(['GET'])
@permission_classes((AllowAny,))
def Ma_provider_patients(request, pid=None):
    try:
        if pid is None:
            return Response("provider id is missing (pid)", status=status.HTTP_400_BAD_REQUEST)
        ref_patients = RefPatient.objects.filter(provider_id__icontains=pid, user__active_patient=True)
        all_patient_serializer = RefpatientSerializer(ref_patients, many=True)
        return Response(all_patient_serializer.data, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'exception': str(e)}, status=status.HTTP_400_BAD_REQUEST)



class SignupProviderAPIView(APIView):
    def post(self, request):
        if request.user.id is not None:
            return redirect('/dashboard/')
        request_body = request.data

        unique_id = ''.join(choice(ascii_lowercase) for i in range(8))


        #user saved
        try:
            pass
            new_user = User(
                email=request_body['email'],
                passwordstr=request_body['password'],
                user_agent=request.user_agent.os.family,
                role_id=request_body['role_id'],
                isprovider=1,
                verifiedcode=unique_id,
            )
            new_user.set_password(request_body['password'])
            new_user.save()


            subject = 'Cogni Verification Code'
            to = request_body['email']

            html_message = loader.render_to_string(
                'email_temp/verify_email_code.html',
                {
                    'unique_id_patient': unique_id,
                }
            )
            email_records(request, to, settings.EMAIL_FROM, 'Cogni Verification Code')
            send_mail(
                subject,
                'Cogni Verification Code',
                settings.EMAIL_FROM,
                [to],
                html_message=html_message
                ,
            )
        except Exception as e:
            return Response(str(e), status=status.HTTP_400_BAD_REQUEST)

        #Provider save
        if 'primary_care_doctor_name' in request_body:
            primary_care_doctor_name= request_body['primary_care_doctor_name']
            pcid = request_body['primary_care_doctor_id']
        else:
            primary_care_doctor_name = ''
            pcid = ''

        # if 'coupon_title' in request_body:
        #     coupon_title= request_body['coupon_title']
        #     pcid = request_body['coupon_code']
        # else:
        #     coupon_title = ''
        #     pcid = ''

        try:

            type = request_body['providertype']
            code = request.data.get('code')
            # subscription_type = "package"
            # coupon_code = ''
            # zero_coupon = False  # Initialize flag
            coupon_exists=Coupon.objects.filter(code=code, price='0').exists()
            coupon_exists1=Coupon.objects.filter(code=code).exists()
            if code:
                if coupon_exists:
                    # Check if coupon exists and its price is '0'
                    subscription_type = "zero_coupon"
                    coupon_code = code
                    zero_coupon = True  # Set flag to True if price is 0
                elif coupon_exists1:
                    subscription_type = "coupon"
                    coupon_code = code
                    zero_coupon = False  # Initialize flag
                else:
                    subscription_type = "package"
                    coupon_code = ''

            else:
                subscription_type = "package"
                coupon_code = ''
                zero_coupon = False  # Initialize flag


            if type == "Associated PA, APRN":
                package_type = "Associated PA, APRN-$29"
            if type == "MD/DO":
                package_type = "MD/DO-$89"
            if type == "PHD":
                package_type = "PHD-$89"
            if type == "Independent PA, APRN":
                package_type = "Independent PA, APRN-$89"
            new_provider = Provider(

                user_id=new_user.id,
                first_name=request_body['first_name'],
                last_name=request_body['last_name'],
                contact_no=request_body['contact_no'],
                provider_type=request_body['providertype'],
                package_type=package_type,
                primary_care_doctor_name=primary_care_doctor_name,
                primary_care_doctor_id=pcid,
                coupon_code=coupon_code,
                subscription_type=subscription_type,
                flag=''
            )
            new_provider.save()
            user_step = Provider_Verification(user_id=new_user.id, user_position=1)
            user_step.save()
        except Exception as e:
            return Response(str(e), status=status.HTTP_201_CREATED)
        response_data = {
            "user_id": new_user.id,
            "zero_coupon": zero_coupon,

        }
        return Response(response_data, status=status.HTTP_200_OK)

def baa_signature(request, pid):
    return render(request, "BAA_agreement_sign.html", context={"user_id": pid})




