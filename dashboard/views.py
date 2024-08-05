import datetime
import time
from datetime import timedelta, date
import json
import os
from cogni.settings import BASE_DIR
import requests.utils
from django.contrib.auth.decorators import login_required
import stripe as stripe
from django.conf import settings
from django.contrib import messages
from rest_framework.views import exception_handler
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from django.core.serializers import serialize
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from rest_framework.decorators import api_view, permission_classes
from rest_framework.views import APIView
from rest_framework.response import Response
from django.http import HttpResponse, HttpResponseRedirect
import statistics
from django.templatetags.static import static
from django.template import loader
from django.db import connections
from django.core.mail import send_mail
from rest_framework.permissions import IsAuthenticated
from fpdf import FPDF
from django.http import FileResponse

from django.http.response import HttpResponse
from backend.models import Subscriptionpackage, StripeCustomer
from accounts.models import Patient, RefPatient, Provider, Provider_Verification,Add_provider
from payments.models import Product_detail,Coupon
from cogni.views import get_user_progress_bar_avg
from taketester.models import UserAnswer
from taketester.views import send_fax_directly_ciq, create_ciq_report_directly
from .forms import SleepDiaruForm
from .models import SleepDiary,Logfile, PatientEfficiency, ProviderCard, VideoSessions, VideoQuestions, VideoAnswers, \
    VideoSessionsCompleted, VideoViews, SendFax, Providerhandbooks
import math
from django.db.models import Q
import logging
from .serializer import ProviderhandbooksSerializer
from rest_framework import status
from rest_framework.permissions import AllowAny



# Create your views here.

User = get_user_model()
#video_view_count = 0
#lock_diary = 0

def profile(pid):
    try:
        patient = RefPatient.objects.get(user_id=pid)
        provider_id = patient.provider_id
        provider_id = str(provider_id[4:])
        provider = Provider.objects.get(provider_ref=provider_id)

        provider_name =provider.first_name+" "+provider.last_name
        provider_contact= provider.contact_no

        provider_image = provider.provider_image
        provider_data = {"provider_name":provider_name,
                   "provider_contact":provider_contact,
                   "provider_image":provider_image}
        # return render(request, 'patient/dashboard.html', context)
        return provider_data
        print(provider_name,provider_contact)
    except Exception as e:
        print(e)
        return redirect('/')


@login_required
def dashboard(request, pid=0):
        mylist = []
        mysearch = ""
        user_name = ""
        user_image = ""
        user_access = ""
        ma = False
        malist = False


        try:



            checkUser = request.user.id
            if checkUser is None:
                return redirect('/')
            if pid > 0:
                checkUser = pid
                print(pid)
            if request.user.role_id == 3:
                user_profile = Patient.objects.get(user_id=request.user.id)
                user_name = user_profile.first_name + " " + user_profile.last_name

            elif request.user.role_id == 2:
                user_profile = RefPatient.objects.get(user_id=request.user.id)
                user_name = user_profile.first_name + " " + user_profile.last_name
            elif request.user.role_id == 1:
                user_profile = Provider.objects.get(user_id=request.user.id)
                user_name = user_profile.first_name + " " + user_profile.last_name
                user_image = user_profile.provider_image
                provider_access = Provider_Verification.objects.get(user_id=request.user.id)
                user_access = provider_access.user_position
                access = Provider_Verification.objects.get(user_id=request.user.id)
                access = access.user_position
            elif request.user.role_id == 5:
                user_profile = Provider.objects.get(user_id=request.user.id)
                user_name = user_profile.first_name + " " + user_profile.last_name
                user_image = user_profile.provider_image
                provider_access = Provider_Verification.objects.get(user_id=request.user.id)
                user_access = provider_access.user_position

            userInfo = user_profile
            reqWeeks = 6
            if request.user.role_id != 1 and request.user.role_id != 5:
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
            loggedUser = User.objects.get(id=request.user.id)
            if request.user.role_id == 1:
                print("Yes 1")
                loggedUser = User.objects.get(id=request.user.id)

                if user_profile:
                    try:
                        # request.user.
                        if request.method == 'POST':

                            if request.POST['mysearch'] != '':
                                mysearch = request.POST['mysearch']
                                user_ref_data_array = RefPatient.objects.filter(Q(provider_id__icontains=request.user.id,
                                                                                  first_name__icontains=request.POST[
                                                                                      'mysearch']) | Q(
                                    provider_id__icontains=request.user.id, last_name__icontains=request.POST['mysearch']))

                        else:
                            user_ref_data_array = RefPatient.objects.filter(provider_id__icontains=request.user.id)
                            print("Provider ref: ", user_ref_data_array)

                    except User.DoesNotExist:
                        print("User does not exist")
                        return redirect('/')
                try:
                    data = Provider.objects.get(user_id=request.user.id)
                    code = data.coupon_code
                    coupon = Coupon.objects.filter(code=code, price='0').exists()
                    if coupon:
                       subscription = None
                       product = "coupon"
                       sub_status = "Active"
                       product_price = "0"

                    else:

                        # Retrieve the subscription & product
                        if StripeCustomer.objects.filter(user_id=request.user.id).exists():
                            sub_status = Provider.objects.get(user_id=request.user.id)
                            sub_status = sub_status.subscription_status
                            stripe_customer = StripeCustomer.objects.get(user_id=request.user.id)
                            cus = stripe_customer.stripeCustomerId
                            stripe.api_key = settings.STRIPE_SECRET_KEY
                            subscription = stripe.Subscription.retrieve(stripe_customer.stripeSubscriptionId)
                            product = stripe.Product.retrieve(subscription.plan.product)
                            product_price = subscription.plan.amount_decimal[0:3]
                            inv = stripe.Invoice.list(customer=cus)
                            for i, item in enumerate(inv):
                                d = {}
                                inv_id = inv.data[i]['id']
                                invoice_url = inv.data[i]['invoice_pdf']
                                invoice_status = inv.data[i]['status']
                                dat = inv.data[i]['created']
                                date = datetime.datetime.fromtimestamp(dat)
                                date = date.strftime("%d/%m/%Y")
                                invoice_date = date
                                d['invoice_url'] = invoice_url
                                d['invoice_status'] = invoice_status
                                d['invoice_date'] = invoice_date
                                d['invoice_id'] = inv_id
                                mylist.append(d)
                        else:
                            return redirect('/')
                except StripeCustomer.DoesNotExist:
                    print("Provider Subscription does not exist")
                    return redirect('/')

                # SUB PROVIDER
                try:
                    provider_list = []
                    print("Yes in SUB PROVIDER")
                    subprovider = Add_provider.objects.filter(mid=request.user.id).exists()
                    if subprovider == True:
                        ma_provider = Add_provider.objects.filter(mid=request.user.id, status=True)

                        for pro in ma_provider:
                            d = {}
                            provider = Provider.objects.get(user_id=pro.pid)
                            provider_name = provider.first_name + " " + provider.last_name
                            provider_ref = provider.provider_ref
                            provider_id = pro.pid
                            d['provider_name'] = provider_name
                            d['provider_ref'] = provider_ref
                            d['provider_id'] = provider_id
                            provider_list.append(d)

                        print(provider_list)
                    else:
                        pass
                except Exception as e:
                    print(e)
                    return redirect('/')

                # MA RECORD
                try:
                    ma_provider = Add_provider.objects.filter(pid=request.user.id)
                    ma_provider_list = []
                    for pro in ma_provider:
                        d = {}
                        provider = Provider.objects.get(user_id=pro.mid)
                        provider_fname = provider.first_name
                        provider_lname = provider.last_name
                        main_provider_id = request.user.id
                        provider_id = pro.mid
                        provider_status = pro.status
                        matype = provider.package_type
                        if matype == "MA":
                            type = "MA"
                        else:
                            type = "Provider"
                        print(provider_status)
                        d['provider_fname'] = provider_fname
                        d['provider_lname'] = provider_lname
                        d['main_provider_id'] = main_provider_id
                        d['provider_id'] = provider_id
                        d['type'] = type
                        d['provider_status'] = provider_status
                        ma_provider_list.append(d)
                    list_length = len(ma_provider_list)
                    if list_length > 0:
                        malist = True

                except StripeCustomer.DoesNotExist:
                    print("Provider Ma does not exist")
                    return redirect('/')
                context = {
                    "title": _title,
                    "provider_list": provider_list,
                    "base_url": settings.BASE_URL,
                    "first_name": '',
                    "week": reqWeeks,
                    "user_name": user_name,
                    "user_image": user_image,
                    "userdata": user_profile,
                    "loggedUser": loggedUser,
                    "role_id": request.user.role_id,
                    "user_ref_data_array": user_ref_data_array,
                    'subscription': subscription,
                    'product': product,
                    'access': access,
                    'malist': malist,
                    "ma_list": ma_provider_list,
                    'status': sub_status,
                    'price': product_price,
                    'invoice': mylist,
                    'mysearch': mysearch,
                    'user_access': user_access,
                    'total_record': user_ref_data_array.count(),
                    'total_invoice': len(mylist),
                    #'provider_data': provider_data,

                }
                return render(request, "dashboard_provider.html", context)
            #################################### MA ROLE ID 5 ###############################

            if request.user.role_id == 5:
                print("Yes in MA")
                user_profile = Provider.objects.get(user_id=request.user.id)
                user_name = user_profile.first_name + " " + user_profile.last_name
                user_image = user_profile.provider_image
                ma_provider = Add_provider.objects.filter(mid=request.user.id, status=True)
                provider_list = []
                for pro in ma_provider:
                    d = {}
                    provider = Provider.objects.get(user_id=pro.pid)
                    provider_name = provider.first_name + " " + provider.last_name
                    provider_ref = provider.provider_ref
                    provider_id = pro.pid
                    d['provider_name'] = provider_name
                    d['provider_ref'] = provider_ref
                    d['provider_id'] = provider_id
                    provider_list.append(d)

                print(provider_list)
                context = {
                    "title": _title,
                    "base_url": settings.BASE_URL,

                    "user_name": user_name,
                    "user_image": user_image,

                    "role_id": 5,
                    "provider_list": provider_list,

                    'user_access': user_access,


                }
                return render(request, "ma_dashboard.html", context)
        except Exception as e:
            print(e)
            return redirect('/')


        try:




                # user_profile = PatientProfile.objects.get(patient_user_id=request.user.id)
                UsersleepData = SleepDiary.objects.filter(patient_id=request.user.id, is_updated=1)
                isSleepDiaryData = UsersleepData.count()
                sleepdiary_ids = SleepDiary.objects.raw(
                    "SELECT id, max(id) lastid , min(id) as firstid FROM dashboard_sleepdiary WHERE patient_id=%s",
                    [int(request.user.id)])
                sleepdiary_dates = SleepDiary.objects.raw(
                    "SELECT id,date FROM dashboard_sleepdiary WHERE id IN(%s,%s)",
                    [int(sleepdiary_ids[0].firstid), int(sleepdiary_ids[0].lastid)])
                sleep_diary_entries = SleepDiary.objects.raw(
                    "SELECT id,count(*) as sleep_diary_entries FROM dashboard_sleepdiary WHERE patient_id=%s and is_updated=1",
                    [int(request.user.id)])

                next_entry_date = SleepDiary.objects.raw(
                    "SELECT id,date FROM dashboard_sleepdiary WHERE patient_id=%s and is_updated=0 limit 1",
                    [int(request.user.id)])

                viewVideosResult = VideoAnswers.objects.raw(
                    "SELECT id,count(*) as countvideos FROM video_answers WHERE user_id=%s",
                    [int(request.user.id)])

                video_view_count = video_count(request.user.id)


                label_tag = "Do it Now"
                Weeks = 1
                days = 1
                dayscount = int(sleep_diary_entries[0].sleep_diary_entries)
                days = dayscount
                view = 0
                now = datetime.date.today()
                current_date = now.strftime("%A %B %d ,%Y")

                if dayscount < 7:
                    Weeks = 1
                    days = days + 1

                if dayscount < 14 and dayscount >= 7:
                    Weeks = 2
                    days = days - 6

                if dayscount < 21 and dayscount >= 14:
                    Weeks = 3
                    days = days - 13

                if dayscount < 28 and dayscount >= 21:
                    Weeks = 4
                    days = days - 20

                if dayscount < 35 and dayscount >= 28:
                    Weeks = 5
                    days = days - 27

                if dayscount < 42 and dayscount >= 35:
                    Weeks = 6
                    days = days - 34

                if dayscount < 49 and dayscount >= 42:
                    Weeks = 7
                    days = days - 41

                if days == 0:
                    days = 1


                next_session_week = Weeks - 1

                date_time_obj1 = datetime.datetime.strptime(str(next_entry_date[0].date), '%Y-%m-%d')
                date_time_obj = datetime.date.strftime(date_time_obj1, "%A, %B %d, %Y")
                today = datetime.date.today()
                year = today.year
                pre_exists = UserAnswer.objects.filter(user_id=request.user.id, question__is_pre=True, question__year=year).count()
                post_exists = UserAnswer.objects.filter(user_id=request.user.id, question__is_post=True,
                                                        question__year=year).count()

                if video_view_count == 1 and sleep_diary_entries[0].sleep_diary_entries == 0:
                    if pre_exists == 15 and post_exists == 0:
                        rec = SendFax.objects.filter(patient_id=request.user.id).exists()

                        if rec == True:
                            pass
                        else:
                            res = create_ciq_report_directly(request.user.id)
                            if res == "success":
                                recs = SendFax(patient_id = request.user.id,pre_ciq = 1)
                                recs.save()
                                print("Record Save Successfully!")
                            else:
                                print("Fax Send Failed please check Fax Number!!")
                if video_view_count == 7:
                    if pre_exists == 15 and post_exists == 15:
                        rec = SendFax.objects.filter(patient_id=request.user.id).exists()
                        if rec == True:
                            res = create_ciq_report_directly(request.user.id)
                            if res == "success":
                                recs = SendFax.objects.get(patient_id=request.user.id)
                                recs.post_ciq = 1
                                recs.save()
                                print("Record Save Successfully!")
                            else:
                                print("Fax Send Failed please check Fax Number!!")
                        else:
                            pass




                sleep_entry = ""
                last_week = ""
                each_day_quote = ""
                avgvalue = "00.00"
                presbedtime = "--:-- --"
                s_time = "--:-- --"
                if sleep_diary_entries[0].sleep_diary_entries == 0:
                    sleep_entry = "No Entry"
                    last_week = "1"
                if sleep_diary_entries[0].sleep_diary_entries == 1:
                    sleep_entry = "Week 1 Day 1"
                    last_week = "1"
                    each_day_quote = "Keep up the good work!"

                if sleep_diary_entries[0].sleep_diary_entries == 2:
                    sleep_entry = "Week 1 Day 2"
                    last_week = "1"
                    each_day_quote = "Sleeping through the night is possible!"
                if sleep_diary_entries[0].sleep_diary_entries == 3:
                    sleep_entry = "Week 1 Day 3"
                    last_week = "1"
                    each_day_quote = "You can do this!"
                if sleep_diary_entries[0].sleep_diary_entries == 4:
                    sleep_entry = "Week 1 Day 4"
                    last_week = "1"
                    each_day_quote = "Insomnia is no match for you!"
                if sleep_diary_entries[0].sleep_diary_entries == 5:
                    sleep_entry = "Week 1 Day 5"
                    last_week = "1"
                    each_day_quote = "Sleep restrictions may be difficult but they are worth it!"
                if sleep_diary_entries[0].sleep_diary_entries == 6:
                    sleep_entry = "Week 1 Day 6"
                    last_week = "1"
                    each_day_quote = "You deserve a good night's sleep"
                if sleep_diary_entries[0].sleep_diary_entries == 7:
                    val = PatientEfficiency.objects.filter(patient_id=request.user.id).count()
                    if val == 1:
                        print("yes in this condition")
                        sleep_entry = "Week 1 Day 7"
                        last_week = "1"
                        each_day_quote = "Positive thoughts can make a world of difference for your sleep!"

                        rec = SendFax.objects.filter(patient_id = request.user.id, weekno = 1).exists()
                        if rec == True:
                            pass
                        else:
                            res = create_pdf_report_weekly_directly(request.user.id, 1)
                            if res == "success":
                                rec = SendFax.objects.get(patient_id = request.user.id)
                                rec.weekno = 1
                                rec.save()
                            else:
                                print("first week fax send failed")
                    else:
                        avgsleepefficieny(request.user.id)
                        sugges_wakeup_time(request.user.id)
                        sleep_entry = "Week 1 Day 7"
                        last_week = "1"
                        each_day_quote = "Positive thoughts can make a world of difference for your sleep!"
                if sleep_diary_entries[0].sleep_diary_entries == 8:
                    sleep_entry = "Week 2 Day 1"
                    last_week = "2"
                    each_day_quote = "Lock negative thoughts away in your NTL!"
                if sleep_diary_entries[0].sleep_diary_entries == 9:
                    sleep_entry = "Week 2 Day 2"
                    last_week = "2"
                    each_day_quote = "You have power over your thoughts"
                if sleep_diary_entries[0].sleep_diary_entries == 10:
                    sleep_entry = "Week 2 Day 3"
                    last_week = "2"
                    each_day_quote = "You are not alone in your fight against insomnia!"
                if sleep_diary_entries[0].sleep_diary_entries == 11:
                    sleep_entry = "Week 2 Day 4"
                    last_week = "2"
                    each_day_quote = "You've got this!"
                if sleep_diary_entries[0].sleep_diary_entries == 12:
                    sleep_entry = "Week 2 Day 5"
                    last_week = "2"
                    each_day_quote = "Tip: You can use your NTL during the day to lock negative thoughts away!"
                if sleep_diary_entries[0].sleep_diary_entries == 13:
                    sleep_entry = "Week 2 Day 6"
                    last_week = "2"
                    each_day_quote = "Don't give up!"
                if sleep_diary_entries[0].sleep_diary_entries == 14:
                    val = PatientEfficiency.objects.filter(patient_id=request.user.id).count()
                    if val == 2:
                        sleep_entry = "Week 2 Day 7"
                        last_week = "2"
                        each_day_quote = "Insomnia is tough but you're tougher"

                        rec = SendFax.objects.filter(patient_id=request.user.id, weekno=2).exists()
                        if rec == True:
                            pass
                        else:
                            res = create_pdf_report_weekly_directly(request.user.id, 2)
                            if res == "success":
                                rec = SendFax.objects.get(patient_id=request.user.id)
                                rec.weekno = 2
                                rec.save()
                            else:
                                print("second week fax send failed.")
                    else:
                        if not last_week:
                            avgsleepefficieny(request.user.id)
                            sugges_wakeup_time(request.user.id)
                        avgsleepefficieny(request.user.id)
                        sugges_wakeup_time(request.user.id)
                        sleep_entry = "Week 2 Day 7"
                        last_week = "2"
                        each_day_quote = "Insomnia is tough but you're tougher"
                if sleep_diary_entries[0].sleep_diary_entries == 15:
                    sleep_entry = "Week 3 Day 1"
                    last_week = "3"
                    each_day_quote = "Believe in yourself"
                if sleep_diary_entries[0].sleep_diary_entries == 16:
                    sleep_entry = "Week 3 Day 2"
                    last_week = "3"
                    each_day_quote = "Keep moving forward"
                if sleep_diary_entries[0].sleep_diary_entries == 17:
                    sleep_entry = "Week 3 Day 3"
                    last_week = "3"
                    each_day_quote = "Give yourself some credit for all you’ve done so far"
                if sleep_diary_entries[0].sleep_diary_entries == 18:
                    sleep_entry = "Week 3 Day 4"
                    last_week = "3"
                    each_day_quote = "Everyday is a new beginning"
                if sleep_diary_entries[0].sleep_diary_entries == 19:
                    sleep_entry = "Week 3 Day 5"
                    last_week = "3"
                    each_day_quote = "Staying positive can make all the difference"
                if sleep_diary_entries[0].sleep_diary_entries == 20:
                    sleep_entry = "Week 3 Day 6"
                    last_week = "3"
                    each_day_quote = "All progress is good progress"
                if sleep_diary_entries[0].sleep_diary_entries == 21:
                    val = PatientEfficiency.objects.filter(patient_id=request.user.id).count()
                    if val == 3:
                        sleep_entry = "Week 3 Day 7"
                        last_week = "3"
                        each_day_quote = "There is something good in every day"
                        rec = SendFax.objects.filter(patient_id=request.user.id, weekno=3).exists()
                        if rec == True:
                            pass
                        else:
                            res = create_pdf_report_weekly_directly(request.user.id, 3)
                            if res == "success":
                                rec = SendFax.objects.get(patient_id=request.user.id)
                                rec.weekno = 3
                                rec.save()
                            else:
                                print("third week fax send failed.")
                    else:
                        if not last_week:
                            avgsleepefficieny(request.user.id)
                            sugges_wakeup_time(request.user.id)
                        avgsleepefficieny(request.user.id)
                        sugges_wakeup_time(request.user.id)
                        sleep_entry = "Week 3 Day 7"
                        last_week = "3"
                        each_day_quote = "There is something good in every day"
                if sleep_diary_entries[0].sleep_diary_entries == 22:
                    sleep_entry = "Week 4 Day 1"
                    last_week = "4"
                    each_day_quote = "You are taking the right steps to get your sleep back on track!"
                if sleep_diary_entries[0].sleep_diary_entries == 23:
                    sleep_entry = "Week 4 Day 2"
                    last_week = "4"
                    each_day_quote = "You are on the road to overcoming insomnia"
                if sleep_diary_entries[0].sleep_diary_entries == 24:
                    sleep_entry = "Week 4 Day 3"
                    last_week = "4"
                    each_day_quote = "Restful sleep is just a nighttime away"
                if sleep_diary_entries[0].sleep_diary_entries == 25:
                    sleep_entry = "Week 4 Day 4"
                    last_week = "4"
                    each_day_quote = "Quality sleep will transform your life. Keep it up!"
                if sleep_diary_entries[0].sleep_diary_entries == 26:
                    sleep_entry = "Week 4 Day 5"
                    last_week = "4"
                    each_day_quote = "Learn to love your sleep again"
                if sleep_diary_entries[0].sleep_diary_entries == 27:
                    sleep_entry = "Week 4 Day 6"
                    last_week = "4"
                    each_day_quote = "Your life is about to become so much better"
                if sleep_diary_entries[0].sleep_diary_entries == 28:
                    val = PatientEfficiency.objects.filter(patient_id=request.user.id).count()
                    if val == 4:
                        sleep_entry = "Week 4 Day 7"
                        last_week = "4"
                        each_day_quote = "The time is right for overcoming insomnia"
                        rec = SendFax.objects.filter(patient_id=request.user.id, weekno=4).exists()
                        if rec == True:
                            pass
                        else:
                            res = create_pdf_report_weekly_directly(request.user.id, 4)
                            if res == "success":
                                rec = SendFax.objects.get(patient_id=request.user.id)
                                rec.weekno = 4
                                rec.save()
                            else:
                                print("fourth week fax send failed.")
                    else:
                        if not last_week:
                            avgsleepefficieny(request.user.id)
                            sugges_wakeup_time(request.user.id)

                        avgsleepefficieny(request.user.id)
                        sugges_wakeup_time(request.user.id)
                        sleep_entry = "Week 4 Day 7"
                        last_week = "4"
                        each_day_quote = "The time is right for overcoming insomnia"
                if sleep_diary_entries[0].sleep_diary_entries == 29:
                    sleep_entry = "Week 5 Day 1"
                    last_week = "5"
                    each_day_quote = "You're addressing your sleeplessness head-on. Way to go!"
                if sleep_diary_entries[0].sleep_diary_entries == 30:
                    sleep_entry = "Week 5 Day 2"
                    last_week = "5"
                    each_day_quote = "Overcoming sleeplessness is happening now!"
                if sleep_diary_entries[0].sleep_diary_entries == 31:
                    sleep_entry = "Week 5 Day 3"
                    last_week = "5"
                    each_day_quote = "Don't let insomnia drag you down! This is a fight you will win!"
                if sleep_diary_entries[0].sleep_diary_entries == 32:
                    sleep_entry = "Week 5 Day 4"
                    last_week = "5"
                    each_day_quote = "Love yourself enough to put your sleep health first"
                if sleep_diary_entries[0].sleep_diary_entries == 33:
                    sleep_entry = "Week 5 Day 5"
                    last_week = "5"
                    each_day_quote = "Self-care, self-value, and self-worth start with quality sleep"
                if sleep_diary_entries[0].sleep_diary_entries == 34:
                    sleep_entry = "Week 5 Day 6"
                    last_week = "5"
                    each_day_quote = "Sleep will help you become an even better version of yourself"
                if sleep_diary_entries[0].sleep_diary_entries == 35:
                    val = PatientEfficiency.objects.filter(patient_id=request.user.id).count()
                    if val == 5:
                        sleep_entry = "Week 5 Day 7"
                        last_week = "5"
                        each_day_quote = "We're rooting for you! You're not in this alone!"
                        rec = SendFax.objects.filter(patient_id=request.user.id, weekno=5).exists()
                        if rec == True:
                            pass
                        else:
                            res = create_pdf_report_weekly_directly(request.user.id, 5)
                            if res == "success":
                                rec = SendFax.objects.get(patient_id=request.user.id)
                                rec.weekno = 5
                                rec.save()
                            else:
                                print("fifth week fax send failed.")
                    else:
                        if not last_week:
                            avgsleepefficieny(request.user.id)
                            sugges_wakeup_time(request.user.id)
                        avgsleepefficieny(request.user.id)
                        sugges_wakeup_time(request.user.id)
                        sleep_entry = "Week 5 Day 7"
                        last_week = "5"
                        each_day_quote = "We're rooting for you! You're not in this alone!"
                if sleep_diary_entries[0].sleep_diary_entries == 36:
                    sleep_entry = "Week 6 Day 1"
                    last_week = "6"
                    each_day_quote = "Keep pushing forward. Quality sleep will happen"
                if sleep_diary_entries[0].sleep_diary_entries == 37:
                    sleep_entry = "Week 6 Day 2"
                    last_week = "6"
                    each_day_quote = "It's time to shape your destiny - and it starts with sleep!"
                if sleep_diary_entries[0].sleep_diary_entries == 38:
                    sleep_entry = "Week 6 Day 3"
                    last_week = "6"
                    each_day_quote = "Embrace sleep and the amazing life you're supposed to be living"
                if sleep_diary_entries[0].sleep_diary_entries == 39:
                    sleep_entry = "Week 6 Day 4"
                    last_week = "6"
                    each_day_quote = "Deep, revitalizing sleep awaits you"
                if sleep_diary_entries[0].sleep_diary_entries == 40:
                    sleep_entry = "Week 6 Day 5"
                    last_week = "6"
                    each_day_quote = "Quality sleep is possible"
                if sleep_diary_entries[0].sleep_diary_entries == 41:
                    sleep_entry = "Week 6 Day 6"
                    last_week = "6"
                    each_day_quote = "Live, breathe, and dream sleep"
                if sleep_diary_entries[0].sleep_diary_entries == 42:
                    val = PatientEfficiency.objects.filter(patient_id=request.user.id).count()
                    if val == 6:
                        sleep_entry = "Week 6 Day 7"
                        last_week = "6"
                        each_day_quote = "Stay strong and fight sleeplessness"
                        rec = SendFax.objects.filter(patient_id=request.user.id, weekno=6).exists()
                        if rec == True:
                            pass
                        else:
                            res = create_pdf_report_weekly_directly(request.user.id, 6)
                            if res == "success":
                                rec = SendFax.objects.get(patient_id=request.user.id)
                                rec.weekno = 6
                                rec.save()
                            else:
                                print("six week fax send failed.")
                    else:
                        if not last_week:
                            avgsleepefficieny(request.user.id)
                            sugges_wakeup_time(request.user.id)
                        avgsleepefficieny(request.user.id)
                        sugges_wakeup_time(request.user.id)
                        sleep_entry = "Week 6 Day 7"
                        last_week = "6"
                        each_day_quote = "Stay strong and fight sleeplessness"

                # now creat code to watch video (New Dashboard)
                if sleep_diary_entries[0].sleep_diary_entries == 0 and video_view_count == 1:
                    last_week = "1"
                if sleep_diary_entries[0].sleep_diary_entries == 0 and video_view_count == 0:
                    last_week = "0"
                    view = 1
                    video_view_count += 1
                    label_tag = "Complete Now"
                if sleep_diary_entries[0].sleep_diary_entries == 7 and video_view_count == 1:
                    view = 1
                    video_view_count += 1
                    label_tag = "Complete Now"
                if sleep_diary_entries[0].sleep_diary_entries == 7 and video_view_count == 2:
                    last_week = "2"
                if sleep_diary_entries[0].sleep_diary_entries == 7 and video_view_count == 1:
                    view = 1
                    video_view_count += 1
                    label_tag = "Complete Now"
                if sleep_diary_entries[0].sleep_diary_entries == 14 and video_view_count == 3:
                    last_week = "3"
                if sleep_diary_entries[0].sleep_diary_entries == 14 and video_view_count == 2:
                    view = 1
                    video_view_count += 1
                    label_tag = "Complete Now"
                if sleep_diary_entries[0].sleep_diary_entries == 21 and video_view_count == 4:
                    last_week = "4"
                if sleep_diary_entries[0].sleep_diary_entries == 21 and video_view_count == 3:
                    view = 1
                    video_view_count += 1
                    label_tag = "Complete Now"
                if sleep_diary_entries[0].sleep_diary_entries == 28 and video_view_count == 5:
                    last_week = "5"
                if sleep_diary_entries[0].sleep_diary_entries == 28 and video_view_count == 4:
                    view = 1
                    video_view_count += 1
                    label_tag = "Complete Now"
                if sleep_diary_entries[0].sleep_diary_entries == 35 and video_view_count == 6:
                    last_week = "6"
                if sleep_diary_entries[0].sleep_diary_entries == 35 and video_view_count == 5:
                    view = 1
                    video_view_count += 1
                    label_tag = "Complete Now"
                if sleep_diary_entries[0].sleep_diary_entries == 42 and video_view_count == 7:
                    last_week = "7"
                    view = 2
                    #lock_diary = 1

                if sleep_diary_entries[0].sleep_diary_entries == 42 and video_view_count == 6:
                    view = 1
                    video_view_count += 1
                    label_tag = "Complete Now"
                # for week-2
                if sleep_diary_entries[0].sleep_diary_entries == 7 and current_date == date_time_obj and video_view_count == 1:
                    view = 1
                    video_view_count += 1
                # for week-3
                if sleep_diary_entries[0].sleep_diary_entries == 14 and current_date == date_time_obj and video_view_count == 2:
                    view = 1
                    video_view_count += 1
                # for week-4
                if sleep_diary_entries[0].sleep_diary_entries == 21 and current_date == date_time_obj and video_view_count == 3:
                    view = 1
                    video_view_count += 1
                # for week-5
                if sleep_diary_entries[0].sleep_diary_entries == 28 and current_date == date_time_obj and video_view_count == 4:
                    view = 1
                    video_view_count += 1
                # for week-6
                if sleep_diary_entries[0].sleep_diary_entries == 35 and current_date == date_time_obj and video_view_count == 5:
                    view = 1
                    video_view_count += 1
                # for week-7
                if sleep_diary_entries[0].sleep_diary_entries == 42 and current_date == date_time_obj and video_view_count == 6:
                    view = 1
                    video_view_count += 1
                if PatientEfficiency.objects.filter(patient_id=request.user.id).exists():
                    data = PatientEfficiency.objects.filter(patient_id=request.user.id).order_by("-id")[0]
                    avgvalue = data.sleep_efficiency
                    preb_time = data.bed_time
                    s_time = data.sugg_wake_up
                    t1 = datetime.datetime.strptime(preb_time, ("%H:%M:%S"))
                    t2 = datetime.datetime.strptime(s_time, ("%H:%M:%S"))
                    tt1 = datetime.timedelta(hours=t1.hour, minutes=t1.minute).total_seconds()
                    t1s = datetime.timedelta(minutes=t1.minute).total_seconds()
                    s_time = round_time(s_time)
                    tt2 = datetime.timedelta(hours=t2.hour, minutes=t2.minute).total_seconds()
                    if tt1 > tt2:
                        df = tt1 - tt2
                        sdf = 3600 - t1s
                        ssdf = 43200 - (t1s + sdf)
                        if df < 19800:
                            xx = 19800 - df
                            x1 = t1 - datetime.timedelta(seconds=xx)
                            x1 = datetime.datetime.strftime(x1, '%H:%M:%S')
                            presbedtime = round_time(str(x1))
                        if df > 43200:
                            fdf = df - 23400
                            if fdf < 43200:
                                presbedtime = round_time(preb_time)
                            else:
                                xx = df - 19800
                                x1 = t1 - datetime.timedelta(seconds=xx)
                                x1 = x1 - datetime.timedelta(seconds=ssdf)
                                x1 = datetime.datetime.strftime(x1, '%H:%M:%S')
                                presbedtime = round_time(str(x1))
                        else:
                            presbedtime = round_time(preb_time)

                    if tt1 < tt2:
                        df = tt2 - tt1
                        if df < 19800:
                            xx = 19800 - df
                            x1 = t1 - datetime.timedelta(seconds=xx)
                            x1 = datetime.datetime.strftime(x1, '%H:%M:%S')
                            presbedtime = round_time(str(x1))
                        else:
                            presbedtime = round_time(preb_time)
                provider_data = profile(request.user.id)
                rest_day = [0,7,14,21,28,35,42]
                context = {
                    "title": _title,
                    "avgsleep": avgvalue,
                    "avgbedtime": presbedtime,
                    "sug_time": s_time,
                    "base_url": settings.BASE_URL,
                    "first_name": '',
                    'quote': each_day_quote,
                    #"lock_diary": lock_diary,
                    "entry": sleep_entry,
                    "rest_day": rest_day,
                    "week": reqWeeks,
                    "view": view,
                    "lweek": last_week,
                    "video_view": video_view_count,
                    "userdata": user_profile,
                    "loggedUser": loggedUser,
                    "patient": pid,
                    "today_date": current_date,
                    "isSleepDiaryData": isSleepDiaryData,
                    "sleepdiary_startDate": sleepdiary_dates[0].date,
                    "sleepdiary_endDate": sleepdiary_dates[1].date,
                    "sleep_diary_entries": sleep_diary_entries[0].sleep_diary_entries,
                    "Weeks": Weeks,
                    "days": days,
                    "user_name": user_name,
                    "user_image": user_image,
                    "role_id": request.user.role_id,
                    "label_data": label_tag,
                    "next_session_week": next_session_week,
                    "next_entry_date": date_time_obj,
                    "answer_videos": viewVideosResult[0].countvideos,
                    "provider_data":provider_data,
                    "ma":ma
                }

                return render(request, "dashboard.html", context)

        except Exception as e:
            print(e)
            return redirect('/')


