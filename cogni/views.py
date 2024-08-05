import json
import os
import urllib

from django.conf import settings
from django.db import connections
from django.shortcuts import render, redirect, reverse
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from accounts.models import  Provider, RefPatient, Patient
from rest_framework.views import APIView
from django.core.serializers import serialize
from rest_framework import permissions, status, generics
from rest_framework.response import Response
from accounts.forms import LoginForm
from django.contrib import messages
from datetime import timedelta, date
import calendar, datetime
from rest_framework.views import exception_handler
from rest_framework.response import Response
from cogni.settings import BASE_DIR
from dashboard.models import SleepDiary, PatientEfficiency
import re
from django.core.mail import send_mail, EmailMessage
from django.template import loader
from django.views.generic import TemplateView

# from payments.views import isPaymentSuccess
from django.core.files.storage import FileSystemStorage
from accounts.models import Add_provider
from payments.models import Coupon
from payments.views import isPaymentSuccess

User = get_user_model()


def guestLogin(request):
    if request.session.has_key('guest') and request.session['guest']:
        return redirect(settings.BASE_URL)
    if request.method == 'POST':

        form = LoginForm(request.POST)
        context = {
            'form': form
        }

        if form.is_valid():
            email = request.POST['email']
            password = request.POST['password']
         
            if email == 'cogni@cognisleep.com' and password == 'cogni?123':
                request.session['guest'] = True
                request.session.set_expiry(3600)
                request.session.save()
                return redirect(settings.BASE_URL)
            else:
                messages.error(request, "Invalid Email  / Password,try again.")
                return render(request, "registration/login1.html", {'form': form})
        else:
            _title = settings.BASE_TITLE
            form = LoginForm()
            context = {
                'form': form,
                'title': _title,
                'base_url': settings.BASE_URL
            }
            return render(request, "registration/login1.html", context)

    else:

        _title = settings.BASE_TITLE
        form = LoginForm()
        context = {
            'form': form,
            'title': _title,
            'base_url': settings.BASE_URL
        }
        return render(request, "registration/login1.html", context)


def home_page(request):
    _title = settings.BASE_TITLE
    if request.user.id is not None:
        paymentSuccess = isPaymentSuccess(request.user.email)
    else:
        paymentSuccess = None
    context = {
        "title": _title,
        'base_url': settings.BASE_URL,
        'video_url': settings.VIDEO_URL,
        'payment_success': paymentSuccess,

    }
    return render(request, "home.html", context)


def calculator(request):
    _title = "CogniSleep |  Cogni-Calculator"

    context = {
        "title": _title,
        "base_url": settings.BASE_URL,
        "first_name": '',
        "patient": 0,

    }

    return render(request, "dashboard_calculator_tabs.html", context)

def about_page(request):
    _title = settings.BASE_TITLE + ' |  About us'

    context = {
        "title": _title,
        'base_url': settings.BASE_URL,
        "page_Sel": "about"
    }


    return render(request, "about.html", context)

def contactus(request):
    try:

        if request.method == "POST":

            subject = 'Cognisleep | Contact us'
            to = request.POST.get("email")
            request_file = request.FILES['myfile'] if 'myfile' in request.FILES else None
            print(request_file)
            if request_file:
                fs = FileSystemStorage()
                file = fs.save(request_file.name, request_file)
                file_url = fs.url(file)
                print("image save successfully")
                print(file_url)
            response_captcha = int(request.POST.get("response_captcha"))
            if response_captcha is not 1:
                _title = settings.BASE_TITLE + ' |  Contact us'
                messages.error(request, "Recaptcha is not verified!")
                return render(request, "contactus.html", {"title": _title, 'base_url': settings.BASE_URL})

            html_message = loader.render_to_string(
                'email_temp/contact_us_email.html',
                {
                    'unique_id_patient': "",
                    'fullname': request.POST.get('fullname'),
                    'email': request.POST.get('email'),
                    'phone': request.POST.get('phone'),
                    'message': request.POST.get('message'),
                }
            )
            if request_file:
                msg = EmailMessage(subject, html_message, [to], settings.EMAIL_FROM)
                msg.content_subtype = "html"
                filepath = os.path.join(BASE_DIR, 'media/' + str(request_file))
                msg.attach_file(filepath)
                msg.send()
            else:
                email_records(request,to,settings.EMAIL_FROM,request.POST.get('message'))
                send_mail(
                    subject,
                    'Cognisleep | Contact us',
                    [to],
                    settings.EMAIL_FROM,
                    html_message=html_message
                    ,
                )

            _title = settings.BASE_TITLE + ' |  Contact us'
            messages.success(request, "Thank you for contacting CogniSleep. You will receive an emailed response to your inquiry  in the next 30 minutes.")
            return render(request, "contactus.html", {"title": _title, 'base_url': settings.BASE_URL})
    except Exception as e:
        print(e)

    _title = settings.BASE_TITLE + ' |  Contact us'
    return render(request, "contactus.html", {"title": _title, 'base_url': settings.BASE_URL})


