from datetime import timedelta
from datetime import timedelta
import datetime

import stripe
from django.contrib import messages
from django.contrib.auth import authenticate
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.conf import settings
from django.template import loader
from rest_framework import status
from stripe.api_resources import subscription
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from cogni.views import email_records
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404, redirect
from rest_framework.views import exception_handler
from rest_framework.response import Response
# Create your views here.
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view

from accounts.admin import User
from accounts.forms import LoginForm
from accounts.models import RefPatient, Patient, Provider, Provider_Verification
from cogni.views import get_user_progress_bar_avg
from .models import Subscriptionpackage
from dashboard.models import SleepDiary, VideoSessions, Logfile
from django.http.response import JsonResponse, HttpResponse, HttpResponseRedirect
from payments.models import Product_detail, Coupon_Product_detail, Coupon
from django.core.serializers import serialize
from django.contrib.auth.decorators import login_required


def Dashboard(request):
    try:
        _title = "CogniSleep |  Admin"

        if (request.session.get('role_id') != 4):
            return redirect("/")

        refPatients = User.objects.filter(role_id=2, isverified=1).count()
        # patients = Patient.objects.filter(user__active_patient=1).count()
        providers = User.objects.filter(role_id=1, isverified=1).count()
        # refPatients = RefPatient.objects.filter(user__role_id=2).count()
        # print("Hello")
        # patients = Patient.objects.filter(user__active_patient=1).count()
        # providers = Provider_Verification.objects.count()#Provider.objects.filter(user__role_id=1).count()
        userOS = User.objects.filter(user_agent="Windows").count()
        userOS1 = User.objects.filter(user_agent="Android").count()
        userOS2 = User.objects.filter(user_agent="Mac OS X").count()
        userOS3 = User.objects.filter(user_agent="IOS").count()
        refpkg = User.objects.filter(package=1).count()
        pkg = User.objects.filter(package=2).count()
        notify = Provider.objects.filter(subscription_status='Pending').count()
        n_notify = Provider_Verification.objects.filter(user_position=3).count()
        context = {
            'n_notify': n_notify,
            'notification': notify,
            "title": _title,
            "REFERRAL_SUBSCRIPTION_FROM_PHYSICIAN_PROVIDER_COUNTER": refpkg,
            "COGNISLEEP_INTENSE_LEARNERS_COUNTER": pkg,
            "user_agent_window": userOS,
            "user_agent_mac_IOS": userOS2,
            "user_agent_android": userOS1,
            "user_agent_IOS": userOS3,
            "providers": providers,
            # "patients": patients,
            "refPatients": refPatients,
            'base_url': settings.BASE_URL,

            "active_tab": "dashboard"
        }

        return render(request, "backend/dashboard.html", context)
    except Exception as e:
        return redirect('/backend/dashboard/')


def adminLogin(request):
    try:
        _title = "CogniSleep |  Admin"
        if request.method == 'POST':
            form = LoginForm(request.POST)
            if form.is_valid():
                email = request.POST['email']
                print(email)
                password = request.POST['password']
                print(password)
                validUser = authenticate(email=email, password=password)
                if (validUser == None or validUser.role_id != 4):
                    print(" I am in if condition")
                    messages.error(request, "Incorrect Email or Password.")
                else:
                    print("I am in else conditin")
                    request.session["admin_id"] = validUser.id
                    request.session["role_id"] = validUser.role_id
                    print("return redirect")
                    return redirect('/backend/dashboard/')

        form = LoginForm()

        notify = Provider.objects.filter(subscription_status='Pending').count()
        n_notify = Provider_Verification.objects.filter(user_position=3).count()
        context = {
            'n_notify': n_notify,
            'notification': notify,
            "title": _title,
            'form': form,
            'base_url': settings.BASE_URL,
            "active_tab": "dashboard"
        }

        return render(request, "backend/login.html", context)
    except Exception as e:
        return redirect('/')


def Cpatients(request):
    try:
        _title = "CogniSleep |  Admin"
        notify = Provider.objects.filter(subscription_status='Pending').count()
        n_notify = Provider_Verification.objects.filter(user_position=3).count()
        context = {
            'n_notify': n_notify,
            "title": _title,
            'notification': notify,
            'base_url': settings.BASE_URL,
            "active_tab": "cpatient"
        }
        return render(request, "backend/Cpatients.html", context)
    except Exception as e:
        return redirect('/')


def Providers(request):
    try:
        _title = "CogniSleep | Verified Provider"
        if ("admin_id" not in request.session):
            return redirect('/backend/')

        if request.method == 'POST':

            if request.POST['mysearch'] != '':
                all_current_active_patients = User.objects.raw(
                    "SELECT providers.first_name,providers.last_name,providers.provider_ref,providers.practice_name,providers.subscription_status,accounts_user.email,accounts_user.username, accounts_user.id, providers.user_id, providers.contact_no,DATE(providers.timestamp) as date,TIME(providers.timestamp) as time  FROM  accounts_user inner join providers on accounts_user.id = providers.user_id inner join provider_verification on accounts_user.id = provider_verification.user_id where accounts_user.admin = 0 and accounts_user.role_id=1 and accounts_user.active=1 and providers.subscription_status is not null and provider_verification.user_position = 4 and CONCAT(first_name, last_name, email, provider_ref, subscription_status) like %s",
                    ['%' + request.POST['mysearch'] + '%'])
                print("YES ELIF")
                paginator = Paginator(all_current_active_patients, 25)
                page = request.GET.get('page')
                contacts = paginator.get_page(page)
                print(contacts)
                notify = Provider.objects.filter(subscription_status='Pending').count()
                n_notify = Provider_Verification.objects.filter(user_position=3).count()
                context = {
                    'n_notify': n_notify,
                    "title": _title,
                    "base_url": settings.BASE_URL,
                    "first_name": '',
                    'notification': notify,
                    "all_current_active_patients": contacts,
                    "mysearch": request.POST['mysearch'],

                }

                return render(request, "backend/provider_change.html", context)

        # all_current_active_patients = User.objects.raw(
        #     "SELECT providers.first_name,providers.last_name,providers.provider_ref,providers.practice_name,providers.total_patients,providers.subscription_status,accounts_user.email,accounts_user.username, accounts_user.id,provider_verification.user_position, providers.user_id, providers.contact_no,DATE(providers.timestamp) as date,TIME(providers.timestamp) as time  FROM  accounts_user inner join providers on accounts_user.id = providers.user_id inner join provider_verification on accounts_user.id = provider_verification.user_id where accounts_user.role_id = 1 and  accounts_user.active=1  and providers.subscription_status is not null and provider_verification.user_position = 4 order by accounts_user.id desc")
        all_current_active_patients = User.objects.raw(
            "SELECT providers.first_name, providers.last_name, providers.provider_ref, providers.practice_name, providers.total_patients, providers.subscription_status,providers.subscription_type, accounts_user.email, accounts_user.username, accounts_user.id, provider_verification.user_position, providers.user_id, providers.contact_no, DATE(providers.timestamp) as date, TIME(providers.timestamp) as time FROM accounts_user INNER JOIN providers ON accounts_user.id = providers.user_id INNER JOIN provider_verification ON accounts_user.id = provider_verification.user_id WHERE accounts_user.role_id = 1 AND accounts_user.active = 1 AND providers.subscription_status IS NOT NULL AND provider_verification.user_position = 4 ORDER BY CASE WHEN providers.subscription_status = 'pending' THEN 1 WHEN providers.subscription_status = 'active' THEN 2 ELSE 3 END, accounts_user.id DESC"
        )

        paginator = Paginator(all_current_active_patients, 25)
        page = request.GET.get('page')
        contacts = paginator.get_page(page)
        notify = Provider.objects.filter(subscription_status='Pending').count()
        n_notify = Provider_Verification.objects.filter(user_position=3).count()


        context = {
            'n_notify': n_notify,
            "title": _title,
            "base_url": settings.BASE_URL,
            "first_name": '',
            'notification': notify,
            "all_current_active_patients": contacts,


        }

        return render(request, "backend/provider_change.html", context)
    except Exception as e:
        return redirect('/backend/dashboard/')