def round_time(t):
    try:

        ts = datetime.datetime.strptime(t, '%H:%M:%S')
        period = timedelta(minutes=15)
        period_seconds = period.total_seconds()
        td = timedelta(hours=ts.hour, minutes=ts.minute)
        half_period_seconds = period_seconds / 2
        remainder = td.total_seconds() % period_seconds
        if remainder >= half_period_seconds:
            pres_time = timedelta(seconds=td.total_seconds() + (period_seconds - remainder))
        else:
            pres_time = timedelta(seconds=td.total_seconds() - remainder)
        ft = datetime.datetime.strptime(str(pres_time), "%H:%M:%S").time()
        return ft.strftime("%I:%M %p")
    except Exception as e:
        print(e)
        return redirect('/')

def provider_subscription_detail(request):
    user_name = ""
    user_image = ""
    user_access = ""
    try:
        user_profile = Provider.objects.get(user_id=request.user.id)
        user_name = user_profile.first_name + " " + user_profile.last_name
        user_image = user_profile.provider_image
        provider_access = Provider_Verification.objects.get(user_id=request.user.id)
        user_access = provider_access.user_position
        package = user_profile.provider_type
        if StripeCustomer.objects.filter(user_id=request.user.id).exists():
            sub_status = Provider.objects.get(user_id=request.user.id)
            sub_status = sub_status.subscription_status
            product = Product_detail.objects.get(product_name=package)


        else:
            return redirect('/')
    except StripeCustomer.DoesNotExist:
        print("Provider Subscription does not exist")
        return redirect('/')

    context = {

        'product': product,
        'status': sub_status,
        "user_name": user_name,
        "user_image": user_image,
        "role_id": 1,
        'user_access': user_access,

    }
    return render(request, "subscription_detail_provider.html", context)
def provider_invoice(request):
    user_name = ""
    user_image = ""
    user_access = ""
    try:
        mylist = []
        user_profile = Provider.objects.get(user_id=request.user.id)
        user_name = user_profile.first_name + " " + user_profile.last_name
        user_image = user_profile.provider_image
        provider_access = Provider_Verification.objects.get(user_id=request.user.id)
        user_access = provider_access.user_position
        if StripeCustomer.objects.filter(user_id=request.user.id).exists():
            sub_status = Provider.objects.get(user_id=request.user.id)
            sub_status = sub_status.subscription_status
            stripe_customer = StripeCustomer.objects.get(user_id=request.user.id)
            cus = stripe_customer.stripeCustomerId
            stripe.api_key = settings.STRIPE_SECRET_KEY
            subscription = stripe.Subscription.retrieve(stripe_customer.stripeSubscriptionId)
            product = stripe.Product.retrieve(subscription.plan.product)
            product_price = subscription.plan.amount_decimal[0:2]
            inv = stripe.Invoice.list(customer=cus)
            for i, item in enumerate(inv):
                d = {}
                inv_id = inv.data[i]['id']
                invoice_url = inv.data[i]['invoice_pdf']
                invoice_number = inv.data[i]['number']
                invoice_status = inv.data[i]['status']
                dat = inv.data[i]['created']
                date = datetime.datetime.fromtimestamp(dat)
                date = date.strftime("%m/%d/%Y")
                invoice_date = date
                d['invoice_url'] = invoice_url
                d['invoice_status'] = invoice_status
                d['invoice_date'] = invoice_date
                d['invoice_id'] = inv_id
                d['number']= invoice_number
                mylist.append(d)
        else:
            return redirect('/')
    except StripeCustomer.DoesNotExist:
        print("Provider Subscription does not exist")
        return redirect('/')

    context = {
        "user_name": user_name,
        "user_image": user_image,
        "userdata": user_profile,
        "role_id": request.user.role_id,
        'subscription': subscription,
        'product': product,
        'status': sub_status,
        'price': product_price,
        'invoice': mylist,
        'user_access': user_access,
        'total_invoice': len(mylist),


    }
    return render(request, "provider_invoice.html", context)
def avgsleepefficieny(userid):
    try:
        print("YOUR USER ID", userid)
        sleep_diary_entries = SleepDiary.objects.raw(
            "SELECT id,count(*) as sleep_diary_entries FROM dashboard_sleepdiary WHERE patient_id=%s and is_updated=1",
            [int(userid)])
        queryset = SleepDiary.objects.raw(
            "SELECT id,sleep_efficiency FROM dashboard_sleepdiary WHERE patient_id=%s and is_updated=1",
            [int(userid)])
        dayscount = int(sleep_diary_entries[0].sleep_diary_entries)
        print("days updated", dayscount)
        days = dayscount
        totallength = 0
        sleepefficiency = 0
        dataset = []
        for i in queryset:
            totallength += 1
            dataset.append(i.sleep_efficiency)
        for i in range(0, len(dataset)):
            dataset[i] = float(dataset[i])
        print(totallength)
        print(days)

        if days == 7:
            sumresult = sum(dataset[0:7])
            sleepefficiency = sumresult / 7
            sleepefficiency = (format(sleepefficiency, ".2f"))
            updatesleepefficieny(sleepefficiency, userid, '1')
        if days == 14:
            sumresult = sum(dataset[7:14])
            sleepefficiency = sumresult / 7
            sleepefficiency = (format(sleepefficiency, ".2f"))
            print("last week sleepefficiency", sleepefficiency)
            updatesleepefficieny(sleepefficiency, userid, '2')
        if days == 21:
            sumresult = sum(dataset[14:21])
            print("SE SUM", sumresult)
            sleepefficiency = sumresult / 7
            sleepefficiency = (format(sleepefficiency, ".2f"))
            updatesleepefficieny(sleepefficiency, userid, '3')
        if days == 28:
            sumresult = sum(dataset[21:28])
            sleepefficiency = sumresult / 7
            sleepefficiency = (format(sleepefficiency, ".2f"))
            updatesleepefficieny(sleepefficiency, userid, '4')
        if days == 35:
            print(dataset[28:35])
            sumresult = sum(dataset[28:35])
            sleepefficiency = sumresult / 7
            sleepefficiency = (format(sleepefficiency, ".2f"))
            updatesleepefficieny(sleepefficiency, userid, '5')
        if days == 42:
            sumresult = sum(dataset[35:42])
            print(sumresult)
            sleepefficiency = sumresult / 7
            sleepefficiency = (format(sleepefficiency, ".2f"))
            print(sleepefficiency)
            updatesleepefficieny(sleepefficiency, userid, '6')
    except Exception as e:
        print(e)
        return redirect('/')


def avgbedtime(userid, sea):
    print("SEA ", sea)
    try:
        sleep_diary_entries = SleepDiary.objects.raw(
            "SELECT id,count(*) as sleep_diary_entries FROM dashboard_sleepdiary WHERE patient_id=%s and is_updated=1",
            [int(userid)])
        '''queryset = SleepDiary.objects.raw(
            "SELECT id,total_gotup_time,total_sleep_time FROM dashboard_sleepdiary WHERE patient_id=%s and is_updated=1",
            [int(userid)])'''
        queryset = SleepDiary.objects.raw(
            "SELECT id,desire_wakeup_time,total_sleep_time FROM dashboard_sleepdiary WHERE patient_id=%s and is_updated=1",
            [int(userid)])
        dayscount = int(sleep_diary_entries[0].sleep_diary_entries)
        days = dayscount
        totallength = 0
        e_w_time = []
        avg_slp_time = []
        sleepminutes = []
        sleephour = []
        for i in queryset:
            totallength += 1
            time = i.desire_wakeup_time
            avg_time = i.total_sleep_time
            e_w_time.append(time)
            avg_slp_time.append(avg_time)
        for i in range(0, len(avg_slp_time)):
            avg_slp_time[i] = float(avg_slp_time[i])

        if days == 7:
            try:
                e_time = min(e_w_time[0:7])
                avg_sleep_time = sum(avg_slp_time[0:7])
                avg_sleep_time = avg_sleep_time / 7
                avg_sleep_time = str(avg_sleep_time).split(".")
                hour2 = int(avg_sleep_time[0])
                min2 = int(avg_sleep_time[1][0:2])
                min2 = int((min2 / 100) * 60)
                if hour2 < 0:
                    hour2 = 24 + hour2
                if hour2 > 24:
                    hour2 = hour2 - 24
                if hour2 == 24:
                    hour2 = 0
                if hour2 < 10 and hour2 >= 0:
                    hour2 = "0" + str(hour2)
                if min2 < 0:
                    min2 = 60 + min2
                if min2 < 10 and min2 >= 0:
                    min2 = "0" + str(min2)
                endtime = str(hour2) + ":" + str(min2) + ":" + "00"
                d1 = datetime.datetime.strptime(e_time, "%H:%M:%S")
                d2 = datetime.datetime.strptime(endtime, "%H:%M:%S")
                tt1 = datetime.timedelta(hours=d1.hour, minutes=d1.minute).total_seconds()
                tt2 = datetime.timedelta(hours=d2.hour, minutes=d2.minute).total_seconds()
                d3 = tt1 - tt2
                if d3 < 0:
                    d3 = 86400 + d3
                d3 = datetime.timedelta(seconds=d3)

                d3 = datetime.datetime.strptime(str(d3), "%H:%M:%S").time()
                d3 = d3.strftime("%H:%M:%S")
                print(d3)
                updatebasetime(d3, userid, "1")
                updatebedtime(d3, userid, "1")
            except Exception as e:
                print(e)
                return redirect('/')
        if days == 14:
            try:
                data = PatientEfficiency.objects.get(patient_id=userid, week_no="1")
                base_time_db = data.sugg_wake_up
                pres_time = data.bed_time
                print(base_time_db)
                e_time = min(e_w_time[7:14])
                print(e_time)
                if e_time == base_time_db:
                    print("Yes both same")
                    d1 = datetime.datetime.strptime(pres_time, "%H:%M:%S")
                    tt1 = datetime.timedelta(hours=d1.hour, minutes=d1.minute).total_seconds()
                    if sea == -15:
                        if tt1 < 900:
                            tt1 = 900 - tt1
                        else:
                            tt1 = tt1 - 900
                    if sea == 0:
                        tt1 = tt1
                    if sea == 15:
                        ts = tt1 + 900
                        if ts > 86400:
                            tt1 = ts - 86400
                        else:
                            tt1 = ts
                    d3 = tt1
                    d3 = datetime.timedelta(seconds=d3)
                    d3 = datetime.datetime.strptime(str(d3), "%H:%M:%S").time()
                    d3 = d3.strftime("%H:%M:%S")
                    updatebasetime(d3, userid, "2")
                    updatebedtime(d3, userid, "2")
                else:
                    print("both differnet")
                    avg_sleep_time = sum(avg_slp_time[7:14])
                    avg_sleep_time = avg_sleep_time / 7
                    avg_sleep_time = str(avg_sleep_time).split(".")
                    hour2 = int(avg_sleep_time[0])
                    min2 = int(avg_sleep_time[1][0:2])
                    min2 = int((min2 / 100) * 60)
                    if hour2 < 0:
                        hour2 = 24 + hour2
                    if hour2 > 24:
                        hour2 = hour2 - 24
                    if hour2 == 24:
                        hour2 = 0
                    if hour2 < 10 and hour2 >= 0:
                        hour2 = "0" + str(hour2)
                    if min2 < 0:
                        min2 = 60 + min2
                    if min2 < 10 and min2 >= 0:
                        min2 = "0" + str(min2)
                    endtime = str(hour2) + ":" + str(min2) + ":" + "00"
                    d1 = datetime.datetime.strptime(e_time, "%H:%M:%S")
                    d2 = datetime.datetime.strptime(endtime, "%H:%M:%S")
                    tt1 = datetime.timedelta(hours=d1.hour, minutes=d1.minute).total_seconds()
                    tt2 = datetime.timedelta(hours=d2.hour, minutes=d2.minute).total_seconds()
                    d3 = tt1 - tt2
                    print(d3)
                    if d3 < 0:
                        d3 = 86400 + d3
                    d3 = datetime.timedelta(seconds=d3)

                    d3 = datetime.datetime.strptime(str(d3), "%H:%M:%S").time()
                    d3 = d3.strftime("%H:%M:%S")
                    print(d3)
                    updatebasetime(d3, userid, "2")
                    updatebedtime(d3, userid, "2")

            except Exception as e:
                print(e)
                return redirect('/')

        if days == 21:
            try:
                data = PatientEfficiency.objects.get(patient_id=userid, week_no="2")
                base_time_db = data.sugg_wake_up
                pres_time = data.bed_time
                print(base_time_db)
                e_time = min(e_w_time[14:21])
                print(e_time)
                if e_time == base_time_db:
                    print("Yes both same")
                    d1 = datetime.datetime.strptime(pres_time, "%H:%M:%S")
                    tt1 = datetime.timedelta(hours=d1.hour, minutes=d1.minute).total_seconds()
                    if sea == -15:
                        if tt1 < 900:
                            tt1 = 900 - tt1
                        else:
                            tt1 = tt1 - 900
                    if sea == 0:
                        tt1 = tt1
                    if sea == 15:
                        ts = tt1 + 900
                        if ts > 86400:
                            tt1 = ts - 86400
                        else:
                            tt1 = ts
                    d3 = tt1
                    d3 = datetime.timedelta(seconds=d3)
                    d3 = datetime.datetime.strptime(str(d3), "%H:%M:%S").time()
                    d3 = d3.strftime("%H:%M:%S")
                    updatebasetime(d3, userid, "3")
                    updatebedtime(d3, userid, "3")
                else:
                    print("both differnet")
                    avg_sleep_time = sum(avg_slp_time[14:21])
                    avg_sleep_time = avg_sleep_time / 7
                    avg_sleep_time = str(avg_sleep_time).split(".")
                    hour2 = int(avg_sleep_time[0])
                    min2 = int(avg_sleep_time[1][0:2])
                    min2 = int((min2 / 100) * 60)
                    if hour2 < 0:
                        hour2 = 24 + hour2
                    if hour2 > 24:
                        hour2 = hour2 - 24
                    if hour2 == 24:
                        hour2 = 0
                    if hour2 < 10 and hour2 >= 0:
                        hour2 = "0" + str(hour2)
                    if min2 < 0:
                        min2 = 60 + min2
                    if min2 < 10 and min2 >= 0:
                        min2 = "0" + str(min2)
                    endtime = str(hour2) + ":" + str(min2) + ":" + "00"
                    d1 = datetime.datetime.strptime(e_time, "%H:%M:%S")
                    d2 = datetime.datetime.strptime(endtime, "%H:%M:%S")
                    tt1 = datetime.timedelta(hours=d1.hour, minutes=d1.minute).total_seconds()
                    tt2 = datetime.timedelta(hours=d2.hour, minutes=d2.minute).total_seconds()
                    d3 = tt1 - tt2
                    print(d3)
                    if d3 < 0:
                        d3 = 86400 + d3
                    d3 = datetime.timedelta(seconds=d3)

                    d3 = datetime.datetime.strptime(str(d3), "%H:%M:%S").time()
                    d3 = d3.strftime("%H:%M:%S")
                    print(d3)
                    updatebasetime(d3, userid, "3")
                    updatebedtime(d3, userid, "3")


            except Exception as e:
                print(e)
                return redirect('/')
        if days == 28:
            print("YES IN 28")
            try:
                data = PatientEfficiency.objects.get(patient_id=userid, week_no="3")
                base_time_db = data.sugg_wake_up
                pres_time = data.bed_time
                print(base_time_db)
                e_time = min(e_w_time[21:28])
                print(e_time)
                if e_time == base_time_db:
                    print("Yes both same")
                    d1 = datetime.datetime.strptime(pres_time, "%H:%M:%S")
                    tt1 = datetime.timedelta(hours=d1.hour, minutes=d1.minute).total_seconds()
                    if sea == -15:
                        if tt1 < 900:
                            tt1 = 900 - tt1
                        else:
                            tt1 = tt1 - 900
                    if sea == 0:
                        tt1 = tt1
                    if sea == 15:
                        ts = tt1 + 900
                        if ts > 86400:
                            tt1 = ts - 86400
                        else:
                            tt1 = ts
                    d3 = tt1
                    d3 = datetime.timedelta(seconds=d3)
                    d3 = datetime.datetime.strptime(str(d3), "%H:%M:%S").time()
                    d3 = d3.strftime("%H:%M:%S")
                    updatebasetime(d3, userid, "4")
                    updatebedtime(d3, userid, "4")
                else:
                    print("both differnet")
                    avg_sleep_time = sum(avg_slp_time[21:28])
                    avg_sleep_time = avg_sleep_time / 7
                    avg_sleep_time = str(avg_sleep_time).split(".")
                    hour2 = int(avg_sleep_time[0])
                    min2 = int(avg_sleep_time[1][0:2])
                    min2 = int((min2 / 100) * 60)
                    if hour2 < 0:
                        hour2 = 24 + hour2
                    if hour2 > 24:
                        hour2 = hour2 - 24
                    if hour2 == 24:
                        hour2 = 0
                    if hour2 < 10 and hour2 >= 0:
                        hour2 = "0" + str(hour2)
                    if min2 < 0:
                        min2 = 60 + min2
                    if min2 < 10 and min2 >= 0:
                        min2 = "0" + str(min2)
                    endtime = str(hour2) + ":" + str(min2) + ":" + "00"
                    d1 = datetime.datetime.strptime(e_time, "%H:%M:%S")
                    d2 = datetime.datetime.strptime(endtime, "%H:%M:%S")
                    tt1 = datetime.timedelta(hours=d1.hour, minutes=d1.minute).total_seconds()
                    tt2 = datetime.timedelta(hours=d2.hour, minutes=d2.minute).total_seconds()
                    d3 = tt1 - tt2
                    print(d3)
                    if d3 < 0:
                        d3 = 86400 + d3
                    d3 = datetime.timedelta(seconds=d3)

                    d3 = datetime.datetime.strptime(str(d3), "%H:%M:%S").time()
                    d3 = d3.strftime("%H:%M:%S")
                    print(d3)
                    updatebasetime(d3, userid, "4")
                    updatebedtime(d3, userid, "4")
            except Exception as e:
                print(e)
                return redirect('/')
        if days == 35:

            try:
                data = PatientEfficiency.objects.get(patient_id=userid, week_no="4")
                base_time_db = data.sugg_wake_up
                pres_time = data.bed_time
                print(base_time_db)
                e_time = min(e_w_time[28:35])
                print(e_time)
                if e_time == base_time_db:
                    print("Yes both same")
                    d1 = datetime.datetime.strptime(pres_time, "%H:%M:%S")
                    tt1 = datetime.timedelta(hours=d1.hour, minutes=d1.minute).total_seconds()
                    if sea == -15:
                        if tt1 < 900:
                            tt1 = 900 - tt1
                        else:
                            tt1 = tt1 - 900
                    if sea == 0:
                        tt1 = tt1
                    if sea == 15:
                        ts = tt1 + 900
                        if ts > 86400:
                            tt1 = ts - 86400
                        else:
                            tt1 = ts
                    d3 = tt1
                    d3 = datetime.timedelta(seconds=d3)
                    d3 = datetime.datetime.strptime(str(d3), "%H:%M:%S").time()
                    d3 = d3.strftime("%H:%M:%S")
                    updatebasetime(d3, userid, "5")
                    updatebedtime(d3, userid, "5")
                else:
                    print("both differnet")
                    avg_sleep_time = sum(avg_slp_time[28:35])
                    avg_sleep_time = avg_sleep_time / 7
                    avg_sleep_time = str(avg_sleep_time).split(".")
                    hour2 = int(avg_sleep_time[0])
                    min2 = int(avg_sleep_time[1][0:2])
                    min2 = int((min2 / 100) * 60)
                    if hour2 < 0:
                        hour2 = 24 + hour2
                    if hour2 > 24:
                        hour2 = hour2 - 24
                    if hour2 == 24:
                        hour2 = 0
                    if hour2 < 10 and hour2 >= 0:
                        hour2 = "0" + str(hour2)
                    if min2 < 0:
                        min2 = 60 + min2
                    if min2 < 10 and min2 >= 0:
                        min2 = "0" + str(min2)
                    endtime = str(hour2) + ":" + str(min2) + ":" + "00"
                    d1 = datetime.datetime.strptime(e_time, "%H:%M:%S")
                    d2 = datetime.datetime.strptime(endtime, "%H:%M:%S")
                    tt1 = datetime.timedelta(hours=d1.hour, minutes=d1.minute).total_seconds()
                    tt2 = datetime.timedelta(hours=d2.hour, minutes=d2.minute).total_seconds()
                    d3 = tt1 - tt2
                    print(d3)
                    if d3 < 0:
                        d3 = 86400 + d3
                    d3 = datetime.timedelta(seconds=d3)

                    d3 = datetime.datetime.strptime(str(d3), "%H:%M:%S").time()
                    d3 = d3.strftime("%H:%M:%S")
                    print(d3)
                    updatebasetime(d3, userid, "5")
                    updatebedtime(d3, userid, "5")
            except Exception as e:
                print(e)
                return redirect('/')
        if days == 42:
            try:
                data = PatientEfficiency.objects.get(patient_id=userid, week_no="5")
                base_time_db = data.sugg_wake_up
                pres_time = data.bed_time
                print(base_time_db)
                e_time = min(e_w_time[35:42])
                print(e_time)
                if e_time == base_time_db:
                    print("Yes both same")
                    d1 = datetime.datetime.strptime(pres_time, "%H:%M:%S")
                    tt1 = datetime.timedelta(hours=d1.hour, minutes=d1.minute).total_seconds()
                    if sea == -15:
                        if tt1 < 900:
                            tt1 = 900 - tt1
                        else:
                            tt1 = tt1 - 900
                    if sea == 0:
                        tt1 = tt1
                    if sea == 15:
                        ts = tt1 + 900
                        if ts > 86400:
                            tt1 = ts - 86400
                        else:
                            tt1 = ts
                    d3 = tt1
                    d3 = datetime.timedelta(seconds=d3)
                    d3 = datetime.datetime.strptime(str(d3), "%H:%M:%S").time()
                    d3 = d3.strftime("%H:%M:%S")
                    updatebasetime(d3, userid, "6")
                    updatebedtime(d3, userid, "6")
                else:
                    print("both differnet")
                    avg_sleep_time = sum(avg_slp_time[35:42])
                    avg_sleep_time = avg_sleep_time / 7
                    avg_sleep_time = str(avg_sleep_time).split(".")
                    hour2 = int(avg_sleep_time[0])
                    min2 = int(avg_sleep_time[1][0:2])
                    min2 = int((min2 / 100) * 60)
                    if hour2 < 0:
                        hour2 = 24 + hour2
                    if hour2 > 24:
                        hour2 = hour2 - 24
                    if hour2 == 24:
                        hour2 = 0
                    if hour2 < 10 and hour2 >= 0:
                        hour2 = "0" + str(hour2)
                    if min2 < 0:
                        min2 = 60 + min2
                    if min2 < 10 and min2 >= 0:
                        min2 = "0" + str(min2)
                    endtime = str(hour2) + ":" + str(min2) + ":" + "00"
                    d1 = datetime.datetime.strptime(e_time, "%H:%M:%S")
                    d2 = datetime.datetime.strptime(endtime, "%H:%M:%S")
                    tt1 = datetime.timedelta(hours=d1.hour, minutes=d1.minute).total_seconds()
                    tt2 = datetime.timedelta(hours=d2.hour, minutes=d2.minute).total_seconds()
                    d3 = tt1 - tt2
                    print(d3)
                    if d3 < 0:
                        d3 = 86400 + d3
                    d3 = datetime.timedelta(seconds=d3)

                    d3 = datetime.datetime.strptime(str(d3), "%H:%M:%S").time()
                    d3 = d3.strftime("%H:%M:%S")
                    print(d3)
                    updatebasetime(d3, userid, "6")
                    updatebedtime(d3, userid, "6")
            except Exception as e:
                print(e)
                return redirect('/')
    except Exception as e:
        print(e)
        return redirect('/')


def sugges_wakeup_time(userid):
    try:

        print("YOUR USER ID", userid)

        sleep_diary_entries = SleepDiary.objects.raw(
            "SELECT id,count(*) as sleep_diary_entries FROM dashboard_sleepdiary WHERE patient_id=%s and is_updated=1",
            [int(userid)])
        queryset = SleepDiary.objects.raw(
            "SELECT id,desire_wakeup_time FROM dashboard_sleepdiary WHERE patient_id=%s and is_updated=1",
            [int(userid)])
        dayscount = int(sleep_diary_entries[0].sleep_diary_entries)
        days = dayscount
        totallength = 0
        s_w_time = []
        for i in queryset:
            totallength += 1
            time = i.desire_wakeup_time
            s_w_time.append(time)
        if days == 7:
            try:
                s_time = min(s_w_time[0:7])
                updatewakeuptime(s_time, userid, 1)
            except Exception as e:
                print(e)
                return redirect('/')
        if days == 14:
            try:
                s_time = min(s_w_time[7:14])
                updatewakeuptime(s_time, userid, 2)
            except Exception as e:
                print(e)
                return redirect('/')
        if days == 21:
            try:
                s_time = min(s_w_time[14:21])
                updatewakeuptime(s_time, userid, 3)
            except Exception as e:
                print(e)
                return redirect('/')
        if days == 28:
            try:
                s_time = min(s_w_time[21:28])
                updatewakeuptime(s_time, userid, 4)
            except Exception as e:
                print(e)
                return redirect('/')
        if days == 35:
            try:
                s_time = min(s_w_time[28:35])
                updatewakeuptime(s_time, userid, 5)
            except Exception as e:
                print(e)
                return redirect('/')
        if days == 42:
            try:
                s_time = min(s_w_time[35:42])
                updatewakeuptime(s_time, userid, 6)
            except Exception as e:
                print(e)
                return redirect('/')

    except Exception as e:
        print(e)
        return redirect('/')


@login_required
def accountdetails(request, pid=0):

    user_name = ""
    user_image = ""
    provider = ""
    provider_rec = ""
    user_access = ""
    try:
        checkUser = request.user.id
        print(checkUser)
        if checkUser is None:
            return redirect('/')
        if pid > 0:
            checkUser = pid
        if request.user.role_id == 3:
            user_profile = Patient.objects.get(user_id=request.user.id)
            user_name = user_profile.first_name + " " + user_profile.last_name

        elif request.user.role_id == 2:
            user_profile = RefPatient.objects.get(user_id=request.user.id)
            user_name = user_profile.first_name + " " + user_profile.last_name
            user_profile = RefPatient.objects.get(user_id=request.user.id)
            provider = user_profile.provider_id[4::]
            provider_rec = Provider.objects.get(provider_ref=provider)
        elif request.user.role_id == 1:
            user_profile = Provider.objects.get(user_id=request.user.id)
            user_name = user_profile.first_name + " " + user_profile.last_name
            user_image = user_profile.provider_image
            provider_access = Provider_Verification.objects.get(user_id=request.user.id)
            user_access = provider_access.user_position

        userInfo = user_profile
        reqWeeks = 6
        #global lock_diary
        video_view_count = video_count(request.user.id)
        if request.user.role_id != 1:
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
        loggedUser = User.objects.get(id=request.user.id)

        if request.user.role_id == 1:
            loggedUser = User.objects.get(id=request.user.id)

            if user_profile:
                try:
                    user_ref_data_array = RefPatient.objects.filter(provider_id__icontains=request.user.id)
                    print("Provider ref: ", user_ref_data_array)
                except User.DoesNotExist:
                    print("User does not exist")

            context = {
                "title": _title,
                "base_url": settings.BASE_URL,
                "first_name": '',
                #"lock_diary": lock_diary,
                "video_view":video_view_count,
                "week": reqWeeks,
                "user_name": user_name,
                "user_image": user_image,
                "role_id": request.user.role_id,
                "userdata": user_profile,
                "loggedUser": loggedUser,
                "user_access": user_access,
                "user_ref_data_array": user_ref_data_array,

            }
            return render(request, "dashboard_account_details.html", context)

        # user_profile = PatientProfile.objects.get(patient_user_id=request.user.id)
        UsersleepData = SleepDiary.objects.filter(patient_id=request.user.id, is_updated=1)
        isSleepDiaryData = UsersleepData.count()

        sleepdiary_ids = SleepDiary.objects.raw(
            "SELECT id, max(id) lastid , min(id) as firstid FROM dashboard_sleepdiary WHERE patient_id=%s",
            [int(request.user.id)])

        sleepdiary_dates = SleepDiary.objects.raw(
            "SELECT id,date FROM dashboard_sleepdiary WHERE id IN(%s,%s)",
            [int(sleepdiary_ids[0].firstid), int(sleepdiary_ids[0].lastid)])
        avgvalue = "00.00"
        presbedtime = "--:-- --"
        s_time = "--:-- --"
        if PatientEfficiency.objects.filter(patient_id=request.user.id).exists():
            data = PatientEfficiency.objects.filter(patient_id=request.user.id).order_by("-id")[0]
            avgvalue = data.sleep_efficiency
            preb_time = data.bed_time
            s_time = data.sugg_wake_up
            t1 = datetime.datetime.strptime(preb_time, ("%H:%M:%S"))
            t2 = datetime.datetime.strptime(s_time, ("%H:%M:%S"))
            tt1 = datetime.timedelta(hours=t1.hour, minutes=t1.minute).total_seconds()
            t1s = datetime.timedelta(minutes=t1.minute).total_seconds()
            s_time = round_time(s_time)
            tt2 = datetime.timedelta(hours=t2.hour, minutes=t2.minute).total_seconds()
            if tt1 > tt2:
                df = tt1 - tt2
                sdf = 3600 - t1s
                ssdf = 43200 - (t1s + sdf)
                if df < 19800:
                    xx = 19800 - df
                    x1 = t1 - datetime.timedelta(seconds=xx)
                    x1 = datetime.datetime.strftime(x1, '%H:%M:%S')
                    presbedtime = round_time(str(x1))
                if df > 43200:
                    fdf = df - 23400
                    if fdf < 43200:
                        presbedtime = round_time(preb_time)
                    else:
                        xx = df - 19800
                        x1 = t1 - datetime.timedelta(seconds=xx)
                        x1 = x1 - datetime.timedelta(seconds=ssdf)
                        x1 = datetime.datetime.strftime(x1, '%H:%M:%S')
                        presbedtime = round_time(str(x1))
                else:
                    presbedtime = round_time(preb_time)

            if tt1 < tt2:
                df = tt2 - tt1
                if df < 19800:
                    xx = 19800 - df
                    x1 = t1 - datetime.timedelta(seconds=xx)
                    x1 = datetime.datetime.strftime(x1, '%H:%M:%S')
                    presbedtime = round_time(str(x1))
                else:
                    presbedtime = round_time(preb_time)

        context = {
            "title": _title,
            "avgsleep": avgvalue,
            "avgbedtime": presbedtime,
            "sug_time": s_time,
            "base_url": settings.BASE_URL,
            "first_name": '',
            #"lock_diary": lock_diary,
            "video_view":video_view_count,
            "week": reqWeeks,
            "provider": provider_rec,
            "userdata": user_profile,
            "loggedUser": loggedUser,
            "patient": pid,
            "user_name": user_name,
            "user_image":user_image,
            "role_id": request.user.role_id,
            "user_access": user_access,
            "isSleepDiaryData": isSleepDiaryData,
            "sleepdiary_startDate": sleepdiary_dates[0].date,
            "sleepdiary_endDate": sleepdiary_dates[1].date

        }

        return render(request, "dashboard_account_details.html", context)
    except Exception as e:
        print(e)
        return redirect('/')


def updatesleepefficieny(sleep_ef, userid, week):
    sef = float(sleep_ef)
    try:
        if PatientEfficiency.objects.filter(patient_id=userid, week_no=week).exists():
            print("YES IN IF")
            if sef < 85.00:
                print(sef)
                print("yes smaler than 85")
                avgbedtime(userid, 15)
            if sef >= 85 and sef < 90:
                print(sef)
                print("yes greter and equal than 85")
                avgbedtime(userid, 0)
            if sef >= 90:
                print(sef)
                print("yes greater or equal 90")
                avgbedtime(userid, -15)
            print("YES SAVE IN IF")
            data = PatientEfficiency.objects.get(patient_id=userid, week_no=week)
            data.sleep_efficiency = sleep_ef
            data.save()
        else:
            print("YES IN ELSE")
            if sef < 85.00:
                print(sef)
                print("yes smaler than 85")
                avgbedtime(userid, 15)
            if sef >= 85 and sef < 90:
                print(sef)
                print("yes greter and equal than 85")
                avgbedtime(userid, 0)
            if sef >= 90:
                print(sef)
                print("yes greater or equal 90")
                avgbedtime(userid, -15)
            print("YES SAVE IN ELSE")
            data = PatientEfficiency.objects.get(patient_id=userid, week_no=week)
            data.sleep_efficiency = sleep_ef
            data.save()
            print("record save successfully")
    except Exception as e:
        print(e)
        return redirect('/')


def updatebasetime(basetime, userid, week):
    try:
        if PatientEfficiency.objects.filter(patient_id=userid, week_no=week).exists():
            data = PatientEfficiency.objects.get(patient_id=userid, week_no=week)
            data.base_time = basetime
            data.save()
        else:
            data = PatientEfficiency(patient_id=userid, week_no=week, base_time=basetime)
            data.save()
            print("record save successfully")
    except Exception as e:
        print(e)
        return redirect('/')


def updatebedtime(bedtime, userid, week):
    try:
        if PatientEfficiency.objects.filter(patient_id=userid, week_no=week).exists():
            data = PatientEfficiency.objects.get(patient_id=userid, week_no=week)
            data.bed_time = bedtime
            data.save()
        else:
            data = PatientEfficiency(patient_id=userid, week_no=week, bed_time=bedtime)
            data.save()
            print("record save successfully")
    except Exception as e:
        print(e)
        return redirect('/')


def updatewakeuptime(wake_time, userid, week):
    try:
        if PatientEfficiency.objects.filter(patient_id=userid, week_no=week).exists():
            data = PatientEfficiency.objects.get(patient_id=userid, week_no=week)
            data.sugg_wake_up = wake_time
            data.save()
        else:
            data = PatientEfficiency(patient_id=userid, week_no=week, sugg_wake_up=wake_time)
            data.save()
            print("record save successfully")
    except Exception as e:
        print(e)
        return redirect('/')