def cogni_questions(request):
    _title = "CogniSleep |  cogni_questions"
    a = 1
    return render(request, "cogni_questions.html", {"title": _title, 'base_url': settings.BASE_URL, 'a': a})


# Patient Pages

def patient_login(request):
    _title = "CogniSleep |  Login"
    return render(request, "login.html", {"title": _title, 'base_url': settings.BASE_URL})


# Provider Pages


def provider_login(request):
    _title = "CogniSleep |  Provider Login"
    return render(request, "provider_login.html", {"title": _title, 'base_url': settings.BASE_URL})


def provider_registration(request):
    _title = "CogniSleep |  Register Provider"
    return render(request, "register_provider.html", {"title": _title, 'base_url': settings.BASE_URL})


# Static Pages

def patients(request):
    _title = "CogniSleep |  Consumers"

    context = {
        "title": _title,
        'base_url': settings.BASE_URL,
        "page_Sel": "patient"
    }

    return render(request, "consumers.html", context)




def comingsoon(request):
    _title = "CogniSleep |  Coming Soon"

    context = {
        "title": _title,
        'base_url': settings.BASE_URL,
    }

    return render(request, "comingsoon.html", context)


def employers(request):
    _title = "CogniSleep |  Business"


    context = {
        "title": _title,
        'base_url': settings.BASE_URL,
        "page_Sel": "employers"
    }
    return render(request, "business.html", context)


def providers(request):
    _title = "CogniSleep |  Providers"
    context = {
        "title": _title,
        'base_url': settings.BASE_URL,
        "page_Sel": "providers"
    }
    return render(request, "providers.html", context)


def pricing(request, pid=6):

    _title = "CogniSleep |  Pricing"

    context = {
        "title": _title,
        'base_url': settings.BASE_URL,
        "pid": pid,
        "page_Sel": "pricing"
    }
    return render(request, "provider_subscription_home.html", context)


def terms(request):
    _title = "CogniSleep |  Terms"
    return render(request, "terms_conditions.html", {"title": _title, 'base_url': settings.BASE_URL})


def acknowledge_page(request, pid):
    _title = "CogniSleep |  Acknowledge"

    request.session["package"] = pid
    if "isQDone" not in request.session:
        if pid == 1:
            return redirect("/accounts/patientregform/")
        else:
            return redirect("/questions/cogni_questions")

    context = {
        "title": _title,
        'base_url': settings.BASE_URL,
        "pid": pid
    }

    return render(request, "acknowledge_page.html", context)


def faq(request):
    _title = "CogniSleep |  FAQs"
    context = {
        "title": _title,
        'base_url': settings.BASE_URL,
        "page_Sel": "faq"
    }
    return render(request, "faq.html",context)


def blog(request):
    _title = "CogniSleep |  Blog"
    return render(request, "blog.html", {"title": _title, 'base_url': settings.BASE_URL})


def do_you_have_sleeping_problem(request):
    _title = "CogniSleep |  Blog"
    return render(request, "do-you-have-sleeping-problem.html", {"title": _title, 'base_url': settings.BASE_URL})


def cogni_science(request):
    _title = "CogniSleep |  Proof it Works"

    context = {
        "title": _title,
        'base_url': settings.BASE_URL,

        "page_Sel": "cogni_science"
    }

    return render(request, "proofitworks.html",context)