@login_required
def dashboardofprovider(request, pid):
    try:
        user_profile = Provider.objects.get(user_id=pid)
        userInfo = user_profile
        reqWeeks = 6

        _title = "CogniSleep |  Cogni-Dashboard"
        user_ref_data_array = []
        # loggedUser = User.objects.get(id=pid)

        loggedUser = User.objects.get(id=pid)

        if user_profile:
            try:
                # request.user.
                user_ref_data_array = RefPatient.objects.filter(provider_id__icontains=pid)
                print("Provider ref: ", user_ref_data_array)
            except User.DoesNotExist:
                print("User does not exist")
        notify = Provider.objects.filter(subscription_status='Pending').count()
        n_notify = Provider_Verification.objects.filter(user_position=3).count()
        context = {
            'n_notify': n_notify,
            "title": _title,
            "base_url": settings.BASE_URL,
            "first_name": '',
            "week": reqWeeks,
            'notification': notify,
            "userdata": user_profile,
            "loggedUser": loggedUser,
            "user_ref_data_array": user_ref_data_array,

        }
        return render(request, "backend/dashboard_provider_2.html", context)
    except Exception as e:
        return redirect('/backend/dashboard/')


def Patients(request):
    try:
        _title = "CogniSleep |  Patient"
        if ("admin_id" not in request.session):
            return redirect('/backend/')

        if request.method == 'POST':
            if request.POST['date_from'] != '' and request.POST['date_to'] != '' and request.POST['mysearch'] != '':
                all_current_active_patients = User.objects.raw(
                    "SELECT patients.first_name,patients.last_name,accounts_user.email,accounts_user.username, accounts_user.id, patients.user_id, patients.contact_no,DATE(patients.timestamp) as date,TIME(patients.timestamp) as time  FROM  accounts_user inner join patients on accounts_user.id = patients.user_id where DATE(patients.timestamp) BETWEEN %s and %s and accounts_user.admin = 0 and accounts_user.role_id=3 and accounts_user.active=1  and CONCAT(first_name, last_name, email, contact_no) like %s",
                    [request.POST['date_from'], request.POST['date_to'], '%' + request.POST['mysearch'] + '%'])

                notify = Provider.objects.filter(subscription_status='Pending').count()
                paginator = Paginator(all_current_active_patients, 25)
                page = request.GET.get('page')
                contacts = paginator.get_page(page)
                n_notify = Provider_Verification.objects.filter(user_position=3).count()
                context = {
                    'n_notify': n_notify,
                    "title": _title,
                    "base_url": settings.BASE_URL,
                    "first_name": '',
                    'notification': notify,
                    "all_current_active_patients": contacts,
                    "date_from": request.POST['date_from'],
                    "date_to": request.POST['date_to'],
                    "mysearch": request.POST['mysearch'],

                }

                return render(request, "backend/patients.html", context)

            elif request.POST['date_from'] == '' and request.POST['date_to'] == '' and request.POST['mysearch'] != '':

                all_current_active_patients = User.objects.raw(
                    "SELECT patients.first_name,patients.last_name,accounts_user.email,accounts_user.username, accounts_user.id, patients.user_id, patients.contact_no,DATE(patients.timestamp) as date,TIME(patients.timestamp) as time  FROM  accounts_user inner join patients on accounts_user.id = patients.user_id where accounts_user.admin = 0 and accounts_user.role_id=3 and accounts_user.active=1  and CONCAT(first_name, last_name, email, contact_no) like %s",
                    ['%' + request.POST['mysearch'] + '%'])

                paginator = Paginator(all_current_active_patients, 25)
                page = request.GET.get('page')
                contacts = paginator.get_page(page)
                print(contacts)
                notify = Provider.objects.filter(subscription_status='Pending').count()
                n_notify = Provider_Verification.objects.filter(user_position=3).count()
                context = {
                    'n_notify': n_notify,
                    "title": _title,
                    "base_url": settings.BASE_URL,
                    "first_name": '',
                    "all_current_active_patients": contacts,
                    'notification': notify,
                    "date_from": request.POST['date_from'],
                    "date_to": request.POST['date_to'],
                    "mysearch": request.POST['mysearch'],

                }

                return render(request, "backend/patients.html", context)

            elif request.POST['date_from'] != '' and request.POST['date_to'] != '' and request.POST['mysearch'] == '':

                all_current_active_patients = User.objects.raw(
                    "SELECT patients.first_name,patients.last_name,accounts_user.email,accounts_user.username, accounts_user.id, patients.user_id, patients.contact_no,DATE(patients.timestamp) as date,TIME(patients.timestamp) as time  FROM  accounts_user inner join patients on accounts_user.id = patients.user_id where DATE(patients.timestamp) BETWEEN %s and %s and accounts_user.admin = 0 and accounts_user.role_id=3 and accounts_user.active=1 ",
                    [request.POST['date_from'], request.POST['date_to']])
                paginator = Paginator(all_current_active_patients, 25)
                page = request.GET.get('page')
                contacts = paginator.get_page(page)
                notify = Provider.objects.filter(subscription_status='Pending').count()
                n_notify = Provider_Verification.objects.filter(user_position=3).count()
                context = {
                    'n_notify': n_notify,
                    "title": _title,
                    "base_url": settings.BASE_URL,
                    "first_name": '',
                    'notification': notify,
                    "all_current_active_patients": contacts,
                    "date_from": request.POST['date_from'],
                    "date_to": request.POST['date_to'],
                    "mysearch": request.POST['mysearch'],

                }

                return render(request, "backend/patients.html", context)

        all_current_active_patients = User.objects.raw(
            "SELECT patients.first_name,patients.last_name,accounts_user.email,accounts_user.username, accounts_user.id, patients.user_id, patients.contact_no,DATE(patients.timestamp) as date,TIME(patients.timestamp) as time  FROM  accounts_user inner join patients on accounts_user.id = patients.user_id where accounts_user.role_id = 3 and  accounts_user.active=1   order by accounts_user.id desc")
        paginator = Paginator(all_current_active_patients, 25)
        page = request.GET.get('page')
        notify = Provider.objects.filter(subscription_status='Pending').count()
        contacts = paginator.get_page(page)
        n_notify = Provider_Verification.objects.filter(user_position=3).count()
        context = {
            'n_notify': n_notify,
            "title": _title,
            "base_url": settings.BASE_URL,
            "first_name": '',
            'notification': notify,
            "all_current_active_patients": contacts,

        }

        return render(request, "backend/patients.html", context)
    except Exception as e:
        return redirect('/backend/dashboard/')