@login_required
def accountdetailsbyprovider(request, pid):
    user_name = ""
    user_image = ""
    user_access = ""
    if request.user.role_id == 1:
        user_profile = Provider.objects.get(user_id=request.user.id)
        user_name = user_profile.first_name + " " + user_profile.last_name
        user_image = user_profile.provider_image
        provider_access = Provider_Verification.objects.get(user_id=request.user.id)
        user_access = provider_access.user_position
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

        context = {
            "title": _title,
            "base_url": settings.BASE_URL,
            "first_name": '',
            "email": email,
            "week": reqWeeks,
            "userdata": user_profile,
            "loggedUser": loggedUser,
            "patient": pid,
            "user_name": user_name,
            "user_image": user_image,
            "user_access": user_access,
            "role_id": request.user.role_id,
            "isSleepDiaryData": isSleepDiaryData,
            "sleepdiary_startDate": sleepdiary_dates[0].date,
            "sleepdiary_endDate": sleepdiary_dates[1].date

        }

        return render(request, "dashboard_account_details_by_provider.html", context)
    except Exception as e:
        print(e)
        return redirect('/')

@login_required
def dashboardPatient(request, pid):
    try:
        checkUser = request.user.id
        if checkUser is None:
            return redirect('/')
        valid_patient = 0
        try:
            # user_profile = RefPatient.objects.get(user_id=pid, provider_id=request.user.id)
            user_profile = RefPatient.objects.get(user_id=pid)
        except Exception:
            valid_patient = 1

        if valid_patient == 1:
            print("valid 1")
            return redirect("/")

        userInfo = user_profile
        reqWeeks = 6
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

        _title = "CogniSleep |  Patient-Dashboard"
        user_ref_data_array = []
        loggedUser = User.objects.get(id=request.user.id)

        if loggedUser.role_id == 1:

            context = {
                "title": _title,
                "base_url": settings.BASE_URL,
                "first_name": '',
                "week": reqWeeks,
                "userdata": user_profile,
                "loggedUser": loggedUser,
                "patient": pid,

            }
            if user_profile:
                return render(request, "provider_view_dashboard.html", context)
            else:
                return redirect('/')
        else:
            return redirect('/')
    except Exception as e:
        print(e)
        return redirect('/')
    # user_profile = PatientProfile.objects.get(patient_user_id=request.user.id)


def provider_card(request):
    user_access = ""
    try:
        checkUser = request.user.id
        if checkUser is None:
            return redirect('/')
        _title = "CogniSleep |  Cogni-Dashboard"
        loggedUser = User.objects.get(id=request.user.id)

        if loggedUser.role_id == 1:
            user_profile = Provider.objects.get(user_id=request.user.id)
            provider_access = Provider_Verification.objects.get(user_id=request.user.id)
            user_access = provider_access.user_position

            context = {
                "title": _title,
                "base_url": settings.BASE_URL,
                "first_name": '',
                "userdata": user_profile,
                "loggedUser": loggedUser,
                "user_access": user_access,

            }

            return render(request, "new_card.html", context)

        if request.user.role_id == 3:
            user_profile = Patient.objects.get(user_id=request.user.id)
        elif request.user.role_id == 2:
            user_profile = RefPatient.objects.get(user_id=request.user.id)

        context = {
            "title": _title,
            "base_url": settings.BASE_URL,
            "first_name": '',
            "userdata": user_profile,
            "loggedUser": loggedUser,

        }

        return render(request, "dashboard.html", context)
    except Exception as e:
        print(e)
        return redirect('/')


def daterange(date1, date2):
    try:
        for n in range(int((date2 - date1).days) + 1):
            yield date1 + timedelta(n)
    except Exception as e:
        print(e)
        return redirect('/')


def tutorials(request):
    try:
        _title = "CogniSleep |  Cogni-Dashboard"
        loggedUser = request.user.id
        if loggedUser is None:
            return redirect('/')
        context = {
            "title": _title,
            "base_url": settings.BASE_URL,
            "first_name": '',
            "loggedUser": loggedUser,
            "patient": 0,

        }

        return render(request, "tutorials.html", context)
    except Exception as e:
        print(e)
        return redirect('/')


def contactus(request):
    try:
        _title = "CogniSleep |  Cogni-Dashboard"
        loggedUser = request.user.id
        if loggedUser is None:
            return redirect('/')

        context = {
            "title": _title,
            "base_url": settings.BASE_URL,
            "first_name": '',
            "loggedUser": loggedUser,

        }

        return render(request, "contactus.html", context)
    except Exception as e:
        print(e)
        return redirect('/')


def progress(request, pid=0):
    user_name = ""
    user_image = ""
    ma = False
    try:

        checkUser = request.user.id
        if checkUser is None:
            return redirect('/')
        _title = "CogniSleep |  Cogni-Dashboard"
        if pid > 0:
            checkUser = pid
        loggedUser = User.objects.get(id=checkUser)
        if request.user.role_id == 3:
            user_profile = Patient.objects.get(user_id=request.user.id)
            user_name = user_profile.first_name + " " + user_profile.last_name

        elif request.user.role_id == 2:
            user_profile = RefPatient.objects.get(user_id=request.user.id)
            user_name = user_profile.first_name + " " + user_profile.last_name
        elif request.user.role_id == 1:
            user_profile = Provider.objects.get(user_id=request.user.id)
            user_name = user_profile.first_name + " " + user_profile.last_name
            user_image = user_profile.provider_image

        # print("Logged User: ", request.user.id)
        labels = ['Day 1', "Day 2", "Day 3", "Day 4", "Day 5", "Day 6", "Day 7"]
        default_items = [2, 4, 3, 2.5, 2.5, 1.5, 5.5]

        avgvalue = "00.00"
        presbedtime = "--:-- --"
        s_time = "--:-- --"
        if PatientEfficiency.objects.filter(patient_id=request.user.id).exists():
            data = PatientEfficiency.objects.filter(patient_id=request.user.id).order_by("-id")[0]
            avgvalue = data.sleep_efficiency
            preb_time = data.bed_time
            s_time = data.sugg_wake_up
            t1 = datetime.datetime.strptime(preb_time, ("%H:%M:%S"))
            t2 = datetime.datetime.strptime(s_time, ("%H:%M:%S"))
            tt1 = datetime.timedelta(hours=t1.hour, minutes=t1.minute).total_seconds()
            t1s = datetime.timedelta(minutes=t1.minute).total_seconds()
            s_time = round_time(s_time)
            tt2 = datetime.timedelta(hours=t2.hour, minutes=t2.minute).total_seconds()
            if tt1 > tt2:
                df = tt1 - tt2
                sdf = 3600 - t1s
                ssdf = 43200 - (t1s + sdf)
                if df < 19800:
                    xx = 19800 - df
                    x1 = t1 - datetime.timedelta(seconds=xx)
                    x1 = datetime.datetime.strftime(x1, '%H:%M:%S')
                    presbedtime = round_time(str(x1))
                if df > 43200:
                    fdf = df - 23400
                    if fdf < 43200:
                        presbedtime = round_time(preb_time)
                    else:
                        xx = df - 19800
                        x1 = t1 - datetime.timedelta(seconds=xx)
                        x1 = x1 - datetime.timedelta(seconds=ssdf)
                        x1 = datetime.datetime.strftime(x1, '%H:%M:%S')
                        presbedtime = round_time(str(x1))
                else:
                    presbedtime = round_time(preb_time)

            if tt1 < tt2:
                df = tt2 - tt1
                if df < 19800:
                    xx = 19800 - df
                    x1 = t1 - datetime.timedelta(seconds=xx)
                    x1 = datetime.datetime.strftime(x1, '%H:%M:%S')
                    presbedtime = round_time(str(x1))
                else:
                    presbedtime = round_time(preb_time)
        #global lock_diary
        video_view_count = video_count(request.user.id)
        context = {
            "title": _title,
            "avgsleep": avgvalue,
            "avgbedtime": presbedtime,
            "sug_time": s_time,
            #"lock_diary": lock_diary,
            "video_view":video_view_count,
            "base_url": settings.BASE_URL,
            "first_name": '',
            "userdata": user_profile,
            "user_name": user_name,
            "user_image": user_image,
            "role_id": request.user.role_id,
            "loggedUser": loggedUser,
            "labels": labels,
            "default": default_items,
            "patient": pid,
            "ma":ma

        }
        # print(context)
        return render(request, "progress.html", context)
    except Exception as e:
        print(e)
        return redirect('/')


def progress_byprovider(request, pid):
    user_name = ""
    user_image = ""
    user_access = ""
    try:
        print("YES INSIDE PROGRESS PROVIDER")
        _title = "CogniSleep |  Cogni-Dashboard"
        print(request.user.role_id)
        loggedUser = User.objects.get(id=pid)
        if request.user.role_id == 3:
            user_profile = Patient.objects.get(user_id=request.user.id)
            user_name = user_profile.first_name + " " + user_profile.last_name

        elif request.user.role_id == 2:
            user_profile = RefPatient.objects.get(user_id=request.user.id)
            user_name = user_profile.first_name + " " + user_profile.last_name
        elif request.user.role_id == 1:
            user_profile = Provider.objects.get(user_id=request.user.id)
            user_name = user_profile.first_name + " " + user_profile.last_name
            user_image = user_profile.provider_image
            provider_access = Provider_Verification.objects.get(user_id=request.user.id)
            user_access = provider_access.user_position
        elif request.user.role_id == 5:
            user_profile = Provider.objects.get(user_id=request.user.id)
            user_name = user_profile.first_name + " " + user_profile.last_name
            user_image = user_profile.provider_image
            provider_access = Provider_Verification.objects.get(user_id=request.user.id)
            user_access = provider_access.user_position

        # print("Logged User: ", request.user.id)
        labels = ['Day 1', "Day 2", "Day 3", "Day 4", "Day 5", "Day 6", "Day 7"]
        default_items = [2, 4, 3, 2.5, 2.5, 1.5, 5.5]

        context = {
            "title": _title,
            "base_url": settings.BASE_URL,
            "first_name": '',
            "userdata": user_profile,
            "loggedUser": loggedUser,
            "labels": labels,
            "user_image": user_image,
            "user_name": user_name,
            "role_id": request.user.role_id,
            "default": default_items,
            "user_access": user_access,
            "patient": pid,

        }
        # print(context)
        return render(request, "progress_byprovider.html", context)
    except Exception as e:
        print(e)
        return redirect('/')


def ntl(request, pid=0):
    user_name = ""
    user_image = ""
    ma = False
    try:
        checkUser = request.user.id
        if checkUser is None:
            return redirect('/')
        _title = "CogniSleep |  Cogni-NTL"
        if pid > 0:
            checkUser = pid
        loggedUser = User.objects.get(id=checkUser)
        if request.user.role_id == 3:
            user_profile = Patient.objects.get(user_id=request.user.id)
            user_name = user_profile.first_name + " " + user_profile.last_name

        elif request.user.role_id == 2:
            user_profile = RefPatient.objects.get(user_id=request.user.id)
            user_name = user_profile.first_name + " " + user_profile.last_name
        elif request.user.role_id == 1:
            user_profile = Provider.objects.get(user_id=request.user.id)
            user_name = user_profile.first_name + " " + user_profile.last_name
            user_image = user_profile.provider_image

        avgvalue = "00.00"
        presbedtime = "--:-- --"
        s_time = "--:-- --"
        if PatientEfficiency.objects.filter(patient_id=request.user.id).exists():
            data = PatientEfficiency.objects.filter(patient_id=request.user.id).order_by("-id")[0]
            avgvalue = data.sleep_efficiency
            preb_time = data.bed_time
            s_time = data.sugg_wake_up
            t1 = datetime.datetime.strptime(preb_time, ("%H:%M:%S"))
            t2 = datetime.datetime.strptime(s_time, ("%H:%M:%S"))
            tt1 = datetime.timedelta(hours=t1.hour, minutes=t1.minute).total_seconds()
            t1s = datetime.timedelta(minutes=t1.minute).total_seconds()
            s_time = round_time(s_time)
            tt2 = datetime.timedelta(hours=t2.hour, minutes=t2.minute).total_seconds()
            if tt1 > tt2:
                df = tt1 - tt2
                sdf = 3600 - t1s
                ssdf = 43200 - (t1s + sdf)
                if df < 19800:
                    xx = 19800 - df
                    x1 = t1 - datetime.timedelta(seconds=xx)
                    x1 = datetime.datetime.strftime(x1, '%H:%M:%S')
                    presbedtime = round_time(str(x1))
                if df > 43200:
                    fdf = df - 23400
                    if fdf < 43200:
                        presbedtime = round_time(preb_time)
                    else:
                        xx = df - 19800
                        x1 = t1 - datetime.timedelta(seconds=xx)
                        x1 = x1 - datetime.timedelta(seconds=ssdf)
                        x1 = datetime.datetime.strftime(x1, '%H:%M:%S')
                        presbedtime = round_time(str(x1))
                else:
                    presbedtime = round_time(preb_time)

            if tt1 < tt2:
                df = tt2 - tt1
                if df < 19800:
                    xx = 19800 - df
                    x1 = t1 - datetime.timedelta(seconds=xx)
                    x1 = datetime.datetime.strftime(x1, '%H:%M:%S')
                    presbedtime = round_time(str(x1))
                else:
                    presbedtime = round_time(preb_time)
        #global lock_diary
        video_view_count = video_count(request.user.id)
        ntl = 1
        context = {
            "title": _title,
            "avgsleep": avgvalue,
            "avgbedtime": presbedtime,
            "sug_time": s_time,
            #"lock_diary": lock_diary,
            "video_view":video_view_count,
            "base_url": settings.BASE_URL,
            "first_name": '',
            "user_name": user_name,
            "user_image": user_image,
            "role_id": request.user.role_id,
            "userdata": user_profile,
            "loggedUser": loggedUser,
            "patient": pid,
            "ntl":ntl,
            "ma":ma

        }
        # print(context)
        return render(request, "dashboard_locker.html", context)
    except Exception as e:
        print(e)
        return redirect('/')


def getVideoContent(vid):
    try:
        videoArr = {
            0: '<h3 class="dashboard-video-title">WELCOME TO COGNISLEEP!</h3>' + "<p>We are so glad you Joined our Cognisleep Insomnia Buster Program. Below is a Introduction Video that will Highlight what you will be"
               + "learning in this program.Click the Play Button to Begin</p>",

            1: '<h3 class="dashboard-video-title">Session ' + str(vid) + '</h3>'
               + '<p>Hello, welcome to the first video of your CogniSleep journey.</p>'
               + '<p>In this video we will discuss:</p>'
               + '<ul>'
               + '<li>The Stages of Sleep</li>'
               + '<li>Sleeping Pills</li>'
               + '<li>Stimulus Control </li>'
               + '<li>Your CogniSleep Diary </li>'
               + '</ul>'
            ,

            2: '<h3 class="dashboard-video-title">Session ' + str(vid) + '</h3>'
               + '<p>Welcome back! For the past week, you have been inputting your sleep data into the CogniSleep Diary. You will see your weekly progress on the CogniSleep Data Sheet.</p>'
               + '<p>This week we will look at:</p>'
               + '<ul>'
               + '<li>Your CogniSleep Diary Entries</li>'
               + '<li>Sleep Efficiency</li>'
               + '<li>Effects of Negative Thoughts on Sleep</li>'
               + '<li>The 20-Minute Rule – Get out of bed if you cannot sleep for more than 20-30 minutes</li>'
               + '<li>Negative Thoughts Lockbox</li>'
               + '</ul>'
            ,

            3: '<h3 class="dashboard-video-title">Session ' + str(vid) + '</h3>'
               + '<p>You’re doing a great job! This week we will:</p>'
               + '<ul>'
               + '<li>Compare your sleep efficiencies to see how you are doing with your sleep restrictions </li>'
               + '<li>Discuss Sleep-Friendly Lifestyle Changes'
               + '<ul>'
               + '<li>Role of Exercise in promoting sleep</li>'
               + '<li>Avoid Stimulants, like Alcohol, Nicotine, and Caffeine </li>'
               + '</ul>'
               + '</li>'
               + '<li>Effects of Negative Thoughts on Sleep</li>'
               + '<li>The 20-Minute Rule – Get out of bed if you cannot sleep for more than 20-30 minutes</li>'
               + '<li>Negative Thoughts Lockbox</li>'
               + '</ul>'
            ,

            4: '<h3 class="dashboard-video-title">Session ' + str(vid) + '</h3>'
               + '<p>Today we are going to:</p>'
               + '<ul>'
               + '<li>Revisit Sleep Restrictions </li>'
               + '<li>Exercise: When & How Much'
               + '<li>Food, Drink & Sleep'
               + '<ul>'
               + '<li>Make your Bedroom Sleep-Friendly</li>'
               + '<li>Avoid Stimulants, like Alcohol, Nicotine, and Caffeine </li>'
               + '</ul>'
               + '</li>'
               + '<li>Effects of Negative Thoughts on Sleep</li>'
               + '<li>The 20-Minute Rule – Get out of bed if you cannot sleep for more than 20-30 minutes</li>'
               + '<li>Negative Thoughts Lockbox</li>'
               + '</ul>'
            ,

            5: '<h3 class="dashboard-video-title">Session ' + str(vid) + '</h3>'
               + '<p>Today we are going to discuss:</p>'
               + '<ul>'
               + '<li>Negative Thoughts and Stressors</li>'
               + '<li>Cognitive Distortions</li>'
               + '<li>Review The Negative Thought Lockbox</li>'
               + '</ul>'
            ,

            6: '<h3 class="dashboard-video-title">Session ' + str(vid) + '</h3>'
               + '<p>Today we are going to discuss:</p>'
               + '<ul>'
               + '<li>Worrying  </li>'
               + '<li>Relaxation Techniques'
               + '<ul>'
               + '<li>Worries vs Positive Alternatives </li>'
               + '<li>Reverse Thinking Techniques</li>'
               + '</ul>'
               + '</li>'
               + '</ul>'
            ,
            7: '<h3 class="dashboard-video-title">Session ' + str(vid) + '</h3>'
               + '<p>Today we are going to discuss:</p>'
               + '<ul>'
               + '<li>Worrying  </li>'
               + '<li>Relaxation Techniques'
               + '<ul>'
               + '<li>Worries vs Positive Alternatives </li>'
               + '<li>Reverse Thinking Techniques</li>'
               + '</ul>'
               + '</li>'
               + '</ul>'
            ,

        }

        return videoArr[int(vid)]

    except Exception as e:
        print(e)
        return redirect('/')


def videos(request, vid, pid=0):
    user_name = ""
    user_image = ""
    ma = False
    try:
        _title = "CogniSleep |  Cogni-Dashboard"
        bedtime_array = []
        user = request.user.id
        print("Yes you are here in videos")

        if user is None:
            return redirect('/')
        if pid != 0:
            valid_patient = 0
            try:
                user_profile = RefPatient.objects.get(provider_id=user, user_id=pid)
            except Exception:
                valid_patient = 1

            if valid_patient == 1:
                return redirect("/dashboard")

            user = pid

        weeks = []
        weekMsg = None
        weekVideo = 1
        week_counter = 0
        week_day = 0
        week_days_array = []
        invoice_for_today = SleepDiary.objects.raw(
            "SELECT * FROM dashboard_sleepdiary where patient_id=%s and time_went_to_bed!='' and time_fell_asleep!='' and time_got_up!='' ",
            [str(user)])

        for value in invoice_for_today:
            total_percent_sleep = get_user_progress_bar_avg(value.time_went_to_bed, value.time_fell_asleep,
                                                            value.time_got_up,
                                                            value.no_of_times_awakend, value.date)
            bedtime_array.append(total_percent_sleep)

        for value in bedtime_array:

            if week_counter == 6:
                result = {"weekday": week_day, "avg_data": value, }
                weeks.append(result)
                week_counter = 0
                week_day += 1
                weekVideo += 1
                week_days_array = []
            else:
                week_days_array.append(value)
                week_counter += 1
        # if(weekVideo > 1):
        #    weekVideo += 1

        loggedUser = User.objects.get(id=user)

        reqWeeks = 6
        if request.user.role_id != 1:
            if request.user.role_id == 3:
                user_profile = Patient.objects.get(user_id=request.user.id)
                user_name = user_profile.first_name + " " + user_profile.last_name

            elif request.user.role_id == 2:
                user_profile = RefPatient.objects.get(user_id=request.user.id)
                user_name = user_profile.first_name + " " + user_profile.last_name
            elif request.user.role_id == 1:
                user_profile = Provider.objects.get(user_id=request.user.id)
                user_name = user_profile.first_name + " " + user_profile.last_name
                user_image = user_profile.provider_image
            loggedUser = request.user.id
            userInfo = user_profile
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
        reqWeeks = 6
        video_array = []

        print(vid)
        print(weekVideo)
        if (int(vid)) > (weekVideo):
            return redirect('/dashboard/videos/0')

        video_array = VideoSessions.objects.all()
        video_content = VideoSessions.objects.get(id=vid)
        if (vid >= 0):
            video_questions = VideoQuestions.objects.filter(video_sessions_id=vid)
        else:
            video_questions = {}

        existVCompleted = VideoSessionsCompleted.objects.filter(patient_id=request.user.id).count()
        if existVCompleted > 0:
            is_videos_compelted = 1;
        else:
            is_videos_compelted = 0;
        l1 = []
        try:
            efficiency = PatientEfficiency.objects.filter(patient_id=request.user.id).order_by('week_no').values()
            for i in efficiency:
                l1.append(i['sleep_efficiency'])

        except Exception as e:
            print(e)

        avgvalue = "00.00"
        presbedtime = "--:-- --"
        s_time = "--:-- --"
        if PatientEfficiency.objects.filter(patient_id=request.user.id).exists():
            data = PatientEfficiency.objects.filter(patient_id=request.user.id).order_by("-id")[0]
            avgvalue = data.sleep_efficiency
            preb_time = data.bed_time
            s_time = data.sugg_wake_up
            t1 = datetime.datetime.strptime(preb_time, ("%H:%M:%S"))
            t2 = datetime.datetime.strptime(s_time, ("%H:%M:%S"))
            tt1 = datetime.timedelta(hours=t1.hour, minutes=t1.minute).total_seconds()
            t1s = datetime.timedelta(minutes=t1.minute).total_seconds()
            s_time = round_time(s_time)
            tt2 = datetime.timedelta(hours=t2.hour, minutes=t2.minute).total_seconds()
            if tt1 > tt2:
                df = tt1 - tt2
                sdf = 3600 - t1s
                ssdf = 43200 - (t1s + sdf)
                if df < 19800:
                    xx = 19800 - df
                    x1 = t1 - datetime.timedelta(seconds=xx)
                    x1 = datetime.datetime.strftime(x1, '%H:%M:%S')
                    presbedtime = round_time(str(x1))
                if df > 43200:
                    fdf = df - 23400
                    if fdf < 43200:
                        presbedtime = round_time(preb_time)
                    else:
                        xx = df - 19800
                        x1 = t1 - datetime.timedelta(seconds=xx)
                        x1 = x1 - datetime.timedelta(seconds=ssdf)
                        x1 = datetime.datetime.strftime(x1, '%H:%M:%S')
                        presbedtime = round_time(str(x1))
                else:
                    presbedtime = round_time(preb_time)

            if tt1 < tt2:
                df = tt2 - tt1
                if df < 19800:
                    xx = 19800 - df
                    x1 = t1 - datetime.timedelta(seconds=xx)
                    x1 = datetime.datetime.strftime(x1, '%H:%M:%S')
                    presbedtime = round_time(str(x1))
                else:
                    presbedtime = round_time(preb_time)
        #global lock_diary
        video_view_count = video_count(request.user.id)
        context = {
            "title": _title,
            "avgsleep": avgvalue,
            "avgbedtime": presbedtime,
            "sug_time": s_time,
            #"lock_diary": lock_diary,
            "video_view":video_view_count,
            "base_url": settings.BASE_URL,
            "first_name": '',
            "weeks": reqWeeks,
            "weekMsg": weekMsg,
            "weekVideo": weekVideo,
            "userdata": user_profile,
            "loggedUser": loggedUser,
            "videos": video_array,
            "se": l1,
            "user_name":user_name,
            "user_image": user_image,
            "role_id": request.user.role_id,
            "video_content": video_content,
            "video_questions": video_questions,
            "current_video_id": vid,
            "patient": pid,
            "all_video_compeleted": is_videos_compelted,
            "ma":ma

        }

        return render(request, "dashboard_videos_tabs.html", context)
    except Exception as e:
        print(e)
        return redirect('/')


def convert24(str1):
    # Checking if last two elements of time
    # is AM and first two elements are 12
    try:
        if str1[-2:] == "AM" and str1[:2] == "12":
            return "00" + str1[2:-2]

            # remove the AM
        elif str1[-2:] == "AM":
            return str1[:-2]

            # Checking if last two elements of time
        # is PM and first two elements are 12
        elif str1[-2:] == "PM" and str1[:2] == "12":
            return str1[:-2]

        else:
            # add 12 to hours and remove PM
            return str(int(str1[:2]) + 12) + str1[2:8]

    except Exception as e:
        print(e)
        return redirect('/')


def get_week_days(start_dt, end_dt):
    try:
        num_days = (end_dt - start_dt).days + 1
        num_weeks = (num_days) // 7
        a = 0
        # condition 1
        if end_dt.strftime('%a') == 'Sat':

            if start_dt.strftime('%a') != 'Sun':
                a = 1
        # condition 2

        if start_dt.strftime('%a') == 'Sun':

            if end_dt.strftime('%a') != 'Sat':
                a = 1
            # condition 3

        if end_dt.strftime('%a') == 'Sun':
            if start_dt.strftime('%a') not in ('Mon', 'Sun'):
                a = 2
            # condition 4
        if start_dt.weekday() not in (0, 6):

            if (start_dt.weekday() - end_dt.weekday()) >= 2:
                a = 2
            working_days = num_days - (num_weeks * 2) - a

            return working_days
    except Exception as e:
        print(e)
        return redirect('/')


