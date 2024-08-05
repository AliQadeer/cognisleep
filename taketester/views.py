from django.shortcuts import render, redirect, reverse
from django.conf import settings
from rest_framework import status
from accounts.models import RefPatient, Provider, Provider_Verification
from cogni.views import email_records
from .models import TakeTester_questions, Guest_User, DealBreakerQuestions, Question_new, UserAnswer, Options_new
from django import template
import requests
from rest_framework.views import exception_handler
from rest_framework.response import Response
from django.core.mail import send_mail
from django.template import loader
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView
from django.shortcuts import render
from django.contrib import messages
from collections import Counter
from rest_framework.permissions import AllowAny
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.db.models import Count
from dashboard.models import SendFax, SleepDiary
from .forms import GuestUserForm
from .serializer import QuestionSerializer, UserAnswerSerializer, SaveQuestionSerializer, OptionsSerializer
import datetime
import os
from cogni.settings import BASE_DIR
from fpdf import FPDF
from django.http import FileResponse

# Create your views here.

register = template.Library()


class GuestView(TemplateView):
    template_name = 'guest_user_form.html'

    def get(self, request):
        form = GuestUserForm()

        return render(request, self.template_name, {'form': form})


def acknowledge_page(request, id):
    if id !="":
        context = {
            'title': 'Cogni Sleep |  cogni_questions',
            'base_url': settings.BASE_URL,
            'price_selec': id

        }
        messages.error(request, "User already exist.")
        return render(request, "cogni_questions.html", context)

    context = {
        'title': 'Cogni Sleep |  cogni_questions',
        'base_url': settings.BASE_URL,
        'price_selec': id

    }
    messages.error(request, "User already exist.")
    return render(request, "cogni_questions.html", context)


def cogni_questions(request):
    offset = 0
    limit = 1
    progressbar_ref = 0
    question_array = []
    question_code_array = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    ans_code_array = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]


    request.session['ans_code'] = '1'
    class_name = "result_bar_green"
    txt_insomnia_points = "You May Not Have Insomnia"
    txt_insomnia_msg = "However, you still may have a sleep disorder like sleep apnea, Restless Leg Syndrome, or others. Please click the next button to answer a few more questions about your sleep."
    sr = 0
    ans_sr = 1
    answer_radiovalue = ''
    if "ans_sr" in request.POST:
        myans = int(request.POST['ans_sr'])+1
    else:
        myans = 1

    # all_questions = TakeTester_questions.objects.all()[offset:limit]
    # all_questions = TakeTester_questions.objects.raw('SELECT * FROM taketester_taketester_questions limit %s ,1',
    #                                                  [offset])
    all_questions = TakeTester_questions.objects.raw('SELECT * FROM taketester_taketester_questions limit %s ,1',[offset])
    if request.method == 'POST' and 'getmyResult' in request.POST :
        response_captcha = int(request.POST.get("response_captcha"))
        if response_captcha is not 1:
            form = GuestUserForm(request.POST)

            context = {
                'title': 'Cogni Sleep |  cogni_questions',
                'base_url': settings.BASE_URL,
                'offset': offset,
                'limit': limit,
                'alldone': True,
                'class_name': class_name,
                'txt_insomnia_points': txt_insomnia_points,
                'txt_insomnia_msg': txt_insomnia_msg,
                'insomnia_value': request.POST['insomnia_value'],
                'form_guest': form

            }
            messages.error(request, "Recaptcha is not verified")
            return render(request, "cogni_questions.html", context)

        if request.method == 'POST':
            form_guest_user = GuestUserForm(request.POST or None)

            if form_guest_user.is_valid():

                guser = Guest_User.objects.filter(email__iexact=form_guest_user.cleaned_data['email'])
                if not guser.exists():
                    form_guest_user.save()
                    editForm = Guest_User.objects.get(email=form_guest_user.cleaned_data['email'])
                    editForm.txt_insomnia_points = request.POST['txt_insomnia_points']
                    editForm.txt_insomnia_msg = request.POST['txt_insomnia_msg']
                    editForm.result_value = int(request.POST['insomnia_value'])
                    editForm.save()

                    request.session['guest_email'] = form_guest_user.cleaned_data['email']
                    request.session['guest_first_name'] = form_guest_user.cleaned_data['first_name']
                    request.session['guest_last_name'] = form_guest_user.cleaned_data['last_name']
                    request.session['guest_phone'] = form_guest_user.cleaned_data['phone']
                    request.session.save()


                else:
                    form = GuestUserForm(request.POST)

                    context = {
                        'title': 'Cogni Sleep |  cogni_questions',
                        'base_url': settings.BASE_URL,
                        'offset': offset,
                        'limit': limit,
                        'alldone': True,
                        'class_name': class_name,
                        'txt_insomnia_points': txt_insomnia_points,
                        'txt_insomnia_msg': txt_insomnia_msg,
                        'insomnia_value': request.POST['insomnia_value'],
                        'form_guest': form

                    }
                    messages.error(request, "User already exist.")
                    return render(request, "cogni_questions.html", context)

            print(request.POST)

            context_data = {
                'title': 'Cogni Sleep |  cogni_questions',
                'base_url': settings.BASE_URL,
                'offset': offset,
                'limit': limit,
                'alldone': True,
                'class_name': request.POST['class_name'],
                'txt_insomnia_points': request.POST['txt_insomnia_points'],
                'txt_insomnia_msg': request.POST['txt_insomnia_msg'],
                'insomnia_value': request.POST['insomnia_value']

            }

            subject = 'Guest User'
            to = request.POST['email']

            html_message = loader.render_to_string(
                'email_temp/guest_template.html',
                {
                    'class_name': request.POST['class_name'],
                    'txt_insomnia_points': request.POST['txt_insomnia_points'],
                    'txt_insomnia_msg': request.POST['txt_insomnia_msg']

                }
            )
            email_records(request, to, settings.EMAIL_FROM, subject)
            send_mail(
                subject,
                'hello',
                settings.EMAIL_FROM,
                [to,settings.EMAIL_FROM],
                html_message=html_message
                ,
            )
            request.session['isQDone'] = "yes"
            return render(request, "cogni-no-insomnia-questions.html", context_data)

    if request.method == 'POST':
        all_questions = TakeTester_questions.objects.raw('SELECT * FROM taketester_taketester_questions WHERE id = %s',
                                                         [myans])

        print(request.POST)
        print(request.session['ans_code'])
        if 'prev' in request.POST:
            offset = int(request.POST['offset']) - 1
        if 'next' in request.POST:
            offset = int(request.POST['offset']) + 1
            sr = int(request.POST['sr']) + 1
            ans_sr = int(request.POST['ans_sr']) + 1

            _array = request.POST['question_code_array']
            question_code_array = [int(x.strip()) for x in _array.split(',') if x]

            _array = request.POST['ans_code_array']
            ans_code_array = [int(x.strip()) for x in _array.split(',') if x]

            insomnia_value = calculate_insomnia(ans_code_array)

        if ans_sr > TakeTester_questions.objects.all().count():

            _array = request.POST['question_code_array']
            question_code_array = [int(x.strip()) for x in _array.split(',') if x]

            _array = request.POST['ans_code_array']
            ans_code_array = [int(x.strip()) for x in _array.split(',') if x]

            if request.POST['ans'] == 'Not at all':
                ans_code_array[int(request.POST['sr'])] = 10

            if request.POST['ans'] == 'Just a little':
                ans_code_array[int(request.POST['sr'])] = 8

            if request.POST['ans'] == 'Somewhat':
                ans_code_array[int(request.POST['sr'])] = 6

            if request.POST['ans'] == 'Often':
                ans_code_array[int(request.POST['sr'])] = 4

            if request.POST['ans'] == 'Very often':
                ans_code_array[int(request.POST['sr'])] = 2

            insomnia_value = calculate_insomnia(ans_code_array)

            if int(insomnia_value) == 100:
                class_name = "result_bar_green"
                txt_insomnia_points = "You May Not Have Insomnia"
                txt_insomnia_msg = "However, you still may have a sleep disorder like sleep apnea, Restless Leg Syndrome, or others. Please click the next button to answer a few more questions about your sleep."

            elif int(insomnia_value) < 100 and int(insomnia_value) >= 80:
                class_name = "result_bar_red"
                txt_insomnia_points = "You May Have Mild Insomnia"
                txt_insomnia_msg = "Your test results are showing that you may have Mild Insomnia. Now is the time to prevent your condition from progressing to a more serious form of insomnia. You are a great candidate for CogniSleep!"

            elif int(insomnia_value) < 80 and int(insomnia_value) >= 60:
                class_name = "result_bar_red"
                txt_insomnia_points = "You May have Moderate Insomnia"
                txt_insomnia_msg = "Your test results are showing that you are experiencing Moderate Insomnia. Now is the time for treatment to prevent your condition from progressing to Severe Insomnia. You are a great candidate for CogniSleep!"

            elif int(insomnia_value) < 60 and int(insomnia_value) >= 0:
                class_name = "result_bar_red"
                txt_insomnia_points = "You May have Severe Insomnia"
                txt_insomnia_msg = "Your test results are showing that you may have Severe Insomnia and CogniSleep can help you. It is crucial that you receive the tools you need to battle your Insomnia and get the quality sleep you deserve. You are a great candidate for CogniSleep! "

            form = GuestUserForm()

            context = {
                'title': 'Cogni Sleep |  cogni_questions',
                'base_url': settings.BASE_URL,
                'offset': offset,
                'limit': limit,
                'alldone': True,
                'class_name': class_name,
                'txt_insomnia_points': txt_insomnia_points,
                'txt_insomnia_msg': txt_insomnia_msg,
                'insomnia_value': insomnia_value,
                'form_guest': form

            }

            return render(request, "cogni_questions.html", context)

        else:

            _array = request.POST['question_code_array']
            question_code_array = [int(x.strip()) for x in _array.split(',') if x]

            _array = request.POST['ans_code_array']
            ans_code_array = [int(x.strip()) for x in _array.split(',') if x]

            if 'next' in request.POST:

                if request.POST['ans'] == 'Not at all':
                    ans_code_array[int(request.POST['sr'])] = 10

                if request.POST['ans'] == 'Just a little':
                    ans_code_array[int(request.POST['sr'])] = 8

                if request.POST['ans'] == 'Somewhat':
                    ans_code_array[int(request.POST['sr'])] = 6

                if request.POST['ans'] == 'Often':
                    ans_code_array[int(request.POST['sr'])] = 4

                if request.POST['ans'] == 'Very often':
                    ans_code_array[int(request.POST['sr'])] = 2

                question_code_array[int(request.POST['sr'])] = int(request.POST['question'])
                progressbar_ref = int(request.POST['progressbar_ref']) + 10

                ans = ans_code_array[sr]
                context = {
                    'title': 'Cogni Sleep |  cogni_questions',
                    'base_url': settings.BASE_URL,
                    'questions': all_questions,
                    'offset': offset,
                    'limit': limit,
                    'progressbar_ref': progressbar_ref,
                    'question_code_array': str(question_code_array).strip('[]'),
                    'ans_code_array': str(ans_code_array).strip('[]'),
                    'ans_sr': ans_sr,
                    'sr': sr,
                    'answer_radiovalue': ans,
                    'isback': False

                }
                print(question_code_array)
                print(ans_code_array)

                return render(request, "cogni_questions.html", context)

            if 'prev' in request.POST:
                progressbar_ref = int(request.POST['progressbar_ref']) - 10
                offset = int(request.POST['offset']) - 1
                sr = int(request.POST['sr']) - 1
                ans_sr = int(request.POST['ans_sr']) - 1
                ans = ans_code_array[sr]

                context = {
                    'title': 'Cogni Sleep |  cogni_questions',
                    'base_url': settings.BASE_URL,
                    'questions': all_questions,
                    'offset': offset,
                    'limit': limit,
                    'progressbar_ref': progressbar_ref,
                    'question_code_array': str(question_code_array).strip('[]'),
                    'ans_code_array': str(ans_code_array).strip('[]'),
                    'ans_sr': ans_sr,
                    'sr': sr,
                    'answer_radiovalue': ans,
                    'isback': True

                }
                print(context)

                return render(request, "cogni_questions.html", context)

    else:

        context = {
            'title': 'Cogni Sleep |  cogni_questions',
            'base_url': settings.BASE_URL,
            'offset': offset,
            'questions': all_questions,
            'limit': limit,
            'progressbar_ref': progressbar_ref,
            'question_code_array': str(question_code_array).strip('[]'),
            'ans_code_array': str(ans_code_array).strip('[]'),
            'ans_sr': ans_sr,
            'sr': sr,
            'answer_radiovalue': answer_radiovalue

        }

        print(question_code_array)
        print(ans_code_array)

        return render(request, "cogni_questions.html", context)