def refPatient(request):
    try:
        _title = "CogniSleep |  Patient"
        if ("admin_id" not in request.session):
            return redirect('/backend/')

        if request.method == 'POST':
            if request.POST['mysearch'] != '':
                print("YES REFPATIENT")
                all_current_active_patients = User.objects.raw(
                    "SELECT ref_patients.first_name,ref_patients.last_name,accounts_user.email,accounts_user.username, accounts_user.id, ref_patients.user_id, ref_patients.contact_no,DATE(ref_patients.timestamp) as date,TIME(ref_patients.timestamp) as time  FROM  accounts_user inner join ref_patients on accounts_user.id = ref_patients.user_id where accounts_user.admin = 0 and accounts_user.role_id=2 and accounts_user.active=1  and CONCAT(first_name, last_name, email, contact_no) like %s",
                    ['%' + request.POST['mysearch'] + '%'])

                paginator = Paginator(all_current_active_patients, 25)
                page = request.GET.get('page')
                contacts = paginator.get_page(page)
                notify = Provider.objects.filter(subscription_status='Pending').count()
                n_notify = Provider_Verification.objects.filter(user_position=3).count()
                context = {
                    'n_notify': n_notify,
                    "title": _title,
                    "base_url": settings.BASE_URL,
                    "first_name": '',
                    'notification': notify,
                    "all_current_active_patients": contacts,
                    # "date_from": request.POST['date_from'],
                    # "date_to": request.POST['date_to'],
                    "mysearch": request.POST['mysearch'],

                }

                return render(request, "backend/refpatients.html", context)

        all_current_active_patients = User.objects.raw(
            "SELECT ref_patients.first_name,ref_patients.last_name,accounts_user.email,accounts_user.username, accounts_user.id, ref_patients.user_id, ref_patients.provider_id, ref_patients.contact_no,DATE(ref_patients.timestamp) as date,TIME(ref_patients.timestamp) as time  FROM  accounts_user inner join ref_patients on accounts_user.id = ref_patients.user_id where accounts_user.role_id = 2 and  accounts_user.active=1   order by accounts_user.id desc")
        paginator = Paginator(all_current_active_patients, 25)
        page = request.GET.get('page')
        contacts = paginator.get_page(page)
        notify = Provider.objects.filter(subscription_status='Pending').count()
        n_notify = Provider_Verification.objects.filter(user_position=3).count()
        context = {
            'n_notify': n_notify,
            "title": _title,
            "base_url": settings.BASE_URL,
            "first_name": '',
            'notification': notify,
            "all_current_active_patients": contacts,

        }

        return render(request, "backend/refpatients.html", context)
    except Exception as e:
        print(e)
        return redirect('/backend/dashboard/')


def provider_detail(request, pid):
    try:
        _title = "CogniSleep | Active_provider_details"
        if ("admin_id" not in request.session):
            return redirect('/backend/')

        user_details = User.objects.raw(
            "SELECT providers.first_name,providers.last_name,accounts_user.email,accounts_user.username, accounts_user.id, providers.user_id, providers.contact_no, accounts_user.package,providers.type_of_practice,providers.practice_name,providers.practice_phone_number,providers.practice_address,providers.fax_no FROM  accounts_user inner join providers on accounts_user.id = providers.user_id where accounts_user.id = %s and accounts_user.active=1  ",
            [pid])
        ref_patent = RefPatient.objects.filter(provider_id__icontains=pid)
        notify = Provider.objects.filter(subscription_status='Pending').count()
        n_notify = Provider_Verification.objects.filter(user_position=3).count()
        context = {
            'n_notify': n_notify,
            "title": _title,
            "base_url": settings.BASE_URL,
            "first_name": '',
            'notification': notify,
            "user_details": user_details[0],
            "ref_patent": ref_patent,
            "serial_data": [1, 2, 4, 8, 16, 32, 64, 128, 256, 512]

        }

        return render(request, "backend/active_provider_details.html", context)
    except Exception as e:
        return redirect('/backend/dashboard/')