def diary(request, wday, pid=0):
    user_name = ""
    user_image = ""
    ma = False
    try:
        userID = request.user.id

        if userID is None:
            return redirect('/')
        if pid != 0:
            valid_patient = 0
            try:
                userInfo = RefPatient.objects.get(doctor_ref_number=userID, user_id=pid)
            except Exception:
                valid_patient = 1

            if valid_patient == 1:
                return redirect("/dashboard")

            userID = pid


        if request.user.role_id == 3:
            userInfo = Patient.objects.get(user_id=userID)
            user_name = userInfo.first_name + " " + userInfo.last_name
        elif request.user.role_id == 2:
            userInfo = RefPatient.objects.get(user_id=userID)
            user_name = userInfo.first_name + " " + userInfo.last_name

        UsersleepData = SleepDiary.objects.filter(patient_id=userID)

        print("UserData: ", UsersleepData.count())

        bed_time = "00:00"
        reqWeeks = 6
        if userInfo.package_no == 'PRIMARY CARE SUBSCRIPTION':
            reqWeeks = 6
        elif userInfo.package_no == 'REFERRAL SUBSCRIPTION FROM PHYSICIAN/PROVIDER':
            reqWeeks = 6
        elif userInfo.package_no == 'COGNISLEEP INTENSE LEARNERS':
            reqWeeks = 8
        elif userInfo.package_no == 'COGNISLEEP TRADITIONAL':
            reqWeeks = 12
        elif userInfo.package_no == 'COGNISLEEP PLUS':
            reqWeeks = 15
        else:
            reqWeeks = 6

        no_of_days = reqWeeks * 7
        week_day = wday

        bedtime_array = []
        weekDates_array = []
        weekDay_array = []
        weekDays_array = []

        today = datetime.datetime.now().date()

        if week_day == 0:
            start = userInfo.timestamp.date() + timedelta(days=1)
        else:
            start = userInfo.timestamp.date() + timedelta(days=week_day * 7 + 1)
        end = start + timedelta(days=7 - 1)
        end__ = userInfo.timestamp.date() + timedelta(days=7)

        start_date = datetime.date(start.year, start.month, start.day)
        end_date = datetime.date(end.year, end.month, end.day)

        invoice_for_today = SleepDiary.objects.raw(
            "SELECT * FROM dashboard_sleepdiary where patient_id=%s and date BETWEEN %s and %s",
            [str(userID), start_date, end_date])
        get_oldBedTimes = SleepDiary.objects.raw(
            "SELECT * FROM dashboard_sleepdiary where patient_id=%s and time_went_to_bed!=''  ",
            [str(userID)])

        user_date_array = []

        for dt in daterange(start, end):
            weekDates_array.append(dt.strftime("%Y/%m/%d"))
            if dt.weekday() == 0:
                weekDay_array.append(dt.strftime("%Y/%m/%d"))

        _title = "CogniSleep |  Cogni-Dashboard"
        loggedUser = userID

        weekday = []

        x = 1
        for week in weekDates_array:

            if x <= 8:
                week_array = {
                    "x": x,
                    "week_date": week,

                }
                weekday.append(week_array)
                x += 1

        for x in range(1, reqWeeks + 1):

            if int(x) == week_day:

                if PatientEfficiency.objects.filter(patient_id=userID, week_no=x).exists():
                    data = PatientEfficiency.objects.get(patient_id=userID, week_no=x)
                    week_array = {
                        "x": x,
                        "week_date": week,
                        "is_selected": 1,
                        "eff": data.sleep_efficiency
                    }
                    weekDays_array.append(week_array)
                else:
                    week_array = {
                        "x": x,
                        "week_date": week,
                        "is_selected": 1,
                        "eff": ""
                    }
                    weekDays_array.append(week_array)
            else:

                if PatientEfficiency.objects.filter(patient_id=userID, week_no=x).exists():
                    data = PatientEfficiency.objects.get(patient_id=userID, week_no=x)
                    week_array = {
                        "x": x,
                        "week_date": week,
                        "is_selected": 0,
                        "eff": data.sleep_efficiency
                    }
                    weekDays_array.append(week_array)
                else:
                    week_array = {
                        "x": x,
                        "week_date": week,
                        "is_selected": 0,
                        "eff": ""
                    }
                    weekDays_array.append(week_array)

        # print(weekDays_array)

        #global lock_diary
        video_view_count = video_count(request.user.id)
        wokeuptime = ""
        gotuptime = ""
        outofbed = ""
        nextDate = SleepDiary.objects.raw(
            "SELECT id,date as sleep_diary_entries FROM dashboard_sleepdiary WHERE patient_id=%s and is_updated=0 limit 1",
            [int(request.user.id)])

        if request.method == 'POST':
            print("Yes POST METHOD")
            if request.user.role_id == 3:
                curUserID = Patient.objects.get(user_id=request.user.id)
            elif request.user.role_id == 2:
                curUserID = RefPatient.objects.get(user_id=request.user.id)
            elif request.user.role_id == 1:
                curUserID = RefPatient.objects.get(user_id=request.user.id)

            if request.user.role_id == 1:
                return redirect("/dashboard/")
            # print(request.get_full_path())
            # print(request.POST)

            form = SleepDiaruForm(request.POST)
            print(form.errors)
            print("validating form")
            if form.is_valid():
                print("YES FORM IS VALID")
                print(request.POST)
                print(request.POST.get('sdate'))
                date_time_obj1 = datetime.datetime.strptime(str(nextDate[0].sleep_diary_entries), '%Y-%m-%d')
                print(date_time_obj1)
                # sleepData = SleepDiary.objects.filter(date=request.POST.get('sdate'), patient_id=request.user.id)
                sleepData = SleepDiary.objects.filter(date=date_time_obj1, patient_id=request.user.id)
                # print(date_time_obj1)
                print("sleep diary data count:", sleepData.count())
                sleepdur_id = sleepData.get().id
                if sleepData.count() > 0 and sleepData.get().is_updated == 1:
                    messages.error(request, "Date already exist.")
                    # print("Date already exist.")
                    avgvalue = "00.00"
                    presbedtime = "--:-- --"
                    s_time = "--:-- --"
                    if PatientEfficiency.objects.filter(patient_id=request.user.id).exists():
                        data = PatientEfficiency.objects.filter(patient_id=request.user.id).order_by("-id")[0]
                        avgvalue = data.sleep_efficiency
                        preb_time = data.bed_time
                        s_time = data.sugg_wake_up
                        t1 = datetime.datetime.strptime(preb_time, ("%H:%M:%S"))
                        t2 = datetime.datetime.strptime(s_time, ("%H:%M:%S"))
                        tt1 = datetime.timedelta(hours=t1.hour, minutes=t1.minute).total_seconds()
                        t1s = datetime.timedelta(minutes=t1.minute).total_seconds()
                        s_time = round_time(s_time)
                        tt2 = datetime.timedelta(hours=t2.hour, minutes=t2.minute).total_seconds()
                        if tt1 > tt2:
                            df = tt1 - tt2
                            sdf = 3600 - t1s
                            ssdf = 43200 - (t1s + sdf)
                            if df < 19800:
                                xx = 19800 - df
                                x1 = t1 - datetime.timedelta(seconds=xx)
                                x1 = datetime.datetime.strftime(x1, '%H:%M:%S')
                                presbedtime = round_time(str(x1))
                            if df > 43200:
                                fdf = df - 23400
                                if fdf < 43200:
                                    presbedtime = round_time(preb_time)
                                else:
                                    xx = df - 19800
                                    x1 = t1 - datetime.timedelta(seconds=xx)
                                    x1 = x1 - datetime.timedelta(seconds=ssdf)
                                    x1 = datetime.datetime.strftime(x1, '%H:%M:%S')
                                    presbedtime = round_time(str(x1))
                            else:
                                presbedtime = round_time(preb_time)

                        if tt1 < tt2:
                            df = tt2 - tt1
                            if df < 19800:
                                xx = 19800 - df
                                x1 = t1 - datetime.timedelta(seconds=xx)
                                x1 = datetime.datetime.strftime(x1, '%H:%M:%S')
                                presbedtime = round_time(str(x1))
                            else:
                                presbedtime = round_time(preb_time)
                    context = {
                        "title": _title,
                        "avgsleep": avgvalue,
                        "avgbedtime": presbedtime,
                        "sug_time": s_time,
                        #"lock_diary": lock_diary,
                        "video_view":video_view_count,
                        "base_url": settings.BASE_URL,
                        "first_name": '',
                        "loggedUser": loggedUser,
                        "form": form,
                        "tags": "dairy",
                        "patient": pid,
                        "user_name": user_name,
                        "user_image": user_image,
                        "role_id": request.user.role_id,
                        "weekDay_array": weekday,
                        "current_week": wday,
                        "weekDays_array": weekDays_array,
                        'start_date': datetime.date.strftime(date_time_obj1, "%Y-%m-%d")
                    }
                    return render(request, "sleepdiary.html", context)
                else:
                    try:
                        print("yes yes yes")
                        a1 = request.POST.get('awakeduringnight')
                        if a1 != "":
                            awakeduringnight = hourtomin(a1)
                        else:
                            awakeduringnight = a1
                        a2 = request.POST.get('awaketooearly')
                        if a2 != "":
                            awaketooearly = hourtomin(a2)
                        else:
                            awaketooearly = a2
                        a3 = request.POST.get('problemfallingasleep')
                        if a3 != "":
                            problemfallingasleep = hourtomin(a3)
                        else:
                            problemfallingasleep = a3
                        a4 = request.POST.get('delayedgettingup')
                        if a4 != "":
                            delayedgettingup = hourtomin(a4)
                        else:
                            delayedgettingup = a4
                    except Exception as e:
                        print(e)

                    tempdate = SleepDiary.objects.get(id=sleepdur_id)
                    print("Yes Updated")
                    tempdate.date = date_time_obj1  # request.POST.get('sdate')
                    tempdate.time_in_bed = request.POST.get('timeinbed')
                    # tempdate.time_in_bed = totalbed_time
                    tempdate.total_sleep_time = request.POST.get('totalsleeptime')
                    # tempdate.total_sleep_time = totalsleep_time
                    tempdate.sleep_efficiency = request.POST.get('sleepefficiency')
                    tempdate.comment = request.POST.get('comment')
                    # tempdate.sleep_efficiency = sleep_eff_final
                    tempdate.problem_falling_asleep = problemfallingasleep  # request.POST.get('problemfallingasleep')
                    tempdate.awake_during_night = awakeduringnight  # request.POST.get('awakeduringnight')
                    tempdate.awake_too_early = awaketooearly  # request.POST.get('awaketooearly')
                    tempdate.delayed_getting_up = delayedgettingup  # request.POST.get('delayedgettingup')
                    tempdate.overslept = request.POST.get('overslept')
                    tempdate.time_went_to_bed = form.cleaned_data['time_went_to_bed'] + ":00"
                    tempdate.lights_out = form.cleaned_data['lights_out'] + ":00"
                    if form.cleaned_data['minutes_fall_asleep'] == "":
                        tempdate.minutes_fall_asleep = "0"
                    else:
                        tempdate.minutes_fall_asleep = form.cleaned_data['minutes_fall_asleep']
                    tempdate.time_fell_asleep = request.POST.get('totalsleep') + ":00"
                    tempdate.time_got_up = form.cleaned_data['time_got_up'] + ":00"
                    # tempdate.time_got_up = wokeuptime
                    tempdate.out_of_bed = form.cleaned_data['out_of_bed'] + ":00"
                    # tempdate.out_of_bed = outofbed
                    if form.cleaned_data['minutes_fellback_sleep'] == "":
                        tempdate.minutes_fellback_sleep = "0"
                    else:
                        tempdate.minutes_fellback_sleep = form.cleaned_data['minutes_fellback_sleep']
                    tempdate.desire_wakeup_time = form.cleaned_data['desire_wakeup_time'] + ":00"
                    # tempdate.nap_time_asleep = form.cleaned_data['nap_time_asleep'] + ":00"
                    if form.cleaned_data['number_of_naps'] == "":
                        tempdate.number_of_naps = "0"
                    else:
                        tempdate.number_of_naps = form.cleaned_data['number_of_naps']
                    if form.cleaned_data['totlatime_napping_minutes'] == "":
                        tempdate.totlatime_napping_minutes = "0"
                    else:
                        tempdate.totlatime_napping_minutes = form.cleaned_data['totlatime_napping_minutes']
                    if form.cleaned_data['no_of_times_awakend'] == "":
                        tempdate.no_of_times_awakend = "0"
                    else:
                        tempdate.no_of_times_awakend = form.cleaned_data['no_of_times_awakend']
                    if form.cleaned_data['total_time_awakened'] == "":
                        tempdate.total_time_awakened = "0"
                    else:
                        tempdate.total_time_awakened = form.cleaned_data['total_time_awakened']
                    tempdate.total_gotup_time = request.POST.get('totalgotup') + ":00"
                    # tempdate.total_gotup_time = outofbed
                    tempdate.day_avg = day_avg(request.POST.get('totalsleep'), request.POST.get('totalgotup'),
                                               form.cleaned_data['time_went_to_bed'])

                    tempdate.is_updated = 1
                    tempdate.save()
                    logdata = Logfile(user_id = request.user.id, sleep_diary_date = date_time_obj1 ,patient_id = request.user.id,user_type = "Patient")
                    logdata.save();

                    # print("Date saved")
                    form = SleepDiaruForm()
                    date_time_obj1 = datetime.datetime.strptime(str(nextDate[0].sleep_diary_entries), '%Y-%m-%d')
                    date_time_obj = datetime.date.strftime(date_time_obj1, "%m/%d/%Y")

                    form.fields["date"].initial = date_time_obj
                    avgvalue = "00.00"
                    presbedtime = "--:-- --"
                    s_time = "--:-- --"
                    if PatientEfficiency.objects.filter(patient_id=request.user.id).exists():
                        data = PatientEfficiency.objects.filter(patient_id=request.user.id).order_by("-id")[0]
                        avgvalue = data.sleep_efficiency
                        preb_time = data.bed_time
                        s_time = data.sugg_wake_up
                        t1 = datetime.datetime.strptime(preb_time, ("%H:%M:%S"))
                        t2 = datetime.datetime.strptime(s_time, ("%H:%M:%S"))
                        tt1 = datetime.timedelta(hours=t1.hour, minutes=t1.minute).total_seconds()
                        t1s = datetime.timedelta(minutes=t1.minute).total_seconds()
                        s_time = round_time(s_time)
                        tt2 = datetime.timedelta(hours=t2.hour, minutes=t2.minute).total_seconds()
                        if tt1 > tt2:
                            df = tt1 - tt2
                            sdf = 3600 - t1s
                            ssdf = 43200 - (t1s + sdf)
                            if df < 19800:
                                xx = 19800 - df
                                x1 = t1 - datetime.timedelta(seconds=xx)
                                x1 = datetime.datetime.strftime(x1, '%H:%M:%S')
                                presbedtime = round_time(str(x1))
                            if df > 43200:
                                fdf = df - 23400
                                if fdf < 43200:
                                    presbedtime = round_time(preb_time)
                                else:
                                    xx = df - 19800
                                    x1 = t1 - datetime.timedelta(seconds=xx)
                                    x1 = x1 - datetime.timedelta(seconds=ssdf)
                                    x1 = datetime.datetime.strftime(x1, '%H:%M:%S')
                                    presbedtime = round_time(str(x1))
                            else:
                                presbedtime = round_time(preb_time)

                        if tt1 < tt2:
                            df = tt2 - tt1
                            if df < 19800:
                                xx = 19800 - df
                                x1 = t1 - datetime.timedelta(seconds=xx)
                                x1 = datetime.datetime.strftime(x1, '%H:%M:%S')
                                presbedtime = round_time(str(x1))
                            else:
                                presbedtime = round_time(preb_time)
                    context = {
                        "title": _title,
                        "avgsleep": avgvalue,
                        "avgbedtime": presbedtime,
                        "sug_time": s_time,
                        #"lock_diary": lock_diary,
                        "video_view":video_view_count,
                        "base_url": settings.BASE_URL,
                        "first_name": '',
                        "loggedUser": loggedUser,
                        "form": form,
                        "patient": pid,
                        "current_week": wday,
                        "tags": "dairy",
                        "user_name": user_name,
                        "user_image": user_image,
                        "role_id": request.user.role_id,
                        "weekDay_array": weekday,
                        "weekDays_array": weekDays_array,
                        'start_date': datetime.date.strftime(date_time_obj1, "%Y-%m-%d"),
                        "ma":ma
                    }

                    messages.success(request, "Sleep diary data submitted successfully.")

                    return render(request, "sleepdiary_submitted.html", context)
        else:
            print("Form reload")
            form = SleepDiaruForm()
            date_time_obj1 = datetime.datetime.strptime(str(nextDate[0].sleep_diary_entries), '%Y-%m-%d')
            date_time_obj = datetime.date.strftime(date_time_obj1, "%m/%d/%Y")
            # date_time_obj2 = datetime.date.strftime(date_time_obj1, "%Y-%m-%d")
            # print(date_time_obj2)
            form.fields["date"].initial = date_time_obj
            avgvalue = "00.00"
            presbedtime = "--:-- --"
            s_time = "--:-- --"
            if PatientEfficiency.objects.filter(patient_id=request.user.id).exists():
                data = PatientEfficiency.objects.filter(patient_id=request.user.id).order_by("-id")[0]
                avgvalue = data.sleep_efficiency
                preb_time = data.bed_time
                s_time = data.sugg_wake_up
                t1 = datetime.datetime.strptime(preb_time, ("%H:%M:%S"))
                t2 = datetime.datetime.strptime(s_time, ("%H:%M:%S"))
                tt1 = datetime.timedelta(hours=t1.hour, minutes=t1.minute).total_seconds()
                t1s = datetime.timedelta(minutes=t1.minute).total_seconds()
                s_time = round_time(s_time)
                tt2 = datetime.timedelta(hours=t2.hour, minutes=t2.minute).total_seconds()
                if tt1 > tt2:
                    df = tt1 - tt2
                    sdf = 3600 - t1s
                    ssdf = 43200 - (t1s + sdf)
                    if df < 19800:
                        xx = 19800 - df
                        x1 = t1 - datetime.timedelta(seconds=xx)
                        x1 = datetime.datetime.strftime(x1, '%H:%M:%S')
                        presbedtime = round_time(str(x1))
                    if df > 43200:
                        fdf = df - 23400
                        if fdf < 43200:
                            presbedtime = round_time(preb_time)
                        else:
                            xx = df - 19800
                            x1 = t1 - datetime.timedelta(seconds=xx)
                            x1 = x1 - datetime.timedelta(seconds=ssdf)
                            x1 = datetime.datetime.strftime(x1, '%H:%M:%S')
                            presbedtime = round_time(str(x1))
                    else:
                        presbedtime = round_time(preb_time)

                if tt1 < tt2:
                    df = tt2 - tt1
                    if df < 19800:
                        xx = 19800 - df
                        x1 = t1 - datetime.timedelta(seconds=xx)
                        x1 = datetime.datetime.strftime(x1, '%H:%M:%S')
                        presbedtime = round_time(str(x1))
                    else:
                        presbedtime = round_time(preb_time)
            context = {
                "title": _title,
                "avgsleep": avgvalue,
                "avgbedtime": presbedtime,
                "sug_time": s_time,
                #"lock_diary": lock_diary,
                "video_view":video_view_count,
                "base_url": settings.BASE_URL,
                "first_name": '',
                "loggedUser": loggedUser,
                "form": form,
                "user_name": user_name,
                "user_image": user_image,
                "role_id": request.user.role_id,
                "tags": "dairy",
                "current_week": wday,
                "weekDay_array": weekday,
                "weekDays_array": weekDays_array,
                "user_sleep_diarys": invoice_for_today,
                "time_went_to_bed": bed_time,
                "patient": pid,
                "entrydate": date_time_obj,
                'start_date': date_time_obj  # datetime.date.strftime(date_time_obj1, "%Y-%m-%d")

            }
            return render(request, "sleepdiary.html", context)

        # print("User data", UsersleepData.count())

        date_time_obj1 = datetime.datetime.strptime(str(nextDate[0].sleep_diary_entries), '%Y-%m-%d')
        print(date_time_obj1)
        date_time_obj = datetime.date.strftime(date_time_obj1, "%m/%d/%Y")
        print("Yes again reload")
        form.fields["date"].initial = date_time_obj
        avgvalue = "00.00"
        presbedtime = "--:-- --"
        s_time = "--:-- --"
        if PatientEfficiency.objects.filter(patient_id=request.user.id).exists():
            data = PatientEfficiency.objects.filter(patient_id=request.user.id).order_by("-id")[0]
            avgvalue = data.sleep_efficiency
            preb_time = data.bed_time
            s_time = data.sugg_wake_up
            t1 = datetime.datetime.strptime(preb_time, ("%H:%M:%S"))
            t2 = datetime.datetime.strptime(s_time, ("%H:%M:%S"))
            tt1 = datetime.timedelta(hours=t1.hour, minutes=t1.minute).total_seconds()
            t1s = datetime.timedelta(minutes=t1.minute).total_seconds()
            s_time = round_time(s_time)
            tt2 = datetime.timedelta(hours=t2.hour, minutes=t2.minute).total_seconds()
            if tt1 > tt2:
                df = tt1 - tt2
                sdf = 3600 - t1s
                ssdf = 43200 - (t1s + sdf)
                if df < 19800:
                    xx = 19800 - df
                    x1 = t1 - datetime.timedelta(seconds=xx)
                    x1 = datetime.datetime.strftime(x1, '%H:%M:%S')
                    presbedtime = round_time(str(x1))
                if df > 43200:
                    fdf = df - 23400
                    if fdf < 43200:
                        presbedtime = round_time(preb_time)
                    else:
                        xx = df - 19800
                        x1 = t1 - datetime.timedelta(seconds=xx)
                        x1 = x1 - datetime.timedelta(seconds=ssdf)
                        x1 = datetime.datetime.strftime(x1, '%H:%M:%S')
                        presbedtime = round_time(str(x1))
                else:
                    presbedtime = round_time(preb_time)

            if tt1 < tt2:
                df = tt2 - tt1
                if df < 19800:
                    xx = 19800 - df
                    x1 = t1 - datetime.timedelta(seconds=xx)
                    x1 = datetime.datetime.strftime(x1, '%H:%M:%S')
                    presbedtime = round_time(str(x1))
                else:
                    presbedtime = round_time(preb_time)
        context = {
            "title": _title,
            "avgsleep": avgvalue,
            "avgbedtime": presbedtime,
            "sug_time": s_time,
            #"lock_diary": lock_diary,
            "video_view":video_view_count,
            "base_url": settings.BASE_URL,
            "first_name": '',
            "loggedUser": loggedUser,
            "form": form,
            "tags": "dairy",
            "user_name":user_name,
            "user_image": user_image,
            "role_id": request.user.role_id,
            "weekDay_array": weekday,
            "weekDays_array": weekDays_array,
            "invoice_for_today_list": user_date_array,
            "user_sleep_diarys": invoice_for_today,
            "week_day": int(week_day),
            "current_week": wday,
            "entrydate": date_time_obj,
            "time_went_to_bed": bed_time,
            'start_date': date_time_obj

        }

        return render(request, "sleepdiary.html", context)

    except Exception as e:
        print(e)
        return redirect('/')


def hourtomin(hour):
    a2 = float(hour)
    a3 = a2 * 60
    a4 = int(a3)
    return a4

@login_required
def view_sleep_diary(request, weekNm=0, pID=0):
    user_name = ""
    user_image = ""
    ma = False
    try:
        _title = "CogniSleep |  Sleep Dairy"

        if (pID > 0):
            userId = pID
        else:
            userId = request.user.id

        if userId == None or (request.user.isprovider == 1 and pID == 0):
            return redirect('/')
        if pID != 0:
            valid_patient = 0
            try:
                userInfo = RefPatient.objects.get(user_id=pID)

            except Exception:
                valid_patient = 1

            if valid_patient == 1:
                return redirect("/dashboard")
        else:
            if request.user.role_id == 3:
                userInfo = Patient.objects.get(user_id=userId)
                user_name = userInfo.first_name + " " + userInfo.last_name
            elif request.user.role_id == 2:
                userInfo = RefPatient.objects.get(user_id=userId)
                user_name = userInfo.first_name + " " + userInfo.last_name

        UsersleepData = SleepDiary.objects.filter(patient_id=userId)

        print("UserData: ", UsersleepData.count())

        bed_time = "00:00"
        reqWeeks = 6
        if userInfo.package_no == 'PRIMARY CARE SUBSCRIPTION':
            reqWeeks = 6
        elif userInfo.package_no == 'REFERRAL SUBSCRIPTION FROM PHYSICIAN/PROVIDER':
            reqWeeks = 6
        elif userInfo.package_no == 'COGNISLEEP INTENSE LEARNERS':
            reqWeeks = 8
        elif userInfo.package_no == 'COGNISLEEP TRADITIONAL':
            reqWeeks = 12
        elif userInfo.package_no == 'COGNISLEEP PLUS':
            reqWeeks = 15
        else:
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
            [str(userId), start_date, end_date])

        # print("invoice_for_today", invoice_for_today)
        user_date_array = []
        loggedUser = userId

        for x in range(1, reqWeeks + 1):

            if int(x) == week_day + 1:
                if PatientEfficiency.objects.filter(patient_id=userId, week_no=x).exists():
                    data = PatientEfficiency.objects.get(patient_id=userId, week_no=x)
                    week_array = {
                        "x": x,
                       # "is_selected": 1,
                        "eff": data.sleep_efficiency
                    }
                    weekDays_array.append(week_array)
                else:
                    week_array = {
                        "x": x,
                        # "week_date": week,
                        #"is_selected": 1,
                        "eff": ""
                    }
                    weekDays_array.append(week_array)
            else:
                if PatientEfficiency.objects.filter(patient_id=userId, week_no=x).exists():
                    data = PatientEfficiency.objects.get(patient_id=userId, week_no=x)
                    week_array = {
                        "x": x,
                        #"is_selected": 0,
                        "eff": data.sleep_efficiency
                    }
                    weekDays_array.append(week_array)
                else:
                    week_array = {
                        "x": x,
                        # "week_date": week,
                       # "is_selected": 0,
                        "eff": ""
                    }
                    weekDays_array.append(week_array)

        avgvalue = "00.00"
        presbedtime = "--:-- --"
        s_time = "--:-- --"
        if PatientEfficiency.objects.filter(patient_id=request.user.id).exists():
            data = PatientEfficiency.objects.filter(patient_id=request.user.id).order_by("-id")[0]
            avgvalue = data.sleep_efficiency
            preb_time = data.bed_time
            s_time = data.sugg_wake_up
            t1 = datetime.datetime.strptime(preb_time, ("%H:%M:%S"))
            t2 = datetime.datetime.strptime(s_time, ("%H:%M:%S"))
            tt1 = datetime.timedelta(hours=t1.hour, minutes=t1.minute).total_seconds()
            t1s = datetime.timedelta(minutes=t1.minute).total_seconds()
            s_time = round_time(s_time)
            tt2 = datetime.timedelta(hours=t2.hour, minutes=t2.minute).total_seconds()
            if tt1 > tt2:
                df = tt1 - tt2
                sdf = 3600 - t1s
                ssdf = 43200 - (t1s + sdf)
                if df < 19800:
                    xx = 19800 - df
                    x1 = t1 - datetime.timedelta(seconds=xx)
                    x1 = datetime.datetime.strftime(x1, '%H:%M:%S')
                    presbedtime = round_time(str(x1))
                if df > 43200:
                    fdf = df - 23400
                    if fdf < 43200:
                        presbedtime = round_time(preb_time)
                    else:
                        xx = df - 19800
                        x1 = t1 - datetime.timedelta(seconds=xx)
                        x1 = x1 - datetime.timedelta(seconds=ssdf)
                        x1 = datetime.datetime.strftime(x1, '%H:%M:%S')
                        presbedtime = round_time(str(x1))
                else:
                    presbedtime = round_time(preb_time)

            if tt1 < tt2:
                df = tt2 - tt1
                if df < 19800:
                    xx = 19800 - df
                    x1 = t1 - datetime.timedelta(seconds=xx)
                    x1 = datetime.datetime.strftime(x1, '%H:%M:%S')
                    presbedtime = round_time(str(x1))
                else:
                    presbedtime = round_time(preb_time)
        #global lock_diary
        video_view_count = video_count(request.user.id)
        weekNo = getweeknumber(userId)
        context = {
            "title": _title,
            "avgsleep": avgvalue,
            "avgbedtime": presbedtime,
            "sug_time": s_time,
            #"lock_diary": lock_diary,
            "video_view":video_view_count,
            "base_url": settings.BASE_URL,
            "loggedUser": loggedUser,
            "tags": "dairy",
            "week": weekNo,
            "user_name": user_name,
            "user_image": user_image,
            "role_id": request.user.role_id,
            "weekDays_array": weekDays_array,
            "invoice_for_today_list": user_date_array,
            "user_sleep_diarys": invoice_for_today1,
            "patient": pID,
            "time_went_to_bed": bed_time,
            "ma":ma,

        }

        return render(request, "dashboard_view_sleepdiary_tabs.html", context)
    except Exception as e:
        print(e)
        return redirect('/')




def getweeknumber(pid):
    try:
        print(pid)
        total_data = SleepDiary.objects.filter(patient_id=pid, is_updated=1).count()
        # print("invoice_for_today", invoice_for_today)
        if (total_data <= 7 and total_data >= 0):
            weekNo = 1
        elif (total_data <= 14 and total_data > 7):
            weekNo = 2
        elif (total_data <= 21 and total_data > 14):
            weekNo = 3
        elif (total_data <= 28 and total_data > 21):
            weekNo = 4
        elif (total_data <= 35 and total_data > 28):
            weekNo = 5
        else:
            weekNo = 6
        print("Hello total count ========", total_data)
        print(weekNo)
        return weekNo
    except Exception as e:
        print(e)
        return redirect('/')

@login_required
def view_sleep_diary_byprovider(request, weekNm=0, pID=0):
    user_name = ""
    user_image = ""
    user_access = ""
    ma = False
    show = False
    if request.user.role_id == 1:
        user_profile = Provider.objects.get(user_id=request.user.id)
        user_name = user_profile.first_name + " " + user_profile.last_name
        user_image = user_profile.provider_image
        contact = user_profile.contact_no
        provider_access = Provider_Verification.objects.get(user_id=request.user.id)
        user_access = provider_access.user_position

    try:
        _title = "CogniSleep |  Sleep Dairy"
        print("YES HERE")
        if (pID > 0):
            userId = pID
        else:
            userId = request.user.id

        if userId == None or (request.user.isprovider == 1 and pID == 0):
            return redirect('/')
        if pID != 0:
            valid_patient = 0
            try:
                userInfo = RefPatient.objects.get(user_id=pID)

            except Exception:
                valid_patient = 1

            if valid_patient == 1:
                return redirect("/dashboard")
        else:
            if request.user.role_id == 3:
                userInfo = Patient.objects.get(user_id=userId)

            elif request.user.role_id == 2:
                userInfo = RefPatient.objects.get(user_id=userId)


        UsersleepData = SleepDiary.objects.filter(patient_id=userId)

        print("UserData: ", UsersleepData.count())

        bed_time = "00:00"
        reqWeeks = 6
        if userInfo.package_no == 'PRIMARY CARE SUBSCRIPTION':
            reqWeeks = 6
        elif userInfo.package_no == 'REFERRAL SUBSCRIPTION FROM PHYSICIAN/PROVIDER':
            reqWeeks = 6
        elif userInfo.package_no == 'COGNISLEEP INTENSE LEARNERS':
            reqWeeks = 8
        elif userInfo.package_no == 'COGNISLEEP TRADITIONAL':
            reqWeeks = 12
        elif userInfo.package_no == 'COGNISLEEP PLUS':
            reqWeeks = 15
        else:
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
            [str(userId), start_date, end_date])

        user_date_array = []
        loggedUser = userId

        for x in range(1, reqWeeks + 1):

            if int(x) == week_day + 1:
                week_array = {
                    "x": x,
                    # "week_date": week,
                    #"is_selected": 1
                }
                weekDays_array.append(week_array)
            else:
                week_array = {
                    "x": x,
                    # "week_date": week,
                    #"is_selected": 0
                }
                weekDays_array.append(week_array)
        list = []
        today = datetime.date.today()
        year = today.year
        pre_exists = UserAnswer.objects.filter(user_id=userId, question__is_pre=True,
                                               question__year=year).count()
        post_exists = UserAnswer.objects.filter(user_id=userId, question__is_post=True,
                                                question__year=year).count()
        if pre_exists == 15 or post_exists == 15:
            show = True
        avgvalue = "00.00"
        presbedtime = "--:-- --"
        s_time = "--:-- --"
        if PatientEfficiency.objects.filter(patient_id=pID).exists():
            try:
                data = PatientEfficiency.objects.filter(patient_id=pID).order_by("week_no").values()
                print(data)
                for i in data:
                    d = {}
                    avgvalue = i['sleep_efficiency']
                    preb_time = i['bed_time']
                    s_time = i['sugg_wake_up']
                    t1 = datetime.datetime.strptime(preb_time, ("%H:%M:%S"))
                    t2 = datetime.datetime.strptime(s_time, ("%H:%M:%S"))
                    tt1 = datetime.timedelta(hours=t1.hour, minutes=t1.minute).total_seconds()
                    t1s = datetime.timedelta(minutes=t1.minute).total_seconds()
                    s_time = round_time(s_time)
                    d['sugg_wake_up'] = s_time
                    tt2 = datetime.timedelta(hours=t2.hour, minutes=t2.minute).total_seconds()
                    if tt1 > tt2:
                        df = tt1 - tt2
                        sdf = 3600 - t1s
                        ssdf = 43200 - (t1s + sdf)
                        if df < 19800:
                            xx = 19800 - df
                            x1 = t1 - datetime.timedelta(seconds=xx)
                            x1 = datetime.datetime.strftime(x1, '%H:%M:%S')
                            presbedtime = round_time(str(x1))
                        if df > 43200:
                            fdf = df - 23400
                            if fdf < 43200:
                                presbedtime = round_time(preb_time)
                            else:
                                xx = df - 19800
                                x1 = t1 - datetime.timedelta(seconds=xx)
                                x1 = x1 - datetime.timedelta(seconds=ssdf)
                                x1 = datetime.datetime.strftime(x1, '%H:%M:%S')
                                presbedtime = round_time(str(x1))
                        else:
                            presbedtime = round_time(preb_time)

                    if tt1 < tt2:
                        df = tt2 - tt1
                        if df < 19800:
                            xx = 19800 - df
                            x1 = t1 - datetime.timedelta(seconds=xx)
                            x1 = datetime.datetime.strftime(x1, '%H:%M:%S')
                            presbedtime = round_time(str(x1))
                        else:
                            presbedtime = round_time(preb_time)
                    d['prescribe_bedtime'] = presbedtime
                    d['sleep_efficieny'] = avgvalue
                    list.append(d)
            except Exception as e:
                print(e)
        weekNo = getweeknumber(pID)
        today = date.today()

        # dd/mm/YY
        d1 = today.strftime("%m/%d/%Y")

        context = {
            "title": _title,
            "base_url": settings.BASE_URL,
            "loggedUser": loggedUser,
            "tags": "dairy",
            "week": weekNo,
            "date": d1,
            "contact": contact,
            'userinfo' : userInfo,
            "weekDays_array": weekDays_array,
            "user_image":user_image,
            "user_name":user_name,
            "user_access": user_access,
            "role_id": request.user.role_id,
            "invoice_for_today_list": user_date_array,
            "user_sleep_diarys": invoice_for_today1,
            "patient": pID,
            "efficiency": list,
            "show":show,
            "time_went_to_bed": bed_time,
            "ma":ma

        }

        return render(request, "dashboard_provider_view_sleepdiary_tabs.html", context)
    except Exception as e:
        print(e)
        return redirect('/')


@csrf_exempt
def sleep_diary_week_data(request, weekNm=0, pID=0):
    try:
        if (pID > 0):
            userId = pID
        else:
            # this is for admin dashboard request
            if (request.POST.get("admin_request_id")):
                userId = int(request.POST.get("admin_request_id"))
                request.user.isprovider = 0
                request.user.role_id = 3  # this is for admin dashboard request
            elif (request.POST.get("admin_request_ref_id")):
                userId = int(request.POST.get("admin_request_ref_id"))
                request.user.isprovider = 0
                request.user.role_id = 2
            else:
                userId = request.user.id

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
                return JsonResponse(data)
        else:
            if request.user.role_id == 3:
                userInfo = Patient.objects.get(user_id=userId)
            elif request.user.role_id == 2:
                userInfo = RefPatient.objects.get(user_id=userId)

        if (weekNm > 0):
            week_day = weekNm - 1
        else:
            week_day = weekNm
        print("my week value", weekNm)
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
        view_sleep_diary_byprovider(request, weekNm, pID)

        data = {
            "success": "true",
            "week_data": invoice_for_today,
            "user_id": userId

        }

        return JsonResponse(data)
    except Exception as e:
        print(e)
        return redirect('/')


def certificate(request):
    try:
        print("YES IN CERTIFICATE")
        if request.user.id is None:
            print("NOT FOUND")
            return redirect('/')

        existVCompleted = VideoSessionsCompleted.objects.filter(patient_id=request.user.id).count()
        print(existVCompleted)
        if existVCompleted > 0:
            print("FOUND")
            existVCompleted = VideoSessionsCompleted.objects.filter(patient_id=request.user.id)
        else:
            return redirect('/')
        if request.user.role_id == 3:
            user_profile = Patient.objects.get(user_id=request.user.id)
        elif request.user.role_id == 2:
            user_profile = RefPatient.objects.get(user_id=request.user.id)
        date1 = existVCompleted[0].created_at
        date = date1.strftime("%B #, %Y")
        day = date1.day
        if (3 < day < 21) or (23 < day < 31):

            day = str(day) + 'th'
        else:

            suffixes = {1: 'st', 2: 'nd', 3: 'rd'}

            day = str(day) + suffixes[day % 10]
        f_date = (date.replace('#', day))
        name = profile(request.user.id)
        context = {
            "patient_id": existVCompleted[0].patient_id,
            "date": f_date,
            "name": user_profile.first_name + " " + user_profile.last_name,
            'provider_name': name,
        }

        return render(request, "certificate.html", context)
    except Exception as e:
        print(e)
        return redirect('/')


class SessionCompleted(APIView):

    def post(self, request, *args, **kwargs):
        try:
            # doctor_refnumber = request.data.get('ref_name')
            userId = request.data.get('user_id')
            existVCompleted = VideoSessionsCompleted.objects.filter(patient_id=userId).count()
            if (existVCompleted == 0):
                VSessionsCompleted = VideoSessionsCompleted();
                VSessionsCompleted.patient_id = userId
                VSessionsCompleted.completed = 1;
                VSessionsCompleted.save();
                return JsonResponse({
                    'success': 1,
                    'successMsg': 1,
                })
            return JsonResponse({
                'success': 1,
            })
        except Exception as e:
            print(e)
            return redirect('/')


def savelastvideo(request):
    try:
        print("yes in final video")
        userId = request.user.id
        print(userId)
        # global video_view_count
        queryset = VideoViews.objects.filter(patient_id=int(userId))
        if queryset.exists():
            print("Found data")
            updaterecord = VideoViews.objects.get(patient_id=int(userId))
            updaterecord.view_video = 7
            updaterecord.save()
            if VideoSessionsCompleted.objects.filter(patient_id=userId).exists():
                print("yes in if before else")
                return redirect("/dashboard")
            else:
                print("YES- NO FINAL SAVE")
                data = VideoSessionsCompleted(patient_id=userId, completed=1)
                data.save()
                subject = 'Certificate of Completion for CogniSleep Program'
                to = request.user.email

                html_message = loader.render_to_string(
                    'email_temp/completion_email.html',
                    {}
                )
                email_records(request, to, settings.EMAIL_FROM, 'Certificate of Completion for CogniSleep Program')
                send_mail(
                    subject,
                    'Certificate of Completion for CogniSleep Program',
                    settings.EMAIL_FROM,
                    [to],
                    html_message=html_message
                    ,
                )
                return redirect("/dashboard")

        return redirect("/dashboard")
    except Exception as e:
        print(e)
        return redirect('/')


@csrf_exempt
@api_view(["POST"])
def answers(request, vid):
    try:
        print("THIS IS VIDEO ID", vid)
        userId = request.data.get('user_id')
        print("video section ma id check",userId)
        # print(request.data.get('answers'))
        answers = json.loads(request.data.get('answers'))
        print("Hurrah! you are in answers")
        for key, value in answers.items():
            VideoQAnswers = VideoAnswers()
            VideoQAnswers.answer = value
            VideoQAnswers.video_questions_id = key
            VideoQAnswers.user_id = int(userId)
            VideoQAnswers.save()

        print(userId)
        video_view_count = video_count(int(userId))
        queryset = VideoViews.objects.filter(patient_id=int(userId))
        if queryset.exists():
            updaterecord = VideoViews.objects.get(patient_id=int(userId))
            if int(vid) <= int(updaterecord.view_video):
                pass
            else:
                updaterecord.view_video = vid
                updaterecord.save()
        else:
            print("record saving")
            saverecord = VideoViews(patient_id=userId, view_video=0)
            saverecord.save()
        if userId == None:
            data = {
                "status": 0,
            }
            return JsonResponse(data)

        data = {
            "status": 1,
        }

        return JsonResponse(data)
    except Exception as e:
        print(e)
        return redirect('/')


def day_avg(v1, v2, v3):
    try:
        timefeelsleep = time_to_sec(v1)
        timegotup = time_to_sec(v2)
        timewenttobed = time_to_sec(v3)

        print("timefeelsleep: ", timefeelsleep)
        print("timegotup: ", timegotup)
        print("timewenttobed: ", timewenttobed)

        cal1 = int(timefeelsleep) - int(timegotup)
        cal2 = int(timewenttobed) - int(timegotup)

        if cal1 != 0 and cal2 != 0:
            result = (cal1 / cal2) * 100
            return abs(round(result, 2))
        else:
            return 0
    except Exception as e:
        print(e)
        return redirect('/')


def time_to_sec(time_str):
    try:
        return sum(x * int(t) for x, t in zip([1, 60, 3600], reversed(time_str.split(":"))))
    except Exception as e:
        print(e)
        return redirect('/')


def calculate_time_net(times):
    try:
        date_time_str = str(timedelta(seconds=sum(
            # map(lambda f: int(f[0]) * 3600 + int(f[1]) * 60, map(lambda f: f.split(':'), times))) / len(times)))
            #
            # map(lambda f: int(f[0]) * 3600 + int(f[1]) * 60, map(lambda f: f.split(':'), times))) / len(
            # times)))

            map(lambda f: int(f[0]) * 3600 + int(f[1]) * 24 * 60 + int(f[2]),
                map(lambda f: f.split(':'), times))) / len(
            times)))

        tim = ampmformat(date_time_str)
        result = list(tim.strip(":"))
        print("Result ", str(len(result)))
        print("Result ", result)
        if len(result) == 11:
            return result[0] + result[1] + ":" + result[3] + result[4] + " " + result[9] + result[10]
        else:
            return result[0] + result[1] + ":" + result[3] + result[4] + " " + result[16] + result[17]
    except Exception as e:
        print(e)
        return redirect('/')


def ampmformat(hhmmss):
    try:
        ampm = hhmmss.split(":")
        if (len(ampm) == 0) or (len(ampm) > 3):
            return hhmmss

        hour = int(ampm[0]) % 24
        isam = (hour >= 0) and (hour < 12)

        if isam:
            ampm[0] = ('12' if (hour == 0) else "%02d" % (hour))
        else:
            ampm[0] = ('12' if (hour == 12) else "%02d" % (hour - 12))

        # return ':'.join(ampm) + (' AM' if isam else ' PM')
        return ':'.join(ampm) + (' AM' if isam else ' PM')
    except Exception as e:
        print(e)
        return redirect('/')