def daily_progress_chart(request,pid = 0):
    authentication_classes = []
    permission_classes = []
    print("YES INSIDE BAR")
    checkUser = request.user.id
    print(checkUser)
    print(pid)
    if "admin_request" in request.GET:
        print("first if")
        request.user.id = pid
        checkUser = pid
        pid = 0
        request.user.role_id = 3
    if "admin_request_ref_id" in request.GET:
        print("second if")
        request.user.id = pid
        checkUser = pid
        pid = 0
        request.user.role_id = 2
    #if checkUser == None :
    #    print("third if")
    #    return redirect('/')
    _title = "CogniSleep |  Cogni-Dashboard"
    if pid > 0:
        checkUser = pid


    #if request.user.role_id == 2:
    #   userInfo = RefPatient.objects.get(user_id=checkUser)
    #elif request.user.role_id == 3:
    #    userInfo = Patient.objects.get(user_id=checkUser)
    #else:
    userInfo = RefPatient.objects.get(user_id=checkUser)
    #end else
    start = userInfo.timestamp.date() + timedelta(days=1)
    end = start + timedelta(days=7 - 1)

    #print("Start date", start)
    #print("Start end", end)

    invoice_for_today = SleepDiary.objects.raw(
        "SELECT * FROM dashboard_sleepdiary where patient_id=%s and time_went_to_bed!='' and time_fell_asleep!='' and total_gotup_time!='' ",
        [str(checkUser)])

    user_full_package = SleepDiary.objects.raw(
        "SELECT * FROM dashboard_sleepdiary where patient_id=%s ", [str(checkUser)])

    #print("user_full_package", len(list(user_full_package)))

    bedtime_array = []

    for value in invoice_for_today:
        total_percent_sleep = get_user_progress_bar_avg(value.time_went_to_bed, value.time_fell_asleep,
                                                        value.total_gotup_time,
                                                        value.no_of_times_awakend, value.date)
        bedtime_array.append(total_percent_sleep)

    #print(bedtime_array)
    week_days_array = []
    weeks = []
    week_counter = 0
    week_day = 0
    start_date = ""
    labels_weekly = []
    default_items_weekly = []
    monthly_count = 0
    labels_biweekly = []
    default_items_biweekly = []
    labels_monthly = []
    default_items_monthly = []

    for value in bedtime_array:

        if week_counter == 7:
            result = sum(week_days_array) / float(len(week_days_array))
            default_items_weekly.append(round(result, 2))
            labels_weekly.append("Week " + str(week_day+1))
            result = {"weekday": week_day, "avg_data": value, }
            weeks.append(result)
            week_counter = 0
            week_day += 1
            week_days_array = []
        else:
            week_days_array.append(value)
            week_counter += 1

    print("chart 7 days: ", list(weeks))
    labels = []
    default_items = []
    week_day = 0
    week_counter = 0

    for value in bedtime_array:

        if week_counter == 14:
            result = sum(week_days_array) / float(len(week_days_array))
            default_items_biweekly.append(round(result, 2))
            labels_biweekly.append("Week " + str(week_day+1))
            result = {"weekday": week_day, "avg_data": value, }
            weeks.append(result)
            week_counter = 0
            week_day += 1
            week_days_array = []
        else:
            week_days_array.append(value)
            week_counter += 1



    print("chart 7 days: ", list(weeks))
    labels = []
    default_items = []

    x = 1
    for value in invoice_for_today:
        total_percent_sleep = get_user_progress_bar_avg(value.time_went_to_bed, value.time_fell_asleep,
                                                        value.total_gotup_time,
                                                        value.no_of_times_awakend, value.date)
        default_items.append(total_percent_sleep)
        if x < 31:
            monthly_count += total_percent_sleep
        labels.append("Day " + str(x))
        x += 1
    default_items_monthly.append(monthly_count / 30)
    labels_monthly.append("Monthly")
    progress_data = 0
    #print("week_days_array : ", str(monthly_count / 30))
    #print("Weeko : ", str(monthly_count))
    if pid != 0:
        if PatientEfficiency.objects.filter(patient_id=pid).exists():
            progress_data = PatientEfficiency.objects.filter(patient_id=pid)
            progress_data = serialize('json', progress_data)
    if pid == 0:
        if PatientEfficiency.objects.filter(patient_id=checkUser).exists():
            progress_data = PatientEfficiency.objects.filter(patient_id=checkUser)
            progress_data = serialize('json', progress_data)
    invoice_for_today= serialize('json', invoice_for_today)
    if len(list(invoice_for_today)) != 0:

        data = {
            "success": "true",
            "labels": labels,
            "default": default_items,
            "labels_weekly": labels_weekly,
            "default_items_weekly": default_items_weekly,
            "labels_biweekly": labels_biweekly,
            "default_items_biweekly": default_items_biweekly,
            "labels_monthly": labels_monthly,
            "default_items_monthly": default_items_monthly,
            'invoice_for_today':invoice_for_today,
            'progress_data': progress_data
        }
        return JsonResponse(data)
    else:

        data = {
            "success": "false",
            "labels": labels,
            "default": default_items,
            "labels_weekly": labels_weekly,
            "default_items_weekly": default_items_weekly,
            "labels_biweekly": labels_biweekly,
            "default_items_biweekly": default_items_biweekly,
            "labels_monthly": labels_monthly,
            "default_items_monthly": default_items_monthly,
            'invoice_for_today':invoice_for_today

        }

        return JsonResponse(data)


