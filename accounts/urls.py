from django.contrib.auth import views
from django.urls import path, include, re_path
# from knox import views as know_views
from django.conf.urls import url
from . import views
from django.contrib.auth.views import LogoutView
from .views import *

urlpatterns = [
    path('login/', LoginPatient, name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('change_password/', Change_password),
    path('change_details/', Change_details),
    path('disapproved/', disapproved),
    path('updateid/', update_id),
    path('signup/', Signup_Provider),
    path('signup/<str:email>/<int:pid>/', Signup_Provider),
    path('success/', Verify_success),
    path('pro_logout/', pro_logout),
    path('signup_BBA_done_admin_two/<int:pid>/', signup_BBA_done_admin_two),

    path('forgot_password/', forgot_password),
    path('under_review/', under_review),
    path('provider_card/', provider_card),
    path('patientnform/<int:pid>/', UserRegterNForm, name='registern'),
    path('payment/', payment, name='payment'),
    path('forgetlink/<int:pid>', forgetlink),
    path('baa_signature/<int:pid>', baa_signature),
    path('patientregform/', UserRegterForm, name='register'),
    path('patient_verification/', PatientVerification, name='verify'),
    path('provider_verification/', ProviderVerification, name='verify'),
    path('provider_login/', LoginProvider, name='login'),
    path('provider_registration/', ProviderRegterForm, name='providerregister'),
    url(r'^validate_email/', validate_email),
    re_path(r'^api/ValidateEmail/', ValidateEmail.as_view()),
    re_path(r'^RegisterUser/', RegisterUser.as_view()),
    re_path(r'^Loginapi/$', LoginAPI.as_view()),

    # ===============================================

    # API URL WORKING

    # ===============================================

    # path('api/login/', APILoginPatient.as_view(), name='apilogin'),
    # path('api/change-password/', APIChangePassword.as_view(), name="apichangepassword"),
    # path('api/provider_login/', APILoginProvider.as_view(), name='apiproviderlogin'),
    path('api/signup_provider/', SignupProviderAPIView.as_view(), name='signup_provider'),
    # path('api/provider_type/', ProviderTypeAPIView.as_view(), name='provider_type'),
    # path('api/user_detail/<int:id>', UserDetailAPIView.as_view(), name='user_detail'),
    # path('api/providerReg/<int:id>', ProviderRegFormAPIView.as_view(), name='providerRegx   '),

    # ===============================================

    # MA URL WORKING

    # ===============================================
    path('submit_invite/<int:pid>/<str:email>/<str:type>/', Send_Provider_Ma_Invitatiton, name='send_invitation'),
    path('ma_refbypro/', ma_Referedbypro.as_view()),
    path('register_ma/<int:pid>/<int:iid>/', ma_signup),
    path('add_provider/<int:pid>/<int:spid>/', add_provider),
    path('accept_provider/<int:pid>/<int:mid>', add_provider_page),
    path('ma_provider_patients/<int:pid>/', Ma_provider_patients),
    path('signup_BBA/', Signup_BBA.as_view()),
    path('signup_BBA_done/', Signup_BBA_Done.as_view()),
    path('signup_BBA_done_admin/', Signup_BBA_Done_admin.as_view()),

]