def refpatient_detail(request, pid):
    try:
        _title = "CogniSleep | Referral Patient"
        if ("admin_id" not in request.session):
            return redirect('/backend/')
        try:
            user_details = User.objects.raw(
                "SELECT ref_patients.user_id as current_user_id,ref_patients.first_name,ref_patients.last_name,accounts_user.email,accounts_user.username, accounts_user.id, ref_patients.user_id, ref_patients.contact_no,DATE(ref_patients.timestamp) as date,TIME(ref_patients.timestamp) as time  FROM  accounts_user inner join ref_patients on accounts_user.id = ref_patients.user_id where accounts_user.admin = 0 and accounts_user.role_id=2 and accounts_user.active=1  and accounts_user.id = %s and ref_patients.user_id = %s  ",
                [str(pid), str(pid)])
        except Exception as ex:
            messages.error(request, "You don't have access")
            return redirect('/backend/refpatients/')

        if request.method == 'POST':
            if (request.data.get('password') == request.data.get('confirm_password')):
                u = User.objects.get(id=pid)
                u.set_password(request.data.get('password'))
                u.passwordstr = request.data.get('password')
                u.save()
            else:
                messages.error(request, "Password is not matched")

        userInfo = RefPatient.objects.get(user_id=pid)
        # user sleep dairy
        start = userInfo.timestamp.date() + timedelta(days=1)
        end = start + timedelta(days=7 - 1)
        end__ = userInfo.timestamp.date() + timedelta(days=7)

        start_date = datetime.date(start.year, start.month, start.day)
        end_date = datetime.date(end.year, end.month, end.day)
        invoice_for_today1 = SleepDiary.objects.raw(
            "SELECT * FROM dashboard_sleepdiary where patient_id=%s and date BETWEEN %s and %s",
            [str(pid), start_date, end_date])
        reqWeeks = 6
        bedtime_array = []
        week_day = 0
        weekVideo = 1
        week_counter = 0
        weekDays_array = []

        for x in range(1, reqWeeks + 1):

            if int(x) == week_day + 1:
                week_array = {
                    "x": x,
                    # "week_date": week,
                    "is_selected": 1
                }
                weekDays_array.append(week_array)
            else:
                week_array = {
                    "x": x,
                    # "week_date": week,
                    "is_selected": 0
                }
                weekDays_array.append(week_array)
        labels = ['Day 1', "Day 2", "Day 3", "Day 4", "Day 5", "Day 6", "Day 7"]
        invoice_for_today = SleepDiary.objects.raw(
            "SELECT * FROM dashboard_sleepdiary where patient_id=%s and time_went_to_bed!='' and time_fell_asleep!='' and time_got_up!='' ",
            [str(pid)])
        for value in invoice_for_today:
            total_percent_sleep = get_user_progress_bar_avg(value.time_went_to_bed, value.time_fell_asleep,
                                                            value.time_got_up,
                                                            value.no_of_times_awakend, value.date)
            bedtime_array.append(total_percent_sleep)

        for value in bedtime_array:

            if week_counter == 6:
                weekVideo += 1
                week_days_array = [value]
            else:
                week_counter += 1

        video_array = VideoSessions.objects.all()
        default_items = [2, 4, 3, 2.5, 2.5, 1.5, 5.5]
        notify = Provider.objects.filter(subscription_status='Pending').count()
        n_notify = Provider_Verification.objects.filter(user_position=3).count()
        context = {
            'n_notify': n_notify,
            "title": _title,
            "base_url": settings.BASE_URL,

            "user_sleep_diarys": invoice_for_today1,
            "weekDays_array": weekDays_array,
            "first_name": '',
            'notification': notify,
            "user_details": user_details[0],
            "videos": video_array,
            "labels": labels,
            "weekVideo": weekVideo,
            "default": default_items,
            # "ref_patent": ref_patent,
            "serial_data": [1, 2, 4, 8, 16, 32, 64, 128, 256, 512]

        }

        return render(request, "backend/active_refpatient_details.html", context)
    except Exception as e:
        return redirect('/backend/dashboard/')


def patient_detail(request, pid):
    try:
        _title = "CogniSleep | Referral Patient"
        if ("admin_id" not in request.session):
            return redirect('/backend/')
        # if request.session["login_admin"] == None:
        if 'login_admin' not in request.session:
            messages.error(request, "You don't have access")
            return redirect('/backend/patients/')

        if request.method == 'POST':
            if (request.data.get('password') == request.data.get('confirm_password')):
                u = User.objects.get(id=pid)
                u.set_password(request.data.get('password'))
                u.passwordstr = request.data.get('password')
                u.save()
            else:
                messages.error(request, "Password is not matched")
        user_details = User.objects.raw(
            "SELECT patients.first_name,patients.user_id as current_user_id,patients.timestamp,patients.last_name,accounts_user.email,patients.package_no,accounts_user.username, accounts_user.id, patients.user_id, patients.contact_no,DATE(patients.timestamp) as date,TIME(patients.timestamp) as time  FROM  accounts_user inner join patients on accounts_user.id = patients.user_id where accounts_user.admin = 0 and accounts_user.role_id=3 and accounts_user.active=1  and accounts_user.id = %s   ",
            [pid])

        userInfo = Patient.objects.get(user_id=pid)
        # user sleep dairy
        start = userInfo.timestamp.date() + timedelta(days=1)
        end = start + timedelta(days=7 - 1)
        end__ = userInfo.timestamp.date() + timedelta(days=7)

        start_date = datetime.date(start.year, start.month, start.day)
        end_date = datetime.date(end.year, end.month, end.day)
        invoice_for_today1 = SleepDiary.objects.raw(
            "SELECT * FROM dashboard_sleepdiary where patient_id=%s and date BETWEEN %s and %s",
            [str(pid), start_date, end_date])
        bedtime_array = []
        reqWeeks = 6
        week_day = 0
        weekVideo = 1
        week_counter = 0
        weekDays_array = []
        for x in range(1, reqWeeks + 1):

            if int(x) == week_day + 1:
                week_array = {
                    "x": x,
                    # "week_date": week,
                    "is_selected": 1
                }
                weekDays_array.append(week_array)
            else:
                week_array = {
                    "x": x,
                    # "week_date": week,
                    "is_selected": 0
                }
                weekDays_array.append(week_array)
            # print("Logged User: ", request.user.id)
        labels = ['Day 1', "Day 2", "Day 3", "Day 4", "Day 5", "Day 6", "Day 7"]
        invoice_for_today = SleepDiary.objects.raw(
            "SELECT * FROM dashboard_sleepdiary where patient_id=%s and time_went_to_bed!='' and time_fell_asleep!='' and time_got_up!='' ",
            [str(pid)])
        for value in invoice_for_today:
            total_percent_sleep = get_user_progress_bar_avg(value.time_went_to_bed, value.time_fell_asleep,
                                                            value.time_got_up,
                                                            value.no_of_times_awakend, value.date)
            bedtime_array.append(total_percent_sleep)
        for value in bedtime_array:

            if week_counter == 6:
                weekVideo += 1
                week_days_array = []
            else:
                week_counter += 1
        video_array = VideoSessions.objects.all()
        default_items = [2, 4, 3, 2.5, 2.5, 1.5, 5.5]
        notify = Provider.objects.filter(subscription_status='Pending').count()
        n_notify = Provider_Verification.objects.filter(user_position=3).count()
        context = {
            'n_notify': n_notify,
            "title": _title,
            "base_url": settings.BASE_URL,
            "first_name": '',
            "user_sleep_diarys": invoice_for_today1,
            "weekDays_array": weekDays_array,
            "user_details": user_details[0],
            "videos": video_array,
            "labels": labels,
            'notification': notify,
            "weekVideo": weekVideo,
            "default": default_items,
            # "ref_patent": ref_patent,
            "serial_data": [1, 2, 4, 8, 16, 32, 64, 128, 256, 512]

        }

        return render(request, "backend/active_patient_details.html", context)
    except Exception as e:
        return redirect('/backend/dashboard/')