def provider_subscription(request, pid=0):
    try:
        print(pid)
        checkUser = request.user.id
        print(checkUser)
        if checkUser is None:
            return redirect('/')
        if request.method == 'POST':
            print("TRUE");
            sub_pkg = ProviderCard()

            sub_pkg.provider_id = checkUser
            sub_pkg.name_on_card = request.POST.get('provider_name')
            sub_pkg.card_number = request.POST.get('card_number')
            sub_pkg.cvc_code = request.POST.get('cvc_code')
            sub_pkg.exp_date = request.POST.get('exp_date')
            sub_pkg.save()
            print("Record Save Successfully")
        if request.user.role_id == 1:
            package_detail = Subscriptionpackage.objects.all().order_by("date")

            _title = "CogniSleep |  Cogni-Dashboard"

            context = {
                "title": _title,
                "base_url": settings.BASE_URL,
                "packages": package_detail,

            }
            return render(request, "provider_subscription.html", context)

    except Exception as e:
        print(e)
        return redirect('/')


def relaxation(request):
    user_name = ""
    user_image = ""
    avgvalue = "00.00"
    presbedtime = "--:-- --"
    s_time = "--:-- --"
    ma = False
    try:
        if request.user.role_id == 3:
            user_profile = Patient.objects.get(user_id=request.user.id)
            user_name = user_profile.first_name + " " + user_profile.last_name

        elif request.user.role_id == 2:
            user_profile = RefPatient.objects.get(user_id=request.user.id)
            user_name = user_profile.first_name + " " + user_profile.last_name
        elif request.user.role_id == 1:
            user_profile = Provider.objects.get(user_id=request.user.id)
            user_name = user_profile.first_name + " " + user_profile.last_name
            user_image = user_profile.provider_image
        if PatientEfficiency.objects.filter(patient_id=request.user.id).exists():
            data = PatientEfficiency.objects.filter(patient_id=request.user.id).order_by("-id")[0]
            avgvalue = data.sleep_efficiency
            preb_time = data.bed_time
            s_time = data.sugg_wake_up
            t1 = datetime.datetime.strptime(preb_time, ("%H:%M:%S"))
            t2 = datetime.datetime.strptime(s_time, ("%H:%M:%S"))
            tt1 = datetime.timedelta(hours=t1.hour, minutes=t1.minute).total_seconds()
            t1s = datetime.timedelta(minutes=t1.minute).total_seconds()
            s_time = round_time(s_time)
            tt2 = datetime.timedelta(hours=t2.hour, minutes=t2.minute).total_seconds()
            if tt1 > tt2:
                df = tt1 - tt2
                sdf = 3600 - t1s
                ssdf = 43200 - (t1s + sdf)
                if df < 19800:
                    xx = 19800 - df
                    x1 = t1 - datetime.timedelta(seconds=xx)
                    x1 = datetime.datetime.strftime(x1, '%H:%M:%S')
                    presbedtime = round_time(str(x1))
                if df > 43200:
                    fdf = df - 23400
                    if fdf < 43200:
                        presbedtime = round_time(preb_time)
                    else:
                        xx = df - 19800
                        x1 = t1 - datetime.timedelta(seconds=xx)
                        x1 = x1 - datetime.timedelta(seconds=ssdf)
                        x1 = datetime.datetime.strftime(x1, '%H:%M:%S')
                        presbedtime = round_time(str(x1))
                else:
                    presbedtime = round_time(preb_time)

            if tt1 < tt2:
                df = tt2 - tt1
                if df < 19800:
                    xx = 19800 - df
                    x1 = t1 - datetime.timedelta(seconds=xx)
                    x1 = datetime.datetime.strftime(x1, '%H:%M:%S')
                    presbedtime = round_time(str(x1))
                else:
                    presbedtime = round_time(preb_time)

        context = {
            "title": "Relaxation",
            "avgsleep": avgvalue,
            "avgbedtime": presbedtime,
            "sug_time": s_time,
            "user_name": user_name,
            "user_image": user_image,
            "role_id": request.user.role_id,
            "base_url": settings.BASE_URL,
            "ma":ma

        }

        return render(request, "relaxation.html", context)

    except Exception as e:
        print(e)
        return redirect('/')


def updatevalue(request, wid, pid, sid, ppid):

    try:
        data = PatientEfficiency.objects.get(patient_id=ppid, week_no=wid)
        print(data)
        data.bed_time = pid + ":00"
        data.sugg_wake_up = sid + ":00"
        data.save()
        print("record update successfully")
        return HttpResponse(status=200)
    except Exception as e:
        print(e)
        return redirect('/')




ch = 8
@login_required
def create_pdf_report_weekly(request):
    try:

        if request.method == 'POST':
            start_week = int(request.POST.get('start_week'))
            end_week = int(request.POST.get('end_week'))
            id = request.POST.get('pid')

            count = 1
            f_end = int(end_week) * 7
            if start_week == 1:
                f_start = 1
                count = f_start
            elif start_week == 2:
                f_start = 8
                count = f_start
            elif start_week == 3:
                f_start = 15
                count = f_start
            elif start_week == 4:
                f_start = 22
                count = f_start
            elif start_week == 5:
                f_start = 29
                count = f_start
            elif start_week == 6:
                f_start = 36
                count = f_start
            patient = RefPatient.objects.get(user_id=id)
            patient_name = patient.first_name + " " + patient.last_name
            provider_id = patient.provider_id
            sleep_report = SleepDiary.objects.filter(patient_id=id, is_updated=1)
            # df = pd.DataFrame(list(sleep_report))
            # print(df.is_updated)
            provider_id = str(provider_id[12:])
            provider = Provider.objects.get(user_id=provider_id)
            provider_name = provider.first_name + " " + provider.last_name
            today = datetime.date.today()
            today = today.strftime('%m-%d-%Y')
            class PDF(FPDF):
                def header(self):
                    # Position at 1.5 cm from bottom
                    filepath = os.path.join(BASE_DIR, 'static/assets/images/logo-1.png')
                    self.image(filepath, 10, 10, 100);
                    self.set_font('Arial', 'B', 15);
                    self.cell(125);
                    # self.set_x(110)
                    # self.set_y(20)
                    self.cell(40, 25, "| Patient: " + patient_name, 0, 0, 'C');
                    self.cell(45);
                    self.cell(40, 25, "| Provider: " + provider_name, 0, 0, 'C');
                    self.cell(45);
                    self.cell(40, 25, "| Report Date: " + today, 0, 0, 'C');
                    self.cell(45);
                    self.cell(80, 25, "| Weekly Report From: Week " + str(start_week) + " To Week " + str(end_week), 0, 0, 'C');
                    self.ln(30);

                # Page footer
                def footer(self):
                    # Position at 1.5 cm from bottom
                    self.set_y(-15)
                    # Arial italic 8
                    self.set_font('Arial', 'I', 14)
                    # Page number
                    self.cell(0, 10, 'Page ' + str(self.page_no()) + '/{nb}', 0, 0, 'C')
            pdf = PDF(orientation='L', unit='mm', format=(230, 550))
            pdf.alias_nb_pages()
            pdf.add_page()

            for x in range(int(start_week), int(end_week) + 1):
                if (int(end_week) - int(start_week)) > 1:
                    if x > 1:
                        pdf.add_page()

                pdf.set_font('Arial', 'B', 18)
                pdf.cell(w=0, h=10, txt="Week" + str(x), ln=1,
                         align='C')
                pdf.ln(10)

                # Table Header
                pdf.set_font('Arial', 'B', 12)
                x1_value = pdf.get_x()
                y1_value = pdf.get_y()
                y2_value = y1_value + 15.0
                pdf.line(x1_value, y1_value, 535, y1_value)
                pdf.line(x1_value, y2_value, 535, y2_value)
                pdf.line(x1_value,y1_value,x1_value,y2_value)
                pdf.line(535, y1_value, 535, y2_value)
                pdf.cell(w=12, h=ch, txt='Days', border=0, ln=0, align='C')
                pdf.cell(w=27, h=ch, txt='Time Went', border=0, ln=0, align='C')
                pdf.cell(w=20, h=ch, txt='Lights', border=0, ln=0, align='C')
                pdf.cell(w=28, h=ch, txt='Minutes To', border=0, ln=0, align='C')
                pdf.cell(w=40, h=ch, txt='How Many Times', border=0, ln=0, align='C')
                pdf.cell(w=30, h=ch, txt='Awake During', border=0, ln=0, align='C')
                pdf.cell(w=26, h=ch, txt='Time You', border=0, ln=0, align='C')
                pdf.cell(w=34, h=ch, txt='Minutes Fell', border=0, ln=0, align='C')
                pdf.cell(w=28, h=ch, txt='Got Up', border=0, ln=0, align='C')
                pdf.cell(w=32, h=ch, txt='Desired', border=0, ln=0, align='C')
                pdf.cell(w=20, h=ch, txt='No. Of', border=0, ln=0, align='C')
                pdf.cell(w=38, h=ch, txt='Total Time', border=0, ln=0, align='C')
                pdf.cell(w=17, h=ch, txt='Time In', border=0, ln=0, align='C')
                pdf.cell(w=19, h=ch, txt='Time', border=0, ln=0, align='C')
                pdf.cell(w=20, h=ch, txt='Sleep', border=0, ln=0, align='C')
                pdf.cell(w=32, h=ch, txt='Problem', border=0, ln=0, align='C')
                pdf.cell(w=28, h=ch, txt='Awake', border=0, ln=0, align='C')
                pdf.cell(w=24, h=ch, txt='Awake', border=0, ln=0, align='C')
                pdf.cell(w=28, h=ch, txt='Delayed', border=0, ln=0, align='C')
                pdf.cell(w=20, h=ch, txt='Overslept', border=0, ln=1, align='C')




                pdf.cell(w=12, h=ch, txt='', border=0, ln=0, align='C')
                pdf.cell(w=27, h=ch, txt='To Bed', border=0, ln=0, align='C')
                pdf.cell(w=20, h=ch, txt='Out', border=0, ln=0, align='C')
                pdf.cell(w=28, h=ch, txt='Fall Asleep', border=0, ln=0, align='C')
                pdf.cell(w=40, h=ch, txt='You Woke Up', border=0, ln=0, align='C')
                pdf.cell(w=30, h=ch, txt='The Night', border=0, ln=0, align='C')
                pdf.cell(w=26, h=ch, txt='Woke Up', border=0, ln=0, align='C')
                pdf.cell(w=34, h=ch, txt='Back To Sleep', border=0, ln=0, align='C')
                pdf.cell(w=28, h=ch, txt='From Bed', border=0, ln=0, align='C')
                pdf.cell(w=32, h=ch, txt='Wake Up Time', border=0, ln=0, align='C')
                pdf.cell(w=20, h=ch, txt='Naps', border=0, ln=0, align='C')
                pdf.cell(w=38, h=ch, txt='Napping In Mints', border=0, ln=0, align='C')
                pdf.cell(w=17, h=ch, txt='Bed', border=0, ln=0, align='C')
                pdf.cell(w=19, h=ch, txt='Asleep', border=0, ln=0, align='C')
                pdf.cell(w=20, h=ch, txt='Effcy %', border=0, ln=0, align='C')
                pdf.cell(w=32, h=ch, txt='Falling Asleep', border=0, ln=0, align='C')
                pdf.cell(w=28, h=ch, txt='During Night', border=0, ln=0, align='C')
                pdf.cell(w=24, h=ch, txt='Too Early', border=0, ln=0, align='C')
                pdf.cell(w=28, h=ch, txt='Getting Up', border=0, ln=0, align='C')
                pdf.cell(w=20, h=ch, txt='', border=0, ln=1, align='C')


                # Table contents
                pdf.set_font('Arial', '', 12)
                i = 1
                for index, item in enumerate(sleep_report, start=1):
                    print("COUNT", count)
                    print("INDEX", index)
                    if count == index:
                        if count <= f_end:
                            if i == 1 or i <= 7:
                                pdf.set_text_color(0, 0, 0)
                                pdf.cell(w=12, h=ch,
                                         txt=str(i),
                                         border=1, ln=0, align='C')
                                a = datetime.datetime.strptime(item.time_went_to_bed, '%H:%M:%S').time()
                                a = a.strftime('%I:%M %p')
                                pdf.set_text_color(0, 0, 0)
                                pdf.cell(w=27, h=ch,
                                         txt=str(a),
                                         border=1, ln=0, align='C')
                                a = datetime.datetime.strptime(item.lights_out, '%H:%M:%S').time()
                                a = a.strftime('%I:%M %p')
                                pdf.set_text_color(0, 0, 0)
                                pdf.cell(w=20, h=ch,
                                         txt=str(a),
                                         border=1, ln=0, align='C')
                                pdf.set_text_color(0, 0, 0)
                                pdf.cell(w=28, h=ch,
                                         txt=str(item.minutes_fall_asleep),
                                         border=1, ln=0, align='C')
                                pdf.set_text_color(0, 0, 0)
                                pdf.cell(w=40, h=ch,
                                         txt=str(item.no_of_times_awakend),
                                         border=1, ln=0, align='C')
                                pdf.set_text_color(0, 0, 0)
                                pdf.cell(w=30, h=ch,
                                         txt=str(item.awake_during_night),
                                         border=1, ln=0, align='C')
                                a = datetime.datetime.strptime(item.time_got_up, '%H:%M:%S').time()
                                a = a.strftime('%I:%M %p')
                                pdf.set_text_color(0, 0, 0)
                                pdf.cell(w=26, h=ch,
                                         txt=str(a),
                                         border=1, ln=0, align='C')
                                pdf.set_text_color(0, 0, 0)
                                pdf.cell(w=34, h=ch,
                                         txt=str(item.minutes_fellback_sleep),
                                         border=1, ln=0, align='C')
                                a = datetime.datetime.strptime(item.out_of_bed, '%H:%M:%S').time()
                                a = a.strftime('%I:%M %p')
                                pdf.set_text_color(0, 0, 0)
                                pdf.cell(w=28, h=ch,
                                         txt=str(a),
                                         border=1, ln=0, align='C')
                                a = datetime.datetime.strptime(item.desire_wakeup_time, '%H:%M:%S').time()
                                a = a.strftime('%I:%M %p')
                                pdf.set_text_color(0, 0, 0)
                                pdf.cell(w=32, h=ch,
                                         txt=str(a),
                                         border=1, ln=0, align='C')
                                pdf.set_text_color(0, 0, 0)
                                pdf.cell(w=20, h=ch,
                                         txt=str(item.number_of_naps),
                                         border=1, ln=0, align='C')
                                pdf.set_text_color(0, 0, 0)
                                pdf.cell(w=38, h=ch,
                                         txt=str(item.totlatime_napping_minutes),
                                         border=1, ln=0, align='C')
                                pdf.set_text_color(0, 0, 0)
                                pdf.cell(w=17, h=ch,
                                         txt=str(item.time_in_bed),
                                         border=1, ln=0, align='C')
                                pdf.set_text_color(0, 0, 0)
                                if(float(item.total_sleep_time) < 5.5):
                                    pdf.set_font('Arial', 'B', 13)
                                    pdf.set_text_color(255, 0, 0)
                                    pdf.cell(w=19, h=ch,
                                             txt=str(item.total_sleep_time),
                                             border=1, ln=0, align='C')
                                else:
                                    pdf.cell(w=19, h=ch,
                                             txt=str(item.total_sleep_time),
                                             border=1, ln=0, align='C')

                                pdf.set_font('Arial', '', 12)
                                pdf.set_text_color(0, 0, 0)
                                pdf.cell(w=20, h=ch,
                                         txt=str(item.sleep_efficiency),
                                         border=1, ln=0, align='C')

                                pdf.set_text_color(255, 0, 0)
                                pdf.cell(w=32, h=ch,
                                         txt=str(item.problem_falling_asleep),
                                         border=1, ln=0, align='C')
                                pdf.set_text_color(255, 0, 0)
                                pdf.cell(w=28, h=ch,
                                         txt=str(item.awake_during_night),
                                         border=1, ln=0, align='C')
                                pdf.set_text_color(255, 0, 0)
                                pdf.cell(w=24, h=ch,
                                         txt=str(item.awake_too_early),
                                         border=1, ln=0, align='C')
                                pdf.set_text_color(255, 0, 0)
                                pdf.cell(w=28, h=ch,
                                         txt=str(item.delayed_getting_up),
                                         border=1, ln=0, align='C')
                                pdf.set_text_color(255, 0, 0)
                                pdf.cell(w=22, h=ch,
                                         txt=str(item.overslept),
                                         border=1, ln=1, align='C')
                                pdf.set_text_color(0, 0, 0)
                                if(item.comment):
                                    pdf.multi_cell(w=525, h=ch,
                                             txt="Comment: "+ str(item.comment),
                                             border=1, align='L')
                                    pdf.ln(0)

                                i = i + 1
                                count = count + 1
                                continue
                            else:
                                break
                        else:
                            count = count + 1
                            continue
                    else:
                        continue

            pdf.set_text_color(0, 0, 0)
            pdf.cell(w=0,h=12, txt="", ln=1)
            pdf.cell(w=0, h=12, txt="", ln=1)
            pdf.cell(w=30, h=16, txt="Signature: ", border=0, ln=0, align='L')
            x = pdf.get_x()
            y = pdf.get_y()
            pdf.line(x - 9, y + 9, x + 100, y + 9)
            pdf.cell(180)
            pdf.cell(w=30, h=16, txt="Date: ", border=0, ln=0, align='L')
            x = pdf.get_x()
            y = pdf.get_y()
            pdf.line(x - 18, y + 9, (x + 100), y + 9)
            file_name = patient_name + "_" + id + "_" + provider_id + ".pdf"
            filepath = os.path.join(BASE_DIR, 'media')
            pdf.output(filepath+"/"+file_name, 'F')

            return FileResponse(open(filepath+"/"+file_name, 'rb'), as_attachment=True, content_type='application/pdf')

    except Exception as e:
        print(e)
        return redirect('/')

def video_count(id):
    try:
        queryset = VideoViews.objects.filter(patient_id=id)
        if queryset.exists():
            print("Found data")
            getdata = VideoViews.objects.get(patient_id=id)
            video_view_count = getdata.view_video
            return video_view_count
        else:
            return 0
    except Exception as e:
        print(e)
        return redirect('/')

def setting(request, pid=0):
    mylist = []
    mysearch = ""
    user_name = ""
    user_image = ""
    user_access = ""

    try:

        checkUser = request.user.id
        if checkUser is None:
            return redirect('/')
        if pid > 0:
            checkUser = pid
            print(pid)
        if request.user.role_id == 3:
            user_profile = Patient.objects.get(user_id=request.user.id)
            user_name = user_profile.first_name + " " + user_profile.last_name

        elif request.user.role_id == 2:
            user_profile = RefPatient.objects.get(user_id=request.user.id)
            user_name = user_profile.first_name + " " + user_profile.last_name
        elif request.user.role_id == 1:
            user_profile = Provider.objects.get(user_id=request.user.id)
            user_name = user_profile.first_name + " " + user_profile.last_name
            user_image = user_profile.provider_image
            provider_access = Provider_Verification.objects.get(user_id=request.user.id)
            user_access = provider_access.user_position
            print("YESSSSSSSSSSSSSSSS provider 1")

            try:
                print("Yes 2")
                # Retrieve the subscription & product
                if StripeCustomer.objects.filter(user_id=request.user.id).exists():
                    sub_status = Provider.objects.get(user_id=request.user.id)
                    sub_status = sub_status.subscription_status
                    stripe_customer = StripeCustomer.objects.get(user_id=request.user.id)
                    cus = stripe_customer.stripeCustomerId
                    stripe.api_key = settings.STRIPE_SECRET_KEY
                    subscription = stripe.Subscription.retrieve(stripe_customer.stripeSubscriptionId)
                    product = stripe.Product.retrieve(subscription.plan.product)
                    product_price = subscription.plan.amount_decimal[0:2]
                    inv = stripe.Invoice.list(customer=cus)
                    for i, item in enumerate(inv):
                        d = {}
                        inv_id = inv.data[i]['id']
                        invoice_url = inv.data[i]['invoice_pdf']
                        invoice_status = inv.data[i]['status']
                        dat = inv.data[i]['created']
                        invoice_number = inv.data[i]['number']
                        date = datetime.datetime.fromtimestamp(dat)
                        date = date.strftime("%m/%d/%Y")
                        invoice_date = date
                        d['invoice_url'] = invoice_url
                        d['invoice_status'] = invoice_status
                        d['invoice_date'] = invoice_date
                        d['invoice_id'] = inv_id
                        d['number'] = invoice_number
                        mylist.append(d)
                else:
                    return redirect('/')
            except StripeCustomer.DoesNotExist:
                print("Provider Subscription does not exist")
            user_step = Provider_Verification.objects.get(user_id=request.user.id)

            user_code = user_step.user_position
            # if user_code == "4":

            context = {

                "base_url": settings.BASE_URL,
                "first_name": '',
                "user_name": user_name,
                "user_code": user_code,
                "user_image": user_image,
                "userdata": user_profile,
                "role_id": request.user.role_id,
                'subscription': subscription,
                'product': product,
                'status': sub_status,
                'price': product_price,
                'invoice': mylist,
                'mysearch': mysearch,
                'user_access': user_access,
                'total_invoice': len(mylist),


                # 'provider_data': provider_data,

            }
            return render(request, "setting.html", context)
            # else:
            #     return redirect('/')
    except Exception as e:
        print(e)
        return redirect('/')

@login_required
def patient_account_detail(request,pid=0):

    user_name = ""
    user_image = ""
    provider = ""
    provider_rec = ""
    user_access = ""
    try:
        checkUser = request.user.id
        print(checkUser)
        if checkUser is None:
            return redirect('/')
        if pid > 0:
            checkUser = pid
        if request.user.role_id == 3:
            user_profile = Patient.objects.get(user_id=request.user.id)
            user_name = user_profile.first_name + " " + user_profile.last_name

        elif request.user.role_id == 2:
            user_profile = RefPatient.objects.get(user_id=request.user.id)
            user_name = user_profile.first_name + " " + user_profile.last_name
            user_profile = RefPatient.objects.get(user_id=request.user.id)
            provider = user_profile.provider_id[4::]
            provider_rec = Provider.objects.get(provider_ref=provider)
        elif request.user.role_id == 1:
            user_profile = Provider.objects.get(user_id=request.user.id)
            user_name = user_profile.first_name + " " + user_profile.last_name
            user_image = user_profile.provider_image
            provider_access = Provider_Verification.objects.get(user_id=request.user.id)
            user_access = provider_access.user_position

        context = {


            "base_url": settings.BASE_URL,
            "first_name": '',
            "provider": provider_rec,
            "userdata": user_profile,

            "patient": pid,
            "user_name": user_name,
            "user_image":user_image,
            "role_id": request.user.role_id,
            "user_access": user_access,


        }

        return render(request, "patient_account_detail.html", context)
    except Exception as e:
        print(e)
        return redirect('/')

class Referedbypro(APIView):

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
            ref_patient = RefPatient.objects.get(user=user)
            first_name = ref_patient.first_name[:2] if ref_patient.first_name else ""
            last_name = ref_patient.last_name[:2] if ref_patient.last_name else ""
            provider_id = request.data.get('provider_id')

            if provider_id:
                provider_ids = first_name + last_name + provider_id
                # Check if RefPatient exists for the user
                ref_patient = RefPatient.objects.filter(user=user).first()

                if ref_patient:
                    # Update provider_id
                    ref_patient.provider_id = provider_ids
                    ref_patient.save()

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


def email_records(request,to_,from_,msg):
    try:
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        cursor = connections['default'].cursor()
        cursor.execute("INSERT INTO emails(to_,from_,msg,ip) VALUES( %s , %s, %s, %s )", [to_, from_,msg,ip])
    except Exception as e:
        print(e)
        return redirect('/')


class ProviderCardDetailAPIView(APIView):
    def post(self, request):
        request_body = request.data
        #card saved
        try:
            new_provider_card = ProviderCard(
                provider_id=request_body['provider_id'],
                name_on_card=request_body['name_on_card'],
                exp_date=request_body['exp_date'],
                cvc_code=request_body['cvc_code'],
                card_number=request_body['card_number'],
            )
            new_provider_card.save()
        except Exception as e:
            return Response(str(e), status=status.HTTP_400_BAD_REQUEST)


        return Response("Card added Successfully", status=status.HTTP_400_BAD_REQUEST)

ch = 8
def create_pdf_report_weekly_directly(pid,weekno):
    try:

        if pid != None and weekno != None:
            print(pid)
            print(weekno)
            start_week = weekno
            end_week = weekno
            id = pid

            count = 1
            f_end = int(end_week) * 7
            if start_week == 1:
                f_start = 1
                count = f_start
            elif start_week == 2:
                f_start = 8
                count = f_start
            elif start_week == 3:
                f_start = 15
                count = f_start
            elif start_week == 4:
                f_start = 22
                count = f_start
            elif start_week == 5:
                f_start = 29
                count = f_start
            elif start_week == 6:
                f_start = 36
                count = f_start
            patient = RefPatient.objects.get(user_id=id)
            patient_name = patient.first_name + " " + patient.last_name
            provider_id = patient.provider_id
            provider_id = str(provider_id[12:])
            provider = Provider.objects.get(user_id=provider_id)
            provider_name = provider.first_name + " " + provider.last_name
            sleep_report = SleepDiary.objects.filter(patient_id=id, is_updated=1)
            today = datetime.date.today()
            today = today.strftime('%m-%d-%Y')
            # df = pd.DataFrame(list(sleep_report))
            # print(df.is_updated)
            class PDF(FPDF):
                def header(self):
                    # Position at 1.5 cm from bottom
                    filepath = os.path.join(BASE_DIR, 'static/assets/images/logo-1.png')
                    self.image(filepath, 10, 10, 100);
                    self.set_font('Arial', 'B', 15);
                    self.cell(125);
                    # self.set_x(110)
                    # self.set_y(20)
                    self.cell(40, 25, "| Patient: " + patient_name, 0, 0, 'C');
                    self.cell(45);
                    self.cell(40, 25, "| Provider: " + provider_name, 0, 0, 'C');
                    self.cell(45);
                    self.cell(40, 25, "| Report Date: " + today, 0, 0, 'C');
                    self.cell(45);
                    self.cell(80, 25, "| Weekly Report From: Week " + str(start_week) + " To Week " + str(end_week), 0, 0, 'C');
                    self.ln(30);

                # Page footer
                def footer(self):
                    # Position at 1.5 cm from bottom
                    self.set_y(-15)
                    # Arial italic 8
                    self.set_font('Arial', 'I', 14)
                    # Page number
                    self.cell(0, 10, 'Page ' + str(self.page_no()) + '/{nb}', 0, 0, 'C')

            pdf = PDF(orientation='L', unit='mm', format=(230, 550))
            pdf.alias_nb_pages()
            pdf.add_page()

            pdf.set_font('Arial', '', 26)
            pdf.cell(w=0, h=10, txt="Patient Weekly Report", ln=1, align='C')


            for x in range(int(start_week), int(end_week) + 1):
                #pdf.ln(10)
                pdf.set_font('Arial', 'B', 18)
                pdf.cell(w=0, h=10, txt="Week" + str(x), ln=1,
                         align='C')
                pdf.ln(10)

                # Table Header
                pdf.set_font('Arial', 'B', 12)
                x1_value = pdf.get_x()
                y1_value = pdf.get_y()
                y2_value = y1_value + 15.0
                pdf.line(x1_value, y1_value, 535, y1_value)
                pdf.line(x1_value, y2_value, 535, y2_value)
                pdf.line(x1_value,y1_value,x1_value,y2_value)
                pdf.line(535, y1_value, 535, y2_value)
                pdf.cell(w=12, h=ch, txt='Days', border=0, ln=0, align='C')
                pdf.cell(w=27, h=ch, txt='Time Went', border=0, ln=0, align='C')
                pdf.cell(w=20, h=ch, txt='Lights', border=0, ln=0, align='C')
                pdf.cell(w=28, h=ch, txt='Minutes To', border=0, ln=0, align='C')
                pdf.cell(w=40, h=ch, txt='How Many Times', border=0, ln=0, align='C')
                pdf.cell(w=30, h=ch, txt='Awake During', border=0, ln=0, align='C')
                pdf.cell(w=26, h=ch, txt='Time You', border=0, ln=0, align='C')
                pdf.cell(w=34, h=ch, txt='Minutes Fell', border=0, ln=0, align='C')
                pdf.cell(w=28, h=ch, txt='Got Up', border=0, ln=0, align='C')
                pdf.cell(w=32, h=ch, txt='Desired', border=0, ln=0, align='C')
                pdf.cell(w=20, h=ch, txt='No. Of', border=0, ln=0, align='C')
                pdf.cell(w=38, h=ch, txt='Total Time', border=0, ln=0, align='C')
                pdf.cell(w=17, h=ch, txt='Time In', border=0, ln=0, align='C')
                pdf.cell(w=19, h=ch, txt='Time', border=0, ln=0, align='C')
                pdf.cell(w=20, h=ch, txt='Sleep', border=0, ln=0, align='C')
                pdf.cell(w=32, h=ch, txt='Problem', border=0, ln=0, align='C')
                pdf.cell(w=28, h=ch, txt='Awake', border=0, ln=0, align='C')
                pdf.cell(w=24, h=ch, txt='Awake', border=0, ln=0, align='C')
                pdf.cell(w=28, h=ch, txt='Delayed', border=0, ln=0, align='C')
                pdf.cell(w=20, h=ch, txt='Overslept', border=0, ln=1, align='C')




                pdf.cell(w=12, h=ch, txt='', border=0, ln=0, align='C')
                pdf.cell(w=27, h=ch, txt='To Bed', border=0, ln=0, align='C')
                pdf.cell(w=20, h=ch, txt='Out', border=0, ln=0, align='C')
                pdf.cell(w=28, h=ch, txt='Fall Asleep', border=0, ln=0, align='C')
                pdf.cell(w=40, h=ch, txt='You Woke Up', border=0, ln=0, align='C')
                pdf.cell(w=30, h=ch, txt='The Night', border=0, ln=0, align='C')
                pdf.cell(w=26, h=ch, txt='Woke Up', border=0, ln=0, align='C')
                pdf.cell(w=34, h=ch, txt='Back To Sleep', border=0, ln=0, align='C')
                pdf.cell(w=28, h=ch, txt='From Bed', border=0, ln=0, align='C')
                pdf.cell(w=32, h=ch, txt='Wake Up Time', border=0, ln=0, align='C')
                pdf.cell(w=20, h=ch, txt='Naps', border=0, ln=0, align='C')
                pdf.cell(w=38, h=ch, txt='Napping In Mints', border=0, ln=0, align='C')
                pdf.cell(w=17, h=ch, txt='Bed', border=0, ln=0, align='C')
                pdf.cell(w=19, h=ch, txt='Asleep', border=0, ln=0, align='C')
                pdf.cell(w=20, h=ch, txt='Effcy %', border=0, ln=0, align='C')
                pdf.cell(w=32, h=ch, txt='Falling Asleep', border=0, ln=0, align='C')
                pdf.cell(w=28, h=ch, txt='During Night', border=0, ln=0, align='C')
                pdf.cell(w=24, h=ch, txt='Too Early', border=0, ln=0, align='C')
                pdf.cell(w=28, h=ch, txt='Getting Up', border=0, ln=0, align='C')
                pdf.cell(w=20, h=ch, txt='', border=0, ln=1, align='C')


                # Table contents
                pdf.set_font('Arial', '', 12)
                i = 1
                for index, item in enumerate(sleep_report, start=1):
                    print("COUNT", count)
                    print("INDEX", index)
                    if count == index:
                        if count <= f_end:
                            if i == 1 or i <= 7:
                                pdf.set_text_color(0, 0, 0)
                                pdf.cell(w=12, h=ch,
                                         txt=str(i),
                                         border=1, ln=0, align='C')
                                a = datetime.datetime.strptime(item.time_went_to_bed, '%H:%M:%S').time()
                                a = a.strftime('%I:%M %p')
                                pdf.set_text_color(0, 0, 0)
                                pdf.cell(w=27, h=ch,
                                         txt=str(a),
                                         border=1, ln=0, align='C')
                                a = datetime.datetime.strptime(item.lights_out, '%H:%M:%S').time()
                                a = a.strftime('%I:%M %p')
                                pdf.set_text_color(0, 0, 0)
                                pdf.cell(w=20, h=ch,
                                         txt=str(a),
                                         border=1, ln=0, align='C')
                                pdf.set_text_color(0, 0, 0)
                                pdf.cell(w=28, h=ch,
                                         txt=str(item.minutes_fall_asleep),
                                         border=1, ln=0, align='C')
                                pdf.set_text_color(0, 0, 0)
                                pdf.cell(w=40, h=ch,
                                         txt=str(item.no_of_times_awakend),
                                         border=1, ln=0, align='C')
                                pdf.set_text_color(0, 0, 0)
                                pdf.cell(w=30, h=ch,
                                         txt=str(item.awake_during_night),
                                         border=1, ln=0, align='C')
                                a = datetime.datetime.strptime(item.time_got_up, '%H:%M:%S').time()
                                a = a.strftime('%I:%M %p')
                                pdf.set_text_color(0, 0, 0)
                                pdf.cell(w=26, h=ch,
                                         txt=str(a),
                                         border=1, ln=0, align='C')
                                pdf.set_text_color(0, 0, 0)
                                pdf.cell(w=34, h=ch,
                                         txt=str(item.minutes_fellback_sleep),
                                         border=1, ln=0, align='C')
                                a = datetime.datetime.strptime(item.out_of_bed, '%H:%M:%S').time()
                                a = a.strftime('%I:%M %p')
                                pdf.set_text_color(0, 0, 0)
                                pdf.cell(w=28, h=ch,
                                         txt=str(a),
                                         border=1, ln=0, align='C')
                                a = datetime.datetime.strptime(item.desire_wakeup_time, '%H:%M:%S').time()
                                a = a.strftime('%I:%M %p')
                                pdf.set_text_color(0, 0, 0)
                                pdf.cell(w=32, h=ch,
                                         txt=str(a),
                                         border=1, ln=0, align='C')
                                pdf.set_text_color(0, 0, 0)
                                pdf.cell(w=20, h=ch,
                                         txt=str(item.number_of_naps),
                                         border=1, ln=0, align='C')
                                pdf.set_text_color(0, 0, 0)
                                pdf.cell(w=38, h=ch,
                                         txt=str(item.totlatime_napping_minutes),
                                         border=1, ln=0, align='C')
                                pdf.set_text_color(0, 0, 0)
                                pdf.cell(w=17, h=ch,
                                         txt=str(item.time_in_bed),
                                         border=1, ln=0, align='C')

                                if (float(item.total_sleep_time) < 5.5):
                                    pdf.set_font('Arial', 'B', 13)
                                    pdf.set_text_color(0, 0, 0)
                                    pdf.cell(w=19, h=ch,
                                             txt=str(item.total_sleep_time),
                                             border=1, ln=0, align='C')
                                else:
                                    pdf.cell(w=19, h=ch,
                                             txt=str(item.total_sleep_time),
                                             border=1, ln=0, align='C')
                                pdf.set_font('Arial', '', 12)
                                pdf.set_text_color(0, 0, 0)
                                pdf.cell(w=20, h=ch,
                                         txt=str(item.sleep_efficiency),
                                         border=1, ln=0, align='C')

                                pdf.set_text_color(255, 0, 0)
                                pdf.cell(w=32, h=ch,
                                         txt=str(item.problem_falling_asleep),
                                         border=1, ln=0, align='C')
                                pdf.set_text_color(255, 0, 0)
                                pdf.cell(w=28, h=ch,
                                         txt=str(item.awake_during_night),
                                         border=1, ln=0, align='C')
                                pdf.set_text_color(255, 0, 0)
                                pdf.cell(w=24, h=ch,
                                         txt=str(item.awake_too_early),
                                         border=1, ln=0, align='C')
                                pdf.set_text_color(255, 0, 0)
                                pdf.cell(w=28, h=ch,
                                         txt=str(item.delayed_getting_up),
                                         border=1, ln=0, align='C')
                                pdf.set_text_color(255, 0, 0)
                                pdf.cell(w=22, h=ch,
                                         txt=str(item.overslept),
                                         border=1, ln=1, align='C')
                                pdf.set_text_color(0, 0, 0)
                                if(item.comment):
                                    pdf.multi_cell(w=525, h=ch,
                                             txt="Comment: "+ str(item.comment),
                                             border=1, align='L')
                                    pdf.ln(0)
                                print("all good")
                                i = i + 1
                                count = count + 1
                                continue
                            else:
                                break
                        else:
                            count = count + 1
                            continue
                    else:
                        continue
            print("yhn pa n hi arhaha")
            pdf.set_text_color(0, 0, 0)
            pdf.cell(w=100, h=16, txt="Reviewed By: " + provider_name, border=0, ln=0, align='L')
            pdf.cell(w=0,h=18, txt="", ln=1)
            pdf.cell(w=30, h=16, txt="Provider Signature: ", border=0, ln=0, align='L')
            x = pdf.get_x()
            y = pdf.get_y()
            pdf.line(x + 9, y + 9, x + 100, y + 9)
            pdf.cell(180)
            pdf.cell(w=30, h=16, txt="Date: ", border=0, ln=0, align='L')
            x = pdf.get_x()
            y = pdf.get_y()
            pdf.line(x - 18, y + 9, (x + 100), y + 9)
            file_name = patient_name + "_" + str(id) + "_" + provider_id + ".pdf"
            filepath = os.path.join(BASE_DIR, 'media')
            pdf.output(filepath+"/"+file_name, 'F')
            print("Report Created Successfully", file_name)
            result = send_fax_directly_ciq(file_name, id)
            if result == "success":
                return ("success")
            else:
                return ("failed")


    except Exception as e:
        print(e)
        return redirect('/')

