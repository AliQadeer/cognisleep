from django.contrib.auth import views
from django.urls import  include, re_path, path

from . import views
from django.contrib.auth.views import LoginView, LogoutView
from .views import *
from .views import createcoupon
urlpatterns = [
    path('', adminLogin, name='adminlogin'),
    path('dashboardofprovider/<int:pid>', dashboardofprovider),
    path('patient-admin/view-diary/<int:weekNm>/<int:pID>/', view_sleep_diary_byprovider),
    path('api/view-diary/<int:weekNm>/<int:pID>/', sleep_diary_week_data, name="week-num"),
    path('progress-admin/<int:pid>', progress_byprovider),
    path('subscription_package/', subscription_package),
    path('accountdetails-admin/<int:pid>/', accountdetailsbyprovider),
    path('dashboard/', Dashboard, name='dashboard'),
    path('providers/', Providers, name='pr'),
    path('nonverifiedprovider/', Non_Verified_Provider),
    path('incompleteprovider/', Incomplete_Provider),
    path('verified/<int:pid>/', Verified_Provider),
    path('register_provider_verify/<str:pid>/', views.register_provider_verify),
    path('providers_verify/', provider_verification),
    path('create_coupon/', createcoupon),
    path('admin_verify/', admin_verification),
    path('providers_ref_verify/', provider_ref_verification),
    path('provider_detail/<int:pid>/', provider_detail),
    path('patient_detail/<int:pid>/', patient_detail),
    path('refpatient_detail/<int:pid>/', refpatient_detail),
    path('patients/', Patients),
    path('refpatients/', refPatient),
    path('refpatientslogs/', refPatient_log),
    path('create_package/', create_package),
    path('verified_message/', verified_message),
    path('all_packages/', all_packages),
    path('all_packages_coupon/', all_packages_coupon),
    path('dashboard/Cpatients', Cpatients, name='cpatients'),
    path('delete_user/<int:user_id>/', delete_user, name='delete_user'),

]