@csrf_exempt
@api_view(["POST"])
def provider_verification(request):
    try:
        userId = request.data.get('user_id')
        email = request.data.get('email')
        pass_1 = request.data.get('pass')
        user = authenticate(email=email, password=pass_1)
        if user and user.role_id == 4:
            request.session["login_admin"] = user.id
            data = {
                "status": 1,
                "url": settings.BASE_URL + "/backend/provider_detail/" + userId + "/",
            }

            return JsonResponse(data)
        else:
            data = {
                "status": 0,
            }
            return JsonResponse(data)
    except Exception as e:
        return redirect('/backend/dashboard/')


@csrf_exempt
@api_view(["POST"])
def admin_verification(request):
    try:
        userId = request.data.get('user_id')
        email = request.data.get('email')
        pass_1 = request.data.get('pass')
        user = authenticate(email=email, password=pass_1)
        if user and user.role_id == 4:
            request.session["login_admin"] = user.id
            data = {
                "status": 1,
                "url": settings.BASE_URL + "/backend/patient-admin/view-diary/0/" + userId + "/",
            }

            return JsonResponse(data)
        else:
            data = {
                "status": 0,
            }
            return JsonResponse(data)

    except Exception as e:
        return redirect('/backend/dashboard/')


@csrf_exempt
@api_view(["POST"])
def provider_ref_verification(request):
    try:

        userId = request.data.get('user_id')
        provider_id = request.data.get('provider_id')
        email = request.data.get('email')
        pass_1 = request.data.get('pass')
        user = authenticate(email=email, password=pass_1)

        if user and int(user.id) == int(provider_id):
            request.session["login_provider"] = provider_id
            data = {
                "status": 1,
                "url": settings.BASE_URL + "/backend/refpatient_detail/" + userId + "/",
            }

            return JsonResponse(data)
        else:
            data = {
                "status": 0,
            }
            return JsonResponse(data)
    except Exception as e:
        return redirect('/backend/dashboard/')


def progress_byprovider(request, pid):
    try:
        print("YES INSIDE PROGRESS PROVIDER")
        _title = "CogniSleep |  Cogni-Dashboard"
        # print(request.user.role_id)
        loggedUser = User.objects.get(id=pid)
        # if request.user.role_id == 3:
        #    user_profile = Patient.objects.get(user_id=pid)
        # elif request.user.role_id == 2:
        #    user_profile = RefPatient.objects.get(user_id=pid)
        # elif request.user.role_id == 1:
        user_profile = RefPatient.objects.get(user_id=pid)

        # print("Logged User: ", request.user.id)
        labels = ['Day 1', "Day 2", "Day 3", "Day 4", "Day 5", "Day 6", "Day 7"]
        default_items = [2, 4, 3, 2.5, 2.5, 1.5, 5.5]
        notify = Provider.objects.filter(subscription_status='Pending').count()
        n_notify = Provider_Verification.objects.filter(user_position=3).count()
        context = {
            'n_notify': n_notify,
            "title": _title,
            "base_url": settings.BASE_URL,
            "first_name": '',
            'notification': notify,
            "userdata": user_profile,
            "loggedUser": loggedUser,
            "labels": labels,
            "default": default_items,
            "patient": pid,

        }
        # print(context)
        return render(request, "backend/progress_byprovider.html", context)
    except Exception as e:
        return redirect('/backend/dashboard/')


def view_sleep_diary_byprovider(request, weekNm=0, pID=0):
    try:

        _title = "CogniSleep |  Sleep Dairy"
        if (pID > 0):
            userId = pID

        if pID != 0:
            valid_patient = 0
            try:
                userInfo = RefPatient.objects.get(user_id=pID)

            except Exception:
                valid_patient = 1

            if valid_patient == 1:
                return redirect("/dashboard")

        userInfo = RefPatient.objects.get(user_id=pID)

        UsersleepData = SleepDiary.objects.filter(patient_id=pID)

        print("UserData: ", UsersleepData.count())

        bed_time = "00:00"
        reqWeeks = 6

        if (weekNm > 0):
            week_day = weekNm - 1
        else:
            week_day = weekNm

        weekDays_array = []

        if week_day == 0:
            start = userInfo.timestamp.date() + timedelta(days=1)
        else:
            start = userInfo.timestamp.date() + timedelta(days=week_day * 7 + 1)
        end = start + timedelta(days=7 - 1)
        end__ = userInfo.timestamp.date() + timedelta(days=7)

        start_date = datetime.date(start.year, start.month, start.day)
        end_date = datetime.date(end.year, end.month, end.day)

        # user sleep dairy
        invoice_for_today1 = SleepDiary.objects.raw(
            "SELECT * FROM dashboard_sleepdiary where patient_id=%s and date BETWEEN %s and %s",
            [str(pID), start_date, end_date])
        print(invoice_for_today1)
        user_date_array = []
        loggedUser = userId

        for x in range(1, reqWeeks + 1):

            if int(x) == week_day + 1:
                week_array = {
                    "x": x,
                    # "week_date": week,
                    # "is_selected": 1
                }
                weekDays_array.append(week_array)
            else:
                week_array = {
                    "x": x,
                    # "week_date": week,
                    # "is_selected": 0
                }
                weekDays_array.append(week_array)

        notify = Provider.objects.filter(subscription_status='Pending').count()
        n_notify = Provider_Verification.objects.filter(user_position=3).count()
        context = {
            'n_notify': n_notify,
            "title": _title,
            "base_url": settings.BASE_URL,
            "loggedUser": loggedUser,
            "tags": "dairy",
            "week": weekNm,
            'notification': notify,
            "weekDays_array": weekDays_array,
            "invoice_for_today_list": user_date_array,
            "user_sleep_diarys": invoice_for_today1,
            "patient": pID,
            "time_went_to_bed": bed_time

        }

        return render(request, "backend/dashboard_provider_view_sleepdiary_tabs.html", context)
    except Exception as e:
        print(e)
        return redirect('/backend/dashboard/')