@login_required
def cogni_questionsv2(request):
    offset, limit = 0, 1
    sr = 0
    ans_sr = 1
    deal_breaker_id = 1
    yes_counter = 0
    no_counter = 0

    answer_radiovalue = ''
    print(request.POST)
    if request.method == 'POST':
        if "ans" not in request.POST:
            return redirect(request.META.get('HTTP_REFERER', '/'))


        print(request.POST)
        if 'prev' in request.POST:
            offset = int(request.POST['offset']) - 1
            sr = int(request.POST['sr']) - 1
            ans_sr = int(request.POST['ans_sr']) - 1
            deal_breaker_id = int(request.POST['deal_breaker_id'])
            no_counter = int(request.POST['no_counter']) - 1
            _array = request.POST['answer_array']
            answer_array = [int(x.strip()) for x in _array.split(',') if x]
            # answer_array[int(request.POST['sr'])] = 0
            all_questions = DealBreakerQuestions.objects.raw(
                'SELECT * FROM taketester_dealbreakerquestions where deal_breaker_id=%s  limit %s ,1',
                [deal_breaker_id, offset])

            ans = answer_array[sr]


            context = {
                'title': 'Cogni Sleep |  cogni_questions',
                'base_url': settings.BASE_URL,
                'offset': offset,
                'questions': all_questions,
                'limit': limit,
                'ans_sr': ans_sr,
                'answer_radiovalue': ans,
                'deal_breaker_id': deal_breaker_id,
                'sr': sr,
                'yes_counter': yes_counter,
                'no_counter': no_counter,
                'answer_array': str(answer_array).strip('[]'),
            }

            return render(request, "cogni_questionsv2.html", context)


        if 'next' in request.POST:
            offset = int(request.POST['offset']) + 1
            sr = int(request.POST['sr']) + 1
            ans_sr = int(request.POST['ans_sr']) + 1
            deal_breaker_id = int(request.POST['deal_breaker_id'])

            _array = request.POST['answer_array']
            answer_array = [int(x.strip()) for x in _array.split(',') if x]

            if request.POST['ans'] == 'No':
                newArray = Counter(answer_array)
                print("No array : ", newArray)
                if sr <= 2:
                    deal_breaker_id = int(request.POST['deal_breaker_id']) + 1
                    print("deal_breaker_id: ", deal_breaker_id)
                    offset = 0
                    sr= 0

                    all_questions = DealBreakerQuestions.objects.raw(
                        'SELECT * FROM taketester_dealbreakerquestions where deal_breaker_id=%s  limit %s ,1',
                        [deal_breaker_id, offset])

                    total_deal_breakquestions = DealBreakerQuestions.objects.filter(deal_breaker_id=deal_breaker_id)
                    answer_array = [0] * total_deal_breakquestions.count()

                    context = {
                        'title': 'Cogni Sleep |  cogni_questions',
                        'base_url': settings.BASE_URL,
                        'offset': offset,
                        'questions': all_questions,
                        'limit': limit,
                        'ans_sr': ans_sr,
                        'deal_breaker_id': deal_breaker_id,
                        'sr': sr,
                        'yes_counter': yes_counter,
                        'no_counter': no_counter,
                        'answer_array': str(answer_array).strip('[]'),
                    }

                   # return render(request, "cogni_questionsv2.html", context)

                    if deal_breaker_id == 6:
                        print("Deal break with all no")
                        context = {
                            'title': 'Cogni Sleep |  cogni_questions',
                            'base_url': settings.BASE_URL,
                            #'message_data': "Your test results indicate that it would be best to talk to a doctor about your sleep. <a href='https://sicknwell.com/' target='_blank'>Click Here</a>  to schedule an appointment to see a doctor about your sleep concerns.",
                            'message_data': "Apparently Your Condition is beyond the scope of Cogni Sleep. Please see a doctor about your condition. <a href='https://sicknwell.com/' target='_blank'>Click Here</a>",
                            'site_url': "https://sicknwell.com/"
                        }
                        return render(request, "questionsv2_answer.html", context)

                answer_array[int(request.POST['sr'])] = 0
                total_deal_breakquestions = DealBreakerQuestions.objects.filter(deal_breaker_id=deal_breaker_id)
                print(total_deal_breakquestions.count())

                if sr >= total_deal_breakquestions.count():

                    newArray = answer_array[2:]

                    print(newArray)

                    if deal_breaker_id == 1:

                        if 0 in newArray and 1 in newArray:
                            message_data = "Your test results are showing that you have symptoms of Sleep Apnea. This disorder affects many Americans each year. <a href='https://sicknwell.com/' target='_blank'>Click Here</a> to schedule an appointment to see a doctor about your sleep concerns."
                            site_url = "https://mhsleeptesting.com/"

                        elif 0 in newArray:
                            #We are a bit confused... It seems that based from your responses you are not showing any symptoms of a sleep condition. You might need to be seen by a doctor.
                            message_data = "We are a bit confused. Based on your responses, it seems that you are not showing any symptoms of a sleep condition. You may need to be seen by a doctor."
                            site_url = "https://sicknwell.com/"

                        elif 1 in newArray:
                            message_data = "Your test results are showing that you have symptoms of Sleep Apnea. This disorder affects many Americans each year. <a href='https://sicknwell.com/' target='_blank'>Click Here</a> to schedule an appointment to see a doctor about your sleep concerns."
                            site_url = "https://mhsleeptesting.com/"
                        print(answer_array)

                        context = {
                            'title': 'Cogni Sleep |  cogni_questions',
                            'base_url': settings.BASE_URL,
                            'message_data': message_data,
                            'site_url': site_url
                        }

                        return render(request, "questionsv2_answer.html", context)

                    if deal_breaker_id == 2:

                        if 0 in newArray and 1 in newArray:
                            message_data = "Your Test Results are showing that you have symptoms of Narcolepsy and Hypersomnia. These disorders affect many Americans each year. <a href='https://sicknwell.com/' target='_blank'>Click Here</a> to schedule an appointment to see a doctor about your sleep concerns. "
                            site_url = "https://sicknwell.com/"

                        elif 0 in newArray:
                            message_data = "Your Test Results are showing that you have symptoms of Narcolepsy and Hypersomnia. These disorders affect many Americans each year. <a href='https://sicknwell.com/' target='_blank'>Click Here</a> to schedule an appointment to see a doctor about your sleep concerns. "
                            site_url = "https://sicknwell.com/"

                        elif 1 in newArray:
                            message_data = "Your Test Results are showing that you have symptoms of Narcolepsy and Hypersomnia. These disorders affect many Americans each year. <a href='https://sicknwell.com/' target='_blank'>Click Here</a> to schedule an appointment to see a doctor about your sleep concerns. "
                            site_url = "https://sicknwell.com/"

                        print(answer_array)

                        context = {
                            'title': 'Cogni Sleep |  cogni_questions',
                            'base_url': settings.BASE_URL,
                            'message_data': message_data,
                            'site_url': site_url
                        }

                        return render(request, "questionsv2_answer.html", context)

                    if deal_breaker_id == 3:

                        if 0 in newArray and 1 in newArray:
                            message_data = "Your Test Results are showing that you have symptoms of Periodic Limb Movement Disorder or Restless Leg Syndrome. These disorders affect many Americans each year. <a href='https://sicknwell.com/' target='_blank'>Click Here</a> to schedule an appointment to see a doctor about your sleep concerns."
                            site_url = "https://sicknwell.com/"

                        elif 0 in newArray:
                            message_data = "Your Test Results are showing that you have symptoms of Periodic Limb Movement Disorder or Restless Leg Syndrome. These disorders affect many Americans each year. <a href='https://sicknwell.com/' target='_blank'>Click Here</a> to schedule an appointment to see a doctor about your sleep concerns."
                            site_url = "https://sicknwell.com/"

                        elif 1 in newArray:
                            message_data = "Your Test Results are showing that you have symptoms of Periodic Limb Movement Disorder or Restless Leg Syndrome. These disorders affect many Americans each year. <a href='https://sicknwell.com/' target='_blank'>Click Here</a> to schedule an appointment to see a doctor about your sleep concerns."
                            site_url = "https://sicknwell.com/"

                        print(answer_array)

                        context = {
                            'title': 'Cogni Sleep |  cogni_questions',
                            'base_url': settings.BASE_URL,
                            'message_data': message_data,
                            'site_url': site_url
                        }

                        return render(request, "questionsv2_answer.html", context)

                    if deal_breaker_id == 4:

                        if 0 in newArray and 1 in newArray:
                            message_data = "Your Test Results are showing that you have symptoms of REM Sleep Behavior Disorder (RBD). This disorder affects many Americans each year. <a href='https://sicknwell.com/' target='_blank'>Click Here</a> to schedule an appointment to see a doctor about your sleep concerns. "
                            site_url = "https://sicknwell.com/"

                        elif 0 in newArray:
                            message_data = "Your Test Results are showing that you have symptoms of REM Sleep Behavior Disorder (RBD). This disorder affects many Americans each year. <a href='https://sicknwell.com/' target='_blank'>Click Here</a> to schedule an appointment to see a doctor about your sleep concerns. "
                            site_url = "https://sicknwell.com/"

                        elif 1 in newArray:
                            message_data = "Your Test Results are showing that you have symptoms of REM Sleep Behavior Disorder (RBD). This disorder affects many Americans each year. <a href='https://sicknwell.com/' target='_blank'>Click Here</a> to schedule an appointment to see a doctor about your sleep concerns. "
                            site_url = "https://sicknwell.com/"

                        print(answer_array)

                        context = {
                            'title': 'Cogni Sleep |  cogni_questions',
                            'base_url': settings.BASE_URL,
                            'message_data': message_data,
                            'site_url': site_url
                        }

                        return render(request, "questionsv2_answer.html", context)

                    if deal_breaker_id == 5:

                        if 0 in newArray and 1 in newArray:
                            message_data = "Your Test Results are showing that you have symptoms of Shift Work Disorder. This disorder affects many Americans each year. <a href='https://sicknwell.com/' target='_blank'>Click here</a> to schedule an appointment to see a doctor about your sleep concerns."
                            site_url = "https://sicknwell.com/"

                        elif 0 in newArray:
                            message_data = "Your Test Results are showing that you have symptoms of Shift Work Disorder. This disorder affects many Americans each year. <a href='https://sicknwell.com/' target='_blank'>Click here</a> to schedule an appointment to see a doctor about your sleep concerns."
                            site_url = "https://sicknwell.com/"

                        elif 1 in newArray:
                            message_data = "Your Test Results are showing that you have symptoms of Shift Work Disorder. This disorder affects many Americans each year. <a href='https://sicknwell.com/' target='_blank'>Click here</a> to schedule an appointment to see a doctor about your sleep concerns."
                            site_url = "https://sicknwell.com/"

                        print(answer_array)

                        context = {
                            'title': 'Cogni Sleep |  cogni_questions',
                            'base_url': settings.BASE_URL,
                            'message_data': message_data,
                            'site_url': site_url
                        }

                        return render(request, "questionsv2_answer.html", context)

                all_questions = DealBreakerQuestions.objects.raw(
                    'SELECT * FROM taketester_dealbreakerquestions where deal_breaker_id=%s  limit %s ,1',
                    [deal_breaker_id, offset])

                total_deal_breakquestions = DealBreakerQuestions.objects.filter(deal_breaker_id=deal_breaker_id)
                answer_array = [0] * total_deal_breakquestions.count()

                context = {
                    'title': 'Cogni Sleep |  cogni_questions',
                    'base_url': settings.BASE_URL,
                    'offset': offset,
                    'questions': all_questions,
                    'limit': limit,
                    'ans_sr': ans_sr,
                    'deal_breaker_id': deal_breaker_id,
                    'sr': sr,
                    'yes_counter': yes_counter,
                    'no_counter': no_counter,
                    'answer_array': str(answer_array).strip('[]'),
                }

                return render(request, "cogni_questionsv2.html", context)

            if request.POST['ans'] == 'Yes':

                deal_breaker_id = int(request.POST['deal_breaker_id'])
                answer_array[int(request.POST['sr'])] = 1

                newArray = Counter(answer_array)
                print("No array : ", newArray)

                total_deal_breakquestions = DealBreakerQuestions.objects.filter(deal_breaker_id=deal_breaker_id)
                print(total_deal_breakquestions.count())

                if sr >= total_deal_breakquestions.count():

                    newArray = answer_array[2:]

                    print(newArray)

                    if deal_breaker_id == 1:

                        if 0 in newArray and 1 in newArray:
                            message_data = "Your test results are showing that you have symptoms of Sleep Apnea. This disorder affects many Americans each year. <a href='https://sicknwell.com/' target='_blank'>Click Here</a> to schedule an appointment to see a doctor about your sleep concerns."
                            site_url = "https://mhsleeptesting.com/"

                        elif 0 in newArray:
                            #We are a bit confused... It seems that based from your responses you are not showing any symptoms of a sleep condition. You might need to be seen by a doctor.
                            message_data = "We are a bit confused. Based on your responses, it seems that you are not showing any symptoms of a sleep condition. You may need to be seen by a doctor."
                            site_url = "https://sicknwell.com/"

                        elif 1 in newArray:
                            message_data = "Your test results are showing that you have symptoms of Sleep Apnea. This disorder affects many Americans each year. <a href='https://sicknwell.com/' target='_blank'>Click Here</a> to schedule an appointment to see a doctor about your sleep concerns."
                            site_url = "https://mhsleeptesting.com/"
                        print(answer_array)

                        context = {
                            'title': 'Cogni Sleep |  cogni_questions',
                            'base_url': settings.BASE_URL,
                            'message_data': message_data,
                            'site_url': site_url
                        }

                        return render(request, "questionsv2_answer.html", context)

                    if deal_breaker_id == 2:

                        if 0 in newArray and 1 in newArray:
                            message_data = "Your Test Results are showing that you have symptoms of Narcolepsy and Hypersomnia. These disorders affect many Americans each year. <a href='https://sicknwell.com/' target='_blank'>Click Here</a> to schedule an appointment to see a doctor about your sleep concerns. "
                            site_url = "https://sicknwell.com/"

                        elif 0 in newArray:
                            message_data = "Your Test Results are showing that you have symptoms of Narcolepsy and Hypersomnia. These disorders affect many Americans each year. <a href='https://sicknwell.com/' target='_blank'>Click Here</a> to schedule an appointment to see a doctor about your sleep concerns. "
                            site_url = "https://sicknwell.com/"

                        elif 1 in newArray:
                            message_data = "Your Test Results are showing that you have symptoms of Narcolepsy and Hypersomnia. These disorders affect many Americans each year. <a href='https://sicknwell.com/' target='_blank'>Click Here</a> to schedule an appointment to see a doctor about your sleep concerns. "
                            site_url = "https://sicknwell.com/"

                        print(answer_array)

                        context = {
                            'title': 'Cogni Sleep |  cogni_questions',
                            'base_url': settings.BASE_URL,
                            'message_data': message_data,
                            'site_url': site_url
                        }

                        return render(request, "questionsv2_answer.html", context)

                    if deal_breaker_id == 3:

                        if 0 in newArray and 1 in newArray:
                            message_data = "Your Test Results are showing that you have symptoms of Periodic Limb Movement Disorder or Restless Leg Syndrome. These disorders affect many Americans each year. <a href='https://sicknwell.com/' target='_blank'>Click Here</a> to schedule an appointment to see a doctor about your sleep concerns."
                            site_url = "https://sicknwell.com/"

                        elif 0 in newArray:
                            message_data = "Your Test Results are showing that you have symptoms of Periodic Limb Movement Disorder or Restless Leg Syndrome. These disorders affect many Americans each year. <a href='https://sicknwell.com/' target='_blank'>Click Here</a> to schedule an appointment to see a doctor about your sleep concerns."
                            site_url = "https://sicknwell.com/"

                        elif 1 in newArray:
                            message_data = "Your Test Results are showing that you have symptoms of Periodic Limb Movement Disorder or Restless Leg Syndrome. These disorders affect many Americans each year. <a href='https://sicknwell.com/' target='_blank'>Click Here</a> to schedule an appointment to see a doctor about your sleep concerns."
                            site_url = "https://sicknwell.com/"

                        print(answer_array)

                        context = {
                            'title': 'Cogni Sleep |  cogni_questions',
                            'base_url': settings.BASE_URL,
                            'message_data': message_data,
                            'site_url': site_url
                        }

                        return render(request, "questionsv2_answer.html", context)

                    if deal_breaker_id == 4:

                        if 0 in newArray and 1 in newArray:
                            message_data = "Your Test Results are showing that you have symptoms of REM Sleep Behavior Disorder (RBD). This disorder affects many Americans each year. <a href='https://sicknwell.com/' target='_blank'>Click Here</a> to schedule an appointment to see a doctor about your sleep concerns. "
                            site_url = "https://sicknwell.com/"

                        elif 0 in newArray:
                            message_data = "Your Test Results are showing that you have symptoms of REM Sleep Behavior Disorder (RBD). This disorder affects many Americans each year. <a href='https://sicknwell.com/' target='_blank'>Click Here</a> to schedule an appointment to see a doctor about your sleep concerns. "
                            site_url = "https://sicknwell.com/"

                        elif 1 in newArray:
                            message_data = "Your Test Results are showing that you have symptoms of REM Sleep Behavior Disorder (RBD). This disorder affects many Americans each year. <a href='https://sicknwell.com/' target='_blank'>Click Here</a> to schedule an appointment to see a doctor about your sleep concerns. "
                            site_url = "https://sicknwell.com/"

                        print(answer_array)

                        context = {
                            'title': 'Cogni Sleep |  cogni_questions',
                            'base_url': settings.BASE_URL,
                            'message_data': message_data,
                            'site_url': site_url
                        }

                        return render(request, "questionsv2_answer.html", context)

                    if deal_breaker_id == 5:

                        if 0 in newArray and 1 in newArray:
                            message_data = "Your Test Results are showing that you have symptoms of Shift Work Disorder. This disorder affects many Americans each year. <a href='https://sicknwell.com/' target='_blank'>Click here</a> to schedule an appointment to see a doctor about your sleep concerns."
                            site_url = "https://sicknwell.com/"

                        elif 0 in newArray:
                            message_data = "Your Test Results are showing that you have symptoms of Shift Work Disorder. This disorder affects many Americans each year. <a href='https://sicknwell.com/' target='_blank'>Click here</a> to schedule an appointment to see a doctor about your sleep concerns."
                            site_url = "https://sicknwell.com/"

                        elif 1 in newArray:
                            message_data = "Your Test Results are showing that you have symptoms of Shift Work Disorder. This disorder affects many Americans each year. <a href='https://sicknwell.com/' target='_blank'>Click here</a> to schedule an appointment to see a doctor about your sleep concerns."
                            site_url = "https://sicknwell.com/"

                        print(answer_array)

                        context = {
                            'title': 'Cogni Sleep |  cogni_questions',
                            'base_url': settings.BASE_URL,
                            'message_data': message_data,
                            'site_url': site_url
                        }

                        return render(request, "questionsv2_answer.html", context)

                yes_counter = int(request.POST['yes_counter']) + 1

                all_questions = DealBreakerQuestions.objects.raw(
                    'SELECT * FROM taketester_dealbreakerquestions where deal_breaker_id=%s   limit %s ,1',
                    [deal_breaker_id, offset])

                context = {
                    'title': 'Cogni Sleep |  cogni_questions',
                    'base_url': settings.BASE_URL,
                    'offset': offset,
                    'questions': all_questions,
                    'limit': limit,
                    'ans_sr': ans_sr,
                    'deal_breaker_id': deal_breaker_id,
                    'sr': sr,
                    'yes_counter': yes_counter,
                    'no_counter': no_counter,
                    'answer_array': str(answer_array).strip('[]'),
                }

                print(answer_array)

                return render(request, "cogni_questionsv2.html", context)

    all_questions = DealBreakerQuestions.objects.raw(
        'SELECT * FROM taketester_dealbreakerquestions where deal_breaker_id=%s  limit %s ,1',
        [deal_breaker_id, offset])
    total_deal_breakquestions = DealBreakerQuestions.objects.filter(deal_breaker_id=deal_breaker_id)
    answer_array = [0] * total_deal_breakquestions.count()
    print(answer_array)
    context = {
        'title': 'Cogni Sleep |  cogni_questions',
        'base_url': settings.BASE_URL,
        'offset': offset,
        'questions': all_questions,
        'limit': limit,
        'ans_sr': ans_sr,
        'sr': sr,
        'deal_breaker_id': deal_breaker_id,
        'yes_counter': yes_counter,
        'no_counter': no_counter,
        'answer_array': str(answer_array).strip('[]'),
    }

    return render(request, "cogni_questionsv2.html", context)