def time_to_sec(time_str):
    return sum(x * int(t) for x, t in zip([1, 60, 3600], reversed(time_str.split(":"))))


def get_videos(request):
    authentication_classes = []
    permission_classes = []

    videos = [
        {
            "title": "Video 1",
            "videos_url": "https://cognisleep.com/dev/wp-content/themes/custom/Cogni-Introduction-video.mp4",
            "status": 1
        },
        {
            "title": "Video 2",
            "videos_url": "https://cognisleep.com/dev/wp-content/themes/custom/Cogni-Introduction-video.mp4",
            "status": 0
        },
        {
            "title": "Video 3",
            "videos_url": "https://cognisleep.com/dev/wp-content/themes/custom/Cogni-Introduction-video.mp4",
            "status": 0
        },
        {
            "title": "Video 4",
            "videos_url": "https://cognisleep.com/dev/wp-content/themes/custom/Cogni-Introduction-video.mp4",
            "status": 0
        },
        {
            "title": "Video 5",
            "videos_url": "https://cognisleep.com/dev/wp-content/themes/custom/Cogni-Introduction-video.mp4",
            "status": 0
        },

        {
            "title": "Video 6",
            "videos_url": "https://cognisleep.com/dev/wp-content/themes/custom/Cogni-Introduction-video.mp4",
            "status": 0
        },

    ]

    data = {
        "videos": videos
    }
    return JsonResponse(data)