def subscription_package(request):
    try:
        _title = "CogniSleep | Current Active Patient"
        if ("admin_id" not in request.session):
            return redirect('/backend/')

        if request.method == 'POST':
            print(request.POST.get('package_name'))
            sub_pkg = Subscriptionpackage()

            sub_pkg.date = request.POST.get('entry_date')
            sub_pkg.package_name = request.POST.get('package_name')
            sub_pkg.no_free_months = request.POST.get('free_month')
            sub_pkg.no_discounted_months = request.POST.get('discount_month')
            sub_pkg.discounted_price = request.POST.get('discount_price')
            sub_pkg.base_price = request.POST.get('base_price')
            sub_pkg.package_detail = request.POST.get('package_details')
            sub_pkg.save()
            print("Record Save Successfully")

            if request.POST['mysearch'] != '':
                all_current_active_patients = User.objects.raw(
                    "SELECT providers.first_name,providers.last_name,providers.provider_ref,providers.practice_name,accounts_user.email,accounts_user.username, accounts_user.id, providers.user_id, providers.contact_no,DATE(providers.timestamp) as date,TIME(providers.timestamp) as time  FROM  accounts_user inner join providers on accounts_user.id = providers.user_id where accounts_user.admin = 0 and accounts_user.role_id=1 and accounts_user.active=1  and CONCAT(first_name, last_name, email, provider_ref) like %s",
                    ['%' + request.POST['mysearch'] + '%'])
                print("YES ELIF")
                paginator = Paginator(all_current_active_patients, 25)
                page = request.GET.get('page')
                contacts = paginator.get_page(page)
                print(contacts)
                notify = Provider.objects.filter(subscription_status='Pending').count()
                n_notify = Provider_Verification.objects.filter(user_position=3).count()
                context = {
                    'n_notify': n_notify,
                    "title": _title,
                    "base_url": settings.BASE_URL,
                    "first_name": '',
                    'notification': notify,
                    "all_current_active_patients": contacts,
                    # "date_from": request.POST['date_from'],
                    # "date_to": request.POST['date_to'],
                    "mysearch": request.POST['mysearch'],

                }

                return render(request, "backend/subscription_package.html", context)

        # all_current_active_patients = User.objects.raw(
        #    "SELECT providers.first_name,providers.last_name,providers.provider_ref,providers.practice_name,providers.total_patients,accounts_user.email,accounts_user.username, accounts_user.id, providers.user_id, providers.contact_no,DATE(providers.timestamp) as date,TIME(providers.timestamp) as time  FROM  accounts_user inner join providers on accounts_user.id = providers.user_id where accounts_user.role_id = 1 and  accounts_user.active=1   order by accounts_user.id desc")
        objs = Subscriptionpackage.objects.all().order_by("-date")
        paginator = Paginator(objs, 25)
        page = request.GET.get('page')
        contacts = paginator.get_page(page)
        # contacts = []
        notify = Provider.objects.filter(subscription_status='Pending').count()
        n_notify = Provider_Verification.objects.filter(user_position=3).count()
        context = {
            'n_notify': n_notify,
            "title": _title,
            "base_url": settings.BASE_URL,
            "first_name": '',
            'notification': notify,
            "all_current_active_patients": contacts,

        }

        return render(request, "backend/subscription_package.html", context)
    except Exception as e:
        return redirect('/backend/dashboard/')


def accountdetailsbyprovider(request, pid):
    try:

        userdetail = User.objects.get(id=pid)
        role_id = userdetail.role_id
        email = userdetail.email
        if role_id == 3:
            user_profile = Patient.objects.get(user_id=pid)
        elif role_id == 2:
            print("Yes In 2")
            user_profile = RefPatient.objects.get(user_id=pid)
            print(user_profile.first_name)
        elif role_id == 1:
            user_profile = Provider.objects.get(user_id=pid)
        userInfo = user_profile
        reqWeeks = 6
        if role_id != 1:
            if userInfo.package_no == 'PRIMARY CARE SUBSCRIPTION':
                reqWeeks = 6
            if userInfo.package_no == 'REFERRAL SUBSCRIPTION FROM PHYSICIAN/PROVIDER':
                reqWeeks = 6
            elif userInfo.package_no == 'COGNISLEEP INTENSE LEARNERS':
                reqWeeks = 8
            elif userInfo.package_no == 'COGNISLEEP TRADITIONAL':
                reqWeeks = 12
            elif userInfo.package_no == 'COGNISLEEP PLUS':
                reqWeeks = 15
            else:
                reqWeeks = 6

        _title = "CogniSleep |  Cogni-Dashboard"
        user_ref_data_array = []
        loggedUser = User.objects.get(id=pid)

        # user_profile = PatientProfile.objects.get(patient_user_id=request.user.id)
        UsersleepData = SleepDiary.objects.filter(patient_id=pid, is_updated=1)
        isSleepDiaryData = UsersleepData.count()

        sleepdiary_ids = SleepDiary.objects.raw(
            "SELECT id, max(id) lastid , min(id) as firstid FROM dashboard_sleepdiary WHERE patient_id=%s",
            [int(pid)])

        sleepdiary_dates = SleepDiary.objects.raw(
            "SELECT id,date FROM dashboard_sleepdiary WHERE id IN(%s,%s)",
            [int(sleepdiary_ids[0].firstid), int(sleepdiary_ids[0].lastid)])
        notify = Provider.objects.filter(subscription_status='Pending').count()
        n_notify = Provider_Verification.objects.filter(user_position=3).count()
        context = {
            'n_notify': n_notify,
            "title": _title,
            "base_url": settings.BASE_URL,
            "first_name": '',
            "email": email,
            "week": reqWeeks,
            "userdata": user_profile,
            "loggedUser": loggedUser,
            "patient": pid,
            'notification': notify,
            "isSleepDiaryData": isSleepDiaryData,
            "sleepdiary_startDate": sleepdiary_dates[0].date,
            "sleepdiary_endDate": sleepdiary_dates[1].date

        }

        return render(request, "backend/dashboard_account_details_by_provider.html", context)

    except Exception as e:
        return redirect('/backend/dashboard/')


def Non_Verified_Provider(request):
    try:
        print("yes in non verified")
        _title = "CogniSleep | Non Verified Provider"
        if ("admin_id" not in request.session):
            return redirect('/backend/')

        if request.method == 'POST':

            # elif request.POST['date_from'] == '' and request.POST['date_to'] == '' and request.POST['mysearch'] != '':
            if request.POST['mysearch'] != '':
                all_current_active_patients = User.objects.raw(
                    "SELECT providers.first_name,providers.last_name,providers.provider_ref,providers.package_type,providers.primary_care_doctor_id,providers.flag,providers.practice_name,providers.subscription_status,accounts_user.email,accounts_user.username, accounts_user.id, providers.user_id, providers.contact_no,DATE(providers.timestamp) as date,TIME(providers.timestamp) as time, provider_verification.user_position  FROM  accounts_user inner join providers on accounts_user.id = providers.user_id inner join provider_verification on provider_verification.user_id = accounts_user.id where accounts_user.admin = 0 and accounts_user.role_id=1 and accounts_user.active=1 and provider_verification.user_position = 3 and CONCAT(first_name, last_name, email, provider_ref, subscription_status) like %s",
                    ['%' + request.POST['mysearch'] + '%'])
                print("YES ELIF")
                paginator = Paginator(all_current_active_patients, 25)
                page = request.GET.get('page')
                contacts = paginator.get_page(page)
                print(contacts)
                notify = Provider.objects.filter(subscription_status='Pending').count()
                n_notify = Provider_Verification.objects.filter(user_position=3).count()
                context = {
                    'n_notify': n_notify,
                    "title": _title,
                    "base_url": settings.BASE_URL,
                    "first_name": '',
                    'notification': notify,
                    "all_current_active_patients": contacts,
                    # "date_from": request.POST['date_from'],
                    # "date_to": request.POST['date_to'],
                    "mysearch": request.POST['mysearch'],

                }

                return render(request, "backend/non_verified_provider.html", context)

        all_current_active_patients = User.objects.raw(
            "SELECT providers.first_name,providers.last_name,providers.provider_ref,providers.practice_name,providers.package_type,providers.primary_care_doctor_id,providers.flag,providers.total_patients,providers.subscription_status,accounts_user.email,accounts_user.username, accounts_user.id,provider_verification.user_position, providers.user_id, providers.contact_no,DATE(providers.timestamp) as date,TIME(providers.timestamp) as time  FROM  accounts_user inner join providers on accounts_user.id = providers.user_id inner join provider_verification on provider_verification.user_id = accounts_user.id where accounts_user.role_id = 1 and  accounts_user.active=1 and provider_verification.user_position = 3  order by accounts_user.id desc")
        paginator = Paginator(all_current_active_patients, 25)
        page = request.GET.get('page')
        contacts = paginator.get_page(page)
        notify = Provider.objects.filter(subscription_status='Pending').count()

        n_notify = Provider_Verification.objects.filter(user_position=3).count()
        context = {
            'n_notify': n_notify,
            "title": _title,
            "base_url": settings.BASE_URL,
            "first_name": '',
            'notification': notify,
            "all_current_active_patients": contacts,

        }

        return render(request, "backend/non_verified_provider.html", context)
    except Exception as e:
        return redirect('/backend/dashboard/')