def calculate_insomnia(arr):
    total = 0
    for item in arr:
        total += item
    return total


def thankyou(request):
    context = {
        'title': 'Cogni Sleep |  cogni_questions',
        'base_url': settings.BASE_URL,
    }
    return render(request, "thankyou.html", context)


def send_email_data(subject, from_email, to_email, message):
    send_mail(
        subject,
        message,
        from_email,
        [to_email]
        ,
    )

    return ""



@login_required
@api_view(['GET'])
@permission_classes((AllowAny,))
def cogni_questions(request):
    try:
        print("print 1")
        all_questions = Question_new.objects.all()
        print("print 2")
        all_questions_serializer = QuestionSerializer(all_questions, many=True)
        print("print 3")
        return Response(all_questions_serializer.data, status=status.HTTP_200_OK)
    except Exception as e:
        return Response(str(e), status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes((AllowAny,))
def cogni_answer(request):
    try:
        if "user_id" not in request.data:
            return Response("User id is missing (user_id)", status=status.HTTP_400_BAD_REQUEST)
        else:
            request.data["user"] = request.data['user_id']
        if "question_id" not in request.data:
            return Response("Qusetion id is missing (question_id)", status=status.HTTP_400_BAD_REQUEST)
        else:
            request.data["question"] = request.data['question_id']
        if "option_id" not in request.data:
            return Response("Option id is mising (option_id)", status=status.HTTP_400_BAD_REQUEST)
        else:
            request.data["option_selected"] = request.data['option_id']
        uid = request.data['user_id']
        qid = request.data['question_id']
        res = UserAnswer.objects.filter(user_id = uid,question_id=qid).count()
        if res == 0:
            user_answer_serializer = UserAnswerSerializer(data = request.data)
            if user_answer_serializer.is_valid():
                user_answer_serializer.save()
                return Response("Operation successfull", status=status.HTTP_200_OK)
            else:
                return Response(str(user_answer_serializer.errors), status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response("Record Already exist", status=status.HTTP_200_OK)
    except Exception as e:
        return Response(str(e), status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes((AllowAny,))
def is_submited(request, id=None, flg=None):

    try:
        if id is None:
            return Response("User id is missing (user_id)", status=status.HTTP_400_BAD_REQUEST)
        if flg is None:
            return Response("Pre/Post flag missing (flg)", status=status.HTTP_400_BAD_REQUEST)
        if flg == "pre":
           user_answer_exist = UserAnswer.objects.filter(user_id=id,question__is_pre=True).exists()
           if user_answer_exist:
               answer_count = UserAnswer.objects.filter(user_id=id, question__is_pre=True).count()
               print("Helloooooooooooooo", answer_count)
               if int(answer_count) == 15:
                   return Response("True", status=status.HTTP_200_OK)
               if int(answer_count) < 15:
                   return Response(answer_count, status=status.HTTP_200_OK)
           else:
               return Response(0, status=status.HTTP_200_OK)
        if flg == "post":
            user_answer_exist = UserAnswer.objects.filter(user_id=id, question__is_post=True).exists()
            if user_answer_exist:
                answer_count = UserAnswer.objects.filter(user_id=id, question__is_post=True).count()
                print("Helloooooooooooooo", answer_count)
                if int(answer_count) == 15:
                    return Response("True", status=status.HTTP_200_OK)
                if int(answer_count) < 15:
                    return Response(answer_count, status=status.HTTP_200_OK)
            else:
                return Response(0, status=status.HTTP_200_OK)
    except Exception as e:
        return Response(str(e), status=status.HTTP_400_BAD_REQUEST)

    # try:
    #     if id is None:
    #         return Response("User id is missing", status=status.HTTP_400_BAD_REQUEST)
    #     user_answer_exist = UserAnswer.objects.filter(user_id=id).exists()
    #     if user_answer_exist:
    #         return Response("True", status=status.HTTP_200_OK)
    #     else:
    #         return Response("False", status=status.HTTP_200_OK)
    #
    # except Exception as e:
    #     return Response(str(e), status=status.HTTP_400_BAD_REQUEST)
ch = 8
@login_required
def create_ciq_report(request,pid=None):
    try:
        if pid is not None:
            today = datetime.date.today()
            year = today.year
            today = today.strftime('%m-%d-%Y')
            prelist = [0]
            postlist = [0]
            preoption = [0]
            postoption = [0]
            preresult = [0]
            postresult = [0]

            questions = Question_new.objects.filter(is_pre=True, year = year)

            all_questions = Question_new.objects.filter( year = year)
            pre_exists = UserAnswer.objects.filter(user_id=pid, question__is_pre=True, question__year=year).exists()
            post_exists  = UserAnswer.objects.filter(user_id=pid, question__is_post=True, question__year=year).exists()
            user_answer_post = UserAnswer.objects.filter(user_id=pid, question__is_post=True, question__year=year)
            user_answer_pre = UserAnswer.objects.filter(user_id=pid, question__is_pre=True, question__year=year)
            for item in user_answer_pre:
                date1 = (item.date)
                date1 = date1.strftime('%m-%d-%Y')
                break
            for item in user_answer_post:
                date2 = (item.date)
                date2 = date2.strftime('%m-%d-%Y')
                break
            patient = RefPatient.objects.get(user_id=pid)
            patient_name = patient.first_name+" "+patient.last_name
            provider_id = patient.provider_id
            provider_id = str(provider_id[12:])
            provider = Provider.objects.get(user_id = provider_id)
            provider_name = provider.first_name +" "+ provider.last_name

            for item in all_questions:
                qid = item.id
                a = []
                if item.is_pre is True:
                    option = Options_new.objects.filter(question_new_id=qid).all()
                    for i in option:
                        a. append(i.id)
                    preoption.append(a)
                else:
                    option = Options_new.objects.filter(question_new_id=qid).all()
                    for i in option:
                        a.append(i.id)

                    postoption.append(a)

            for item in user_answer_pre:
                prelist.append(item.option_selected_id)
                res = Options_new.objects.filter(question_new_id=item.question_id).all()
                j = 1
                for i in res:
                    if i.id == item.option_selected_id:
                        preresult.append(j)
                        break
                    else:
                        j += 1
            for item in user_answer_post:
                postlist.append(item.option_selected_id)
                res = Options_new.objects.filter(question_new_id=item.question_id).all()
                j = 1
                for i in res:
                    if i.id == item.option_selected_id:
                        postresult.append(j)
                        break
                    else:
                        j += 1
            class PDF(FPDF):
                def header(self):
                    # Position at 1.5 cm from bottom
                    filepath = os.path.join(BASE_DIR, 'static/assets/images/logo-1.png')
                    self.image(filepath, 10, 10, 100);
                    self.set_font('Arial', 'B', 15);
                    self.cell(125);
                    self.cell(40, 25,"| Patient: "+patient_name, 0, 0, 'C');
                    self.cell(45);
                    self.cell(40, 25, "| Provider: " + provider_name, 0, 0, 'C');
                    self.cell(45);
                    self.cell(40, 25, "| Pre Test Date: " + date1, 0, 0, 'C');
                    self.cell(45);
                    if user_answer_post:
                        self.cell(40, 25, "| Post Test Date: " + date2, 0, 0, 'C');
                    else:
                        self.cell(40, 25, "| Post Test Date: ", 0, 0, 'C');
                    self.cell(45);
                    self.cell(40, 25, "| Generated On: " + today, 0, 0, 'C');
                    self.ln(30);
                    pdf.set_line_width(0.5)


                # Page footer
                def footer(self):
                    # Position at 1.5 cm from bottom
                    self.set_y(-15)
                    # Arial italic 8
                    self.set_font('Arial', 'I', 14)
                    # Page number
                    self.cell(0, 10, 'Page ' + str(self.page_no()) + '/{nb}', 0, 0, 'C')

            pdf = PDF(orientation='L', unit='mm', format=(300, 550))
            pdf.alias_nb_pages()
            pdf.add_page()

            pdf.set_font('Arial', 'B', 18)
            pdf.cell(w=525, h=ch, txt=" CIQ REPORT", border=0, ln=1, align='C')
            pdf.ln()

            pdf.set_font('Arial', 'B', 14)
            pdf.set_fill_color(255, 255, 255)


            pdf.set_text_color(0,0,0)
            pdf.cell(w=20, h=10, txt='S.NO', border='L,T,0,B', ln=0, align='C', fill=True)
            pdf.cell(w=220, h=10, txt='PRE QUESTIONS', border='0,T,0,B', ln=0, align='C', fill=True)
            pdf.cell(w=220, h=10, txt='POST QUESTIONS', border='0,T,0,B', ln=0, align='C', fill=True)
            pdf.cell(w=65, h=10, txt='RESULT', border='0,T,R,B', ln=1, align='C', fill=True)
            pdf.set_font('Arial', 'B', 13)
            if pre_exists == True and post_exists == False:
                print("1")
                i = 1
                for item in questions:
                    if i == 9:
                        pdf.add_page()
                        pdf.set_font('Arial', 'B', 14)
                        pdf.set_text_color(0, 0, 0)
                        pdf.cell(w=20, h=10, txt='S.NO', border='L,T,0,B', ln=0, align='C', fill=True)
                        pdf.cell(w=220, h=10, txt='PRE QUESTIONS', border='0,T,0,B', ln=0, align='C', fill=True)
                        pdf.cell(w=220, h=10, txt='POST QUESTIONS', border='0,T,0,B', ln=0, align='C', fill=True)
                        pdf.cell(w=65, h=10, txt='RESULT', border='0,T,R,B', ln=1, align='C', fill=True)

                    a1 = []
                    pdf.set_font('Arial', 'B', 12)
                    pdf.set_text_color(0, 0, 0)
                    q_length = len(str(item.name))
                    if q_length > 108:
                        pdf.cell(w=20, h=16,
                                 txt="Q-" + str(i),
                                 border='L,0,T,0', ln=0, align='C')
                    else:
                        pdf.cell(w=20, h=ch,
                                 txt="Q-" + str(i),
                                 border='L,0,T,0', ln=0, align='C')
                    x = pdf.get_x()
                    y = pdf.get_y()

                    pdf.set_text_color(0, 0, 0)
                    if q_length > 108:
                        pdf.cell(w=2, h=16, txt='', border='L,T,0,0', ln=0, align='C')
                    else:
                        pdf.cell(w=2, h=ch, txt='', border='L,T,0,0', ln=0, align='C')
                    pdf.multi_cell(w=216, h=ch,
                                   txt=item.name,
                                   border='0,0,T,0', align='L')
                    x1 = pdf.get_x()
                    y1 = pdf.get_y()
                    pdf.set_xy(x + 220, y)
                    if q_length > 108:
                        pdf.cell(w=2, h=16, txt='', border='L,0,0,0', ln=0, align='C')
                    else:
                        pdf.cell(w=2, h=ch, txt='', border='L,0,0,0', ln=0, align='C')
                    if i == 5 or i == 12:
                        pdf.multi_cell(w=216, h=ch,
                                       txt="Post Results will appear after the post questions submission.",
                                       border='0,0,0,0', align='C')
                    else:
                        pdf.multi_cell(w=216, h=ch,
                                       txt="",
                                       border='0,0,0,0', align='L')

                    a = float(pdf.get_y())
                    pdf.set_xy(x + 440, y)
                    pdf.set_font('Arial', 'B', 12)
                    if q_length > 108:
                        pdf.cell(w=65, h=16, txt=" ", border='0', ln=1, align='C')
                    else:
                        pdf.cell(w=65, h=ch, txt=" ", border='0', ln=1, align='C')

                    b = float(pdf.get_y())
                    if b < a:
                        y = pdf.get_y()
                        pdf.set_xy(470, y)
                        pdf.cell(w=65, h=ch, txt="", border='0', ln=1)

                    option = Options_new.objects.filter(question_new_id=item.id).all()

                    for opt in option:
                        a1.append(opt.name)

                    x = pdf.get_x()
                    y = pdf.get_y()
                    pdf.set_font('Arial', 'B', 12)
                    pdf.cell(w=20, h=ch,
                             txt="",
                             border='L,0,0,B', ln=0, align='C')
                    pdf.cell(w=2, h=ch, txt='', border='L,0,0,B', ln=0, align='C')
                    if preoption[i][0] == prelist[i]:
                        pdf.set_font('Arial', 'B', 12)
                        a = "(X)"
                    else:
                        pdf.set_font('Arial', 'B', 12)
                        pdf.set_text_color(0, 0, 0)
                        a = ""
                    pdf.cell(w=54, h=ch,
                             txt=a + " 0 - " + a1[0],
                             border='0,0,0,B', ln=0, align='C')
                    if preoption[i][1] == prelist[i]:
                        pdf.set_font('Arial', 'B', 12)
                        a = "(X)"
                    else:
                        pdf.set_font('Arial', 'B', 12)
                        pdf.set_text_color(0, 0, 0)
                        a = ""
                    pdf.cell(w=54, h=ch,
                             txt=a + " 1 - " + a1[1],
                             border='0,0,0,B', ln=0, align='C')
                    if preoption[i][2] == prelist[i]:
                        pdf.set_font('Arial', 'B', 12)
                        a = "(X)"
                    else:
                        pdf.set_font('Arial', 'B', 12)
                        pdf.set_text_color(0, 0, 0)
                        a = ""
                    pdf.cell(w=54, h=ch,
                             txt=a + " 2 - " + a1[2],
                             border='0,0,0,B', ln=0, align='C')
                    if preoption[i][3] == prelist[i]:
                        pdf.set_font('Arial', 'B', 12)
                        a = "(X)"
                    else:
                        pdf.set_font('Arial', 'B', 12)
                        pdf.set_text_color(0, 0, 0)
                        a = ""
                    pdf.cell(w=54, h=ch,
                             txt=a + " 3 - " + a1[3],
                             border='0,0,0,B', ln=0, align='C')
                    pdf.cell(w=2, h=ch, txt='', border='0,0,R,B', ln=0, align='C')


                    pdf.set_font('Arial', 'B', 12)

                    pdf.cell(w=2, h=ch, txt='', border='0', ln=0, align='C')
                    pdf.cell(w=54, h=ch,
                             txt="",
                             border='0', ln=0, align='C')

                    pdf.cell(w=54, h=ch,
                             txt="",
                             border='0', ln=0, align='C')

                    pdf.cell(w=54, h=ch,
                             txt="",
                             border='0', ln=0, align='C')

                    pdf.cell(w=54, h=ch,
                             txt="",
                             border='0', ln=0, align='C')
                    pdf.cell(w=2, h=ch, txt='', border='0', ln=0, align='C')
                    pdf.cell(w=65, h=ch, txt="", border='0', ln=1)
                    a1.clear()
                    i = i + 1

                pdf.set_text_color(0, 0, 0)
                pdf.cell(w=0,h=12, txt="", ln=1)
                pdf.cell(w=0, h=12, txt="", ln=1)
                pdf.cell(w=30, h=16, txt="Signature: ", border=0, ln=0, align='L')
                x = pdf.get_x()
                y = pdf.get_y()
                pdf.line(x - 8, y + 9, x + 100, y + 9)
                pdf.cell(180)
                pdf.cell(w=30, h=16, txt="Date: ", border=0, ln=0, align='L')
                x = pdf.get_x()
                y = pdf.get_y()
                pdf.line(x - 18, y + 9, (x + 100), y + 9)
                file_name = str(patient.user_id)+"_"+patient.first_name+""+patient.last_name+"_ciq_report.pdf"
                filepath = os.path.join(BASE_DIR, 'media')
                pdf.output(filepath+"/"+file_name, 'F')

                return FileResponse(open(filepath+"/"+file_name, 'rb'), as_attachment=True, content_type='application/pdf')

            if pre_exists == True and post_exists == True:
                i = 1
                for item in questions:
                    if i == 9:
                       pdf.add_page()

                       pdf.set_font('Arial', 'B', 14)
                       pdf.set_text_color(0, 0, 0)
                       pdf.cell(w=20, h=10, txt='S.NO', border='L,T,0,B', ln=0, align='C', fill=True)
                       pdf.cell(w=220, h=10, txt='PRE QUESTIONS', border='0,T,0,B', ln=0, align='C', fill=True)
                       pdf.cell(w=220, h=10, txt='POST QUESTIONS', border='0,T,0,B', ln=0, align='C', fill=True)
                       pdf.cell(w=65, h=10, txt='RESULT', border='0,T,R,B', ln=1, align='C', fill=True)
                    a1 = []
                    pdf.set_font('Arial', 'B', 12)
                    pdf.set_text_color(0, 0, 0)
                    q_length = len(str(item.name))
                    if q_length > 108:
                        pdf.cell(w=20, h=16,
                                 txt="Q-"+str(i),
                                 border='L,0,T,0', ln=0, align='C')
                    else:
                        pdf.cell(w=20, h=ch,
                                 txt="Q-" + str(i),
                                 border='L,0,T,0', ln=0, align='C')
                    x = pdf.get_x()
                    y = pdf.get_y()

                    pdf.set_text_color(0, 0, 0)
                    if q_length > 108:
                        pdf.cell(w=2, h=16, txt='', border='L,T,0,0', ln=0, align='C')
                    else:
                        pdf.cell(w=2, h=ch, txt='', border='L,T,0,0', ln=0, align='C')
                    pdf.multi_cell(w=216, h=ch,
                                   txt=item.name,
                                   border='0,0,T,0', align='L')

                    x1 = pdf.get_x()
                    y1 = pdf.get_y()


                    #pdf.line(x1, y,x1,y1)
                    pdf.set_xy(x + 220, y)
                    if q_length > 108:
                        pdf.cell(w=2, h=16, txt='', border='L,T,0,0', ln=0, align='C')
                    else:
                        pdf.cell(w=2, h=ch, txt='', border='L,T,0,0', ln=0, align='C')
                    pdf.multi_cell(w=216, h=ch,
                                       txt=item.name,
                                       border='0,T,0,0', align='L')

                    a = float(pdf.get_y())
                    pdf.set_xy(x + 440, y)
                    if preresult[i] == postresult[i]:
                        pdf.set_font('Arial', 'B', 14)
                        pdf.cell(w=65, h=ch, txt="Unchanged", border='L,T,R,0', ln=1, align='C')
                    if preresult[i] > postresult[i]:
                        pdf.set_font('Arial', 'B', 14)
                        pdf.cell(w=65, h=ch, txt="Improved", border='L,T,R,0', ln=1, align='C')
                    if preresult[i] < postresult[i]:
                        pdf.set_font('Arial', 'B', 14)
                        pdf.cell(w=65, h=ch, txt="Worsened", border='L,T,R,0', ln=1, align='C')

                    b = float(pdf.get_y())
                    if b < a:
                        y = pdf.get_y()
                        pdf.set_xy(470, y)
                        pdf.cell(w=65, h=ch, txt="", border='L,0,R,0', ln=1)

                    option = Options_new.objects.filter(question_new_id=item.id).all()

                    for opt in option:
                        a1.append(opt.name)

                    x = pdf.get_x()
                    y = pdf.get_y()
                    pdf.set_font('Arial', 'B', 12)
                    pdf.cell(w=20, h=ch,
                             txt="",
                             border='L,0,0,B', ln=0, align='C')
                    pdf.cell(w=2, h=ch, txt='', border='L,0,0,B', ln=0, align='C')
                    if preoption[i][0] == prelist[i]:
                        pdf.set_font('Arial', 'B', 12)
                        a = "(X)"
                    else:
                        pdf.set_font('Arial', 'B', 12)
                        pdf.set_text_color(0, 0, 0)
                        a =""
                    pdf.cell(w=54, h=ch,
                             txt=a+" 0 - " + a1[0],
                             border='0,0,0,B', ln=0, align='C')
                    if preoption[i][1] == prelist[i]:
                        pdf.set_font('Arial', 'B', 12)
                        a = "(X)"
                    else:
                        pdf.set_font('Arial', 'B', 12)
                        pdf.set_text_color(0, 0, 0)
                        a = ""
                    pdf.cell(w=54, h=ch,
                             txt=a+" 1 - " + a1[1],
                             border='0,0,0,B', ln=0, align='C')
                    if preoption[i][2] == prelist[i]:
                        pdf.set_font('Arial', 'B', 12)
                        a = "(X)"
                    else:
                        pdf.set_font('Arial', 'B', 12)
                        pdf.set_text_color(0, 0, 0)
                        a = ""
                    pdf.cell(w=54, h=ch,
                             txt=a+" 2 - " + a1[2],
                             border='0,0,0,B', ln=0, align='C')
                    if preoption[i][3] == prelist[i]:
                        pdf.set_font('Arial', 'B', 12)
                        a = "(X)"
                    else:
                        pdf.set_font('Arial', 'B', 12)
                        pdf.set_text_color(0, 0, 0)
                        a = ""
                    pdf.cell(w=54, h=ch,
                             txt=a+" 3 - " + a1[3],
                             border='0,0,0,B', ln=0, align='C')
                    pdf.cell(w=2, h=ch, txt='', border='0,0,R,B', ln=0, align='C')

                    if postoption[i][0] == postlist[i]:
                        pdf.set_font('Arial', 'B', 12)
                        a = "(X)"
                    else:
                        pdf.set_font('Arial', 'B', 12)
                        pdf.set_text_color(0, 0, 0)
                        a = ""
                    pdf.cell(w=2, h=ch, txt='', border='0,0,0,B', ln=0, align='C')
                    pdf.cell(w=54, h=ch,
                             txt=a+" 0 - " + a1[0],
                             border='0,0,0,B', ln=0, align='C')
                    if postoption[i][1] ==  postlist[i]:
                        pdf.set_font('Arial', 'B', 12)
                        a = "(X)"
                    else:
                        pdf.set_font('Arial', 'B', 12)
                        pdf.set_text_color(0, 0, 0)
                        a = ""
                    pdf.cell(w=54, h=ch,
                             txt=a+" 1 - " + a1[1],
                             border='0,0,0,B', ln=0, align='C')
                    if postoption[i][2] ==  postlist[i]:
                        pdf.set_font('Arial', 'B', 12)
                        a = "(X)"
                    else:
                        pdf.set_font('Arial', 'B', 12)
                        pdf.set_text_color(0, 0, 0)
                        a = ""
                    pdf.cell(w=54, h=ch,
                             txt=a+" 2 - " + a1[2],
                             border='0,0,0,B', ln=0, align='C')
                    if postoption[i][3] ==  postlist[i]:
                        pdf.set_font('Arial', 'B', 12)
                        a = "(X)"
                    else:
                        pdf.set_font('Arial', 'B', 12)
                        pdf.set_text_color(0, 0, 0)
                        a = ""
                    pdf.cell(w=54, h=ch,
                             txt=a+" 3 - " + a1[3],
                             border='0,0,0,B', ln=0, align='C')
                    pdf.cell(w=2, h=ch, txt='', border='0,0,R,B', ln=0, align='C')
                    pdf.cell(w=65, h=ch, txt="", border='0,0,R,B', ln=1)
                    a1.clear()
                    i = i + 1

                pdf.set_text_color(0, 0, 0)
                pdf.cell(w=0, h=12, txt="", ln=1)
                pdf.cell(w=0, h=12, txt="", ln=1)
                pdf.cell(w=30, h=16, txt="Signature: ", border=0, ln=0, align='L')
                x = pdf.get_x()
                y = pdf.get_y()
                pdf.line(x - 8, y + 9, x + 100, y + 9)
                pdf.cell(180)
                pdf.cell(w=30, h=16, txt="Date: ", border=0, ln=0, align='L')
                x = pdf.get_x()
                y = pdf.get_y()
                pdf.line(x - 18, y + 9, (x + 100), y + 9)
                file_name = str(patient.user_id) + "_" + patient.first_name + "" + patient.last_name + "_ciq_report.pdf"
                filepath = os.path.join(BASE_DIR, 'media')
                pdf.output(filepath + "/" + file_name, 'F')



                return FileResponse(open(filepath + "/" + file_name, 'rb'), as_attachment=True,
                                    content_type='application/pdf')

        else:
            return redirect('/')
    except Exception as e:
        print(e)
        return redirect('/')

@api_view(['POST'])
@permission_classes((AllowAny,))
def save_question(request):
    serializer = SaveQuestionSerializer(data=request.data)
    if serializer.is_valid():
        question = serializer.save()
        options_data = request.data.get('options', [])
        for option_data in options_data:
            option_data['question_new'] = question.id
            option_serializer = OptionsSerializer(data=option_data)
            if option_serializer.is_valid():
                option_serializer.save()
            else:
                return Response(option_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        return Response("operation successfull", status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

def add_question(request):
    notify = Provider.objects.filter(subscription_status='Pending').count()
    n_notify = Provider_Verification.objects.filter(user_position=3).count()
    context = {
        'n_notify': n_notify,
        'notification': notify,
    }
    return render(request, "backend/add_question.html", context)
def ciq_report(request):
    try:
        if request.method == "POST":
            date1 = request.POST.get('date1')
            date2 = request.POST.get('date2')
            today = datetime.date.today()
            year = today.year
            preoption = [0]
            postoption = [0]
            preoptioncount = []
            postoptioncount = []
            pre_aggregate = []
            post_aggregate = []
            complete_question_lsit = []


            all_questions = Question_new.objects.filter(year=year)

            # get total number of patient

            k = UserAnswer.objects.filter(question__year=year, question__is_post=True,
                                          date__range=(date1, date2)).values("user_id").annotate(total=Count("user_id"))
            if len(k) == 0:
                messages.warning(request, "No recored found on the given dates.")
                return render(request, "backend/ciq_report.html",
                              context={'total_patient': "null"})
            user_id_list = []
            for index in range(len(k)):
                a_count = k[index]['total']
                if a_count == 15:
                    user_id_list.append(k[index]['user_id'])
            t_patients = len(user_id_list)

            for item in all_questions:
                qid = item.id
                a = []
                ocount = []
                ag = []
                pre_ag = []
                post_ag = []
                if item.is_pre is True:
                    option = Options_new.objects.filter(question_new_id=qid).all()
                    for i in option:
                        a.append(i.id)
                        count = UserAnswer.objects.filter(option_selected_id=i.id, question__year=year,
                                                          question__is_pre=True, date__range=(date1, date2),
                                                          user_id__in=user_id_list).count()
                        res = int(((count / t_patients) * 100))
                        ag.append(res)
                        ocount.append(count)
                    preoption.append(a)
                    preoptioncount.append(ocount)

                    # Calculate the sum of the values
                    total = sum(ag)


                    # If the sum is greater than 100, scale the values down
                    if total > 100:
                        factor = 100 / total
                        x = [int(v * factor) for v in ag]
                        for i in range(len(x)):
                            pre_ag.append(x[i])
                        pre_aggregate.append(pre_ag)
                    # If the sum is less than 100, scale the values up
                    if total < 100:
                        factor = 100 / total
                        y = [int(v * factor) for v in ag]
                        for i in range(len(y)):
                            pre_ag.append(y[i])
                        pre_aggregate.append(pre_ag)
                    if total == 100:
                        pre_aggregate.append(ag)

                else:

                    option = Options_new.objects.filter(question_new_id=qid).all()
                    for i in option:
                        a.append(i.id)
                        count = UserAnswer.objects.filter(option_selected_id=i.id, question__year=year,
                                                          question__is_post=True, date__range=(date1, date2),
                                                          user_id__in=user_id_list).count()
                        res = int(((count / t_patients) * 100))
                        ag.append(res)
                        ocount.append(count)

                    postoption.append(a)
                    postoptioncount.append(ocount)
                    total = sum(ag)

                    # If the sum is greater than 100, scale the values down

                    if total > 100:

                        factor = 100 / total
                        c = [int(v * factor) for v in ag]
                        for i in range(len(c)):
                            post_ag.append(c[i])
                        #c.clear()
                        post_aggregate.append(post_ag)

                    # If the sum is less than 100, scale the values up
                    if total < 100:
                        factor = 100 / total
                        b = [int(v * factor) for v in ag]
                        for i in range(len(b)):
                            post_ag.append(b[i])
                        post_aggregate.append(post_ag)
                    if total == 100:
                        post_aggregate.append(ag)


            fi = []
            fw = []
            fu = []

            for i in range(len(pre_aggregate)):
                j = 0
                w_list = []
                i_list = []
                u_list = []
                value = 0

                for x in range(4):
                    if x == 0:

                        if pre_aggregate[i][j] == post_aggregate[i][j] and post_aggregate[i][j] != 0:
                            u_list.append(pre_aggregate[i][j])
                            value += pre_aggregate[i][j]
                            if value > 99:
                                break
                        if pre_aggregate[i][j] > post_aggregate[i][j] and post_aggregate[i][j] != 0:
                            pre = (pre_aggregate[i][j])
                            post = (post_aggregate[i][j])
                            result = pre - post
                            if value < 99:
                                if (value + post) <= 100.1:
                                    value += post
                                    u_list.append(post)
                                if value < 99:
                                    if (value + result) <= 100.1:
                                        value += result
                                        w_list.append(result)
                                if value > 99:
                                    break
                            else:
                                break
                        if pre_aggregate[i][j] > post_aggregate[i][j] and post_aggregate[i][j] == 0:
                            pre = (pre_aggregate[i][j])
                            post = (post_aggregate[i][j])
                            result = pre - post
                            if value < 99:
                                if (value + post) <= 100.1:
                                    value += post
                                    u_list.append(post)
                                if value < 99:
                                    if (value + result) <= 100.1:
                                        value += result
                                        w_list.append(result)
                                if value > 99:
                                    break
                            else:
                                break
                        if pre_aggregate[i][j] < post_aggregate[i][j]:
                            pre = (pre_aggregate[i][j])
                            post = (post_aggregate[i][j])
                            result = post - pre

                            if value < 99:
                                if (value + pre) <= 100.1:
                                    value += pre
                                    u_list.append(pre)
                                if value < 99:
                                    if (value + result) <= 100.1:
                                        value += result
                                        i_list.append(result)
                                if value > 99:
                                    break
                            else:
                                break
                    if x == 1:

                        if pre_aggregate[i][j] == post_aggregate[i][j] and post_aggregate[i][j] != 0:
                            u_list.append(pre_aggregate[i][j])
                            value += pre_aggregate[i][j]
                            if value > 99:
                                break
                        if pre_aggregate[i][j] > post_aggregate[i][j] and post_aggregate[i][j] != 0:
                            pre = (pre_aggregate[i][j])
                            post = (post_aggregate[i][j])
                            result = pre - post

                            if value < 99:
                                if (value + post) <= 100.1:
                                    value += post
                                    u_list.append(post)
                                if value < 99:
                                    if (value + result) <= 100.1:
                                        value += result
                                        w_list.append(result)
                                if value > 99:
                                    break
                            else:
                                break
                        if pre_aggregate[i][j] < post_aggregate[i][j]:
                            pre = (pre_aggregate[i][j])
                            post = (post_aggregate[i][j])
                            result = post - pre

                            if value < 99:
                                if (value + pre) <= 100.1:
                                    value += pre
                                    u_list.append(pre)
                                if value < 99:
                                    if (value + result) <= 100.1:
                                        value += result
                                        i_list.append(result)
                                if value > 99:
                                    break
                            else:
                                break

                    if x == 2:

                        if pre_aggregate[i][j] == post_aggregate[i][j] and post_aggregate[i][j] != 0:
                            u_list.append(pre_aggregate[i][j])
                            value += pre_aggregate[i][j]
                            if value > 99:
                                break
                        if pre_aggregate[i][j] > post_aggregate[i][j] and post_aggregate[i][j] != 0:
                            pre = (pre_aggregate[i][j])
                            post = (post_aggregate[i][j])
                            result = pre - post

                            if value < 99:
                                if (value + post) <= 100.1:
                                    value += post
                                    u_list.append(post)
                                if value < 99:
                                    if (value + result) <= 100.1:
                                        value += result
                                        #w_list.append(result)
                                        i_list.append(result)
                                if (value + post) > 100:
                                    if post_aggregate[i][3] == 0:
                                        result = 100 - value
                                        u_list.append(result)
                                    else:
                                        break
                            else:
                                break
                        if pre_aggregate[i][j] < post_aggregate[i][j]:
                            pre = (pre_aggregate[i][j])
                            post = (post_aggregate[i][j])
                            result = post - pre

                            if value < 99:
                                if (value + pre) <= 100.1:
                                    value += pre
                                    u_list.append(pre)
                                if value < 99:
                                    if (value + result) <= 100.1:
                                        value += result
                                        #i_list.append(result)
                                        if pre_aggregate[i][3] > 0 and post_aggregate[i][3] > 0:
                                            i_list.append(result)
                                        if pre_aggregate[i][3] == 0 and post_aggregate[i][3] > 0:
                                            i_list.append(result)
                                        if pre_aggregate[i][3] > 0 and post_aggregate[i][3] == 0:
                                            i_list.append(result)
                                        if pre_aggregate[i][3] == 0 and post_aggregate[i][3] == 0:
                                            w_list.append(result)
                                if value > 99:
                                    break
                            else:
                                break

                    if x == 3:

                        if pre_aggregate[i][j] == post_aggregate[i][j] and post_aggregate[i][j] != 0:
                            u_list.append(pre_aggregate[i][j])
                            value += pre_aggregate[i][j]
                            if value > 99:
                                break
                        if pre_aggregate[i][j] > post_aggregate[i][j] and post_aggregate[i][j] != 0:
                            pre = (pre_aggregate[i][j])
                            post = (post_aggregate[i][j])
                            result = pre - post

                            if value < 99:
                                if (value + post) <= 100.1:
                                    value += post
                                    u_list.append(post)
                                if value < 99:
                                    if (value + result) <= 100.1:
                                        value += result
                                        i_list.append(result)
                                if value > 99:
                                    break
                            else:
                                break
                        if pre_aggregate[i][j] < post_aggregate[i][j]:
                            pre = (pre_aggregate[i][j])
                            post = (post_aggregate[i][j])
                            result = post - pre

                            if value < 99:
                                if (value + pre) <= 100.1:
                                    value += pre
                                    u_list.append(pre)
                                if value < 99:
                                    if (value + result) <= 100.1:
                                        value += result
                                        w_list.append(result)
                                if value > 99:
                                    break
                            else:
                                break

                    # if pre_aggregate[i][j] == post_aggregate[i][j]:
                    #     u_list.append(int(pre_aggregate[i][j]))
                    #
                    # if pre_aggregate[i][j] > post_aggregate[i][j]:
                    #     if post_aggregate[i][j] > 0:
                    #         pre = int(pre_aggregate[i][j])
                    #         post = int(post_aggregate[i][j])
                    #         result = pre - post
                    #         # u_list.append(result)
                    #         u_list.append(post)
                    #     if post_aggregate[i][j] == 0:
                    #         pass
                    #
                    # if pre_aggregate[i][j] < post_aggregate[i][j]:
                    #     if pre_aggregate[i][j] == 0 and x != 0:
                    #         w_list.append(int(post_aggregate[i][j]))
                    #     if pre_aggregate[i][j] == 0 and x == 0:
                    #         i_list.append(int(post_aggregate[i][j]))
                    #     if pre_aggregate[i][j] > 0 and post_aggregate[i][j] < 100 and x == 0:
                    #         # i_list.append(post_aggregate[i][j])
                    #         pre = int(pre_aggregate[i][j])
                    #         post = int(post_aggregate[i][j])
                    #         res = post - pre
                    #         i_list.append(res)
                    #         u_list.append(pre)
                    #     if pre_aggregate[i][j] > 0 and post_aggregate[i][j] < 100 and x != 0:
                    #         pre = int(pre_aggregate[i][j])
                    #         post = int(post_aggregate[i][j])
                    #         result = post - pre
                    #         w_list.append(result)
                    #         u_list.append(pre)
                    #     if pre_aggregate[i][j] > 0 and pre_aggregate[i][j] < 100 and post_aggregate[i][j] == 100:
                    #         if x == 0:
                    #             pre = int(pre_aggregate[i][j])
                    #             post = int(post_aggregate[i][j])
                    #             result = post - pre
                    #             i_list.append(result)
                    #             u_list.append(pre)
                    #         else:
                    #             pre = int(pre_aggregate[i][j])
                    #             post = int(post_aggregate[i][j])
                    #             result = post - pre
                    #             w_list.append(result)
                    #             u_list.append(pre)
                    j += 1

                fi.append(i_list)
                fw.append(w_list)
                fu.append(u_list)

            final_fi = []
            final_fw = []
            final_fu = []


            for i in range(len(fi)):
                a = int((sum(fi[i])))
                final_fi.append(a)
            for i in range(len(fw)):
                a = int((sum(fw[i])))
                final_fw.append(a)
            for i in range(len(fu)):
                a = int((sum(fu[i])))
                final_fu.append(a)

            x = 0
            j = 0
            for item in all_questions:
                d = {}
                qid = item.id

                if item.is_pre is True:
                    d['question'] = item.name
                    option = Options_new.objects.filter(question_new_id=qid).all()
                    k = 1
                    for i in option:
                        name = "option" + str(k)
                        d[name] = i.name
                        k += 1
                    d['o1'] = pre_aggregate[j][0]
                    d['o2'] = pre_aggregate[j][1]
                    d['o3'] = pre_aggregate[j][2]
                    d['o4'] = pre_aggregate[j][3]
                    d['o5'] = post_aggregate[j][0]
                    d['o6'] = post_aggregate[j][1]
                    d['o7'] = post_aggregate[j][2]
                    d['o8'] = post_aggregate[j][3]
                    values = [final_fi[x], final_fw[x], final_fu[x]]

                    # Calculate the sum of the values
                    total = sum(values)

                    # If the sum is greater than 100, scale the values down
                    if total > 100:
                        factor = 100 / total
                        values = [int(v * factor) for v in values]

                    # If the sum is less than 100, scale the values up
                    elif total < 100:
                        factor = 100 / total
                        values = [int(v * factor) for v in values]

                    # Print the adjusted values
                    #print(values)
                    # d['improve'] = final_fi[x]
                    # d['worsened'] = final_fw[x]
                    # d['unchanged'] = final_fu[x]
                    d['improve'] = values[0]
                    d['worsened'] = values[1]
                    d['unchanged'] = values[2]

                    x += 1
                    j += 1
                    complete_question_lsit.append(d)
            notify = Provider.objects.filter(subscription_status='Pending').count()
            n_notify = Provider_Verification.objects.filter(user_position=3).count()
            return render(request, "backend/ciq_report.html",
                          context={'n_notify': n_notify,'notification': notify,'total_patient': t_patients, 'mydic': complete_question_lsit, 'pre': pre_aggregate,
                                   'post': post_aggregate, 'date1': date1, 'date2': date2, })
        else:
            notify = Provider.objects.filter(subscription_status='Pending').count()
            n_notify = Provider_Verification.objects.filter(user_position=3).count()
            return render(request, "backend/ciq_report.html",
                          context={'n_notify': n_notify,'notification': notify,'total_patient': "null"})
    except Exception as e:
        print(e)
        return redirect('/')


@login_required
def ciq_report_by_provider(request, pid=None):
    try:
        if pid is not None:
            today = datetime.date.today()
            year = today.year
            prelist = [0]
            postlist = [0]
            preoption = [0]
            postoption = [0]
            preresult = [0]
            postresult = [0]
            final_lsit = []
            all_questions = Question_new.objects.filter( year = year)
            pre_exists = UserAnswer.objects.filter(user_id=pid, question__is_pre=True, question__year=year).exists()
            post_exists  = UserAnswer.objects.filter(user_id=pid, question__is_post=True, question__year=year).exists()
            user_answer_post = UserAnswer.objects.filter(user_id=pid, question__is_post=True, question__year=year)
            user_answer_pre = UserAnswer.objects.filter(user_id=pid, question__is_pre=True, question__year=year)
            post = False
            for item in user_answer_pre:
                date1 = (item.date)
                date1 = date1.strftime('%m-%d-%Y')
                break
            for item in user_answer_post:
                date2 = (item.date)
                date2 = date2.strftime('%m-%d-%Y')
                break
            if pre_exists == True and post_exists == True:
                post = True

                patient = RefPatient.objects.get(user_id=pid)
                patient_name = patient.first_name +" "+ patient.last_name
                provider_id = patient.provider_id
                provider_id = str(provider_id[12:])
                provider = Provider.objects.get(user_id = provider_id)
                provider_name = provider.first_name +" "+ provider.last_name

                for item in all_questions:
                    d = {}
                    qid = item.id
                    a = []
                    if item.is_pre is True:
                        d['question'] = item.name
                        option = Options_new.objects.filter(question_new_id=qid).all()
                        k = 1
                        for i in option:
                            a. append(i.id)
                            name = "option" + str(k)
                            d[name] = i.name
                            k += 1

                        preoption.append(a)
                        final_lsit.append(d)
                    else:
                        option = Options_new.objects.filter(question_new_id=qid).all()
                        for i in option:
                            a.append(i.id)

                        postoption.append(a)
                pre_l = []
                post_l = []
                for item in user_answer_pre:
                    prelist.append(item.option_selected_id)
                    res = Options_new.objects.filter(question_new_id=item.question_id).all()
                    j = 1
                    for i in res:
                        d = {}
                        if i.id == item.option_selected_id:
                            preresult.append(j)
                            d['select'] = j
                            pre_l.append(d)
                            break
                        else:
                            j += 1
                for item in user_answer_post:
                    postlist.append(item.option_selected_id)
                    res = Options_new.objects.filter(question_new_id=item.question_id).all()
                    j = 1
                    for i in res:
                        d = {}
                        if i.id == item.option_selected_id:
                            postresult.append(j)
                            d['select'] = j
                            post_l.append(d)
                            break
                        else:
                            j += 1
                result_list = []
                i = 1

                for j in range(15):
                    d = {}
                    if preresult[i] == postresult[i]:
                        d['result'] = "Unchanged"
                        result_list.append(d)
                        i += 1
                        continue
                    if preresult[i] > postresult[i]:
                        d['result'] = "Improved"
                        result_list.append(d)
                        i += 1
                        continue
                    if preresult[i] < postresult[i]:
                        d['result'] = "Worsened"
                        result_list.append(d)
                        i += 1
                        continue

                zipped = zip(final_lsit,result_list,pre_l,post_l)
                return render(request, "ciq_report_by_provider.html", context={'zipped':zipped,'date1':date1,'date2':date2,'patient_name':patient_name,'provider_name':provider_name, 'post':post})
            if pre_exists == True and post_exists == False:
                patient = RefPatient.objects.get(user_id=pid)
                patient_name = patient.first_name + " " + patient.last_name
                provider_id = patient.provider_id
                provider_id = str(provider_id[12:])
                provider = Provider.objects.get(user_id=provider_id)
                provider_name = provider.first_name + " " + provider.last_name

                for item in all_questions:
                    d = {}
                    qid = item.id
                    a = []
                    if item.is_pre is True:
                        d['question'] = item.name
                        option = Options_new.objects.filter(question_new_id=qid).all()
                        k = 1
                        for i in option:
                            a.append(i.id)
                            name = "option" + str(k)
                            d[name] = i.name
                            k += 1

                        preoption.append(a)
                        final_lsit.append(d)

                pre_l = []

                for item in user_answer_pre:
                    prelist.append(item.option_selected_id)
                    res = Options_new.objects.filter(question_new_id=item.question_id).all()
                    j = 1
                    for i in res:
                        d = {}
                        if i.id == item.option_selected_id:
                            preresult.append(j)
                            d['select'] = j
                            pre_l.append(d)
                            break
                        else:
                            j += 1


                zipped = zip(final_lsit, pre_l)
                return render(request, "ciq_report_by_provider.html",
                              context={'zipped': zipped, 'date1': date1, 'patient_name': patient_name,
                                       'provider_name': provider_name, 'post': post})

        else:
            return redirect('/')
    except Exception as e:
        print(e)
        return redirect('/')

#+18007888395

# def send_fax_ciq(request,pid):
#     try:
#         if pid != None:
#             url = 'https://api2.westfax.com/REST/Fax_SendFax/JSON'
#             payload = {'Username': 'wm@thqcompany.com',
#                        'Password': 'PaperRockeDeliveryToDoc1990',
#                        'Cookies': 'false',
#                        'ProductId': '666fa154-2c59-4be0-8585-48d5e73e0afc',
#                        #'JobName': 'Patient Results',
#                         'BillingCode': 'Patient',
#                         #'Numbers1': '+18007888395',
#                         'Numbers1': '+18007888395',
#                         'ANI': '8885090282',
#                         'FaxQuality': 'Fine'}
#
#             files = {'Files0': open('/home/humayun/Downloads/786_OOOOO_ciq_report (1).pdf', 'rb')}
#             headers = {
#                 'ContentType': 'multipart/form-data'
#             }
#             response = requests.request('POST', url, headers=headers, data=payload, files=files, allow_redirects=False ,verify=False)
#             print(response.text)
#     except Exception as e:
#         print(e)
#         return redirect('/')
def send_fax_directly_ciq(filename,pid):
    try:
        if filename != None and pid != None:
            patient = RefPatient.objects.get(user_id=pid)
            provider_id = patient.provider_id
            provider_id = str(provider_id[12:])
            print(provider_id)
            provider = Provider.objects.get(user_id=provider_id)
            provider_fax_number = provider.fax_no
            print(provider_fax_number)
            url = 'https://api2.westfax.com/REST/Fax_SendFax/JSON'
            payload = {'Username': 'wm@thqcompany.com',
                       'Password': 'PaperRockeDeliveryToDoc1990',
                       'Cookies': 'false',
                       'ProductId': '666fa154-2c59-4be0-8585-48d5e73e0afc',
                       #'JobName': 'Patient Weekly Result',
                        #'Header': 'Results for XYZ',
                        'BillingCode': 'Patient',
                        'Numbers1': provider_fax_number,
                        'CSID': '(888) 509-0282',
                        'ANI': '8885090282',
                        #'StartDate': '27/04/2023',
                        'FaxQuality': 'Fine'}


            filepath = os.path.join(BASE_DIR, 'media')
            send_file_name = filepath+"/"+filename,
            print(send_file_name)
            files = {'Files0': open(os.path.join(BASE_DIR, 'media'+'/'+filename), 'rb')}
            headers = {
                'ContentType': 'multipart/form-data'
            }
            response = requests.request('POST', url, headers=headers, data=payload, files=files, allow_redirects=False ,verify=False)
            if response.status_code == 200:
                # HTTP status code 200 typically indicates a successful request.
                response_data = response.json()  # Assuming the API returns JSON data.

                # Check if the response contains a success indicator (adjust as per API documentation).
                if response_data.get('success'):
                    return ("success")
                else:
                    return ("failed")
            else:
                # Handle HTTP error codes if the request was not successful.
                return ("failed")
    except Exception as e:
        print(e)
        return redirect('/')


ch = 8
def create_ciq_report_directly(pid=None):
    try:
        print("CIQ REPORT DIRECTLY",pid)
        if pid is not None:
            print("YES HERE")
            today = datetime.date.today()
            year = today.year
            today = today.strftime('%m-%d-%Y')
            prelist = [0]
            postlist = [0]
            preoption = [0]
            postoption = [0]
            preresult = [0]
            postresult = [0]

            questions = Question_new.objects.filter(is_pre=True, year = year)
            print("1")
            all_questions = Question_new.objects.filter( year = year)
            pre_exists = UserAnswer.objects.filter(user_id=pid, question__is_pre=True, question__year=year).exists()
            post_exists  = UserAnswer.objects.filter(user_id=pid, question__is_post=True, question__year=year).exists()

            if pre_exists == True:
                print("yes pre true")
                user_answer_pre = UserAnswer.objects.filter(user_id=pid, question__is_pre=True, question__year=year)
                print(user_answer_pre)
                for item in user_answer_pre:
                    date1 = (item.date)
                    date1 = date1.strftime('%m-%d-%Y')
                    print("2")
                    break
                for item in user_answer_pre:
                    prelist.append(item.option_selected_id)
                    res = Options_new.objects.filter(question_new_id=item.question_id).all()
                    j = 1
                    for i in res:
                        if i.id == item.option_selected_id:
                            preresult.append(j)
                            break
                        else:
                            j += 1
            if post_exists == True:
                print("yes post true")
                user_answer_post = UserAnswer.objects.filter(user_id=pid, question__is_post=True, question__year=year)
                print(user_answer_post)
                for item in user_answer_post:
                    date2 = (item.date)
                    date2 = date2.strftime('%m-%d-%Y')
                    print("3")
                    break
                for item in user_answer_post:
                    postlist.append(item.option_selected_id)
                    res = Options_new.objects.filter(question_new_id=item.question_id).all()
                    j = 1
                    for i in res:
                        if i.id == item.option_selected_id:
                            postresult.append(j)
                            break
                        else:
                            j += 1
            patient = RefPatient.objects.get(user_id=pid)
            patient_name = patient.first_name+" "+patient.last_name
            provider_id = patient.provider_id
            provider_id = str(provider_id[12:])
            provider = Provider.objects.get(user_id = provider_id)
            provider_name = provider.first_name +" "+ provider.last_name

            for item in all_questions:
                qid = item.id
                a = []
                if item.is_pre is True:
                    option = Options_new.objects.filter(question_new_id=qid).all()
                    for i in option:
                        a. append(i.id)
                    preoption.append(a)
                else:
                    option = Options_new.objects.filter(question_new_id=qid).all()
                    for i in option:
                        a.append(i.id)

                    postoption.append(a)



            class PDF(FPDF):
                def header(self):
                    # Position at 1.5 cm from bottom
                    filepath = os.path.join(BASE_DIR, 'static/assets/images/logo-1.png')
                    self.image(filepath, 10, 10, 100);
                    self.set_font('Arial', 'B', 15);
                    self.cell(125);
                    self.cell(40, 25,"| Patient: "+patient_name, 0, 0, 'C');
                    self.cell(45);
                    self.cell(40, 25, "| Provider: " + provider_name, 0, 0, 'C');
                    self.cell(45);
                    print("4")
                    self.cell(40, 25, "| Pre Test Date: " + date1, 0, 0, 'C');
                    self.cell(45);
                    if post_exists == True:
                        self.cell(40, 25, "| Post Test Date: " + date2, 0, 0, 'C');
                    else:
                        self.cell(40, 25, "| Post Test Date: ", 0, 0, 'C');
                    print("5")
                    self.cell(45);
                    self.cell(40, 25, "| Generated On: " + today, 0, 0, 'C');
                    self.ln(30);
                    pdf.set_line_width(0.5)


                # Page footer
                def footer(self):
                    # Position at 1.5 cm from bottom
                    self.set_y(-15)
                    # Arial italic 8
                    self.set_font('Arial', 'I', 14)
                    # Page number
                    self.cell(0, 10, 'Page ' + str(self.page_no()) + '/{nb}', 0, 0, 'C')

            pdf = PDF(orientation='L', unit='mm', format=(300, 550))
            pdf.alias_nb_pages()
            pdf.add_page()

            pdf.set_font('Arial', 'B', 18)
            pdf.cell(w=525, h=ch, txt=" CIQ REPORT", border=0, ln=1, align='C')
            pdf.ln()

            pdf.set_font('Arial', 'B', 14)
            pdf.set_fill_color(255, 255, 255)


            pdf.set_text_color(0,0,0)
            pdf.cell(w=20, h=10, txt='S.NO', border='L,T,0,B', ln=0, align='C', fill=True)
            pdf.cell(w=220, h=10, txt='PRE QUESTIONS', border='0,T,0,B', ln=0, align='C', fill=True)
            pdf.cell(w=220, h=10, txt='POST QUESTIONS', border='0,T,0,B', ln=0, align='C', fill=True)
            pdf.cell(w=65, h=10, txt='RESULT', border='0,T,R,B', ln=1, align='C', fill=True)
            pdf.set_font('Arial', 'B', 13)
            if pre_exists == True and post_exists == False:
                print("1")
                i = 1
                for item in questions:
                    if i == 9:
                        pdf.add_page()
                        pdf.set_font('Arial', 'B', 14)
                        pdf.set_text_color(0, 0, 0)
                        pdf.cell(w=20, h=10, txt='S.NO', border='L,T,0,B', ln=0, align='C', fill=True)
                        pdf.cell(w=220, h=10, txt='PRE QUESTIONS', border='0,T,0,B', ln=0, align='C', fill=True)
                        pdf.cell(w=220, h=10, txt='POST QUESTIONS', border='0,T,0,B', ln=0, align='C', fill=True)
                        pdf.cell(w=65, h=10, txt='RESULT', border='0,T,R,B', ln=1, align='C', fill=True)

                    a1 = []
                    pdf.set_font('Arial', 'B', 12)
                    pdf.set_text_color(0, 0, 0)
                    q_length = len(str(item.name))
                    if q_length > 108:
                        pdf.cell(w=20, h=16,
                                 txt="Q-" + str(i),
                                 border='L,0,T,0', ln=0, align='C')
                    else:
                        pdf.cell(w=20, h=ch,
                                 txt="Q-" + str(i),
                                 border='L,0,T,0', ln=0, align='C')
                    x = pdf.get_x()
                    y = pdf.get_y()

                    pdf.set_text_color(0, 0, 0)
                    if q_length > 108:
                        pdf.cell(w=2, h=16, txt='', border='L,T,0,0', ln=0, align='C')
                    else:
                        pdf.cell(w=2, h=ch, txt='', border='L,T,0,0', ln=0, align='C')
                    pdf.multi_cell(w=216, h=ch,
                                   txt=item.name,
                                   border='0,0,T,0', align='L')
                    x1 = pdf.get_x()
                    y1 = pdf.get_y()
                    pdf.set_xy(x + 220, y)
                    if q_length > 108:
                        pdf.cell(w=2, h=16, txt='', border='L,0,0,0', ln=0, align='C')
                    else:
                        pdf.cell(w=2, h=ch, txt='', border='L,0,0,0', ln=0, align='C')
                    if i == 5 or i == 12:
                        pdf.multi_cell(w=216, h=ch,
                                       txt="Post Results will appear after the post questions submission.",
                                       border='0,0,0,0', align='C')
                    else:
                        pdf.multi_cell(w=216, h=ch,
                                       txt="",
                                       border='0,0,0,0', align='L')

                    a = float(pdf.get_y())
                    pdf.set_xy(x + 440, y)
                    pdf.set_font('Arial', 'B', 12)
                    if q_length > 108:
                        pdf.cell(w=65, h=16, txt=" ", border='0', ln=1, align='C')
                    else:
                        pdf.cell(w=65, h=ch, txt=" ", border='0', ln=1, align='C')

                    b = float(pdf.get_y())
                    if b < a:
                        y = pdf.get_y()
                        pdf.set_xy(470, y)
                        pdf.cell(w=65, h=ch, txt="", border='0', ln=1)

                    option = Options_new.objects.filter(question_new_id=item.id).all()

                    for opt in option:
                        a1.append(opt.name)

                    x = pdf.get_x()
                    y = pdf.get_y()
                    pdf.set_font('Arial', 'B', 12)
                    pdf.cell(w=20, h=ch,
                             txt="",
                             border='L,0,0,B', ln=0, align='C')
                    pdf.cell(w=2, h=ch, txt='', border='L,0,0,B', ln=0, align='C')
                    if preoption[i][0] == prelist[i]:
                        pdf.set_font('Arial', 'B', 12)
                        a = "(X)"
                    else:
                        pdf.set_font('Arial', 'B', 12)
                        pdf.set_text_color(0, 0, 0)
                        a = ""
                    pdf.cell(w=54, h=ch,
                             txt=a + " 0 - " + a1[0],
                             border='0,0,0,B', ln=0, align='C')
                    if preoption[i][1] == prelist[i]:
                        pdf.set_font('Arial', 'B', 12)
                        a = "(X)"
                    else:
                        pdf.set_font('Arial', 'B', 12)
                        pdf.set_text_color(0, 0, 0)
                        a = ""
                    pdf.cell(w=54, h=ch,
                             txt=a + " 1 - " + a1[1],
                             border='0,0,0,B', ln=0, align='C')
                    if preoption[i][2] == prelist[i]:
                        pdf.set_font('Arial', 'B', 12)
                        a = "(X)"
                    else:
                        pdf.set_font('Arial', 'B', 12)
                        pdf.set_text_color(0, 0, 0)
                        a = ""
                    pdf.cell(w=54, h=ch,
                             txt=a + " 2 - " + a1[2],
                             border='0,0,0,B', ln=0, align='C')
                    if preoption[i][3] == prelist[i]:
                        pdf.set_font('Arial', 'B', 12)
                        a = "(X)"
                    else:
                        pdf.set_font('Arial', 'B', 12)
                        pdf.set_text_color(0, 0, 0)
                        a = ""
                    pdf.cell(w=54, h=ch,
                             txt=a + " 3 - " + a1[3],
                             border='0,0,0,B', ln=0, align='C')
                    pdf.cell(w=2, h=ch, txt='', border='0,0,R,B', ln=0, align='C')


                    pdf.set_font('Arial', 'B', 12)

                    pdf.cell(w=2, h=ch, txt='', border='0', ln=0, align='C')
                    pdf.cell(w=54, h=ch,
                             txt="",
                             border='0', ln=0, align='C')

                    pdf.cell(w=54, h=ch,
                             txt="",
                             border='0', ln=0, align='C')

                    pdf.cell(w=54, h=ch,
                             txt="",
                             border='0', ln=0, align='C')

                    pdf.cell(w=54, h=ch,
                             txt="",
                             border='0', ln=0, align='C')
                    pdf.cell(w=2, h=ch, txt='', border='0', ln=0, align='C')
                    pdf.cell(w=65, h=ch, txt="", border='0', ln=1)
                    a1.clear()
                    i = i + 1

                pdf.set_text_color(0, 0, 0)
                pdf.cell(w=0,h=12, txt="", ln=1)
                pdf.cell(w=0, h=12, txt="", ln=1)
                pdf.cell(w=30, h=16, txt="Signature: ", border=0, ln=0, align='L')
                x = pdf.get_x()
                y = pdf.get_y()
                pdf.line(x - 8, y + 9, x + 100, y + 9)
                pdf.cell(180)
                pdf.cell(w=30, h=16, txt="Date: ", border=0, ln=0, align='L')
                x = pdf.get_x()
                y = pdf.get_y()
                pdf.line(x - 18, y + 9, (x + 100), y + 9)
                file_name = str(patient.user_id)+"_"+patient.first_name+""+patient.last_name+"_ciq_report.pdf"
                filepath = os.path.join(BASE_DIR, 'media')
                pdf.output(filepath+"/"+file_name, 'F')
                result = send_fax_directly_ciq(file_name, pid)
                print("Report Sent Successfully!")
                if result == "success":
                    return ("success")
                else:
                    return ("failed")

                #print("Report============================================!")
                #return FileResponse(open(filepath+"/"+file_name, 'rb'), as_attachment=True, content_type='application/pdf')

            if pre_exists == True and post_exists == True:
                i = 1
                for item in questions:
                    if i == 9:
                       pdf.add_page()

                       pdf.set_font('Arial', 'B', 14)
                       pdf.set_text_color(0, 0, 0)
                       pdf.cell(w=20, h=10, txt='S.NO', border='L,T,0,B', ln=0, align='C', fill=True)
                       pdf.cell(w=220, h=10, txt='PRE QUESTIONS', border='0,T,0,B', ln=0, align='C', fill=True)
                       pdf.cell(w=220, h=10, txt='POST QUESTIONS', border='0,T,0,B', ln=0, align='C', fill=True)
                       pdf.cell(w=65, h=10, txt='RESULT', border='0,T,R,B', ln=1, align='C', fill=True)
                    a1 = []
                    pdf.set_font('Arial', 'B', 12)
                    pdf.set_text_color(0, 0, 0)
                    q_length = len(str(item.name))
                    if q_length > 108:
                        pdf.cell(w=20, h=16,
                                 txt="Q-"+str(i),
                                 border='L,0,T,0', ln=0, align='C')
                    else:
                        pdf.cell(w=20, h=ch,
                                 txt="Q-" + str(i),
                                 border='L,0,T,0', ln=0, align='C')
                    x = pdf.get_x()
                    y = pdf.get_y()

                    pdf.set_text_color(0, 0, 0)
                    if q_length > 108:
                        pdf.cell(w=2, h=16, txt='', border='L,T,0,0', ln=0, align='C')
                    else:
                        pdf.cell(w=2, h=ch, txt='', border='L,T,0,0', ln=0, align='C')
                    pdf.multi_cell(w=216, h=ch,
                                   txt=item.name,
                                   border='0,0,T,0', align='L')

                    x1 = pdf.get_x()
                    y1 = pdf.get_y()


                    #pdf.line(x1, y,x1,y1)
                    pdf.set_xy(x + 220, y)
                    if q_length > 108:
                        pdf.cell(w=2, h=16, txt='', border='L,T,0,0', ln=0, align='C')
                    else:
                        pdf.cell(w=2, h=ch, txt='', border='L,T,0,0', ln=0, align='C')
                    pdf.multi_cell(w=216, h=ch,
                                       txt=item.name,
                                       border='0,T,0,0', align='L')

                    a = float(pdf.get_y())
                    pdf.set_xy(x + 440, y)
                    if preresult[i] == postresult[i]:
                        pdf.set_font('Arial', 'B', 14)
                        pdf.cell(w=65, h=ch, txt="Unchanged", border='L,T,R,0', ln=1, align='C')
                    if preresult[i] > postresult[i]:
                        pdf.set_font('Arial', 'B', 14)
                        pdf.cell(w=65, h=ch, txt="Improved", border='L,T,R,0', ln=1, align='C')
                    if preresult[i] < postresult[i]:
                        pdf.set_font('Arial', 'B', 14)
                        pdf.cell(w=65, h=ch, txt="Worsened", border='L,T,R,0', ln=1, align='C')

                    b = float(pdf.get_y())
                    if b < a:
                        y = pdf.get_y()
                        pdf.set_xy(470, y)
                        pdf.cell(w=65, h=ch, txt="", border='L,0,R,0', ln=1)

                    option = Options_new.objects.filter(question_new_id=item.id).all()

                    for opt in option:
                        a1.append(opt.name)

                    x = pdf.get_x()
                    y = pdf.get_y()
                    pdf.set_font('Arial', 'B', 12)
                    pdf.cell(w=20, h=ch,
                             txt="",
                             border='L,0,0,B', ln=0, align='C')
                    pdf.cell(w=2, h=ch, txt='', border='L,0,0,B', ln=0, align='C')
                    if preoption[i][0] == prelist[i]:
                        pdf.set_font('Arial', 'B', 12)
                        a = "(X)"
                    else:
                        pdf.set_font('Arial', 'B', 12)
                        pdf.set_text_color(0, 0, 0)
                        a =""
                    pdf.cell(w=54, h=ch,
                             txt=a+" 0 - " + a1[0],
                             border='0,0,0,B', ln=0, align='C')
                    if preoption[i][1] == prelist[i]:
                        pdf.set_font('Arial', 'B', 12)
                        a = "(X)"
                    else:
                        pdf.set_font('Arial', 'B', 12)
                        pdf.set_text_color(0, 0, 0)
                        a = ""
                    pdf.cell(w=54, h=ch,
                             txt=a+" 1 - " + a1[1],
                             border='0,0,0,B', ln=0, align='C')
                    if preoption[i][2] == prelist[i]:
                        pdf.set_font('Arial', 'B', 12)
                        a = "(X)"
                    else:
                        pdf.set_font('Arial', 'B', 12)
                        pdf.set_text_color(0, 0, 0)
                        a = ""
                    pdf.cell(w=54, h=ch,
                             txt=a+" 2 - " + a1[2],
                             border='0,0,0,B', ln=0, align='C')
                    if preoption[i][3] == prelist[i]:
                        pdf.set_font('Arial', 'B', 12)
                        a = "(X)"
                    else:
                        pdf.set_font('Arial', 'B', 12)
                        pdf.set_text_color(0, 0, 0)
                        a = ""
                    pdf.cell(w=54, h=ch,
                             txt=a+" 3 - " + a1[3],
                             border='0,0,0,B', ln=0, align='C')
                    pdf.cell(w=2, h=ch, txt='', border='0,0,R,B', ln=0, align='C')

                    if postoption[i][0] == postlist[i]:
                        pdf.set_font('Arial', 'B', 12)
                        a = "(X)"
                    else:
                        pdf.set_font('Arial', 'B', 12)
                        pdf.set_text_color(0, 0, 0)
                        a = ""
                    pdf.cell(w=2, h=ch, txt='', border='0,0,0,B', ln=0, align='C')
                    pdf.cell(w=54, h=ch,
                             txt=a+" 0 - " + a1[0],
                             border='0,0,0,B', ln=0, align='C')
                    if postoption[i][1] ==  postlist[i]:
                        pdf.set_font('Arial', 'B', 12)
                        a = "(X)"
                    else:
                        pdf.set_font('Arial', 'B', 12)
                        pdf.set_text_color(0, 0, 0)
                        a = ""
                    pdf.cell(w=54, h=ch,
                             txt=a+" 1 - " + a1[1],
                             border='0,0,0,B', ln=0, align='C')
                    if postoption[i][2] ==  postlist[i]:
                        pdf.set_font('Arial', 'B', 12)
                        a = "(X)"
                    else:
                        pdf.set_font('Arial', 'B', 12)
                        pdf.set_text_color(0, 0, 0)
                        a = ""
                    pdf.cell(w=54, h=ch,
                             txt=a+" 2 - " + a1[2],
                             border='0,0,0,B', ln=0, align='C')
                    if postoption[i][3] ==  postlist[i]:
                        pdf.set_font('Arial', 'B', 12)
                        a = "(X)"
                    else:
                        pdf.set_font('Arial', 'B', 12)
                        pdf.set_text_color(0, 0, 0)
                        a = ""
                    pdf.cell(w=54, h=ch,
                             txt=a+" 3 - " + a1[3],
                             border='0,0,0,B', ln=0, align='C')
                    pdf.cell(w=2, h=ch, txt='', border='0,0,R,B', ln=0, align='C')
                    pdf.cell(w=65, h=ch, txt="", border='0,0,R,B', ln=1)
                    a1.clear()
                    i = i + 1

                pdf.set_text_color(0, 0, 0)
                pdf.cell(w=0, h=12, txt="", ln=1)
                pdf.cell(w=0, h=12, txt="", ln=1)
                pdf.cell(w=30, h=16, txt="Signature: ", border=0, ln=0, align='L')
                x = pdf.get_x()
                y = pdf.get_y()
                pdf.line(x - 8, y + 9, x + 100, y + 9)
                pdf.cell(180)
                pdf.cell(w=30, h=16, txt="Date: ", border=0, ln=0, align='L')
                x = pdf.get_x()
                y = pdf.get_y()
                pdf.line(x - 18, y + 9, (x + 100), y + 9)
                file_name = str(patient.user_id) + "_" + patient.first_name + "" + patient.last_name + "_ciq_report.pdf"
                filepath = os.path.join(BASE_DIR, 'media')
                pdf.output(filepath + "/" + file_name, 'F')
                result = send_fax_directly_ciq(file_name,pid)
                print("Report Sent Successfully")
                if result == "success":
                    return ("success")
                else:
                    return ("failed")

                #return FileResponse(open(filepath + "/" + file_name, 'rb'), as_attachment=True,
                #                    content_type='application/pdf')

        else:
            return redirect('/')
    except Exception as e:
        print(e)
        return redirect('/')

@api_view(['GET'])
@permission_classes((AllowAny,))
def custom_fax_send(request,id,start_week,fromDay,end_week,toDay):
        try:
            print("YESSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSS")
            if id is None:
                return Response("pid", status=status.HTTP_400_BAD_REQUEST)
            if start_week is None:
                return Response("sw", status=status.HTTP_400_BAD_REQUEST)
            if fromDay is None:
                return Response("sd", status=status.HTTP_400_BAD_REQUEST)
            if end_week is None:
                return Response("ew", status=status.HTTP_400_BAD_REQUEST)
            if toDay is None:
                return Response("ed", status=status.HTTP_400_BAD_REQUEST)


            count = 1
            f_end = (((end_week) * 7) - (7 - toDay))
            if start_week == 1:
                f_start = fromDay
                count = f_start
            elif start_week == 2:
                f_start = 7 + int(fromDay)
                count = f_start
            elif start_week == 3:
                f_start = 14 + int(fromDay)
                count = f_start
            elif start_week == 4:
                f_start = 21 + int(fromDay)
                count = f_start
            elif start_week == 5:
                f_start = 28 + int(fromDay)
                count = f_start
            elif start_week == 6:
                f_start = 35 + int(fromDay)
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
            #df = pd.DataFrame(list(sleep_report))
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
            pdf.ln(10)
            itr = 1
            for x in range(int(start_week), int(end_week) + 1):
                if (end_week - start_week) > 1:
                    if x > 1:
                        pdf.add_page()
                pdf.set_font('Arial', 'B', 18)
                if end_week > 1:
                    pass
                    #pdf.ln(10)
                pdf.cell(w=0, h=10, txt="Week " + str(x), ln=1,
                         align='C')
                pdf.ln(10)

                # Table Header
                pdf.set_font('Arial', 'B', 12)
                x1_value = pdf.get_x()
                y1_value = pdf.get_y()
                y2_value = y1_value + 15.0
                pdf.line(x1_value, y1_value, 535, y1_value)
                pdf.line(x1_value, y2_value, 535, y2_value)
                pdf.line(x1_value, y1_value, x1_value, y2_value)
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
                if itr == 1:
                    i = fromDay
                else:
                    i = 1
                for index, item in enumerate(sleep_report, start=1):
                    print("COUNT", count)
                    print("INDEX", index)
                    if count == index:

                        if count <= f_end:
                            print("yes true")
                            if i == 1 or i <= 7:
                                print("No")
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
                                pdf.cell(w=19, h=ch,
                                         txt=str(item.total_sleep_time),
                                         border=1, ln=0, align='C')
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
                                if (item.comment):
                                    pdf.multi_cell(w=525, h=ch,
                                                   txt="Comment: " + str(item.comment),
                                                   border=1, align='L')
                                    pdf.ln(0)

                                i = i + 1
                                count = count + 1
                                itr += 1
                                continue
                            else:
                                break
                        else:
                            count = count + 1
                            continue
                    else:
                        continue

            pdf.set_text_color(0, 0, 0)
            pdf.cell(w=0, h=18, txt="", ln=1)
            pdf.cell(w=30, h=16, txt="Signature: ", border=0, ln=0, align='L')
            x = pdf.get_x()
            y = pdf.get_y()
            pdf.line(x-9, y + 9, x + 100, y + 9)
            pdf.cell(180)
            pdf.cell(w=30, h=16, txt="Date: ", border=0, ln=0, align='L')
            x = pdf.get_x()
            y = pdf.get_y()
            pdf.line(x-18, y + 9, (x + 100), y + 9)
            file_name = patient_name + "_" + str(id) + "_" + provider_id + ".pdf"
            filepath = os.path.join(BASE_DIR, 'media')
            pdf.output(filepath + "/" + file_name, 'F')
            print("Report Created Successfully", file_name)
            send_fax_directly_ciq(file_name, id)
            return Response("True", status=status.HTTP_200_OK)


        except Exception as e:
            print(e)
            return Response(str(e), status=status.HTTP_400_BAD_REQUEST)
