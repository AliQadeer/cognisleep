from django.contrib import admin
from django.urls import path, re_path
from django.contrib.auth import views
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls import url, include



from .views import *


urlpatterns = [
    path('', dashboard),
    path('ma_patient_dashboard/<int:pat_id>/', ma_patient_dashboard),
    path('acknowledge_report/<int:pid>/',patient_acknowledge_report),
    path('accountdetails', accountdetails),
    path('relaxation', relaxation),
    path('ma-relaxation/<int:pid>', ma_relaxation),
    path('accountdetails/<int:pid>/',accountdetailsbyprovider),
    path('patient/<int:pid>/', dashboardPatient),
    path('provider_subscription/', provider_subscription),
    path('finalvideo', savelastvideo),
    path('mafinalvideo/<int:pid>', masavelastvideo),
    path('diary/<int:wday>/<int:pid>/', diary),
    path('ma_diary/<int:wday>/<int:pid>/', ma_diary),
    path('tutorials/', tutorials),
    path('certificate/', certificate),
    path('ma-certificate/<int:pid>', ma_certificate),
    path("ntl/",ntl),
    path("ma_ntl/<int:pid>",ma_ntl),
    path('provider_subscription_detail/', provider_subscription_detail),
    path('provider_invoice/',provider_invoice),
    path('videos/<int:vid>/', videos),
    path('ma_videos/<int:vid>/<int:pid>/', ma_videos),
    path("updatevalue/<int:wid>/<str:pid>/<str:sid>/<int:ppid>", updatevalue),
    path('view-diary/<int:weekNm>/<int:pID>/', view_sleep_diary),
    path('ma-view-diary/<int:weekNm>/<int:pID>/', ma_view_sleep_diary),
    path('patient/view-diary/<int:weekNm>/<int:pID>/', view_sleep_diary_byprovider),
    path('api/view-diary/<int:weekNm>/<int:pID>/', sleep_diary_week_data, name="week-num"),
    path('api/v-session-complete/', SessionCompleted.as_view(), name="v-session-complete"),
    # path('api/v-session-complete/', SessionCompleted, name="v-session-complete"),
    path('view-diary/', view_sleep_diary),
    path('patient/videos/<int:vid>/<int:pid>', videos),
    path('patient/ma_videos/<int:vid>/<int:pid>', ma_videos),
    path('progress/', progress),
    path('report/', create_pdf_report_weekly),
    path('progress/<int:pid>', progress_byprovider),
    path('patient/progress/<int:pid>', progress),
    path('ma-progress/<int:pid>', ma_progress),
    path('contactus/', contactus),
    path('provider_card/', provider_card),
    path('calculate_time_net/', calculate_time_net),
    path('answers/<str:vid>/', answers),
    path("updatevalue/<int:wid>/<str:pid>/<str:sid>/<int:ppid>", updatevalue),
    path('setting/', setting),
    path('refbypro/', Referedbypro.as_view()),
    path('patient_account_detail/', patient_account_detail),
    path('api/providerhandbooks/', ProviderhandbooksAPIView, name='providerhandbooks-api'),
    path('gethandbooks/<int:pid>/<int:wid>/', gethandbooks, name='gethandbooks'),
    path('downloadhandbooks/<int:pid>/<int:weekno>/', provider_handbook_report),
    



]

