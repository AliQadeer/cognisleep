"""cogni URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/dev/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import re_path,path
from django.contrib.auth import views
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls import  include
from django.views.static import serve
from django.shortcuts import redirect
from django.shortcuts import render

from .views import (
    home_page,
    about_page,
    provider_login,
    provider_registration,
    patients,
    employers,
    providers,
    pricing,
    faq, blog,
    cogni_science,
    Referedbyprof,
    Patient_status,
    Ma_status,
    daily_progress_chart, get_videos, guestLogin, comingsoon,
    do_you_have_sleeping_problem, acknowledge_page, terms, contactus, Subscription, calculator, Referedbycoupon
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('backend/', include('backend.urls')),
    path('', home_page, name="home_page"),
    path('accounts/',include('accounts.urls')),
    path('payments/',include('payments.urls')),
    path('Permissions/',include('Permissions.urls')),
    path('login/',guestLogin),
    path('about/', about_page),
    path('questions/', include('taketester.urls')),
    path('calculator/', calculator),
    path('provider_login/', provider_login),
    path('provider_registration/', provider_registration),
    path('patients/', patients),
    path('comingsoon/', comingsoon),
    path('employers/', employers),
    path('providers/', providers),
    path('dashboard/', include('dashboard.urls')),
    path('pricing/<int:pid>/', pricing),
    path('terms/', terms),
    path('acknowledge_page/<int:pid>/', acknowledge_page),
    path('cogni_science/', cogni_science),
    path('faq/', faq),
    path('blog/', blog),
    path('contactus/', contactus),
    path('do-you-have-sleeping-problem/', do_you_have_sleeping_problem, name="do-you-have-sleeping-problem"),
    re_path(r'^api/', include('accounts.urls')),
    re_path(r'^api/chart/data/$', daily_progress_chart, name="daily-progress"),
    #re_path(r'^patient/api/chart/data/<int:pid>/$', daily_progress_chart, name="daily-progress2"),
    path('patient/api/chart/data/<int:pid>/', daily_progress_chart, name="daily-progress2"),
    re_path(r'^api/get_videos/data/$', get_videos, name="get_videos"),
    re_path(r'^api/refby/$', Referedbyprof.as_view()),
    re_path(r'^api/refbycoupon/$', Referedbycoupon.as_view()),
    re_path(r'^api/patient_status/$', Patient_status.as_view()),
    re_path(r'^api/ma_status/$', Ma_status.as_view()),
    re_path(r'^api/subs/$', Subscription.as_view()),
    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT, }),
] #+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
#media files uploads
#if settings.DEBUG:
#    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
from django.conf import settings
admin.site.site_header = settings.ADMIN_SITE_HEADER
admin.site.site_title = "Admin"
admin.site.index_title = "Cognisleep"

def custom_404_view(request, exception=None):
    return render(request, '404_page.html', status=404)
handler404 = custom_404_view