def get_user_progress_bar_avg(time_wentto_bed, time_fee_asleep, time_got_up, no_of_times_awakened, udate):
    date = udate
    time_went_to_bed = time_wentto_bed
    time_fee_asleep = time_fee_asleep
    time_got_up = time_got_up
    no_of_times_awakened = no_of_times_awakened

    # convert time went to bed in minuetes
    print("time_went_to_bed : ", time_went_to_bed)
    time_wenttobed = time_went_to_bed.split(":")
    print("time_went_to_bed : ", time_wenttobed)

    time_went_to_bed_hours = int(time_wenttobed[0])
    time_went_to_bed_minutes = int(time_wenttobed[1])
    time_went_to_bed = time_went_to_bed
    time_went_to_bed_total_minutes = (time_went_to_bed_hours * 60) + time_went_to_bed_minutes

    print("Total Minutes time_went_to_bed: ", time_went_to_bed_total_minutes)

    # time_fee_asleep = datetime.datetime.strptime(time_fee_asleep, '%H:%M:%S')
    time_feeasleep = time_fee_asleep.split(":")
    print("time_went_to_bed : ", time_fee_asleep)
    time_fee_asleep_hours = int(time_feeasleep[0])
    time_fee_asleep_minutes = int(time_feeasleep[1])
    time_fee_asleep = time_fee_asleep
    time_fee_asleep_total_minutes = (time_fee_asleep_hours * 60) + time_fee_asleep_minutes

    print("Total Minutes:  time_fee_asleep", time_fee_asleep_total_minutes)

    # time_got_up = datetime.datetime.strptime(time_got_up, '%H:%M:%S')
    time_gotup = time_got_up.split(":")
    print("time_went_to_bed : ", time_got_up)
    time_got_up_hours = int(time_gotup[0])
    time_got_up_minutes = int(time_gotup[1])
    time_got_up = time_got_up
    time_went_to_bed_minutes = (time_went_to_bed_hours * 60) + time_went_to_bed_hours
    time_got_up_total_minutes = (time_got_up_hours * 60) + time_got_up_minutes

    print("Total Minutes: time_got_up ", time_got_up_total_minutes)

    twtb_diff_to_am = 0
    tfs_diff_to_am = 0
    tgu_diff_to_am = 0
    total_time_on_bed = 0
    total_time_sleep = 0

    if time_went_to_bed_total_minutes < 720 and time_fee_asleep_total_minutes < 720 and time_got_up_total_minutes < 720:

        total_time_on_bed = (time_got_up_total_minutes - time_went_to_bed_total_minutes)
        total_time_sleep = (time_got_up_total_minutes - time_fee_asleep_total_minutes)
    elif time_went_to_bed_total_minutes >= 720 and time_fee_asleep_total_minutes >= 720 and time_got_up_total_minutes >= 720:
        total_time_on_bed = (time_got_up_total_minutes - time_went_to_bed_total_minutes)
        total_time_sleep = (time_got_up_total_minutes - time_fee_asleep_total_minutes)
    elif time_went_to_bed_total_minutes >= 720 and time_fee_asleep_total_minutes >= 720 and time_got_up_total_minutes < 720:
        twtb_diff_to_am = 1440 - time_went_to_bed_total_minutes
        tfs_diff_to_am = 1440 - time_fee_asleep_total_minutes
        tgu_diff_to_am = time_got_up_total_minutes;
        total_time_on_bed = twtb_diff_to_am + tgu_diff_to_am
        total_time_sleep = tfs_diff_to_am + tgu_diff_to_am
    elif time_went_to_bed_total_minutes >= 720 and time_fee_asleep_total_minutes < 720 and time_got_up_total_minutes < 720:
        twtb_diff_to_am = 1440 - time_went_to_bed_total_minutes
        tfs_diff_to_am = time_fee_asleep_total_minutes
        tgu_diff_to_am = time_got_up_total_minutes
        total_time_on_bed = twtb_diff_to_am + tgu_diff_to_am
        total_time_sleep = tgu_diff_to_am - tfs_diff_to_am
    elif time_went_to_bed_total_minutes < 720 and time_fee_asleep_total_minutes >= 720 and time_got_up_total_minutes >= 720:
        twtb_diff_to_am = 720 - time_went_to_bed_total_minutes
        tfs_diff_to_am = time_got_up_total_minutes - time_fee_asleep_total_minutes
        tgu_diff_to_am = time_got_up_total_minutes - 720
        total_time_on_bed = time_got_up_total_minutes - time_went_to_bed_total_minutes
        total_time_sleep = time_got_up_total_minutes - time_fee_asleep_total_minutes
    elif time_went_to_bed_total_minutes < 720 and time_fee_asleep_total_minutes < 720 and time_got_up_total_minutes >= 720:
        twtb_diff_to_am = 720 - time_went_to_bed_total_minutes
        tfs_diff_to_am = 720 - time_fee_asleep_total_minutes
        tgu_diff_to_am = time_got_up_total_minutes - 720
        total_time_on_bed = twtb_diff_to_am + tgu_diff_to_am
        total_time_sleep = tfs_diff_to_am + tgu_diff_to_am
    else:

        total_time_on_bed = 0
        total_time_sleep = 0

    print("total_time_on_bed ", total_time_on_bed)
    print("total_time_sleep ", total_time_sleep)
    total_time_on_bed = (time_got_up_total_minutes - time_went_to_bed_total_minutes)
    total_time_sleep = (time_got_up_total_minutes - time_fee_asleep_total_minutes)
    if total_time_on_bed == 0 and total_time_sleep == 0:
        total_percent_sleep = abs(0 * 100)
    else:
         if(total_time_on_bed == 0):
            total_time_on_bed = 1
         total_percent_sleep = abs((total_time_sleep / total_time_on_bed) * 100)
        #total_percent_sleep = abs((total_time_on_bed / total_time_sleep) * 100)

    print("total_percent_sleep : ", round(total_percent_sleep, 2))

    return round(total_percent_sleep, 2)


def login(request):
    response_data = {}
    if request.is_ajax():
        if request.method == 'POST':

            username = request.GET.get('txtuseremail')
            password = request.GET.get('pwd')
            # stayloggedin = request.GET.get('stayloggedin')
            #  if stayloggedin == "true":
            #      pass
            #  else:
            #      request.session.set_expiry(0)
            user = authenticate(username=username, password=password)

            if user is not None:
                if user.is_active:
                    login(request, user)
                    response_data['success'] = 'true'
                else:
                    response_data['success'] = 'false'
            else:
                return HttpResponse('bad')

            return HttpResponse(json.dumps(response_data), content_type="application/json")
        else:
            response_data['success'] = 'false'
            return HttpResponse(json.dumps(response_data), content_type="application/json")