######################################### MA PATIENT DASHBOARD ###############################
@login_required
def ma_patient_dashboard(request, pat_id = 0):
        mylist = []
        mysearch = ""
        user_name = ""
        user_image = ""
        user_access = ""
        ma = True
        try:

            checkUser = request.user.id
            if checkUser is None:
                return redirect('/')



            user_profile = Provider.objects.get(user_id=request.user.id)
            user_name = user_profile.first_name + " " + user_profile.last_name
            user_image = user_profile.provider_image


            userInfo = user_profile
            reqWeeks = 6
            reqWeeks = 6

            _title = "CogniSleep |  Cogni-Ma-Patient-Dashboard"
            user_ref_data_array = []
            loggedUser = User.objects.get(id=pat_id)

            UsersleepData = SleepDiary.objects.filter(patient_id=pat_id, is_updated=1)
            isSleepDiaryData = UsersleepData.count()
            sleepdiary_ids = SleepDiary.objects.raw(
                "SELECT id, max(id) lastid , min(id) as firstid FROM dashboard_sleepdiary WHERE patient_id=%s",
                [int(pat_id)])
            sleepdiary_dates = SleepDiary.objects.raw(
                "SELECT id,date FROM dashboard_sleepdiary WHERE id IN(%s,%s)",
                [int(sleepdiary_ids[0].firstid), int(sleepdiary_ids[0].lastid)])
            sleep_diary_entries = SleepDiary.objects.raw(
                "SELECT id,count(*) as sleep_diary_entries FROM dashboard_sleepdiary WHERE patient_id=%s and is_updated=1",
                [int(pat_id)])

            next_entry_date = SleepDiary.objects.raw(
                "SELECT id,date FROM dashboard_sleepdiary WHERE patient_id=%s and is_updated=0 limit 1",
                [int(pat_id)])

            viewVideosResult = VideoAnswers.objects.raw(
                "SELECT id,count(*) as countvideos FROM video_answers WHERE user_id=%s",
                [int(pat_id)])

            video_view_count = video_count(pat_id)

            label_tag = "Do it Now"
            Weeks = 1
            days = 1
            dayscount = int(sleep_diary_entries[0].sleep_diary_entries)
            days = dayscount
            view = 0
            now = datetime.date.today()
            current_date = now.strftime("%A %B %d ,%Y")

            if dayscount < 7:
                Weeks = 1
                days = days + 1

            if dayscount < 14 and dayscount >= 7:
                Weeks = 2
                days = days - 6

            if dayscount < 21 and dayscount >= 14:
                Weeks = 3
                days = days - 13

            if dayscount < 28 and dayscount >= 21:
                Weeks = 4
                days = days - 20

            if dayscount < 35 and dayscount >= 28:
                Weeks = 5
                days = days - 27

            if dayscount < 42 and dayscount >= 35:
                Weeks = 6
                days = days - 34

            if dayscount < 49 and dayscount >= 42:
                Weeks = 7
                days = days - 41

            if days == 0:
                days = 1

            next_session_week = Weeks - 1

            date_time_obj1 = datetime.datetime.strptime(str(next_entry_date[0].date), '%Y-%m-%d')
            date_time_obj = datetime.date.strftime(date_time_obj1, "%A, %B %d, %Y")
            today = datetime.date.today()
            year = today.year
            print(request.user.id)
            pre_exists = UserAnswer.objects.filter(user_id=pat_id, question__is_pre=True,
                                                   question__year=year).exists()
            post_exists = UserAnswer.objects.filter(user_id=pat_id, question__is_post=True,
                                                    question__year=year).exists()

            print(pre_exists)
            print(post_exists)
            if pre_exists == True and post_exists == False:
                rec = SendFax.objects.filter(patient_id=pat_id).exists()

                if rec == True:
                    pass
                else:
                    create_ciq_report_directly(pat_id)
                    recs = SendFax(patient_id=pat_id, pre_ciq=1)
                    recs.save()
                    print("Record Save Successfully!")
            if pre_exists == True and post_exists == True:
                rec = SendFax.objects.filter(patient_id=pat_id).exists()
                if rec == True:

                    create_ciq_report_directly(pat_id)
                    recs = SendFax.objects.get(patient_id=pat_id)
                    recs.post_ciq = 1
                    recs.save()
                    print("Record Save Successfully!")
                else:
                    pass

            sleep_entry = ""
            last_week = ""
            each_day_quote = ""
            avgvalue = "N/A"
            presbedtime = "N/A"
            s_time = "N/A"
            if sleep_diary_entries[0].sleep_diary_entries == 0:
                sleep_entry = "No Entry"
                last_week = "1"
            if sleep_diary_entries[0].sleep_diary_entries == 1:
                sleep_entry = "Week 1 Day 1"
                last_week = "1"
                each_day_quote = "Keep up the good work!"

            if sleep_diary_entries[0].sleep_diary_entries == 2:
                sleep_entry = "Week 1 Day 2"
                last_week = "1"
                each_day_quote = "Sleeping through the night is possible!"
            if sleep_diary_entries[0].sleep_diary_entries == 3:
                sleep_entry = "Week 1 Day 3"
                last_week = "1"
                each_day_quote = "You can do this!"
            if sleep_diary_entries[0].sleep_diary_entries == 4:
                sleep_entry = "Week 1 Day 4"
                last_week = "1"
                each_day_quote = "Insomnia is no match for you!"
            if sleep_diary_entries[0].sleep_diary_entries == 5:
                sleep_entry = "Week 1 Day 5"
                last_week = "1"
                each_day_quote = "Sleep restrictions may be difficult but they are worth it!"
            if sleep_diary_entries[0].sleep_diary_entries == 6:
                sleep_entry = "Week 1 Day 6"
                last_week = "1"
                each_day_quote = "You deserve a good night's sleep"
            if sleep_diary_entries[0].sleep_diary_entries == 7:
                val = PatientEfficiency.objects.filter(patient_id=pat_id).count()
                if val == 1:
                    print("yes in this condition")
                    sleep_entry = "Week 1 Day 7"
                    last_week = "1"
                    each_day_quote = "Positive thoughts can make a world of difference for your sleep!"

                    rec = SendFax.objects.filter(patient_id=pat_id, weekno=1).exists()
                    if rec == True:
                        pass
                    else:
                        create_pdf_report_weekly_directly(pat_id, 1)
                        rec = SendFax.objects.get(patient_id=pat_id)
                        rec.weekno = 1
                        rec.save()
                else:
                    avgsleepefficieny(pat_id)
                    sugges_wakeup_time(pat_id)
                    sleep_entry = "Week 1 Day 7"
                    last_week = "1"
                    each_day_quote = "Positive thoughts can make a world of difference for your sleep!"
            if sleep_diary_entries[0].sleep_diary_entries == 8:
                sleep_entry = "Week 2 Day 1"
                last_week = "2"
                each_day_quote = "Lock negative thoughts away in your NTL!"
            if sleep_diary_entries[0].sleep_diary_entries == 9:
                sleep_entry = "Week 2 Day 2"
                last_week = "2"
                each_day_quote = "You have power over your thoughts"
            if sleep_diary_entries[0].sleep_diary_entries == 10:
                sleep_entry = "Week 2 Day 3"
                last_week = "2"
                each_day_quote = "You are not alone in your fight against insomnia!"
            if sleep_diary_entries[0].sleep_diary_entries == 11:
                sleep_entry = "Week 2 Day 4"
                last_week = "2"
                each_day_quote = "You've got this!"
            if sleep_diary_entries[0].sleep_diary_entries == 12:
                sleep_entry = "Week 2 Day 5"
                last_week = "2"
                each_day_quote = "Tip: You can use your NTL during the day to lock negative thoughts away!"
            if sleep_diary_entries[0].sleep_diary_entries == 13:
                sleep_entry = "Week 2 Day 6"
                last_week = "2"
                each_day_quote = "Don't give up!"
            if sleep_diary_entries[0].sleep_diary_entries == 14:
                val = PatientEfficiency.objects.filter(patient_id=pat_id).count()
                if val == 2:
                    sleep_entry = "Week 2 Day 7"
                    last_week = "2"
                    each_day_quote = "Insomnia is tough but you're tougher"

                    rec = SendFax.objects.filter(patient_id=pat_id, weekno=2).exists()
                    if rec == True:
                        pass
                    else:
                        create_pdf_report_weekly_directly(pat_id, 2)
                        rec = SendFax.objects.get(patient_id=pat_id)
                        rec.weekno = 2
                        rec.save()
                else:
                    if not last_week:
                        avgsleepefficieny(pat_id)
                        sugges_wakeup_time(pat_id)
                    avgsleepefficieny(pat_id)
                    sugges_wakeup_time(pat_id)
                    sleep_entry = "Week 2 Day 7"
                    last_week = "2"
                    each_day_quote = "Insomnia is tough but you're tougher"
            if sleep_diary_entries[0].sleep_diary_entries == 15:
                sleep_entry = "Week 3 Day 1"
                last_week = "3"
                each_day_quote = "Believe in yourself"
            if sleep_diary_entries[0].sleep_diary_entries == 16:
                sleep_entry = "Week 3 Day 2"
                last_week = "3"
                each_day_quote = "Keep moving forward"
            if sleep_diary_entries[0].sleep_diary_entries == 17:
                sleep_entry = "Week 3 Day 3"
                last_week = "3"
                each_day_quote = "Give yourself some credit for all you’ve done so far"
            if sleep_diary_entries[0].sleep_diary_entries == 18:
                sleep_entry = "Week 3 Day 4"
                last_week = "3"
                each_day_quote = "Everyday is a new beginning"
            if sleep_diary_entries[0].sleep_diary_entries == 19:
                sleep_entry = "Week 3 Day 5"
                last_week = "3"
                each_day_quote = "Staying positive can make all the difference"
            if sleep_diary_entries[0].sleep_diary_entries == 20:
                sleep_entry = "Week 3 Day 6"
                last_week = "3"
                each_day_quote = "All progress is good progress"
            if sleep_diary_entries[0].sleep_diary_entries == 21:
                val = PatientEfficiency.objects.filter(patient_id=pat_id).count()
                if val == 3:
                    sleep_entry = "Week 3 Day 7"
                    last_week = "3"
                    each_day_quote = "There is something good in every day"
                    rec = SendFax.objects.filter(patient_id=pat_id, weekno=3).exists()
                    if rec == True:
                        pass
                    else:
                        create_pdf_report_weekly_directly(pat_id, 3)
                        rec = SendFax.objects.get(patient_id=pat_id)
                        rec.weekno = 3
                        rec.save()
                else:
                    if not last_week:
                        avgsleepefficieny(pat_id)
                        sugges_wakeup_time(pat_id)
                    avgsleepefficieny(pat_id)
                    sugges_wakeup_time(pat_id)
                    sleep_entry = "Week 3 Day 7"
                    last_week = "3"
                    each_day_quote = "There is something good in every day"
            if sleep_diary_entries[0].sleep_diary_entries == 22:
                sleep_entry = "Week 4 Day 1"
                last_week = "4"
                each_day_quote = "You are taking the right steps to get your sleep back on track!"
            if sleep_diary_entries[0].sleep_diary_entries == 23:
                sleep_entry = "Week 4 Day 2"
                last_week = "4"
                each_day_quote = "You are on the road to overcoming insomnia"
            if sleep_diary_entries[0].sleep_diary_entries == 24:
                sleep_entry = "Week 4 Day 3"
                last_week = "4"
                each_day_quote = "Restful sleep is just a nighttime away"
            if sleep_diary_entries[0].sleep_diary_entries == 25:
                sleep_entry = "Week 4 Day 4"
                last_week = "4"
                each_day_quote = "Quality sleep will transform your life. Keep it up!"
            if sleep_diary_entries[0].sleep_diary_entries == 26:
                sleep_entry = "Week 4 Day 5"
                last_week = "4"
                each_day_quote = "Learn to love your sleep again"
            if sleep_diary_entries[0].sleep_diary_entries == 27:
                sleep_entry = "Week 4 Day 6"
                last_week = "4"
                each_day_quote = "Your life is about to become so much better"
            if sleep_diary_entries[0].sleep_diary_entries == 28:
                val = PatientEfficiency.objects.filter(patient_id=pat_id).count()
                if val == 4:
                    sleep_entry = "Week 4 Day 7"
                    last_week = "4"
                    each_day_quote = "The time is right for overcoming insomnia"
                    rec = SendFax.objects.filter(patient_id=pat_id, weekno=4).exists()
                    if rec == True:
                        pass
                    else:
                        create_pdf_report_weekly_directly(pat_id, 4)
                        rec = SendFax.objects.get(patient_id=pat_id)
                        rec.weekno = 4
                        rec.save()
                else:
                    if not last_week:
                        avgsleepefficieny(pat_id)
                        sugges_wakeup_time(pat_id)
                    avgsleepefficieny(pat_id)
                    sugges_wakeup_time(pat_id)
                    sleep_entry = "Week 4 Day 7"
                    last_week = "4"
                    each_day_quote = "The time is right for overcoming insomnia"
            if sleep_diary_entries[0].sleep_diary_entries == 29:
                sleep_entry = "Week 5 Day 1"
                last_week = "5"
                each_day_quote = "You're addressing your sleeplessness head-on. Way to go!"
            if sleep_diary_entries[0].sleep_diary_entries == 30:
                sleep_entry = "Week 5 Day 2"
                last_week = "5"
                each_day_quote = "Overcoming sleeplessness is happening now!"
            if sleep_diary_entries[0].sleep_diary_entries == 31:
                sleep_entry = "Week 5 Day 3"
                last_week = "5"
                each_day_quote = "Don't let insomnia drag you down! This is a fight you will win!"
            if sleep_diary_entries[0].sleep_diary_entries == 32:
                sleep_entry = "Week 5 Day 4"
                last_week = "5"
                each_day_quote = "Love yourself enough to put your sleep health first"
            if sleep_diary_entries[0].sleep_diary_entries == 33:
                sleep_entry = "Week 5 Day 5"
                last_week = "5"
                each_day_quote = "Self-care, self-value, and self-worth start with quality sleep"
            if sleep_diary_entries[0].sleep_diary_entries == 34:
                sleep_entry = "Week 5 Day 6"
                last_week = "5"
                each_day_quote = "Sleep will help you become an even better version of yourself"
            if sleep_diary_entries[0].sleep_diary_entries == 35:
                val = PatientEfficiency.objects.filter(patient_id=pat_id).count()
                if val == 5:
                    sleep_entry = "Week 5 Day 7"
                    last_week = "5"
                    each_day_quote = "We're rooting for you! You're not in this alone!"
                    rec = SendFax.objects.filter(patient_id=pat_id, weekno=5).exists()
                    if rec == True:
                        pass
                    else:
                        create_pdf_report_weekly_directly(pat_id, 5)
                        rec = SendFax.objects.get(patient_id=pat_id)
                        rec.weekno = 5
                        rec.save()
                else:
                    if not last_week:
                        avgsleepefficieny(pat_id)
                        sugges_wakeup_time(pat_id)
                    avgsleepefficieny(pat_id)
                    sugges_wakeup_time(pat_id)
                    sleep_entry = "Week 5 Day 7"
                    last_week = "5"
                    each_day_quote = "We're rooting for you! You're not in this alone!"
            if sleep_diary_entries[0].sleep_diary_entries == 36:
                sleep_entry = "Week 6 Day 1"
                last_week = "6"
                each_day_quote = "Keep pushing forward. Quality sleep will happen"
            if sleep_diary_entries[0].sleep_diary_entries == 37:
                sleep_entry = "Week 6 Day 2"
                last_week = "6"
                each_day_quote = "It's time to shape your destiny - and it starts with sleep!"
            if sleep_diary_entries[0].sleep_diary_entries == 38:
                sleep_entry = "Week 6 Day 3"
                last_week = "6"
                each_day_quote = "Embrace sleep and the amazing life you're supposed to be living"
            if sleep_diary_entries[0].sleep_diary_entries == 39:
                sleep_entry = "Week 6 Day 4"
                last_week = "6"
                each_day_quote = "Deep, revitalizing sleep awaits you"
            if sleep_diary_entries[0].sleep_diary_entries == 40:
                sleep_entry = "Week 6 Day 5"
                last_week = "6"
                each_day_quote = "Quality sleep is possible"
            if sleep_diary_entries[0].sleep_diary_entries == 41:
                sleep_entry = "Week 6 Day 6"
                last_week = "6"
                each_day_quote = "Live, breathe, and dream sleep"
            if sleep_diary_entries[0].sleep_diary_entries == 42:
                val = PatientEfficiency.objects.filter(patient_id=pat_id).count()
                if val == 6:
                    sleep_entry = "Week 6 Day 7"
                    last_week = "6"
                    each_day_quote = "Stay strong and fight sleeplessness"
                    rec = SendFax.objects.filter(patient_id=pat_id, weekno=6).exists()
                    if rec == True:
                        pass
                    else:
                        create_pdf_report_weekly_directly(pat_id, 6)
                        rec = SendFax.objects.get(patient_id=pat_id)
                        rec.weekno = 6
                        rec.save()
                else:
                    if not last_week:
                        avgsleepefficieny(pat_id)
                        sugges_wakeup_time(pat_id)
                    avgsleepefficieny(pat_id)
                    sugges_wakeup_time(pat_id)
                    sleep_entry = "Week 6 Day 7"
                    last_week = "6"
                    each_day_quote = "Stay strong and fight sleeplessness"

            # now creat code to watch video (New Dashboard)
            if sleep_diary_entries[0].sleep_diary_entries == 7 and video_view_count == 2:
                last_week = "2"
            if sleep_diary_entries[0].sleep_diary_entries == 7 and video_view_count == 1:
                view = 1
                video_view_count += 1
                label_tag = "Complete Now"
            if sleep_diary_entries[0].sleep_diary_entries == 14 and video_view_count == 3:
                last_week = "3"
            if sleep_diary_entries[0].sleep_diary_entries == 14 and video_view_count == 2:
                view = 1
                video_view_count += 1
                label_tag = "Complete Now"
            if sleep_diary_entries[0].sleep_diary_entries == 21 and video_view_count == 4:
                last_week = "4"
            if sleep_diary_entries[0].sleep_diary_entries == 21 and video_view_count == 3:
                view = 1
                video_view_count += 1
                label_tag = "Complete Now"
            if sleep_diary_entries[0].sleep_diary_entries == 28 and video_view_count == 5:
                last_week = "5"
            if sleep_diary_entries[0].sleep_diary_entries == 28 and video_view_count == 4:
                view = 1
                video_view_count += 1
                label_tag = "Complete Now"
            if sleep_diary_entries[0].sleep_diary_entries == 35 and video_view_count == 6:
                last_week = "6"
            if sleep_diary_entries[0].sleep_diary_entries == 35 and video_view_count == 5:
                view = 1
                video_view_count += 1
                label_tag = "Complete Now"
            if sleep_diary_entries[0].sleep_diary_entries == 42 and video_view_count == 7:
                last_week = "7"
                view = 2
                # lock_diary = 1
            if sleep_diary_entries[0].sleep_diary_entries == 42 and video_view_count == 6:
                view = 1
                video_view_count += 1
                label_tag = "Complete Now"
            # for week-2
            if sleep_diary_entries[
                0].sleep_diary_entries == 7 and current_date == date_time_obj and video_view_count == 1:
                view = 1
                video_view_count += 1
            # for week-3
            if sleep_diary_entries[
                0].sleep_diary_entries == 14 and current_date == date_time_obj and video_view_count == 2:
                view = 1
                video_view_count += 1
            # for week-4
            if sleep_diary_entries[
                0].sleep_diary_entries == 21 and current_date == date_time_obj and video_view_count == 3:
                view = 1
                video_view_count += 1
            # for week-5
            if sleep_diary_entries[
                0].sleep_diary_entries == 28 and current_date == date_time_obj and video_view_count == 4:
                view = 1
                video_view_count += 1
            # for week-6
            if sleep_diary_entries[
                0].sleep_diary_entries == 35 and current_date == date_time_obj and video_view_count == 5:
                view = 1
                video_view_count += 1
            # for week-7
            if sleep_diary_entries[
                0].sleep_diary_entries == 42 and current_date == date_time_obj and video_view_count == 6:
                view = 1
                video_view_count += 1
            if PatientEfficiency.objects.filter(patient_id=pat_id).exists():
                data = PatientEfficiency.objects.filter(patient_id=pat_id).order_by("-id")[0]
                avgvalue = data.sleep_efficiency
                preb_time = data.bed_time
                s_time = data.sugg_wake_up
                t1 = datetime.datetime.strptime(preb_time, ("%H:%M:%S"))
                t2 = datetime.datetime.strptime(s_time, ("%H:%M:%S"))
                tt1 = datetime.timedelta(hours=t1.hour, minutes=t1.minute).total_seconds()
                t1s = datetime.timedelta(minutes=t1.minute).total_seconds()
                s_time = round_time(s_time)
                tt2 = datetime.timedelta(hours=t2.hour, minutes=t2.minute).total_seconds()
                if tt1 > tt2:
                    df = tt1 - tt2
                    sdf = 3600 - t1s
                    ssdf = 43200 - (t1s + sdf)
                    if df < 19800:
                        xx = 19800 - df
                        x1 = t1 - datetime.timedelta(seconds=xx)
                        x1 = datetime.datetime.strftime(x1, '%H:%M:%S')
                        presbedtime = round_time(str(x1))
                    if df > 43200:
                        fdf = df - 23400
                        if fdf < 43200:
                            presbedtime = round_time(preb_time)
                        else:
                            xx = df - 19800
                            x1 = t1 - datetime.timedelta(seconds=xx)
                            x1 = x1 - datetime.timedelta(seconds=ssdf)
                            x1 = datetime.datetime.strftime(x1, '%H:%M:%S')
                            presbedtime = round_time(str(x1))
                    else:
                        presbedtime = round_time(preb_time)

                if tt1 < tt2:
                    df = tt2 - tt1
                    if df < 19800:
                        xx = 19800 - df
                        x1 = t1 - datetime.timedelta(seconds=xx)
                        x1 = datetime.datetime.strftime(x1, '%H:%M:%S')
                        presbedtime = round_time(str(x1))
                    else:
                        presbedtime = round_time(preb_time)
            provider_data = profile(pat_id)
            rest_day = [0, 7, 14, 21, 28, 35, 42]
            context = {
                "title": _title,
                "avgsleep": avgvalue,
                "avgbedtime": presbedtime,
                "sug_time": s_time,
                "base_url": settings.BASE_URL,
                "first_name": '',
                'quote': each_day_quote,
                # "lock_diary": lock_diary,
                "entry": sleep_entry,
                "rest_day": rest_day,
                "week": reqWeeks,
                "view": view,
                "lweek": last_week,
                "video_view": video_view_count,
                "userdata": user_profile,
                "loggedUser": loggedUser,
                "patient": pat_id,
                "today_date": current_date,
                "isSleepDiaryData": isSleepDiaryData,
                "sleepdiary_startDate": sleepdiary_dates[0].date,
                "sleepdiary_endDate": sleepdiary_dates[1].date,
                "sleep_diary_entries": sleep_diary_entries[0].sleep_diary_entries,
                "Weeks": Weeks,
                "days": days,
                "user_name": user_name,
                "user_image": user_image,
                "role_id": 5,
                "label_data": label_tag,
                "next_session_week": next_session_week,
                "next_entry_date": date_time_obj,
                "answer_videos": viewVideosResult[0].countvideos,
                "provider_data": provider_data,
                "ma":ma
            }

            return render(request, "dashboard.html", context)

        except Exception as e:
            print(e)
            return redirect('/')