def Verified_Provider(request, pid=0):
    print("yes yes yes yse tyse")
    try:
        print("YES IN VERIFIED")
        print(pid)

        if pid != 0 and pid is not None:
            user_data = User.objects.get(id=pid)
            email = user_data.email
            user_step = Provider_Verification.objects.get(user_id=pid)
            user_step.user_position = 4
            user_step.save()

            subject = 'Account Verification'
            to = email

            html_message = loader.render_to_string(
                'email_temp/provider_verification.html', {})
            email_records(request, to, settings.EMAIL_FROM, 'Account Verification')
            send_mail(
                subject,
                'Account Verification',
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
            n_notify = Provider_Verification.objects.filter(user_position=3).count()
            context = {
                'n_notify': n_notify,
                "base_url": settings.BASE_URL,
                "first_name": '',
                'notification': notify,
                "all_current_active_patients": contacts,

            }
            '''messages.success(request, "Provider Verified Successfully!")
            return render(request, "backend/non_verified_provider.html", context)'''
            return redirect('/backend/verified_message/')
    except Exception as e:
        print(e)
        return redirect('/backend/dashboard/')

def delete_user(request, user_id):

    try:
        # Fetch the user to be deleted
        user = get_object_or_404(User, id=user_id)

        # Delete the user
        user.delete()

        # Add a success message
        return redirect('/backend/dashboard/')
    except Exception as e:
        # Handle exceptions, add an error message, or log the error
        messages.error(request, f"Error deleting user: {e}")

    # Redirect to a suitable URL after deletion
    return redirect('/backend/dashboard/')  # Change this URL as needed



def verified_message(request):
    try:
        _title = "CogniSleep | Non Verified Provider"
        if ("admin_id" not in request.session):
            return redirect('/backend/')

        all_current_active_patients = User.objects.raw(
            "SELECT providers.first_name,providers.last_name,providers.provider_ref,providers.practice_name,providers.package_type,providers.primary_care_doctor_id,providers.flag,providers.total_patients,providers.subscription_status,accounts_user.email,accounts_user.username, accounts_user.id,provider_verification.user_position, providers.user_id, providers.contact_no,DATE(providers.timestamp) as date,TIME(providers.timestamp) as time  FROM  accounts_user inner join providers on accounts_user.id = providers.user_id inner join provider_verification on provider_verification.user_id = accounts_user.id where accounts_user.role_id = 1 and  accounts_user.active=1 and provider_verification.user_position = 3  order by accounts_user.id desc")
        paginator = Paginator(all_current_active_patients, 25)
        page = request.GET.get('page')
        contacts = paginator.get_page(page)
        notify = Provider.objects.filter(subscription_status='Pending').count()
        n_notify = Provider_Verification.objects.filter(user_position=3).count()
        context = {
            'n_notify': n_notify,
            "title": _title,
            "base_url": settings.BASE_URL,
            "first_name": '',
            'notification': notify,
            "all_current_active_patients": contacts,

        }
        messages.success(request, "Provider Verified Successfully!")
        return render(request, "backend/non_verified_provider.html", context)
    except Exception as e:
        print(e)
        return redirect('/backend/dashboard/')


def Incomplete_Provider(request):
    try:
        print("yes incomplete provider")
        _title = "CogniSleep | Incomplete Provider Registration"
        if ("admin_id" not in request.session):
            return redirect('/backend/')

        if request.method == 'POST':

            # elif request.POST['date_from'] == '' and request.POST['date_to'] == '' and request.POST['mysearch'] != '':
            if request.POST['mysearch'] != '':
                all_current_active_patients = User.objects.raw(
                    "SELECT providers.first_name,providers.last_name,providers.contact_no,accounts_user.email,accounts_user.username, accounts_user.id, providers.user_id,providers.package_type,providers.primary_care_doctor_id,providers.flag, providers.contact_no,DATE(providers.timestamp) as date,TIME(providers.timestamp) as time, provider_verification.user_position  FROM  accounts_user inner join providers on accounts_user.id = providers.user_id inner join provider_verification on provider_verification.user_id = accounts_user.id where accounts_user.admin = 0 and accounts_user.role_id=1 and accounts_user.active=1 and provider_verification.user_position < 3 and CONCAT(first_name, last_name, email, provider_ref, subscription_status) like %s",
                    ['%' + request.POST['mysearch'] + '%'])
                print("YES ELIF")
                paginator = Paginator(all_current_active_patients, 25)
                page = request.GET.get('page')
                contacts = paginator.get_page(page)
                print(contacts)
                notify = Provider.objects.filter(subscription_status='Pending').count()
                n_notify = Provider_Verification.objects.filter(user_position=3).count()
                context = {
                    'n_notify': n_notify,
                    "title": _title,
                    "base_url": settings.BASE_URL,
                    "first_name": '',
                    'notification': notify,
                    "all_current_active_patients": contacts,
                    # "date_from": request.POST['date_from'],
                    # "date_to": request.POST['date_to'],
                    "mysearch": request.POST['mysearch'],

                }

                return render(request, "backend/incomplete_provider.html", context)

        all_current_active_patients = User.objects.raw(
            "SELECT providers.first_name,providers.last_name,providers.contact_no,accounts_user.email,accounts_user.username, accounts_user.id,provider_verification.user_position, providers.user_id,providers.package_type,providers.primary_care_doctor_id,providers.flag, providers.contact_no,DATE(providers.timestamp) as date,TIME(providers.timestamp) as time  FROM  accounts_user inner join providers on accounts_user.id = providers.user_id inner join provider_verification on provider_verification.user_id = accounts_user.id where accounts_user.role_id = 1 and  accounts_user.active=1 and provider_verification.user_position < 3  order by accounts_user.id desc")
        paginator = Paginator(all_current_active_patients, 25)
        page = request.GET.get('page')
        contacts = paginator.get_page(page)
        notify = Provider.objects.filter(subscription_status='Pending').count()
        n_notify = Provider_Verification.objects.filter(user_position=3).count()
        context = {
            'n_notify': n_notify,
            "title": _title,
            "base_url": settings.BASE_URL,
            "first_name": '',
            'notification': notify,
            "all_current_active_patients": contacts,

        }

        return render(request, "backend/incomplete_provider.html", context)
    except Exception as e:
        return redirect('/backend/dashboard/')


def register_provider_verify(request, pid):
    try:
        if Provider.objects.filter(user_id=pid).exists():
            provider = Provider.objects.get(user_id=pid)
            user_data = User.objects.get(id=pid)
            email = user_data.email
            second_signing_link = user_data.signing_link_2
        notify = Provider.objects.filter(subscription_status='Pending').count()
        n_notify = Provider_Verification.objects.filter(user_position=3).count()
        context = {
            'n_notify': n_notify,
            'notification': notify,
            'email': email,
            'provider': provider,
            'second_signing_link': second_signing_link,

        }
        return render(request, "backend/register_provider_verify.html", context)
    except Exception as e:
        print(e)
        return redirect('/backend/dashboard/')


def create_package(request):
    notify = Provider.objects.filter(subscription_status='Pending').count()
    n_notify = Provider_Verification.objects.filter(user_position=3).count()
    context = {
        'n_notify': n_notify,
        'notification': notify,
    }
    return render(request, "backend/add_new_package.html", context)


def all_packages(request):
    try:
        pkg = Product_detail.objects.all()
        notify = Provider.objects.filter(subscription_status='Pending').count()
        n_notify = Provider_Verification.objects.filter(user_position=3).count()
        context = {
            'n_notify': n_notify,
            'notification': notify,
            "package": pkg,
        }
        return render(request, "backend/packages.html", context)
    except Exception as e:
        print(e)
        return redirect('/backend/dashboard/')


def all_packages_coupon(request):
    try:
        pkg = Coupon_Product_detail.objects.all()
        notify = Provider.objects.filter(subscription_status='Pending').count()
        n_notify = Provider_Verification.objects.filter(user_position=3).count()
        context = {
            'n_notify': n_notify,
            'notification': notify,
            "package": pkg,
        }
        return render(request, "backend/all_coupon_packages.html", context)
    except Exception as e:
        print(e)
        return redirect('/backend/dashboard/')

@csrf_exempt
def sleep_diary_week_data(request, weekNm=0, pID=0):
    try:
        userId = pID

        if pID != 0:
            valid_patient = 0
            try:
                userInfo = RefPatient.objects.get(user_id=pID)
            except Exception:
                valid_patient = 1

            if valid_patient == 1:
                data = {
                    "success": "false",
                }

        userInfo = RefPatient.objects.get(user_id=userId)

        if (weekNm > 0):
            week_day = weekNm - 1
        else:
            week_day = weekNm
        weekvalue = weekNm
        if week_day == 0:
            start = userInfo.timestamp.date() + timedelta(days=1)
        else:
            start = userInfo.timestamp.date() + timedelta(days=week_day * 7 + 1)
        end = start + timedelta(days=7 - 1)

        start_date = datetime.date(start.year, start.month, start.day)
        end_date = datetime.date(end.year, end.month, end.day)

        # user sleep dairy
        invoice_for_today = SleepDiary.objects.raw(
            "SELECT * FROM dashboard_sleepdiary where patient_id=%s and date BETWEEN %s and %s",
            [str(userId), start_date, end_date])
        invoice_for_today = serialize('json', invoice_for_today)

        data = {
            "success": "true",
            "week_data": invoice_for_today,
            "user_id": userId

        }

        return JsonResponse(data)
    except Exception as e:
        print(e)
        return redirect('/')


def refPatient_log(request):
    try:
        _title = "CogniSleep |  Patient"
        if ("admin_id" not in request.session):
            return redirect('/backend/')

        if request.method == 'POST':
            if request.POST['mysearch'] != '' and request.POST['date_from'] != '' and request.POST['date_to'] != '':
                userId = request.POST['mysearch']
                start_date = request.POST['date_from']
                end_date = request.POST['date_to']
                print("YES REFPATIENT")
                all_log = Logfile.objects.raw(
                    "SELECT * FROM log_detail where patient_id=%s and entry_date BETWEEN %s and %s",
                    [str(userId), start_date, end_date])

            if request.POST['mysearch'] != '' and request.POST['date_from'] == '' and request.POST['date_to'] == '':
                userId = request.POST['mysearch']

                print("YES REFPATIENT")
                all_log = Logfile.objects.raw(
                    "SELECT * FROM log_detail where patient_id=%s",
                    [str(userId)])

            paginator = Paginator(all_log, 25)
            page = request.GET.get('page')
            contacts = paginator.get_page(page)

            notify = Provider.objects.filter(subscription_status='Pending').count()
            n_notify = Provider_Verification.objects.filter(user_position=3).count()
            context = {
                'n_notify': n_notify,
                'notification': notify,
                "title": _title,
                "base_url": settings.BASE_URL,
                "first_name": '',
                "all_logs": contacts,
                "mysearch": request.POST['mysearch'],
                "date_from": request.POST['date_from'],
                "date_to": request.POST['date_to'],

            }

            return render(request, "backend/refpatientslogs.html", context)
        all_log = Logfile.objects.raw("SELECT * FROM log_detail order by entry_date DESC")
        print(all_log)
        paginator = Paginator(all_log, 25)
        page = request.GET.get('page')
        contacts = paginator.get_page(page)

        notify = Provider.objects.filter(subscription_status='Pending').count()
        n_notify = Provider_Verification.objects.filter(user_position=3).count()
        context = {
            'n_notify': n_notify,
            'notification': notify,
            "title": _title,
            "base_url": settings.BASE_URL,
            "all_logs": contacts,

        }

        return render(request, "backend/refpatientslogs.html", context)
    except Exception as e:
        print(e)
        return redirect('/backend/dashboard/')


def createcoupon(request):
    return render(request, "backend/create_coupon.html")