def email_records(request,to_,from_,msg):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    cursor = connections['default'].cursor()
    cursor.execute("INSERT INTO emails(to_,from_,msg,ip) VALUES( %s , %s, %s, %s )", [to_, from_,msg,ip])


class Referedbyprof(APIView):

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


class Referedbycoupon(APIView):

    def post(self, request, *args, **kwargs):
        coupon_code = request.data.get('coupon_code')

        if coupon_code:

            try:



                    userData = Coupon.objects.filter(code=coupon_code)
                    jsonData = None

                    for value in userData:
                        jsonData = {
                            "code": value.code,
                            "title": value.title,
                            # "primary_care_office_name": value.practice_address,
                            # "primary_care_doctor_name": value.first_name+" "+value.last_name,

                        }
                        print(value.title)

                    if userData.count() > 0:

                        return Response({
                            'success': True,
                            'message': 'Coupon is valid ',
                            "code": jsonData['code'],
                            "title": jsonData['title'],

                        })

                    else:
                        return Response({
                            'success': False,
                            'message': 'Coupon was not found. Please verify your coupon code.'
                        })
            except Exception:
                return Response({
                    'success': False,
                    'message': 'Coupon was not found. Please verify your coupon code.'
                })


        else:

            return Response({
                'success': False,
                'message': 'Coupon was not found. Please verify your coupon code.',
            })

class Patient_status(APIView):

    def post(self, request, *args, **kwargs):

        user_id = request.data.get('user_id')
        status = request.data.get('status_change')
        #print("Userss ",user_id)
        if user_id:

            try:
                userdt = User.objects.get(id=int(user_id))
                userdt.active_patient = int(status)
                #userdt.active = int(status)
                userdt.save()
                return Response({
                    'success': True,
                })

                # if userdt:
                #     userData = PatientProfile.objects.filter(patient_user_id=userdt.pk)
            except User.DoesNotExist:
                return Response({
                    'success': False,
                })
        else:
            return Response({
                'success': False,
            })


class Ma_status(APIView):

    def post(self, request, *args, **kwargs):
        print("Hello")
        user_id = request.data.get('user_id')
        status = request.data.get('status_change')
        main_id = request.data.get('main_id')
        #print("Userss ",user_id)
        if user_id:

            try:
                userdt = Add_provider.objects.get(mid=(user_id), pid=main_id)
                userdt.status = int(status)
                #userdt.active = int(status)
                userdt.save()
                return Response({
                    'success': True,
                })

                # if userdt:
                #     userData = PatientProfile.objects.filter(patient_user_id=userdt.pk)
            except User.DoesNotExist:
                return Response({
                    'success': False,
                })
        else:
            return Response({
                'success': False,
            })

class Subscription(APIView):

    def post(self, request, *args, **kwargs):
        email = request.data.get('email')
        name = request.data.get('name')

        #''' Begin reCAPTCHA validation '''
        recaptcha_response = int(request.POST.get('g-recaptcha-response'))

        if email == "" or name == "":
            return Response({
                'success': False,
                'message': 'Please, fill the form properly'
            })
        elif recaptcha_response is 1:
            subject = 'Cogni Newsletter Subscription'
            html_message = loader.render_to_string(
                'email_temp/newsletter_subscription.html',
                {
                    'unique_msg': "You have Successfully subscribed Cogni's Newsletter",
                }
            )
            email_records(request, email, settings.EMAIL_FROM, "Subscription")
            send_mail(
                subject,
                'Cogni Newsletter',
                settings.EMAIL_FROM,
                [email],
                html_message=html_message
                ,
            )
            html_message = loader.render_to_string(
                'email_temp/newsletter_subscription.html',
                {
                    'unique_msg': "(" + email + ") " + name.capitalize() + " is subscribed Cogni's Newsletter",
                }
            )
            email_records(request, email, settings.EMAIL_FROM, "Subscription")
            send_mail(
                subject,
                'Cogni New Newsletter Subscriber',
                settings.EMAIL_FROM,
                [email],
                html_message=html_message,
            )
            return Response({
                'success': True,
                'message': 'Successfully Subscribed'
            })

        else:
            return Response({
                'success': False,
                'message': 'Invalid reCAPTCHA. Please try again.'
            })


