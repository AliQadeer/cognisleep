from django.conf import settings
from django.shortcuts import redirect
from django.contrib.sessions.models import Session

import re

from accounts.models import PatientProfile
from payments.views import isPaymentSuccess

EXAMPT_URLs = [re.compile(settings.LOGIN_GUEST_URL.lstrip('/'))]

if hasattr(settings, 'LOGIN_NOT_REQUIRED_URLS'):
    EXAMPT_URLs += [re.compile(url) for url in settings.LOGIN_NOT_REQUIRED_URLS]


class LoginGuestRequiredMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_view(self, request, view_func, view_args, view_kwargs):
        assert hasattr(request, 'session')

        path = request.path_info.lstrip('/')

        if request.session.has_key('guest'):
            msession = request.session['guest']
            print("debugging 01")
            #print(request.session.get_expiry_age())
        else:
            msession = True

        if not msession:
            if not any(url.match(path) for url in EXAMPT_URLs):
                return redirect(settings.LOGIN_GUEST_URL)


class paymentMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        paymentSuccess = None
        if request.user.id is not None and request.user.isprovider != 1:

            try:
                PatientProfile.objects.get(doctor_ref_number="", patient_user_id=request.user.id,
                                           package_no="PRIMARY CARE SUBSCRIPTION")
                paymentSuccess = isPaymentSuccess(request.user.email)
            except:
                paymentSuccess = None

            request.session['payment'] = paymentSuccess
        else:
            request.session['payment'] = None

        dname = request.path.split('/')[1].strip()

        if (dname == "dashboard" and paymentSuccess is not None and paymentSuccess is False):
            return redirect(settings.BASE_URL)

        return response