def ma_diary(request, wday, pid=0):
    user_name = ""
    user_image = ""
    ma = True
    try:
        userID = pid
        print("yes ma duary")
        print(pid)
        print("shakaib")
        user_profile = Provider.objects.get(user_id=request.user.id)
        user_name = user_profile.first_name + " " + user_profile.last_name
        user_image = user_profile.provider_image
        print(user_name)
        userInfo = RefPatient.objects.get(user_id=userID)
        UsersleepData = SleepDiary.objects.filter(patient_id=userID)

        print("UserData: ", UsersleepData.count())

        bed_time = "00:00"
        reqWeeks = 6


        no_of_days = reqWeeks * 7
        week_day = wday

        bedtime_array = []
        weekDates_array = []
        weekDay_array = []
        weekDays_array = []

        today = datetime.datetime.now().date()

        if week_day == 0:
            start = userInfo.timestamp.date() + timedelta(days=1)
        else:
            start = userInfo.timestamp.date() + timedelta(days=week_day * 7 + 1)
        end = start + timedelta(days=7 - 1)
        end__ = userInfo.timestamp.date() + timedelta(days=7)

        start_date = datetime.date(start.year, start.month, start.day)
        end_date = datetime.date(end.year, end.month, end.day)

        invoice_for_today = SleepDiary.objects.raw(
            "SELECT * FROM dashboard_sleepdiary where patient_id=%s and date BETWEEN %s and %s",
            [str(userID), start_date, end_date])
        get_oldBedTimes = SleepDiary.objects.raw(
            "SELECT * FROM dashboard_sleepdiary where patient_id=%s and time_went_to_bed!=''  ",
            [str(userID)])

        user_date_array = []

        for dt in daterange(start, end):
            weekDates_array.append(dt.strftime("%Y/%m/%d"))
            if dt.weekday() == 0:
                weekDay_array.append(dt.strftime("%Y/%m/%d"))

        _title = "CogniSleep |  Cogni-Dashboard"
        loggedUser = userID

        weekday = []

        x = 1
        for week in weekDates_array:

            if x <= 8:
                week_array = {
                    "x": x,
                    "week_date": week,

                }
                weekday.append(week_array)
                x += 1

        for x in range(1, reqWeeks + 1):

            if int(x) == week_day:

                if PatientEfficiency.objects.filter(patient_id=userID, week_no=x).exists():
                    data = PatientEfficiency.objects.get(patient_id=userID, week_no=x)
                    week_array = {
                        "x": x,
                        "week_date": week,
                        "is_selected": 1,
                        "eff": data.sleep_efficiency
                    }
                    weekDays_array.append(week_array)
                else:
                    week_array = {
                        "x": x,
                        "week_date": week,
                        "is_selected": 1,
                        "eff": ""
                    }
                    weekDays_array.append(week_array)
            else:

                if PatientEfficiency.objects.filter(patient_id=userID, week_no=x).exists():
                    data = PatientEfficiency.objects.get(patient_id=userID, week_no=x)
                    week_array = {
                        "x": x,
                        "week_date": week,
                        "is_selected": 0,
                        "eff": data.sleep_efficiency
                    }
                    weekDays_array.append(week_array)
                else:
                    week_array = {
                        "x": x,
                        "week_date": week,
                        "is_selected": 0,
                        "eff": ""
                    }
                    weekDays_array.append(week_array)

        # print(weekDays_array)

        #global lock_diary
        video_view_count = video_count(request.user.id)
        wokeuptime = ""
        gotuptime = ""
        outofbed = ""
        nextDate = SleepDiary.objects.raw(
            "SELECT id,date as sleep_diary_entries FROM dashboard_sleepdiary WHERE patient_id=%s and is_updated=0 limit 1",
            [int(pid)])

        if request.method == 'POST':
            print("Yes POST METHOD")
            if request.user.role_id == 3:
                curUserID = Patient.objects.get(user_id=request.user.id)
            elif request.user.role_id == 2:
                curUserID = RefPatient.objects.get(user_id=request.user.id)
            elif request.user.role_id == 1:
                curUserID = RefPatient.objects.get(user_id=request.user.id)

            if request.user.role_id == 1:
                return redirect("/dashboard/")
            # print(request.get_full_path())
            # print(request.POST)

            form = SleepDiaruForm(request.POST)
            print(form.errors)
            print("validating form")
            if form.is_valid():
                print("YES FORM IS VALID")
                print(request.POST)
                print(request.POST.get('sdate'))
                date_time_obj1 = datetime.datetime.strptime(str(nextDate[0].sleep_diary_entries), '%Y-%m-%d')
                print(date_time_obj1)
                # sleepData = SleepDiary.objects.filter(date=request.POST.get('sdate'), patient_id=request.user.id)
                sleepData = SleepDiary.objects.filter(date=date_time_obj1, patient_id=pid)
                # print(date_time_obj1)
                print("sleep diary data count:", sleepData.count())
                sleepdur_id = sleepData.get().id
                if sleepData.count() > 0 and sleepData.get().is_updated == 1:
                    messages.error(request, "Date already exist.")
                    # print("Date already exist.")
                    avgvalue = "N/A"
                    presbedtime = "N/A"
                    s_time = "N/A"
                    if PatientEfficiency.objects.filter(patient_id=pid).exists():
                        data = PatientEfficiency.objects.filter(patient_id=pid).order_by("-id")[0]
                        avgvalue = data.sleep_efficiency
                        preb_time = data.bed_time
                        s_time = data.sugg_wake_up
                        t1 = datetime.datetime.strptime(preb_time, ("%H:%M:%S"))
                        t2 = datetime.datetime.strptime(s_time, ("%H:%M:%S"))
                        tt1 = datetime.timedelta(hours=t1.hour, minutes=t1.minute).total_seconds()
                        t1s = datetime.timedelta(minutes=t1.minute).total_seconds()
                        s_time = round_time(s_time)
                        tt2 = datetime.timedelta(hours=t2.hour, minutes=t2.minute).total_seconds()
                        if tt1 > tt2:
                            df = tt1 - tt2
                            sdf = 3600 - t1s
                            ssdf = 43200 - (t1s + sdf)
                            if df < 19800:
                                xx = 19800 - df
                                x1 = t1 - datetime.timedelta(seconds=xx)
                                x1 = datetime.datetime.strftime(x1, '%H:%M:%S')
                                presbedtime = round_time(str(x1))
                            if df > 43200:
                                fdf = df - 23400
                                if fdf < 43200:
                                    presbedtime = round_time(preb_time)
                                else:
                                    xx = df - 19800
                                    x1 = t1 - datetime.timedelta(seconds=xx)
                                    x1 = x1 - datetime.timedelta(seconds=ssdf)
                                    x1 = datetime.datetime.strftime(x1, '%H:%M:%S')
                                    presbedtime = round_time(str(x1))
                            else:
                                presbedtime = round_time(preb_time)

                        if tt1 < tt2:
                            df = tt2 - tt1
                            if df < 19800:
                                xx = 19800 - df
                                x1 = t1 - datetime.timedelta(seconds=xx)
                                x1 = datetime.datetime.strftime(x1, '%H:%M:%S')
                                presbedtime = round_time(str(x1))
                            else:
                                presbedtime = round_time(preb_time)
                    context = {
                        "title": _title,
                        "avgsleep": avgvalue,
                        "avgbedtime": presbedtime,
                        "sug_time": s_time,
                        #"lock_diary": lock_diary,
                        "video_view":video_view_count,
                        "base_url": settings.BASE_URL,
                        "first_name": '',
                        "loggedUser": loggedUser,
                        "form": form,
                        "tags": "dairy",
                        "patient": pid,
                        "user_name": user_name,
                        "user_image": user_image,
                        "role_id": 5,
                        "weekDay_array": weekday,
                        "current_week": wday,
                        "weekDays_array": weekDays_array,
                        'start_date': datetime.date.strftime(date_time_obj1, "%Y-%m-%d"),
                        "ma":ma,
                    }
                    return render(request, "sleepdiary.html", context)
                else:
                    try:
                        print("yes yes yes")
                        a1 = request.POST.get('awakeduringnight')
                        if a1 != "":
                            awakeduringnight = hourtomin(a1)
                        else:
                            awakeduringnight = a1
                        a2 = request.POST.get('awaketooearly')
                        if a2 != "":
                            awaketooearly = hourtomin(a2)
                        else:
                            awaketooearly = a2
                        a3 = request.POST.get('problemfallingasleep')
                        if a3 != "":
                            problemfallingasleep = hourtomin(a3)
                        else:
                            problemfallingasleep = a3
                        a4 = request.POST.get('delayedgettingup')
                        if a4 != "":
                            delayedgettingup = hourtomin(a4)
                        else:
                            delayedgettingup = a4
                    except Exception as e:
                        print(e)

                    tempdate = SleepDiary.objects.get(id=sleepdur_id)
                    print("Yes Updated")
                    tempdate.date = date_time_obj1  # request.POST.get('sdate')
                    tempdate.time_in_bed = request.POST.get('timeinbed')
                    # tempdate.time_in_bed = totalbed_time
                    tempdate.total_sleep_time = request.POST.get('totalsleeptime')
                    # tempdate.total_sleep_time = totalsleep_time
                    tempdate.sleep_efficiency = request.POST.get('sleepefficiency')
                    tempdate.comment = request.POST.get('comment')
                    # tempdate.sleep_efficiency = sleep_eff_final
                    tempdate.problem_falling_asleep = problemfallingasleep  # request.POST.get('problemfallingasleep')
                    tempdate.awake_during_night = awakeduringnight  # request.POST.get('awakeduringnight')
                    tempdate.awake_too_early = awaketooearly  # request.POST.get('awaketooearly')
                    tempdate.delayed_getting_up = delayedgettingup  # request.POST.get('delayedgettingup')
                    tempdate.overslept = request.POST.get('overslept')
                    tempdate.time_went_to_bed = form.cleaned_data['time_went_to_bed'] + ":00"
                    tempdate.lights_out = form.cleaned_data['lights_out'] + ":00"
                    tempdate.minutes_fall_asleep = form.cleaned_data['minutes_fall_asleep']
                    tempdate.time_fell_asleep = request.POST.get('totalsleep') + ":00"
                    tempdate.time_got_up = form.cleaned_data['time_got_up'] + ":00"
                    # tempdate.time_got_up = wokeuptime
                    tempdate.out_of_bed = form.cleaned_data['out_of_bed'] + ":00"
                    # tempdate.out_of_bed = outofbed
                    tempdate.minutes_fellback_sleep = form.cleaned_data['minutes_fellback_sleep']
                    tempdate.desire_wakeup_time = form.cleaned_data['desire_wakeup_time'] + ":00"
                    # tempdate.nap_time_asleep = form.cleaned_data['nap_time_asleep'] + ":00"
                    tempdate.number_of_naps = form.cleaned_data['number_of_naps']
                    tempdate.totlatime_napping_minutes = form.cleaned_data['totlatime_napping_minutes']
                    tempdate.no_of_times_awakend = form.cleaned_data['no_of_times_awakend']
                    tempdate.total_time_awakened = form.cleaned_data['total_time_awakened']
                    tempdate.total_gotup_time = request.POST.get('totalgotup') + ":00"
                    # tempdate.total_gotup_time = outofbed
                    tempdate.day_avg = day_avg(request.POST.get('totalsleep'), request.POST.get('totalgotup'),
                                               form.cleaned_data['time_went_to_bed'])

                    tempdate.is_updated = 1
                    tempdate.save()
                    logdata = Logfile(user_id=request.user.id, sleep_diary_date=date_time_obj1,patient_id = userID, user_type="MA")
                    logdata.save();

                    # print("Date saved")
                    form = SleepDiaruForm()
                    date_time_obj1 = datetime.datetime.strptime(str(nextDate[0].sleep_diary_entries), '%Y-%m-%d')
                    date_time_obj = datetime.date.strftime(date_time_obj1, "%m/%d/%Y")

                    form.fields["date"].initial = date_time_obj
                    avgvalue = "N/A"
                    presbedtime = "N/A"
                    s_time = "N/A"
                    if PatientEfficiency.objects.filter(patient_id=pid).exists():
                        data = PatientEfficiency.objects.filter(patient_id=pid).order_by("-id")[0]
                        avgvalue = data.sleep_efficiency
                        preb_time = data.bed_time
                        s_time = data.sugg_wake_up
                        t1 = datetime.datetime.strptime(preb_time, ("%H:%M:%S"))
                        t2 = datetime.datetime.strptime(s_time, ("%H:%M:%S"))
                        tt1 = datetime.timedelta(hours=t1.hour, minutes=t1.minute).total_seconds()
                        t1s = datetime.timedelta(minutes=t1.minute).total_seconds()
                        s_time = round_time(s_time)
                        tt2 = datetime.timedelta(hours=t2.hour, minutes=t2.minute).total_seconds()
                        if tt1 > tt2:
                            df = tt1 - tt2
                            sdf = 3600 - t1s
                            ssdf = 43200 - (t1s + sdf)
                            if df < 19800:
                                xx = 19800 - df
                                x1 = t1 - datetime.timedelta(seconds=xx)
                                x1 = datetime.datetime.strftime(x1, '%H:%M:%S')
                                presbedtime = round_time(str(x1))
                            if df > 43200:
                                fdf = df - 23400
                                if fdf < 43200:
                                    presbedtime = round_time(preb_time)
                                else:
                                    xx = df - 19800
                                    x1 = t1 - datetime.timedelta(seconds=xx)
                                    x1 = x1 - datetime.timedelta(seconds=ssdf)
                                    x1 = datetime.datetime.strftime(x1, '%H:%M:%S')
                                    presbedtime = round_time(str(x1))
                            else:
                                presbedtime = round_time(preb_time)

                        if tt1 < tt2:
                            df = tt2 - tt1
                            if df < 19800:
                                xx = 19800 - df
                                x1 = t1 - datetime.timedelta(seconds=xx)
                                x1 = datetime.datetime.strftime(x1, '%H:%M:%S')
                                presbedtime = round_time(str(x1))
                            else:
                                presbedtime = round_time(preb_time)
                    context = {
                        "title": _title,
                        "avgsleep": avgvalue,
                        "avgbedtime": presbedtime,
                        "sug_time": s_time,
                        #"lock_diary": lock_diary,
                        "video_view":video_view_count,
                        "base_url": settings.BASE_URL,
                        "first_name": '',
                        "loggedUser": loggedUser,
                        "form": form,
                        "patient": pid,
                        "current_week": wday,
                        "tags": "dairy",
                        "user_name": user_name,
                        "user_image": user_image,
                        "role_id": 5,
                        "weekDay_array": weekday,
                        "weekDays_array": weekDays_array,
                        'start_date': datetime.date.strftime(date_time_obj1, "%Y-%m-%d"),
                        "ma":ma,
                    }

                    messages.success(request, "Sleep diary data submitted successfully.")

                    return render(request, "sleepdiary_submitted.html", context)
        else:
            print("Form reload")
            form = SleepDiaruForm()
            date_time_obj1 = datetime.datetime.strptime(str(nextDate[0].sleep_diary_entries), '%Y-%m-%d')
            date_time_obj = datetime.date.strftime(date_time_obj1, "%m/%d/%Y")
            # date_time_obj2 = datetime.date.strftime(date_time_obj1, "%Y-%m-%d")
            # print(date_time_obj2)
            form.fields["date"].initial = date_time_obj
            avgvalue = "N/A"
            presbedtime = "N/A"
            s_time = "N/A"
            if PatientEfficiency.objects.filter(patient_id=pid).exists():
                data = PatientEfficiency.objects.filter(patient_id=pid).order_by("-id")[0]
                avgvalue = data.sleep_efficiency
                preb_time = data.bed_time
                s_time = data.sugg_wake_up
                t1 = datetime.datetime.strptime(preb_time, ("%H:%M:%S"))
                t2 = datetime.datetime.strptime(s_time, ("%H:%M:%S"))
                tt1 = datetime.timedelta(hours=t1.hour, minutes=t1.minute).total_seconds()
                t1s = datetime.timedelta(minutes=t1.minute).total_seconds()
                s_time = round_time(s_time)
                tt2 = datetime.timedelta(hours=t2.hour, minutes=t2.minute).total_seconds()
                if tt1 > tt2:
                    df = tt1 - tt2
                    sdf = 3600 - t1s
                    ssdf = 43200 - (t1s + sdf)
                    if df < 19800:
                        xx = 19800 - df
                        x1 = t1 - datetime.timedelta(seconds=xx)
                        x1 = datetime.datetime.strftime(x1, '%H:%M:%S')
                        presbedtime = round_time(str(x1))
                    if df > 43200:
                        fdf = df - 23400
                        if fdf < 43200:
                            presbedtime = round_time(preb_time)
                        else:
                            xx = df - 19800
                            x1 = t1 - datetime.timedelta(seconds=xx)
                            x1 = x1 - datetime.timedelta(seconds=ssdf)
                            x1 = datetime.datetime.strftime(x1, '%H:%M:%S')
                            presbedtime = round_time(str(x1))
                    else:
                        presbedtime = round_time(preb_time)

                if tt1 < tt2:
                    df = tt2 - tt1
                    if df < 19800:
                        xx = 19800 - df
                        x1 = t1 - datetime.timedelta(seconds=xx)
                        x1 = datetime.datetime.strftime(x1, '%H:%M:%S')
                        presbedtime = round_time(str(x1))
                    else:
                        presbedtime = round_time(preb_time)
            context = {
                "title": _title,
                "avgsleep": avgvalue,
                "avgbedtime": presbedtime,
                "sug_time": s_time,
                #"lock_diary": lock_diary,
                "video_view":video_view_count,
                "base_url": settings.BASE_URL,
                "first_name": '',
                "loggedUser": loggedUser,
                "form": form,
                "user_name": user_name,
                "user_image": user_image,
                "role_id": 5,
                "tags": "dairy",
                "current_week": wday,
                "weekDay_array": weekday,
                "weekDays_array": weekDays_array,
                "user_sleep_diarys": invoice_for_today,
                "time_went_to_bed": bed_time,
                "patient": pid,
                "entrydate": date_time_obj,
                'start_date': date_time_obj,
                "ma":ma,
                # datetime.date.strftime(date_time_obj1, "%Y-%m-%d")

            }
            return render(request, "sleepdiary.html", context)

        # print("User data", UsersleepData.count())

        date_time_obj1 = datetime.datetime.strptime(str(nextDate[0].sleep_diary_entries), '%Y-%m-%d')
        print(date_time_obj1)
        date_time_obj = datetime.date.strftime(date_time_obj1, "%m/%d/%Y")
        print("Yes again reload")
        form.fields["date"].initial = date_time_obj
        avgvalue = "N/A"
        presbedtime = "N/A"
        s_time = "N/A"
        if PatientEfficiency.objects.filter(patient_id=pid).exists():
            data = PatientEfficiency.objects.filter(patient_id=pid).order_by("-id")[0]
            avgvalue = data.sleep_efficiency
            preb_time = data.bed_time
            s_time = data.sugg_wake_up
            t1 = datetime.datetime.strptime(preb_time, ("%H:%M:%S"))
            t2 = datetime.datetime.strptime(s_time, ("%H:%M:%S"))
            tt1 = datetime.timedelta(hours=t1.hour, minutes=t1.minute).total_seconds()
            t1s = datetime.timedelta(minutes=t1.minute).total_seconds()
            s_time = round_time(s_time)
            tt2 = datetime.timedelta(hours=t2.hour, minutes=t2.minute).total_seconds()
            if tt1 > tt2:
                df = tt1 - tt2
                sdf = 3600 - t1s
                ssdf = 43200 - (t1s + sdf)
                if df < 19800:
                    xx = 19800 - df
                    x1 = t1 - datetime.timedelta(seconds=xx)
                    x1 = datetime.datetime.strftime(x1, '%H:%M:%S')
                    presbedtime = round_time(str(x1))
                if df > 43200:
                    fdf = df - 23400
                    if fdf < 43200:
                        presbedtime = round_time(preb_time)
                    else:
                        xx = df - 19800
                        x1 = t1 - datetime.timedelta(seconds=xx)
                        x1 = x1 - datetime.timedelta(seconds=ssdf)
                        x1 = datetime.datetime.strftime(x1, '%H:%M:%S')
                        presbedtime = round_time(str(x1))
                else:
                    presbedtime = round_time(preb_time)

            if tt1 < tt2:
                df = tt2 - tt1
                if df < 19800:
                    xx = 19800 - df
                    x1 = t1 - datetime.timedelta(seconds=xx)
                    x1 = datetime.datetime.strftime(x1, '%H:%M:%S')
                    presbedtime = round_time(str(x1))
                else:
                    presbedtime = round_time(preb_time)
        context = {
            "title": _title,
            "avgsleep": avgvalue,
            "avgbedtime": presbedtime,
            "sug_time": s_time,
            #"lock_diary": lock_diary,
            "video_view":video_view_count,
            "base_url": settings.BASE_URL,
            "first_name": '',
            "loggedUser": loggedUser,
            "form": form,
            "tags": "dairy",
            "user_name":user_name,
            "user_image": user_image,
            "role_id": 5,
            "weekDay_array": weekday,
            "weekDays_array": weekDays_array,
            "invoice_for_today_list": user_date_array,
            "user_sleep_diarys": invoice_for_today,
            "week_day": int(week_day),
            "current_week": wday,
            "entrydate": date_time_obj,
            "time_went_to_bed": bed_time,
            'start_date': date_time_obj,
            "ma":ma,

        }

        return render(request, "sleepdiary.html", context)

    except Exception as e:
        print(e)
        return redirect('/')

def ma_videos(request, vid, pid=0):
    user_name = ""
    user_image = ""
    ma = True
    try:
        _title = "CogniSleep |  Cogni-Dashboard"
        bedtime_array = []
        user = pid
        print("Yes you are here in videos")

        if user is None:
            return redirect('/')

        user_profile_provider = Provider.objects.get(user_id=request.user.id)
        user_name = user_profile_provider.first_name + " " + user_profile_provider.last_name
        user_image = user_profile_provider.provider_image
        weeks = []
        weekMsg = None
        weekVideo = 1
        week_counter = 0
        week_day = 0
        week_days_array = []
        invoice_for_today = SleepDiary.objects.raw(
            "SELECT * FROM dashboard_sleepdiary where patient_id=%s and time_went_to_bed!='' and time_fell_asleep!='' and time_got_up!='' ",
            [str(user)])

        for value in invoice_for_today:
            total_percent_sleep = get_user_progress_bar_avg(value.time_went_to_bed, value.time_fell_asleep,
                                                            value.time_got_up,
                                                            value.no_of_times_awakend, value.date)
            bedtime_array.append(total_percent_sleep)

        for value in bedtime_array:

            if week_counter == 6:
                result = {"weekday": week_day, "avg_data": value, }
                weeks.append(result)
                week_counter = 0
                week_day += 1
                weekVideo += 1
                week_days_array = []
            else:
                week_days_array.append(value)
                week_counter += 1
        # if(weekVideo > 1):
        #    weekVideo += 1

        loggedUser = User.objects.get(id=user)

        reqWeeks = 6



        user_profile = RefPatient.objects.get(user_id=pid)
        user_name = user_profile.first_name + " " + user_profile.last_name

        loggedUser = request.user.id
        userInfo = user_profile
        reqWeeks = 6
        video_array = []

        print(vid)
        print(weekVideo)
        # if (int(vid)) > (weekVideo):
        #     return redirect('/dashboard/videos/0')

        video_array = VideoSessions.objects.all()
        video_content = VideoSessions.objects.get(id=vid)
        if (vid >= 0):
            video_questions = VideoQuestions.objects.filter(video_sessions_id=vid)
        else:
            video_questions = {}

        existVCompleted = VideoSessionsCompleted.objects.filter(patient_id=pid).count()
        if existVCompleted > 0:
            is_videos_compelted = 1;
        else:
            is_videos_compelted = 0;
        l1 = []
        try:
            efficiency = PatientEfficiency.objects.filter(patient_id=pid).order_by('week_no').values()
            for i in efficiency:
                l1.append(i['sleep_efficiency'])

        except Exception as e:
            print(e)

        avgvalue = "00.00"
        presbedtime = "--:-- --"
        s_time = "--:-- --"
        if PatientEfficiency.objects.filter(patient_id=pid).exists():
            data = PatientEfficiency.objects.filter(patient_id=pid).order_by("-id")[0]
            avgvalue = data.sleep_efficiency
            preb_time = data.bed_time
            s_time = data.sugg_wake_up
            t1 = datetime.datetime.strptime(preb_time, ("%H:%M:%S"))
            t2 = datetime.datetime.strptime(s_time, ("%H:%M:%S"))
            tt1 = datetime.timedelta(hours=t1.hour, minutes=t1.minute).total_seconds()
            t1s = datetime.timedelta(minutes=t1.minute).total_seconds()
            s_time = round_time(s_time)
            tt2 = datetime.timedelta(hours=t2.hour, minutes=t2.minute).total_seconds()
            if tt1 > tt2:
                df = tt1 - tt2
                sdf = 3600 - t1s
                ssdf = 43200 - (t1s + sdf)
                if df < 19800:
                    xx = 19800 - df
                    x1 = t1 - datetime.timedelta(seconds=xx)
                    x1 = datetime.datetime.strftime(x1, '%H:%M:%S')
                    presbedtime = round_time(str(x1))
                if df > 43200:
                    fdf = df - 23400
                    if fdf < 43200:
                        presbedtime = round_time(preb_time)
                    else:
                        xx = df - 19800
                        x1 = t1 - datetime.timedelta(seconds=xx)
                        x1 = x1 - datetime.timedelta(seconds=ssdf)
                        x1 = datetime.datetime.strftime(x1, '%H:%M:%S')
                        presbedtime = round_time(str(x1))
                else:
                    presbedtime = round_time(preb_time)

            if tt1 < tt2:
                df = tt2 - tt1
                if df < 19800:
                    xx = 19800 - df
                    x1 = t1 - datetime.timedelta(seconds=xx)
                    x1 = datetime.datetime.strftime(x1, '%H:%M:%S')
                    presbedtime = round_time(str(x1))
                else:
                    presbedtime = round_time(preb_time)
        #global lock_diary
        video_view_count = video_count(pid)
        context = {
            "title": _title,
            "avgsleep": avgvalue,
            "avgbedtime": presbedtime,
            "sug_time": s_time,
            #"lock_diary": lock_diary,
            "video_view":video_view_count,
            "base_url": settings.BASE_URL,
            "first_name": '',
            "weeks": reqWeeks,
            "weekMsg": weekMsg,
            "weekVideo": weekVideo,
            "userdata": user_profile,
            "loggedUser": loggedUser,
            "videos": video_array,
            "se": l1,
            "user_name":user_name,
            "user_image": user_image,
            "role_id": 5,
            "video_content": video_content,
            "video_questions": video_questions,
            "current_video_id": vid,
            "patient": pid,
            "all_video_compeleted": is_videos_compelted,
            "ma":ma

        }

        return render(request, "dashboard_videos_tabs.html", context)
    except Exception as e:
        print(e)
        return redirect('/')

@login_required
def ma_view_sleep_diary(request, weekNm=0, pID=0):
    user_name = ""
    user_image = ""
    ma = True
    try:
        _title = "CogniSleep | Ma-Dashboard"


        userId = pID

        user_profile = Provider.objects.get(user_id=request.user.id)
        user_name = user_profile.first_name + " " + user_profile.last_name
        user_image = user_profile.provider_image
        userInfo = RefPatient.objects.get(user_id=userId)

        UsersleepData = SleepDiary.objects.filter(patient_id=userId)

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
            [str(userId), start_date, end_date])

        # print("invoice_for_today", invoice_for_today)
        user_date_array = []
        loggedUser = userId

        for x in range(1, reqWeeks + 1):

            if int(x) == week_day + 1:
                if PatientEfficiency.objects.filter(patient_id=userId, week_no=x).exists():
                    data = PatientEfficiency.objects.get(patient_id=userId, week_no=x)
                    week_array = {
                        "x": x,
                       # "is_selected": 1,
                        "eff": data.sleep_efficiency
                    }
                    weekDays_array.append(week_array)
                else:
                    week_array = {
                        "x": x,
                        # "week_date": week,
                        #"is_selected": 1,
                        "eff": ""
                    }
                    weekDays_array.append(week_array)
            else:
                if PatientEfficiency.objects.filter(patient_id=userId, week_no=x).exists():
                    data = PatientEfficiency.objects.get(patient_id=userId, week_no=x)
                    week_array = {
                        "x": x,
                        #"is_selected": 0,
                        "eff": data.sleep_efficiency
                    }
                    weekDays_array.append(week_array)
                else:
                    week_array = {
                        "x": x,
                        # "week_date": week,
                       # "is_selected": 0,
                        "eff": ""
                    }
                    weekDays_array.append(week_array)

        avgvalue = "00.00"
        presbedtime = "--:-- --"
        s_time = "--:-- --"
        if PatientEfficiency.objects.filter(patient_id=pID).exists():
            data = PatientEfficiency.objects.filter(patient_id=pID).order_by("-id")[0]
            avgvalue = data.sleep_efficiency
            preb_time = data.bed_time
            s_time = data.sugg_wake_up
            t1 = datetime.datetime.strptime(preb_time, ("%H:%M:%S"))
            t2 = datetime.datetime.strptime(s_time, ("%H:%M:%S"))
            tt1 = datetime.timedelta(hours=t1.hour, minutes=t1.minute).total_seconds()
            t1s = datetime.timedelta(minutes=t1.minute).total_seconds()
            s_time = round_time(s_time)
            tt2 = datetime.timedelta(hours=t2.hour, minutes=t2.minute).total_seconds()
            if tt1 > tt2:
                df = tt1 - tt2
                sdf = 3600 - t1s
                ssdf = 43200 - (t1s + sdf)
                if df < 19800:
                    xx = 19800 - df
                    x1 = t1 - datetime.timedelta(seconds=xx)
                    x1 = datetime.datetime.strftime(x1, '%H:%M:%S')
                    presbedtime = round_time(str(x1))
                if df > 43200:
                    fdf = df - 23400
                    if fdf < 43200:
                        presbedtime = round_time(preb_time)
                    else:
                        xx = df - 19800
                        x1 = t1 - datetime.timedelta(seconds=xx)
                        x1 = x1 - datetime.timedelta(seconds=ssdf)
                        x1 = datetime.datetime.strftime(x1, '%H:%M:%S')
                        presbedtime = round_time(str(x1))
                else:
                    presbedtime = round_time(preb_time)

            if tt1 < tt2:
                df = tt2 - tt1
                if df < 19800:
                    xx = 19800 - df
                    x1 = t1 - datetime.timedelta(seconds=xx)
                    x1 = datetime.datetime.strftime(x1, '%H:%M:%S')
                    presbedtime = round_time(str(x1))
                else:
                    presbedtime = round_time(preb_time)
        #global lock_diary
        video_view_count = video_count(request.user.id)
        weekNo = getweeknumber(userId)
        context = {
            "title": _title,
            "avgsleep": avgvalue,
            "avgbedtime": presbedtime,
            "sug_time": s_time,
            #"lock_diary": lock_diary,
            "video_view":video_view_count,
            "base_url": settings.BASE_URL,
            "loggedUser": loggedUser,
            "tags": "dairy",
            "week": weekNo,
            "user_name": user_name,
            "user_image": user_image,
            "role_id": 5,
            "weekDays_array": weekDays_array,
            "invoice_for_today_list": user_date_array,
            "user_sleep_diarys": invoice_for_today1,
            "patient": pID,
            "time_went_to_bed": bed_time,
            "ma":ma

        }

        return render(request, "dashboard_view_sleepdiary_tabs.html", context)
    except Exception as e:
        print(e)
        return redirect('/')

def ma_progress(request, pid=0):
    user_name = ""
    user_image = ""
    ma = True
    try:
        _title = "CogniSleep | Ma-Dashboard"
        loggedUser = User.objects.get(id=pid)

        user_profile = Provider.objects.get(user_id=request.user.id)
        user_name = user_profile.first_name + " " + user_profile.last_name
        user_image = user_profile.provider_image


        # print("Logged User: ", request.user.id)
        labels = ['Day 1', "Day 2", "Day 3", "Day 4", "Day 5", "Day 6", "Day 7"]
        default_items = [2, 4, 3, 2.5, 2.5, 1.5, 5.5]

        avgvalue = "00.00"
        presbedtime = "--:-- --"
        s_time = "--:-- --"
        if PatientEfficiency.objects.filter(patient_id=pid).exists():
            data = PatientEfficiency.objects.filter(patient_id=pid).order_by("-id")[0]
            avgvalue = data.sleep_efficiency
            preb_time = data.bed_time
            s_time = data.sugg_wake_up
            t1 = datetime.datetime.strptime(preb_time, ("%H:%M:%S"))
            t2 = datetime.datetime.strptime(s_time, ("%H:%M:%S"))
            tt1 = datetime.timedelta(hours=t1.hour, minutes=t1.minute).total_seconds()
            t1s = datetime.timedelta(minutes=t1.minute).total_seconds()
            s_time = round_time(s_time)
            tt2 = datetime.timedelta(hours=t2.hour, minutes=t2.minute).total_seconds()
            if tt1 > tt2:
                df = tt1 - tt2
                sdf = 3600 - t1s
                ssdf = 43200 - (t1s + sdf)
                if df < 19800:
                    xx = 19800 - df
                    x1 = t1 - datetime.timedelta(seconds=xx)
                    x1 = datetime.datetime.strftime(x1, '%H:%M:%S')
                    presbedtime = round_time(str(x1))
                if df > 43200:
                    fdf = df - 23400
                    if fdf < 43200:
                        presbedtime = round_time(preb_time)
                    else:
                        xx = df - 19800
                        x1 = t1 - datetime.timedelta(seconds=xx)
                        x1 = x1 - datetime.timedelta(seconds=ssdf)
                        x1 = datetime.datetime.strftime(x1, '%H:%M:%S')
                        presbedtime = round_time(str(x1))
                else:
                    presbedtime = round_time(preb_time)

            if tt1 < tt2:
                df = tt2 - tt1
                if df < 19800:
                    xx = 19800 - df
                    x1 = t1 - datetime.timedelta(seconds=xx)
                    x1 = datetime.datetime.strftime(x1, '%H:%M:%S')
                    presbedtime = round_time(str(x1))
                else:
                    presbedtime = round_time(preb_time)
        #global lock_diary
        video_view_count = video_count(pid)
        context = {
            "title": _title,
            "avgsleep": avgvalue,
            "avgbedtime": presbedtime,
            "sug_time": s_time,
            #"lock_diary": lock_diary,
            "video_view":video_view_count,
            "base_url": settings.BASE_URL,
            "first_name": '',
            "userdata": user_profile,
            "user_name": user_name,
            "user_image": user_image,
            "role_id": 5,
            "loggedUser": loggedUser,
            "labels": labels,
            "default": default_items,
            "patient": pid,
            "ma":ma

        }
        # print(context)
        return render(request, "progress.html", context)
    except Exception as e:
        print(e)
        return redirect('/')

def ma_ntl(request, pid=0):
    user_name = ""
    user_image = ""
    ma = True
    try:
        print("yessssssssssssssssssssssssss")
        _title = "CogniSleep |  Cogni-NTL"

        loggedUser = User.objects.get(id=pid)

        user_profile = Provider.objects.get(user_id=request.user.id)
        user_name = user_profile.first_name + " " + user_profile.last_name
        user_image = user_profile.provider_image

        avgvalue = "00.00"
        presbedtime = "--:-- --"
        s_time = "--:-- --"
        if PatientEfficiency.objects.filter(patient_id=pid).exists():
            data = PatientEfficiency.objects.filter(patient_id=pid).order_by("-id")[0]
            avgvalue = data.sleep_efficiency
            preb_time = data.bed_time
            s_time = data.sugg_wake_up
            t1 = datetime.datetime.strptime(preb_time, ("%H:%M:%S"))
            t2 = datetime.datetime.strptime(s_time, ("%H:%M:%S"))
            tt1 = datetime.timedelta(hours=t1.hour, minutes=t1.minute).total_seconds()
            t1s = datetime.timedelta(minutes=t1.minute).total_seconds()
            s_time = round_time(s_time)
            tt2 = datetime.timedelta(hours=t2.hour, minutes=t2.minute).total_seconds()
            if tt1 > tt2:
                df = tt1 - tt2
                sdf = 3600 - t1s
                ssdf = 43200 - (t1s + sdf)
                if df < 19800:
                    xx = 19800 - df
                    x1 = t1 - datetime.timedelta(seconds=xx)
                    x1 = datetime.datetime.strftime(x1, '%H:%M:%S')
                    presbedtime = round_time(str(x1))
                if df > 43200:
                    fdf = df - 23400
                    if fdf < 43200:
                        presbedtime = round_time(preb_time)
                    else:
                        xx = df - 19800
                        x1 = t1 - datetime.timedelta(seconds=xx)
                        x1 = x1 - datetime.timedelta(seconds=ssdf)
                        x1 = datetime.datetime.strftime(x1, '%H:%M:%S')
                        presbedtime = round_time(str(x1))
                else:
                    presbedtime = round_time(preb_time)

            if tt1 < tt2:
                df = tt2 - tt1
                if df < 19800:
                    xx = 19800 - df
                    x1 = t1 - datetime.timedelta(seconds=xx)
                    x1 = datetime.datetime.strftime(x1, '%H:%M:%S')
                    presbedtime = round_time(str(x1))
                else:
                    presbedtime = round_time(preb_time)
            #global lock_diary
        video_view_count = video_count(pid)
        ntl = 1
        context = {
            "title": _title,
            "avgsleep": avgvalue,
            "avgbedtime": presbedtime,
            "sug_time": s_time,
            #"lock_diary": lock_diary,
            "video_view":video_view_count,
            "base_url": settings.BASE_URL,
            "first_name": '',
            "user_name": user_name,
            "user_image": user_image,
            "role_id": 5,
            "userdata": user_profile,
            "loggedUser": loggedUser,
            "patient": pid,
            "ntl":ntl,
            "ma":ma

        }
        return render(request, "dashboard_locker.html", context)
    except Exception as e:
        print(e)
        return redirect('/')

def ma_relaxation(request, pid=0):
    user_name = ""
    user_image = ""
    avgvalue = "00.00"
    presbedtime = "--:-- --"
    s_time = "--:-- --"
    ma = True
    try:

        user_profile = Provider.objects.get(user_id=request.user.id)
        user_name = user_profile.first_name + " " + user_profile.last_name
        user_image = user_profile.provider_image

        if PatientEfficiency.objects.filter(patient_id=pid).exists():
            data = PatientEfficiency.objects.filter(patient_id=pid).order_by("-id")[0]
            avgvalue = data.sleep_efficiency
            preb_time = data.bed_time
            s_time = data.sugg_wake_up
            t1 = datetime.datetime.strptime(preb_time, ("%H:%M:%S"))
            t2 = datetime.datetime.strptime(s_time, ("%H:%M:%S"))
            tt1 = datetime.timedelta(hours=t1.hour, minutes=t1.minute).total_seconds()
            t1s = datetime.timedelta(minutes=t1.minute).total_seconds()
            s_time = round_time(s_time)
            tt2 = datetime.timedelta(hours=t2.hour, minutes=t2.minute).total_seconds()
            if tt1 > tt2:
                df = tt1 - tt2
                sdf = 3600 - t1s
                ssdf = 43200 - (t1s + sdf)
                if df < 19800:
                    xx = 19800 - df
                    x1 = t1 - datetime.timedelta(seconds=xx)
                    x1 = datetime.datetime.strftime(x1, '%H:%M:%S')
                    presbedtime = round_time(str(x1))
                if df > 43200:
                    fdf = df - 23400
                    if fdf < 43200:
                        presbedtime = round_time(preb_time)
                    else:
                        xx = df - 19800
                        x1 = t1 - datetime.timedelta(seconds=xx)
                        x1 = x1 - datetime.timedelta(seconds=ssdf)
                        x1 = datetime.datetime.strftime(x1, '%H:%M:%S')
                        presbedtime = round_time(str(x1))
                else:
                    presbedtime = round_time(preb_time)

            if tt1 < tt2:
                df = tt2 - tt1
                if df < 19800:
                    xx = 19800 - df
                    x1 = t1 - datetime.timedelta(seconds=xx)
                    x1 = datetime.datetime.strftime(x1, '%H:%M:%S')
                    presbedtime = round_time(str(x1))
                else:
                    presbedtime = round_time(preb_time)

        context = {
            "title": "Relaxation",
            "avgsleep": avgvalue,
            "avgbedtime": presbedtime,
            "sug_time": s_time,
            "user_name": user_name,
            "user_image": user_image,
            "role_id": 5,
            "base_url": settings.BASE_URL,
            "ma":ma,
            "patient":pid,

        }

        return render(request, "relaxation.html", context)

    except Exception as e:
        print(e)
        return redirect('/')

def ma_certificate(request, pid=0):
    try:
        print("YES IN CERTIFICATE")

        existVCompleted = VideoSessionsCompleted.objects.filter(patient_id=pid).count()
        print(existVCompleted)
        if existVCompleted > 0:
            print("FOUND")
            existVCompleted = VideoSessionsCompleted.objects.filter(patient_id=pid)

        user_profile = RefPatient.objects.get(user_id=pid)
        date1 = existVCompleted[0].created_at
        date = date1.strftime("%B #, %Y")
        day = date1.day
        if (3 < day < 21) or (23 < day < 31):

            day = str(day) + 'th'
        else:

            suffixes = {1: 'st', 2: 'nd', 3: 'rd'}

            day = str(day) + suffixes[day % 10]
        f_date = (date.replace('#', day))
        name = profile(pid)
        context = {
            "patient_id": existVCompleted[0].patient_id,
            "date": f_date,
            "name": user_profile.first_name + " " + user_profile.last_name,
            'provider_name':name,
        }

        return render(request, "certificate.html", context)
    except Exception as e:
        print(e)
        return redirect('/')

def masavelastvideo(request, pid=0):
    try:
        print("yes in final video")
        userId = pid
        print(userId)
        pat = User.objects.get(id =  userId)
        # global video_view_count
        reurl = "/dashboard/ma_patient_dashboard/" + str(userId) + "/"
        queryset = VideoViews.objects.filter(patient_id=int(userId))
        if queryset.exists():
            print("Found data")
            updaterecord = VideoViews.objects.get(patient_id=int(userId))
            updaterecord.view_video = 7
            updaterecord.save()
            if VideoSessionsCompleted.objects.filter(patient_id=userId).exists():
                print("yes in if before else")

                return redirect(reurl)

            else:
                print("YES- NO FINAL SAVE")
                data = VideoSessionsCompleted(patient_id=userId, completed=1)
                data.save()
                subject = 'Certificate of Completion for CogniSleep Program'
                to = pat.email

                html_message = loader.render_to_string(
                    'email_temp/completion_email.html',
                    {}
                )
                email_records(request, to, settings.EMAIL_FROM, 'Certificate of Completion for CogniSleep Program')
                send_mail(
                    subject,
                    'Certificate of Completion for CogniSleep Program',
                    settings.EMAIL_FROM,
                    [to],
                    html_message=html_message
                    ,
                )

                return redirect(reurl)

        return redirect(reurl)
    except Exception as e:
        print(e)
        return redirect('/')


