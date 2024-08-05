from django.urls import path, include

from . import views
from .views import *
# from .views import stripe_config , create_checkout_session

urlpatterns = [
    path('coupons/', CouponAPI.as_view(), name='coupon_api'),
    path('<str:pid>', views.home, name='subscriptions-home'),
    path('reg_subsc/<str:pid>/<str:uid>', views.reg_subsc),
    path('chk_ses/', views.chk_ses),
    path('stripe-webhook/', views.stripe_webhook, name='stripe_webhook'),
    path('config/', views.stripe_config),
    path('cancelled/<int:pid>', views.cancelled),
    path('report/<str:invoice>', views.report),
    path('success/<str:pid>', views.success),
    path('create_product/', views.create_product),
    path('update_product/', views.update_product),
    path('update_product_coupon/', views.update_product_coupon),
    path('coupon_update_price/', views.coupon_update_price),
    path('update_price/', views.update_price),
    path('unsuccessfull/<str:pid>', views.unsuccessfull),
    path('subscription_detail/<int:pid>', views.subscription_detail),
    path('cancel_request/', views.cancel_request),
    path('cancel_pending_request/', views.cancel_pending_request),
    path('verify_coupon/', VerifyCouponCode.as_view()),
    path('api/delete_package/<str:product_id>/', PackageDeleteAPI.as_view(), name='delete_product'),
    path('api/delete_coupon/<str:product_id>/', CouponsDeleteAPI.as_view(), name='delete_product'),

]