@login_required
class ProviderhandbooksAPIView(APIView):



    def post(self, request):
        serializer = ProviderhandbooksSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes((AllowAny,))
def gethandbooks(request,pid,wid):


    providerhandbooks = Providerhandbooks.objects.filter(patient=pid,week_number=wid)


    if providerhandbooks.exists():
        providerhandbooks = Providerhandbooks.objects.get(patient=pid, week_number=wid)
        serializer = ProviderhandbooksSerializer(providerhandbooks)
        print("shakaib jhfiuhfohnff")
        return Response(serializer.data, status=status.HTTP_200_OK)

    else:
        return Response({'exists': False},status=status.HTTP_400_BAD_REQUEST)

ch=8
@login_required
def provider_handbook_report(request,pid,weekno):
    try:
        print("yes in it downlaod")
        if pid != None and weekno != None:
            print(pid)
            print(weekno)
            start_week = weekno
            end_week = weekno
            id = pid
            patient = RefPatient.objects.get(user_id=id)
            patient_name = patient.first_name + " " + patient.last_name
            provider_id = patient.provider_id
            provider_id = str(provider_id[12:])
            provider = Provider.objects.get(user_id=provider_id)
            provider_name = provider.first_name + " " + provider.last_name
            record = Providerhandbooks.objects.get(patient_id = pid, week_number = weekno)
            today = datetime.date.today()
            today = today.strftime('%m-%d-%Y')

            class PDF(FPDF):
                def header(self):
                    # Position at 1.5 cm from bottom
                    #filepath = os.path.join(BASE_DIR, 'static/assets/images/logo-1.png')
                    #self.image(filepath, 10, 10, 100);
                    self.set_font('Arial', 'B', 10);
                    # self.set_x(110)
                    # self.set_y(20)
                    self.cell(60, 10, "Provider Name: " + provider_name, 0, 0, 'L');
                    self.cell(10);
                    self.cell(60, 10, "Contact No: " + provider.contact_no, 0, 0, 'L');
                    filepath = os.path.join(BASE_DIR, 'static/assets/images/logo-1.png')
                    self.image(filepath, 140, 10, 60);
                    pdf.ln()
                    self.cell(60, 10, "Patient Name: " + patient_name, 0, 0, 'L');
                    self.cell(10);
                    self.cell(60, 10, "Date: " + today, 0, 0, 'L');
                    pdf.ln()
                    x = pdf.get_x()
                    y = pdf.get_y()
                    pdf.set_line_width(0.8)
                    pdf.set_draw_color(32,11,148)
                    pdf.line(11, y +5, x + 190, y + 5)
                    pdf.ln(10)


                # Page footer
                def footer(self):
                    # Position at 1.5 cm from bottom
                    self.set_y(-15)
                    y = pdf.get_y()
                    # Arial italic 8
                    #self.set_font('Arial', 'I', 14)
                    pdf.set_line_width(0.8)
                    pdf.set_draw_color(32, 11, 148)
                    pdf.line(0, y, 209, y)
                    # Page number
                    self.cell(5)
                    pdf.set_text_color(32, 11, 148)
                    self.cell(40, 15, "www.cognisleep.com", 0, 0, 'L');
                    self.cell(100);
                    self.cell(40, 15, "support@cognisleep.com", 0, 0, 'L');

            pdf = PDF(orientation='L', unit='mm', format=(297,210))
            pdf.alias_nb_pages()
            pdf.add_page()

            if weekno == 1:
                pdf.set_font('Arial', 'B', 18)
                pdf.set_text_color(32, 11, 148)
                pdf.cell(w=205, h=ch, txt="COGNI SLEEP SESSION 1 REVIEW", ln=1, align='L')
                pdf.ln(10)
                pdf.set_font('Arial', '', 10)
                pdf.set_text_color(0, 0, 0)
                pdf.cell(w=5,h=6,txt="1.",ln=0)
                pdf.multi_cell(w=190, h=6, txt="Sleeping pills only help you fall asleep 10 minutes faster, stop working after 3 months, and can cause dangerous side effects.",align='L')
                pdf.ln(1)
                pdf.cell(w=5, h=6, txt="2.", ln=0)
                pdf.multi_cell(w=190, h=6,txt="Anytime you think you are lying in bed for more than 20 minutes, get up and do something else until you are drowsy.",align='L')
                pdf.ln(1)
                pdf.cell(w=5, h=6, txt="3.", ln=0)
                pdf.multi_cell(w=190, h=6,
                         txt="Fill out your CogniSleep Diary each morning. This includes what time you went to bed, when you fell asleep, how much time you spent awake while in bed, and what time you got up.",align='L')
                pdf.ln(1)
                pdf.cell(w=5, h=6, txt="4.", ln=0)
                pdf.multi_cell(w=190, h=6,
                         txt="Remember to use your bed only for sleep and sexual activity.",align='L')
                pdf.ln(1)
                pdf.cell(w=5, h=6, txt="5.", ln=0)
                pdf.multi_cell(w=190, h=6,
                         txt="Turn your clock away from you so you can't watch it while you're lying in bed.",align='L')
                pdf.ln(1)
                pdf.cell(w=5, h=6, txt="6.", ln=0)
                pdf.multi_cell(w=190, h=6,
                         txt="Limit electronic use while in bed.",align='L')
                pdf.ln(10)
                pdf.set_font('Arial', 'B', 14)
                pdf.set_text_color(32, 11, 148)
                pdf.cell(w=200, h=ch, txt="PROVIDER NOTE", ln=1, align='L')
                x = pdf.get_x()
                y = pdf.get_y()
                print(x)
                print(y)
                pdf.line(11, y + 6, x + 190, y + 6)
                pdf.line(11, y + 14, x + 190, y + 14)
                pdf.line(11, y + 22, x + 190, y + 22)
                pdf.line(11, y + 30, x + 190, y + 30)
                pdf.line(11, y + 38, x + 190, y + 38)
                pdf.line(11, y + 46, x + 190, y + 46)
                pdf.set_text_color(0, 0, 0)
                pdf.set_font('Arial', '', 10)
                txt1 = convert_quotes(record.provider_remark)
                pdf.multi_cell(w=0, h=ch,
                               txt=txt1, align='L')

                pdf.ln(46)
                pdf.set_text_color(32, 11, 148)
                pdf.set_font('Arial', 'B', 14)
                pdf.cell(w=200, h=ch, txt="PATIENT NOTE", ln=1, align='L')
                x = pdf.get_x()
                y = pdf.get_y()
                print(x)
                print(y)
                pdf.line(11, y + 6, x + 190, y + 6)
                pdf.line(11, y + 14, x + 190, y + 14)
                pdf.line(11, y + 22, x + 190, y + 22)
                pdf.line(11, y + 30, x + 190, y + 30)
                pdf.line(11, y + 38, x + 190, y + 38)
                pdf.line(11, y + 46, x + 190, y + 46)
                pdf.set_text_color(0, 0, 0)
                pdf.set_font('Arial', '', 10)
                txt2 = convert_quotes(record.patient_remark)
                pdf.multi_cell(w=0, h=ch,
                               txt=txt2, align='L')

            if weekno == 2:
                pdf.set_font('Arial', 'B', 18)
                pdf.set_text_color(32, 11, 148)
                pdf.cell(w=205, h=ch, txt="COGNI SLEEP SESSION 2 REVIEW", ln=1, align='L')
                pdf.ln(10)
                pdf.set_font('Arial', '', 10)
                pdf.set_text_color(0, 0, 0)
                pdf.cell(w=5, h=6, txt="1.", ln=0)
                pdf.multi_cell(w=190, h=6,
                               txt="Sleep restrictions may seem difficult at first, but after the first few nights, you will have gathered up some exhaustion coins, and things will start to improve.",
                               align='L')
                pdf.ln(1)
                pdf.cell(w=5, h=6, txt="2.", ln=0)
                pdf.multi_cell(w=190, h=6,
                               txt="If you are struggling with negative thoughts, remember to replace them with their positive alternative.",
                               align='L')
                pdf.ln(1)
                pdf.cell(w=5, h=6, txt="3.", ln=0)
                pdf.multi_cell(w=190, h=6,
                               txt="If your negative thoughts are persistent, lock them away in your Negative Thoughts Lockbox located on your dashboard.",
                               align='L')

                pdf.ln(10)
                pdf.set_font('Arial', 'B', 14)
                pdf.set_text_color(32, 11, 148)
                pdf.cell(w=200, h=ch, txt="PROVIDER NOTE", ln=1, align='L')
                x = pdf.get_x()
                y = pdf.get_y()
                print(x)
                print(y)
                pdf.line(11, y + 6, x + 190, y + 6)
                pdf.line(11, y + 14, x + 190, y + 14)
                pdf.line(11, y + 22, x + 190, y + 22)
                pdf.line(11, y + 30, x + 190, y + 30)
                pdf.line(11, y + 38, x + 190, y + 38)
                pdf.line(11, y + 46, x + 190, y + 46)
                pdf.set_text_color(0, 0, 0)
                pdf.set_font('Arial', '', 10)
                txt1 = convert_quotes(record.provider_remark)
                pdf.multi_cell(w=0, h=ch,
                               txt=txt1, align='L')

                pdf.ln(32)
                pdf.set_text_color(32, 11, 148)
                pdf.set_font('Arial', 'B', 14)
                pdf.cell(w=200, h=ch, txt="PATIENT NOTE", ln=1, align='L')
                x = pdf.get_x()
                y = pdf.get_y()
                print(x)
                print(y)
                pdf.line(11, y + 6, x + 190, y + 6)
                pdf.line(11, y + 14, x + 190, y + 14)
                pdf.line(11, y + 22, x + 190, y + 22)
                pdf.line(11, y + 30, x + 190, y + 30)
                pdf.line(11, y + 38, x + 190, y + 38)
                pdf.line(11, y + 46, x + 190, y + 46)
                pdf.set_text_color(0, 0, 0)
                pdf.set_font('Arial', '', 10)
                txt2 = convert_quotes(record.patient_remark)
                pdf.multi_cell(w=0, h=ch,
                               txt=txt2, align='L')


            if weekno == 3:
                pdf.set_font('Arial', 'B', 18)
                pdf.set_text_color(32, 11, 148)
                pdf.cell(w=205, h=ch, txt="COGNI SLEEP SESSION 3 REVIEW", ln=1, align='L')
                pdf.ln(10)
                pdf.set_font('Arial', '', 10)
                pdf.set_text_color(0, 0, 0)
                pdf.cell(w=5, h=6, txt="1.", ln=0)
                pdf.multi_cell(w=190, h=6,
                               txt="Keep filling out your sleep diary every day in its entirety. That information is vital to help determine how well we're doing toward achieving your goals.",
                               align='L')
                pdf.ln(1)
                pdf.cell(w=5, h=6, txt="2.", ln=0)
                pdf.multi_cell(w=190, h=6,
                               txt="Keep up with your sleep restrictions, even though they might be challenging. The longer you stick with them, the easier they'll become.",
                               align='L')
                pdf.ln(1)
                pdf.cell(w=5, h=6, txt="3.", ln=0)
                pdf.multi_cell(w=190, h=6,
                               txt="Battle negative thoughts with positive ones.",
                               align='L')
                pdf.ln(1)
                pdf.cell(w=5, h=6, txt="4.", ln=0)
                pdf.multi_cell(w=190, h=6,
                               txt="If you are having a hard time staying awake, review session 2.",
                               align='L')

                pdf.ln(1)
                pdf.cell(w=5, h=6, txt="5.", ln=0)
                pdf.multi_cell(w=190, h=6,
                               txt="All directions from Session 1 still apply:",
                               align='L')
                pdf.ln(1)
                pdf.cell(w=15, h=6, txt="o", ln=0, align="R")
                pdf.multi_cell(w=170, h=6,
                               txt="Remember to use your bed only for sleep and sexual activity",
                               align='L')
                pdf.ln(1)
                pdf.cell(w=15, h=6, txt="o", ln=0, align="R")
                pdf.multi_cell(w=170, h=6,
                               txt="Keep that clock turned away so that you can't see it when you're lying in bed.",
                               align='L')
                pdf.ln(1)
                pdf.cell(w=15, h=6, txt="o", ln=0, align="R")
                pdf.multi_cell(w=170, h=6,
                               txt="Please continue going to another room and doing a quiet activity until you are drowsy if you've been awake in bed for what you perceive to be 20 minutes or more. With that, I've asked you to avoid 'trying' to sleep and let things happen naturally.",
                               align='L')
                pdf.ln(1)
                pdf.cell(w=15, h=6, txt="o", ln=0, align="R")
                pdf.multi_cell(w=170, h=6,
                               txt="Keep battling your negative sleep thoughts by replacing them with positive ones. Be aggressive in taking away their power.",
                               align='L')
                pdf.ln(1)
                pdf.cell(w=15, h=6, txt="o", ln=0, align="R")
                pdf.multi_cell(w=170, h=6,
                               txt="If you're having trouble staying awake, review the ways to stay awake until bedtime that we discussed in this session.",
                               align='L')

                pdf.ln(1)
                pdf.cell(w=5, h=6, txt="6.", ln=0)
                pdf.multi_cell(w=190, h=6,
                               txt="You've made it half-way through our lessons! Keep up the good work!",
                               align='L')

                pdf.ln(10)
                pdf.set_font('Arial', 'B', 14)
                pdf.set_text_color(32, 11, 148)
                pdf.cell(w=200, h=ch, txt="PROVIDER NOTE", ln=1, align='L')
                x = pdf.get_x()
                y = pdf.get_y()
                print(x)
                print(y)
                pdf.line(11, y + 6, x + 190, y + 6)
                pdf.line(11, y + 14, x + 190, y + 14)
                pdf.line(11, y + 22, x + 190, y + 22)
                pdf.line(11, y + 30, x + 190, y + 30)
                pdf.line(11, y + 38, x + 190, y + 38)
                pdf.line(11, y + 46, x + 190, y + 46)
                pdf.set_text_color(0, 0, 0)
                pdf.set_font('Arial', '', 10)
                txt1 = convert_quotes(record.provider_remark)
                pdf.multi_cell(w=0, h=ch,
                               txt=txt1, align='L')

                pdf.ln(10)
                pdf.add_page()
                pdf.set_text_color(32, 11, 148)
                pdf.set_font('Arial', 'B', 14)
                pdf.cell(w=200, h=ch, txt="PATIENT NOTE", ln=1, align='L')
                x = pdf.get_x()
                y = pdf.get_y()
                print(x)
                print(y)
                pdf.line(11, y + 6, x + 190, y + 6)
                pdf.line(11, y + 14, x + 190, y + 14)
                pdf.line(11, y + 22, x + 190, y + 22)
                pdf.line(11, y + 30, x + 190, y + 30)
                pdf.line(11, y + 38, x + 190, y + 38)
                pdf.line(11, y + 46, x + 190, y + 46)
                pdf.set_text_color(0, 0, 0)
                pdf.set_font('Arial', '', 10)
                txt2 = convert_quotes(record.patient_remark)
                pdf.multi_cell(w=0, h=ch,
                               txt=txt2, align='L')

            if weekno == 4:
                pdf.set_font('Arial', 'B', 18)
                pdf.set_text_color(32, 11, 148)
                pdf.cell(w=205, h=ch, txt="COGNI SLEEP SESSION 4 REVIEW", ln=1, align='L')
                pdf.ln(10)
                pdf.set_font('Arial', '', 10)
                pdf.set_text_color(0, 0, 0)
                pdf.cell(w=5, h=6, txt="1.", ln=0)
                pdf.multi_cell(w=190, h=6,
                               txt="We have discussed keeping your negative thoughts in check.",
                               align='L')
                pdf.ln(1)
                pdf.cell(w=5, h=6, txt="2.", ln=0)
                pdf.multi_cell(w=190, h=6,
                               txt="You have learned to keep track of your sleep data to master better sleep.",
                               align='L')
                pdf.ln(1)
                pdf.cell(w=5, h=6, txt="3.", ln=0)
                pdf.multi_cell(w=190, h=6,
                               txt="You have learned the importance of maintaining a healthy sleep environment.",
                               align='L')
                pdf.ln(1)
                pdf.cell(w=5, h=6, txt="4.", ln=0)
                pdf.multi_cell(w=190, h=6,
                               txt="You have learned good bedtime rituals that include but are not limited to:",
                               align='L')

                pdf.ln(1)
                pdf.cell(w=15, h=6, txt="o", ln=0, align="R")
                pdf.multi_cell(w=170, h=6,
                               txt="Comfortable Environment.",
                               align='L')
                pdf.ln(1)
                pdf.cell(w=15, h=6, txt="o", ln=0, align="R")
                pdf.multi_cell(w=170, h=6,
                               txt="A bedroom temp 60-68 degrees Fahrenheit.",
                               align='L')
                pdf.ln(1)
                pdf.cell(w=15, h=6, txt="o", ln=0, align="R")
                pdf.multi_cell(w=170, h=6,
                               txt="Block light and noise.",
                               align='L')
                pdf.ln(1)
                pdf.cell(w=15, h=6, txt="o", ln=0, align="R")
                pdf.multi_cell(w=170, h=6,
                               txt="Eat a light snack.",
                               align='L')
                pdf.ln(1)
                pdf.cell(w=15, h=6, txt="o", ln=0, align="R")
                pdf.multi_cell(w=170, h=6,
                               txt="Limit fluids.",
                               align='L')


                pdf.ln(10)
                pdf.set_font('Arial', 'B', 14)
                pdf.set_text_color(32, 11, 148)
                pdf.cell(w=200, h=ch, txt="PROVIDER NOTE", ln=1, align='L')
                x = pdf.get_x()
                y = pdf.get_y()
                print(x)
                print(y)
                pdf.line(11, y + 6, x + 190, y + 6)
                pdf.line(11, y + 14, x + 190, y + 14)
                pdf.line(11, y + 22, x + 190, y + 22)
                pdf.line(11, y + 30, x + 190, y + 30)
                pdf.line(11, y + 38, x + 190, y + 38)
                pdf.line(11, y + 46, x + 190, y + 46)
                pdf.set_text_color(0, 0, 0)
                pdf.set_font('Arial', '', 10)
                txt1 = convert_quotes(record.provider_remark)
                pdf.multi_cell(w=0, h=ch,
                               txt=txt1, align='L')

                pdf.ln(45)

                pdf.set_text_color(32, 11, 148)
                pdf.set_font('Arial', 'B', 14)
                pdf.cell(w=200, h=ch, txt="PATIENT NOTE", ln=1, align='L')
                x = pdf.get_x()
                y = pdf.get_y()
                print(x)
                print(y)
                pdf.line(11, y + 6, x + 190, y + 6)
                pdf.line(11, y + 14, x + 190, y + 14)
                pdf.line(11, y + 22, x + 190, y + 22)
                pdf.line(11, y + 30, x + 190, y + 30)
                pdf.line(11, y + 38, x + 190, y + 38)
                pdf.line(11, y + 46, x + 190, y + 46)
                pdf.set_text_color(0, 0, 0)
                pdf.set_font('Arial', '', 10)
                txt2 = convert_quotes(record.patient_remark)
                pdf.multi_cell(w=0, h=ch,
                               txt=txt2, align='L')


            if weekno == 5:
                pdf.set_font('Arial', 'B', 18)
                pdf.set_text_color(32, 11, 148)
                pdf.cell(w=205, h=ch, txt="COGNI SLEEP SESSION 5 REVIEW", ln=1, align='L')
                pdf.ln(10)
                pdf.set_font('Arial', '', 10)
                pdf.set_text_color(0, 0, 0)
                pdf.cell(w=5, h=6, txt="1.", ln=0)
                pdf.multi_cell(w=190, h=6,
                               txt="Remember your weekly sleep efficiency, prescribed bedtimes, and wake times are key to a successful sleep restructuring program.",
                               align='L')
                pdf.ln(1)
                pdf.cell(w=5, h=6, txt="2.", ln=0)
                pdf.multi_cell(w=190, h=6,
                               txt="Remember that these sleep restrictions are meant to be very helpful and are designed to get you sleeping better - if you follow them.",
                               align='L')
                pdf.ln(1)
                pdf.cell(w=5, h=6, txt="3.", ln=0)
                pdf.multi_cell(w=190, h=6,
                               txt="Remember to deal with your negative thoughts SWIFTLY, whether they occur about your sleep or are a daytime nuisance.",
                               align='L')
                pdf.ln(1)
                pdf.cell(w=5, h=6, txt="4.", ln=0)
                pdf.multi_cell(w=190, h=6,
                               txt="You can replace them with their positive alternative; you can write them down and visualize locking them up for the night; or you can tell them 'No' every time one pops into your head and put up a mental wall so they can't get the power over you they want.",
                               align='L')



                pdf.ln(10)
                pdf.set_font('Arial', 'B', 14)
                pdf.set_text_color(32, 11, 148)
                pdf.cell(w=200, h=ch, txt="PROVIDER NOTE", ln=1, align='L')
                x = pdf.get_x()
                y = pdf.get_y()
                print(x)
                print(y)
                pdf.line(11, y + 6, x + 190, y + 6)
                pdf.line(11, y + 14, x + 190, y + 14)
                pdf.line(11, y + 22, x + 190, y + 22)
                pdf.line(11, y + 30, x + 190, y + 30)
                pdf.line(11, y + 38, x + 190, y + 38)
                pdf.line(11, y + 46, x + 190, y + 46)
                pdf.set_text_color(0, 0, 0)
                pdf.set_font('Arial', '', 10)
                txt1 = convert_quotes(record.provider_remark)
                pdf.multi_cell(w=0, h=ch,
                               txt=txt1, align='L')

                pdf.ln(32)
                #pdf.add_page()
                pdf.set_text_color(32, 11, 148)
                pdf.set_font('Arial', 'B', 14)
                pdf.cell(w=200, h=ch, txt="PATIENT NOTE", ln=1, align='L')
                x = pdf.get_x()
                y = pdf.get_y()
                print(x)
                print(y)
                pdf.line(11, y + 6, x + 190, y + 6)
                pdf.line(11, y + 14, x + 190, y + 14)
                pdf.line(11, y + 22, x + 190, y + 22)
                pdf.line(11, y + 30, x + 190, y + 30)
                pdf.line(11, y + 38, x + 190, y + 38)
                pdf.line(11, y + 46, x + 190, y + 46)
                pdf.set_text_color(0, 0, 0)
                pdf.set_font('Arial', '', 10)
                txt2 = convert_quotes(record.patient_remark)
                pdf.multi_cell(w=0, h=ch,
                               txt=txt2, align='L')

            if weekno == 6:
                pdf.set_font('Arial', 'B', 18)
                pdf.set_text_color(32, 11, 148)
                pdf.cell(w=205, h=ch, txt="COGNI SLEEP SESSION 6 REVIEW", ln=1, align='L')
                pdf.ln(10)
                pdf.set_font('Arial', '', 10)
                pdf.set_text_color(0, 0, 0)
                pdf.cell(w=5, h=6, txt="1.", ln=0)
                pdf.multi_cell(w=190, h=6,
                               txt="A quick reminder about Sleep efficiency: for every week your average sleep efficiency is over 90 percent, you can add 15 minutes to your prescribed bedtime. You can also do so if your sleep efficiency is consistently above 85 % and you are feeling rested.",
                               align='L')
                pdf.ln(1)
                pdf.cell(w=5, h=6, txt="2.", ln=0)
                pdf.multi_cell(w=190, h=6,
                               txt="If your weekly average sleep efficiency drops to 85 percent or below, I'd like you to move your bedtime back by 15 minutes.",
                               align='L')
                pdf.ln(1)
                pdf.cell(w=5, h=6, txt="3.", ln=0)
                pdf.multi_cell(w=190, h=6,
                               txt="If you average a sleep efficiency of 85 percent or more for 4 consecutive weeks, it's OK to have some 'cheat nights' here and there, as long as it doesn't make you feel more tired or cause your insomnia to get worse.",
                               align='L')
                pdf.ln(1)
                pdf.cell(w=5, h=6, txt="4.", ln=0)
                pdf.multi_cell(w=190, h=6,
                               txt="If you've been sleeping well and feeling good for about 3 months, it might be OK to be less strict with the program requirements as long as it doesn't result in any rebound insomnia.",
                               align='L')
                pdf.ln(1)
                pdf.cell(w=5, h=6, txt="5.", ln=0)
                pdf.multi_cell(w=190, h=6,
                               txt="You've got to keep a tight grip on your worries and make sure they are not causing you the same problems as your negative thoughts. If you are a worrier, use some of the techniques we discussed to help take away the power of the worry and get your thinking centered on the positive.",
                               align='L')
                pdf.ln(2)
                pdf.multi_cell(w=190, h=6,
                               txt="You have access to Dr. Cogni's relaxation exercise in the main menu. Whether you choose to use this program, or another relaxation or mediation program, try to use one at least once a day, during the daytime at first, to help relieve daytime stress and worries. Once you get good at it, you can use it at night to help you fall asleep or go back to sleep if you wake up in the middle of the night. Happy sleeping!",
                               align='L')

                pdf.ln(10)
                pdf.set_font('Arial', 'B', 14)
                pdf.set_text_color(32, 11, 148)
                pdf.cell(w=200, h=ch, txt="PROVIDER NOTE", ln=1, align='L')
                x = pdf.get_x()
                y = pdf.get_y()
                print(x)
                print(y)
                pdf.line(11, y + 6, x + 190, y + 6)
                pdf.line(11, y + 14, x + 190, y + 14)
                pdf.line(11, y + 22, x + 190, y + 22)
                pdf.line(11, y + 30, x + 190, y + 30)
                pdf.line(11, y + 38, x + 190, y + 38)
                pdf.line(11, y + 46, x + 190, y + 46)
                pdf.set_text_color(0, 0, 0)
                pdf.set_font('Arial', '', 10)
                txt1 = convert_quotes(record.provider_remark)
                pdf.multi_cell(w=0, h=ch,
                               txt=txt1, align='L')

                pdf.ln(10)
                pdf.add_page()
                pdf.set_text_color(32, 11, 148)
                pdf.set_font('Arial', 'B', 14)
                pdf.cell(w=200, h=ch, txt="PATIENT NOTE", ln=1, align='L')
                x = pdf.get_x()
                y = pdf.get_y()
                print(x)
                print(y)
                pdf.line(11, y + 6, x + 190, y + 6)
                pdf.line(11, y + 14, x + 190, y + 14)
                pdf.line(11, y + 22, x + 190, y + 22)
                pdf.line(11, y + 30, x + 190, y + 30)
                pdf.line(11, y + 38, x + 190, y + 38)
                pdf.line(11, y + 46, x + 190, y + 46)
                pdf.set_text_color(0, 0, 0)
                pdf.set_font('Arial', '', 10)
                txt2 = convert_quotes(record.patient_remark)
                pdf.multi_cell(w=0, h=ch,
                               txt=txt2, align='L')

            file_name = patient_name+"_"+str(weekno)+".pdf"
            filepath = os.path.join(BASE_DIR, 'media')
            pdf.output(filepath + "/" + file_name, 'F')
            return FileResponse(open(filepath + "/" + file_name, 'rb'), as_attachment=True,
                                content_type='application/pdf')
    except Exception as e:
        print(e)
        return redirect('/')


def convert_quotes(text):
    text = text.replace("“", "\"").replace("”", "\"")  # Replace curly double quotes with straight quotes
    text = text.replace("‘", "'").replace("’", "'")  # Replace curly single quotes with straight quotes
    return text


ch=8
@login_required
def patient_acknowledge_report(request,pid):
    try:
        if pid != None:
            id = pid
            patient = RefPatient.objects.get(user_id=id)
            patient_name = patient.first_name + " " + patient.last_name
            provider_id = patient.provider_id
            provider_id = str(provider_id[12:])
            provider = Provider.objects.get(user_id=provider_id)
            provider_name = provider.first_name + " " + provider.last_name
            provider_practice = provider.practice_address
            pp = ("\033[1m" + provider_name + "\033[0m")
            today = patient.timestamp#datetime.date.today()
            today = today.strftime('%m-%d-%Y %H:%M:%S')

            class PDF(FPDF):
                def header(self):
                    self.set_font('Arial', 'B', 10);
                    self.cell(60, 10, "Patient Name: " + patient_name, 0, 0, 'L');
                    self.cell(10);
                    self.cell(60, 10, "", 0, 0, 'L');
                    filepath = os.path.join(BASE_DIR, 'static/assets/images/logo-1.png')
                    self.image(filepath, 140, 10, 60);
                    pdf.ln()
                    #self.cell(60, 10, "Patient Name: " + patient_name, 0, 0, 'L');
                    #self.cell(10);
                    self.cell(60, 3, "Date: " + today, 0, 0, 'L');
                    pdf.ln()
                    x = pdf.get_x()
                    y = pdf.get_y()
                    pdf.set_line_width(0.8)
                    pdf.set_draw_color(32,11,148)
                    pdf.line(11, y +5, x + 190, y + 5)
                    pdf.ln(10)
                # Page footer
                def footer(self):
                    self.set_y(-15)
                    y = pdf.get_y()
                    pdf.set_line_width(0.8)
                    pdf.set_draw_color(32, 11, 148)
                    pdf.line(0, y, 209, y)
                    # Page number
                    self.cell(5)
                    pdf.set_text_color(32, 11, 148)
                    self.cell(40, 15, "www.cognisleep.com", 0, 0, 'L');
                    self.cell(100);
                    self.cell(40, 15, "support@cognisleep.com", 0, 0, 'L');



            pdf = PDF(orientation='L', unit='mm', format=(297,210))
            pdf.alias_nb_pages()
            pdf.add_page()


            pdf.set_font('Arial', 'B', 18)
            pdf.set_text_color(32, 11, 148)
            pdf.cell(w=190, h=ch, txt="Cognisleep Consent For Treatment", ln=1, align='C')
            pdf.ln(10)
            pdf.set_font('Arial', '', 10)
            pdf.set_text_color(0, 0, 0)

            pdf.multi_cell(w=190, h=6, txt="Cognisleep is a sleep therapy program that is used to treat Chronic insomnia. Cognisleep is based on the principles of cognitive behavioral therapy for insomnia, also called CBT-I.",align='L')
            pdf.ln(2)

            pdf.multi_cell(w=190, h=6,txt="CBT-I has been found to improve insomnia symptoms in up to 80% of individuals with Chronic insomnia, and 90% of the patients have been able to reduce or stop using sleep medications (Sleep Health Foundation publication Feb 14, 2023).",align='L')
            pdf.ln(2)

            pdf.multi_cell(w=190, h=6,
                     txt="Cognisleep is not a sleeping pill. Cognisleep is a natural and long-lasting alternative to sleeping pills. One of the end results of using Cognisleep is the reduction or complete elimination of sleeping pills.",align='L')
            pdf.ln(2)

            pdf.multi_cell(w=190, h=6,
                     txt="Sleeping pills are associated with significant side effects, and they don't address the core problem of Chronic insomnia. Sleeping pills are best used for a short time and not for an extended period of time.Sleeping pills have been linked to memory loss, daytime grogginess, or sleepiness, and in some cases, addiction, to name a few. The longer sleeping is taken, the more likely you may develop significant side effects (Sleep Foundation publication July 17, 2023).",align='L')
            pdf.ln(2)

            pdf.multi_cell(w=190, h=6,
                     txt="Chronic insomnia is developed over time due to a combination of predisposing, precipitating, and perpetuating factors. Predisposing factors include advancing age, family history of insomnia, female sex, a certain lifestyle, and stress or worry. Precipitating factors include Acute stress, illness, jet lag, or a psychiatric condition (such as an episode of depression) that may lead to poor sleep. The result is that the patient develops Perpetuating factors which include behaviors and negative thoughts as well as negative emotions that maintain the poor sleep cycle. Behaviors involve poor sleep habits, primarily napping and spending extended time in bed trying to force sleep, which dysregulates the sleep-wakecycle and disturbs the sleep drive. ",align='L')
            pdf.ln(2)

            pdf.multi_cell(w=190, h=6,
                     txt="Negative thoughts and emotions otien include unhealthy beliefs about sleep and undue worries, which perpetuate sleep problems. To break the cycle for good, it requires a step-to-step approach that deals with the core of Chronic insomnia. (Spielman AJ, et al. A behavioral perspective on insomnia treatment.Psychiatric Clinics of North America. 1987; 10:541-553.",align='L')
            pdf.ln(2)
            pdf.multi_cell(w=190, h=6,
                           txt="Cognisleep addresses the factors that contribute to chronic insomnia. Cognisleep consists of 6 weekly treatment sessions. While You may go at your own pace, we strongly encourage our patients to finish the program within 6-8 weeks, as it is more effective when used this way",align='L')
            pdf.ln(2)
            pdf.multi_cell(w=190, h=6,
                           txt="The therapy has five main components: Consolidation of sleep, Stimulus control, Cognitive therapy, Instructions on Sleep hygiene, and various uses of Relaxation techniques.",align='L')
            pdf.ln(2)
            #pdf.cell(w=5, h=6, txt="6.", ln=0)
            pdf.multi_cell(w=190, h=6,
                           txt="Certain people may experience a temporary increase in drowsiness at the initiation of treatment, but it is short-term. We encourage patients undergoing Cognisleep treatment to avoid operating a motor vehicle or any other heavy machinery during this period if feeling sleepy.",align='L')
            pdf.ln(1)
            text = "By clicking this box, I understand and agree with the above statements. " \
                   "I consent to Cognisleep treatment at "+provider_practice.upper()+" under the " \
                   "supervision of "+provider_name.upper()+"."


            filepath = os.path.join(BASE_DIR, 'static/assets/images/icons/checkbox.png')
            y= pdf.get_y() + 3

            pdf.image(filepath, 10, y ,5 );
            pdf.ln(1)
            pdf.cell(w=5, h=6, ln=0)
            # Add the text after the checkbox
            pdf.multi_cell(w=190, h=6, txt=text, align="L")




            file_name = patient_name+".pdf"
            filepath = os.path.join(BASE_DIR, 'media')
            pdf.output(filepath + "/" + file_name, 'F')
            return FileResponse(open(filepath + "/" + file_name, 'rb'), as_attachment=True,
                                content_type='application/pdf')
    except Exception as e:
        print(e)
        return redirect('/')