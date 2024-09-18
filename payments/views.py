import datetime
from django.views.decorators.http import require_POST
import stripe as stripe
from django.conf import settings  # new
from django.contrib import messages
from django.core.mail import send_mail
from django.db import connections
from django.http.response import JsonResponse, HttpResponse, HttpResponseRedirect  # new
from django.shortcuts import render, redirect
from django.template import loader
from django.views.decorators.csrf import csrf_exempt  # new
from django.contrib.auth.decorators import login_required
# new
from accounts.admin import User
from accounts.models import Provider, Provider_Verification, RefPatient
from backend.models import StripeCustomer
from payments.models import PaymentRecord, Product_detail
import json

from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from rest_framework.response import Response
from .serializer import GetCouponssSerializer  # Import your serializer
from .models import Coupon  # Import your Coupon model
from .models import Coupon_Product_detail
# from .utils import create_message  # Import your utility function for creating a response message
from rest_framework import permissions, status

stripe.api_key = 'sk_test_51LBfcLKxLHATWwe7yJr8k5XYrxGAlb8LdEhmnWaRm2Q8Z2wzKKT2MYf9sjZDzHnfZzpdVtPXw53CUzys8hwtpXbd00QssamM1K'
#@login_required(login_url='/accounts/provider_login/')
def home(request, pid):
    try:
        user_access = ""
        user_name = ""
        user_image = ""
        user_profile = Provider.objects.get(user_id=pid)
        user_name = user_profile.first_name + " " + user_profile.last_name
        package_name = user_profile.package_type
        user_image = user_profile.provider_image
        provider_access = Provider_Verification.objects.get(user_id=pid)
        user_access = provider_access.user_position
        print(user_profile.subscription_type)
        if user_profile.subscription_type == "package":

        # if user_profile.provider_type == "Coupon User":
        #     package = Product_detail.objects.get(product_description__contains=package_name)
            if package_name == "MD/DO-$89":
                package = Product_detail.objects.get(product_name ="MD/DO")
            if package_name == "Associated PA, APRN-$29":
                package = Product_detail.objects.get(product_name ="Associated PA, APRN")
            if package_name == "PHD-$89":
                package = Product_detail.objects.get(product_name ="PHD")
            if package_name == "Independent PA, APRN-$89":
                package = Product_detail.objects.get(product_name ="Independent PA, APRN")
        else:

            userData = Coupon_Product_detail.objects.get(product_description__contains=user_profile.coupon_code)
            package = userData



        return render(request, 'provider_subscription.html', context={'product':package,'user_name':user_name,'user_image':user_image,"user_access": user_access, "role_id": 1,  'user_id': pid, "subscription_type":user_profile.subscription_type})
    except Exception as e:
        print(e)
        return redirect('/')

def create_product(request):
    try:
        if request.method == "POST":
            print("Yes update product")
            stripe.api_key = settings.STRIPE_SECRET_KEY
            packageprice = request.POST.get("package_price")
            packagename = request.POST.get("package_name")
            packagedesc = request.POST.get("package_description")
            price = str(packageprice) + "00"
            price = int(price)
            product = stripe.Product.create(
                name=packagename,
                description=packagedesc,
                default_price_data={
                    "unit_amount": price,
                    "currency": "usd",
                    "recurring": {"interval": "month"},
                },
                expand=["default_price"],
            )
            print("PRODUCT SAVE SUCCESSFULLY")
            new_product = Product_detail(
                product_id=product.id,
                price_id=product.default_price.id,
                product_name=product.name,
                product_description=product.description,
                price=packageprice)
            new_product.save()
            return redirect('/backend/all_packages/')
    except Exception as e:
        print(e)
        return redirect('/')


class PackageDeleteAPI(APIView):
    def delete(self, request, product_id, *args, **kwargs):
        try:
            # Get the Product_detail instance with the provided product_id

            product_detail_instance = Product_detail.objects.get(product_id=product_id)

            # Delete the instance
            product_detail_instance.delete()

            return Response('package deleted successfully', status=status.HTTP_204_NO_CONTENT)
        except Product_detail.DoesNotExist:
            return Response('package not found', status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            print("Exception:", e)
            return Response('An error occurred while deleting the package', status=status.HTTP_400_BAD_REQUEST)

def update_product(request):
    try:
        print("Yes update")
        if request.method == "POST":
            print("Yes update product")
            stripe.api_key = settings.STRIPE_SECRET_KEY
            productid = request.POST.get("packageid")
            packagename = request.POST.get("package_name")
            packagedesc = request.POST.get("package_Description")
            stripe.Product.modify(
                productid, name = packagename, description = packagedesc )
            print("PACKAGE UPDATED SUCCESSFULLY")
            product_data = Product_detail.objects.get(product_id=productid)
            product_data.product_name = packagename
            product_data.product_description = packagedesc
            product_data.save()
            return redirect('/backend/all_packages/')

    except Exception as e:
        print(e)
        return redirect('/')

def update_product_coupon(request):
    try:
        print("Yes update")
        if request.method == "POST":
            print("Yes update product")
            stripe.api_key = settings.STRIPE_SECRET_KEY
            product_id = request.POST.get("product_id")
            title = request.POST.get("title")
            packagedesc = request.POST.get("description")
            stripe.Product.modify(
                product_id, name = title, description = packagedesc )
            print("PACKAGE UPDATED SUCCESSFULLY")
            product_data = Coupon_Product_detail.objects.get(product_id=product_id)
            product_data.product_name = title
            product_data.product_description = packagedesc
            product_data.save()
            return redirect('/backend/all_packages_coupon/')

    except Exception as e:
        print(e)
        return redirect('/')


def coupon_update_price(request):
    try:
        if request.method == "POST":
            print("Yes update product")
            stripe.api_key = settings.STRIPE_SECRET_KEY
            product_id = request.POST.get("product_id")
            price = request.POST.get("price")
            price = str(price)
            price = int(price)
            stripe.api_key = settings.STRIPE_SECRET_KEY
            new_price = stripe.Price.create(
                product=product_id,
                unit_amount=int(price * 100),
                currency="usd",
                recurring={"interval": "month"},
            )
            print("PRICE CREATED")
            stripe.Product.modify(product_id, default_price=new_price.id)
            print("PRODUCT PRICE UPDATED SUCCESSFULLY")
            product_data = Coupon_Product_detail.objects.get(product_id=product_id)
            product_data.price_id = new_price.id
            product_data.price = price
            product_data.save()
            return redirect('/backend/all_packages_coupon/')
    except Exception as e:
        print(e)
        return redirect('/')
def update_price(request):
    try:
        if request.method == "POST":
            print("Yes update product")
            stripe.api_key = settings.STRIPE_SECRET_KEY
            productid = request.POST.get("packageid")
            packageprice = request.POST.get("package_price")
            price = str(packageprice) + "00"
            price = int(price)
            stripe.api_key = settings.STRIPE_SECRET_KEY
            new_price = stripe.Price.create(
                product=productid,
                unit_amount=price,
                currency="usd",
                recurring={"interval": "month"},
            )
            print("PRICE CREATED")
            stripe.Product.modify(productid, default_price=new_price.id)
            print("PRODUCT PRICE UPDATED SUCCESSFULLY")
            product_data = Product_detail.objects.get(product_id=productid)
            product_data.price_id = new_price.id
            product_data.price = packageprice
            product_data.save()
            return redirect('/backend/all_packages/')
    except Exception as e:
        print(e)
        return redirect('/')

def handle_stripe_event(event):
    # Handle the event based on its type
    if event['type'] == 'payment_intent.succeeded':
        handle_payment_intent_succeeded(event)

    elif event['type'] == 'payment_intent.payment_failed':
        handle_payment_intent_failed(event)

    elif event['type'] == 'invoice.payment_succeeded':
        handle_invoice_payment_succeeded(event)

    elif event['type'] == 'invoice.payment_failed':
        handle_invoice_payment_failed(event)

    # Add more event handlers as needed

def handle_payment_intent_succeeded(event):
    payment_intent = event['data']['object']
    # Add your logic to handle the successful payment intent event
    print(f'PaymentIntent succeeded! ID: {payment_intent.id}')

def handle_payment_intent_failed(event):
    payment_intent = event['data']['object']
    # Add your logic to handle the failed payment intent event
    print(f'PaymentIntent failed! ID: {payment_intent.id}')

def handle_invoice_payment_succeeded(event):
    invoice = event['data']['object']
    # Add your logic to handle the successful invoice payment event
    print(f'Invoice payment succeeded! ID: {invoice.id}')

def handle_invoice_payment_failed(event):
    invoice = event['data']['object']
    # Add your logic to handle the failed invoice payment event
    print(f'Invoice payment failed! ID: {invoice.id}')

# Add more event handlers as needed

@csrf_exempt
@require_POST
def stripe_webhook(request):
    payload = request.body
    sig_header = request.headers.get('Stripe-Signature')

    # Replace 'your_stripe_endpoint_secret' with your actual webhook secret
    endpoint_secret = 'pk_test_51LBfcLKxLHATWwe7cusrpfripSNOxKgdyh2UyjcwyHcY7xtrvZXiIy2zFPbodDcswI2SryjHjYHp01JSztR3Cwa000s6AoRU7M'

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except ValueError as e:
        # Invalid payload
        return JsonResponse({'error': 'Invalid payload'}, status=400)
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        return JsonResponse({'error': 'Invalid signature'}, status=400)

    # Handle the event
    handle_stripe_event(event)

    return JsonResponse({'status': 'success'})


def chk_ses(request):
    user_access = ""
    user_name = ""
    user_image = ""
    stripe_api_key = 'pk_test_51LBfcLKxLHATWwe7cusrpfripSNOxKgdyh2UyjcwyHcY7xtrvZXiIy2zFPbodDcswI2SryjHjYHp01JSztR3Cwa000s6AoRU7M'
    try:

        if request.method == 'POST':
            pid = request.POST.get("user_id")
            user_data = User.objects.get(id=pid)
            user_detail = Provider.objects.get(user_id=pid)

            user_name = user_detail.first_name + " " + user_detail.last_name
            user_image = user_detail.provider_image
            provider_access = Provider_Verification.objects.get(user_id=pid)
            user_access = provider_access.user_position
            price_id = request.POST.get('price_id')
            pkg_name = request.POST.get('pkg_name')
            pkg_price = request.POST.get('pkg_price')
            provider_access = Provider_Verification.objects.get(user_id=pid)
            user_access = provider_access.user_position
            print(price_id)
            context = {
                "price_id": price_id,
                "pkg_name": pkg_name,
                "pkg_price": pkg_price,
                "user_access": user_access,
                "role_id": 1,
                'user_data': user_data,
                'user_detail': user_detail,
                'user_name': user_name,
                'user_image': user_image,
                'stripe_api_key':stripe_api_key,

            }
            return render(request, "checkout_session.html", context)
    except Exception as e:
        print(e)
        return redirect('/')


def report(request, invoice):
    try:

        print("accepted invoice number is ",invoice )
        stripe.api_key = settings.STRIPE_SECRET_KEY
        inv = stripe.Invoice.retrieve(invoice,)
        print(inv)
        account_name = inv['account_name']
        print(account_name)
        billing_reason = inv['billing_reason']
        print(billing_reason)
        dat = inv['created']
        date = datetime.datetime.fromtimestamp(dat)
        date = date.strftime("%m/%d/%Y")
        invoice_date = date
        print(invoice_date)
        currency = inv['currency']
        print(currency)
        customer_name = inv['customer_name']
        print(customer_name)
        customer_email = inv['customer_email']
        print(customer_email)
        amountt = inv['lines'].data[0]['amount']
        print(amountt)
        package = inv['lines'].data[0]['description']
        print(package)
        p1 = inv['lines'].data[0]['period']['end']
        print(p1)
        date = datetime.datetime.fromtimestamp(p1)
        date = date.strftime("%m/%d/%Y")
        end_date = date
        print(end_date)
        p2 = inv['lines'].data[0]['period']['start']
        print(p2)
        date = datetime.datetime.fromtimestamp(p2)
        date = date.strftime("%m/%d/%Y")
        start_date = date
        print(start_date)
        invoice_number = inv['number']
        print(invoice_number)
        invoice_status = inv['status']
        print(invoice_status)
        charge_id = inv['charge']
        charge = stripe.Charge.retrieve(charge_id,)
        country = charge['billing_details']['address']['country']
        print(country)
        card_brand = charge['payment_method_details']['card']['brand']
        print(card_brand)
        last4 = charge['payment_method_details']['card']['last4']
        print(last4)
        pay_type = charge['payment_method_details']['type']
        print(pay_type)
        quantity = "1"
        amountt = str(amountt)[0:2]
        context = {
            "account_name": account_name,
            "billing_reason": billing_reason,
            "invoice_date": invoice_date,
            "currency": currency,
            "customer_name": customer_name,
            "customer_email": customer_email,
            "amountt": amountt,
            "package": package,
            "end_date": end_date,
            "start_date": start_date,
            "invoice_number": invoice_number,
            "invoice_status": invoice_status,
            "country": country,
            "card_brand": card_brand,
            "last4": last4,
            "pay_type": pay_type,
            "quantity": quantity,

        }
        return render(request, "invoice.html", context)
    except Exception as e:
        print(e)
        return redirect('/')

def reg_subsc(request, pid, uid):
    try:

        if request.method == 'GET':
            price_id = pid  # request.POST.get('price_id')
            print("Here is your price id", price_id)
            print(uid)
            data = User.objects.get(id=uid)
            email = data.email
            userid = data.id
            print(userid)
            data = Provider.objects.get(user_id=userid)
            # price = Coupon_Product_detail.objects.get(price_id=price_id)
            fname = data.first_name
            lname = data.last_name

            print(fname)
            print(lname)
            customer = stripe.Customer.create(
                email=email,
                name=fname + " " + lname,
            )
            print(customer.id)
            if data.subscription_type=="coupon":

                subscription = stripe.Subscription.create(
                    customer=customer.id,
                    items=[{
                        'price': price_id,
                    }],
                    payment_behavior='default_incomplete',
                    payment_settings={'save_default_payment_method': 'on_subscription'},
                    expand=['latest_invoice.payment_intent'],
                )
            else:
                # price = Product_detail.objects.get(price_id=price_id)
                subscription = stripe.Subscription.create(
                    customer=customer.id,
                    items=[{
                        'price': price_id,
                    }],
                    payment_behavior='default_incomplete',
                    payment_settings={'save_default_payment_method': 'on_subscription'},
                    expand=['latest_invoice.payment_intent'],
                )
            user = User.objects.get(id=userid)
            provider = Provider.objects.get(user_id=userid)
            StripeCustomer.objects.create(
                user=user,
                stripeCustomerId=customer.id,
                stripeSubscriptionId=subscription.id,
            )
            provider.subscription_status = "Active"
            provider.save()
            stripe_config = {'clientsecret': subscription.latest_invoice.payment_intent.client_secret}
            return JsonResponse(stripe_config,  safe=False)
    except Exception as e:
        print(e)
        return redirect('/')

@csrf_exempt
def stripe_config(request):
    try:
        if request.method == 'GET':
            stripe_config = {'publicKey': settings.STRIPE_PUBLISHABLE_KEY}

            return JsonResponse(stripe_config, safe=False)
    except Exception as e:
        print(e)
        return redirect('/')

def unsuccessfull(request, pid):
    try:
        print("yes unsuccessfull")
        if request.method == 'GET':
            if StripeCustomer.objects.filter(user_id=pid).exists():
                print("yes unsuccessfull 1")
                stripe_customer = StripeCustomer.objects.get(user_id=pid)
                stripe.api_key = settings.STRIPE_SECRET_KEY
                subscription = stripe.Subscription.retrieve(stripe_customer.stripeSubscriptionId)
                stripe.Subscription.delete(subscription.id)
                stripe.Customer.delete(stripe_customer.stripeCustomerId)
                print("deleted")
                stripe_customer.delete()
                provider = Provider.objects.get(user_id=pid)
                provider.subscription_status = "Cancel"
                provider.save()
                print("yes unsuccessfull 2")
            _title = settings.BASE_TITLE + ' |  Contact us'
            context = {
                "title": _title,
                "base_url": settings.BASE_URL,
                "link": settings.BASE_URL + "/dashboard/",
                "link_text": "Dashboard",
                "tags": "success",
            }
        print("Customer Deleted Successfully")
        return HttpResponse(status=200)
    except Exception as e:
        print(e)
        return redirect('/')

def success(request, pid):
    user_access = ""
    user_name = ""
    user_image = ""

    try:
        if request.method == 'GET':
            _title = settings.BASE_TITLE + ' |  Payment Success'

            user_step = Provider_Verification.objects.get(user_id=pid)
            user_step.user_position = 2
            user_step.save()
            user_profile = Provider.objects.get(user_id=pid)
            user_name = user_profile.first_name + " " + user_profile.last_name
            user_image = user_profile.provider_image
            provider_access = Provider_Verification.objects.get(user_id=pid)
            user_access = provider_access.user_position
            context = {
                "title": _title,
                "base_url": settings.BASE_URL,
                "link": settings.BASE_URL + "/accounts/provider_verification",
                "link_text": "Verify Your Account",
                "tags": "success",
                "user_access": user_access,
                "role_id": 1,
                "user_name": user_name,
                "user_image":user_image,
            }

            if StripeCustomer.objects.filter(user_id=pid).exists():
                print("yes exist")
                user = User.objects.get(id=pid)
                provider_email = user.email
                stripe_customer = StripeCustomer.objects.get(user_id=pid)
                stripe.api_key = settings.STRIPE_SECRET_KEY
                subscription = stripe.Subscription.retrieve(stripe_customer.stripeSubscriptionId)
                product = stripe.Product.retrieve(subscription.plan.product)
                product_price = subscription.plan.amount_decimal[0:3]
            # email Subscription Details

                subject = 'CogniSleep Subscription Detail'
                to = provider_email

                html_message = loader.render_to_string(
                    'email_temp/active_subscription.html',
                    {
                        'subscription': subscription,
                        'product': product,
                        'price' : product_price,
                    }
                )
                email_records(request, to, settings.EMAIL_FROM, 'CogniSleep Subscription Detail')
                send_mail(
                    subject,
                    'CogniSleep Subscription Detail',
                    settings.EMAIL_FROM,
                    [to],
                    html_message=html_message
                    ,
                )

            messages.success(request, "Your payment has been successful")
            return render(request, "payment_success.html", context)
    except Exception as e:
        print(e)
        return redirect('/')

def cancel_request(request):
    try:
        UserID = request.user.id
        provider = Provider.objects.get(user_id=UserID)
        provider.subscription_status = "Pending"
        provider.save()
        _title = settings.BASE_TITLE + ' |  Settings'

        mylist = []
        mysearch = ""
        user_name = ""
        user_image = ""
        user_access = ""



        if request.user.role_id == 1:
            user_profile = Provider.objects.get(user_id=request.user.id)
            user_name = user_profile.first_name + " " + user_profile.last_name
            user_image = user_profile.provider_image
            provider_access = Provider_Verification.objects.get(user_id=request.user.id)
            user_access = provider_access.user_position
            print("YESSSSSSSSSSSSSSSS provider 1")


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
            user_step = Provider_Verification.objects.get(user_id=request.user.id)

            context = {

                 "title": _title,
                "base_url": settings.BASE_URL,
                "first_name": '',
                "user_name": user_name,
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
            messages.success(request, "Your Subscription Cancel request has been sent successfully.")
            return render(request, "setting.html", context)

    except Exception as e:
        print(e)
        return redirect('/')

def cancel_pending_request(request):
    try:

        UserID = request.user.id
        provider = Provider.objects.get(user_id=UserID)
        provider.subscription_status = "Active"
        provider.save()
        _title = settings.BASE_TITLE + ' |  Settings'
        mylist = []
        mysearch = ""
        user_name = ""
        user_image = ""
        user_access = ""

        if request.user.role_id == 1:
            user_profile = Provider.objects.get(user_id=request.user.id)
            user_name = user_profile.first_name + " " + user_profile.last_name
            user_image = user_profile.provider_image
            provider_access = Provider_Verification.objects.get(user_id=request.user.id)
            user_access = provider_access.user_position
            print("YESSSSSSSSSSSSSSSS provider 1")

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
            user_step = Provider_Verification.objects.get(user_id=request.user.id)

            context = {

                "title": _title,
                "base_url": settings.BASE_URL,
                "first_name": '',
                "user_name": user_name,
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

        messages.success(request, "Your Subscription Cancel request has been Remove successfully.")
        return render(request, "setting.html", context)
    except Exception as e:
        print(e)
        return redirect('/')

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

def cancelled(request, pid=0):
    try:
        print("YES IN CANCEELED")
        print(pid)

        if pid == 0:
            stripe_customer = StripeCustomer.objects.get(user_id=request.user.id)
        if pid != 0 and pid is not None:
            stripe_customer = StripeCustomer.objects.filter(user_id=pid).first()
            if stripe_customer:
                stripe.api_key = settings.STRIPE_SECRET_KEY
                subscription = stripe.Subscription.retrieve(stripe_customer.stripeSubscriptionId)
                product = stripe.Product.retrieve(subscription.plan.product)
                product_price = subscription.plan.amount_decimal[0:3]
                stripe.Subscription.delete(subscription.id)
                print("deleted")
                stripe_customer.delete()
            provider = Provider.objects.get(user_id=pid)
            provider.subscription_status = "Cancel"
            provider.save()
            users_to_update = User.objects.filter(provider=provider, role_id=5)
            for user in users_to_update:
                user.active = False  # or True, depending on your requirement
                user.save()
            ref_patients = RefPatient.objects.filter(provider_id=provider.id)
            if ref_patients:
                for ref_patient in ref_patients:
                    user = ref_patient.user
                    user.active = False
                    user.save()
            user = User.objects.get(id=pid)
            user.active = False
            user.save()
            provider_email = user.email
                # email Subscription Details

            subject = 'CogniSleep Subscription Cancellation'
            to = provider_email

            html_message = loader.render_to_string(
                'email_temp/cancel_subscription.html',
                {
                    'subscription': subscription,
                    'product': product,
                    'price': product_price,
                }
            )
            email_records(request, to, settings.EMAIL_FROM, 'CogniSleep Subscription Cancellation')
            send_mail(
                subject,
                'CogniSleep Subscription Cancellation',
                settings.EMAIL_FROM,
                [to],
                html_message=html_message
                ,
            )

        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
    except Exception as e:
        print(e)
        return redirect('/')


@login_required
@csrf_exempt
def stripe_webhook(request):
    try:
        stripe.api_key = settings.STRIPE_SECRET_KEY
        endpoint_secret = settings.STRIPE_ENDPOINT_SECRET
        payload = request.body
        sig_header = request.META['HTTP_STRIPE_SIGNATURE']
        event = None

        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, endpoint_secret
            )
        except ValueError as e:
            # Invalid payload
            return HttpResponse(status=400)
        except stripe.error.SignatureVerificationError as e:
            # Invalid signature
            return HttpResponse(status=400)

        # Handle the checkout.session.completed event
        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']

            # Fetch all the required data from session
            client_reference_id = session.get('client_reference_id')
            print(client_reference_id)
            stripe_customer_id = session.get('customer')
            stripe_subscription_id = session.get('subscription')

            # Get the user and create a new StripeCustomer
            user = User.objects.get(id=client_reference_id)
            provider = Provider.objects.get(user_id=client_reference_id)
            StripeCustomer.objects.create(
                user=user,
                stripeCustomerId=stripe_customer_id,
                stripeSubscriptionId=stripe_subscription_id,
            )
            provider.subscription_status = "Active"
            provider.save()
            print(user.email + ' just subscribed.')
            if StripeCustomer.objects.filter(user_id=client_reference_id).exists():
                print("yes exist")
                provider_email = user.email
                stripe_customer = StripeCustomer.objects.get(user_id=client_reference_id)
                stripe.api_key = settings.STRIPE_SECRET_KEY
                subscription = stripe.Subscription.retrieve(stripe_customer.stripeSubscriptionId)
                product = stripe.Product.retrieve(subscription.plan.product)
                product_price = subscription.plan.amount_decimal[0:3]
            # email Subscription Details

                subject = 'CogniSleep Subscription Detail'
                to = provider_email

                html_message = loader.render_to_string(
                    'email_temp/active_subscription.html',
                    {
                        'subscription': subscription,
                        'product': product,
                        'price' : product_price,
                    }
                )
                email_records(request, to, settings.EMAIL_FROM, 'CogniSleep Subscription Detail')
                send_mail(
                    subject,
                    'CogniSleep Subscription Detail',
                    settings.EMAIL_FROM,
                    [to],
                    html_message=html_message
                    ,
                )

        return HttpResponse(status=200)
    except Exception as e:
        print(e)
        return redirect('/')

def subscription_detail(request,pid=0):
    user_access = ""
    user_name = ""
    user_image = ""
    try:
        # Retrieve the subscription & product
        if pid == 0:
            provider_id = request.user.id
            print("pid 0")
            print(provider_id)
        if pid != 0 and pid is not None:
            provider_id = pid
            print("pid not 0")
            print(provider_id)
            provider = Provider.objects.get(user_id=provider_id)
            package = provider.provider_type
            user_profile = Provider.objects.get(user_id=pid)
            user_name = provider.first_name + " " + user_profile.last_name
            user_image = provider.provider_image
            provider_access = Provider_Verification.objects.get(user_id=provider_id)
            user_access = provider_access.user_position

        if StripeCustomer.objects.filter(user_id=provider_id).exists():
            print("yes exist")
            sub_status = provider.subscription_status
            product = None
            if user_profile.coupon_code:
                product = Coupon_Product_detail.objects.get(product_description__contains=user_profile.coupon_code)

            else:
                product = Product_detail.objects.get(product_name=package)

            #stripe.api_key = settings.STRIPE_SECRET_KEY
            #subscription = stripe.Subscription.retrieve(stripe_customer.stripeSubscriptionId)
            #product = stripe.Product.retrieve(subscription.plan.product)
            #product_price = subscription.plan.amount_decimal[0:3]
            # Feel free to fetch any additional data from 'subscription' or 'product'
            # https://stripe.com/docs/api/subscriptions/object
            # https://stripe.com/docs/api/products/object
            _title = settings.BASE_TITLE + ' |  Subscription Package'
            return render(request, 'pay_home.html', {
                "title": _title,
                'product': product,
                "sub_status":sub_status,
                'provider': provider_id,
                "user_access": user_access,
                "role_id": 1,
                "user_name": user_name,
                "user_image": user_image,
            })

    except StripeCustomer.DoesNotExist:
        _title = settings.BASE_TITLE + ' |  No Subscription'
        context = {
            "title": _title,
            "base_url": settings.BASE_URL,
            "link": settings.BASE_URL,
            "link_text": "Home",
            "tags": "danger",
             "user_access": user_access,
            "role_id": 1,
            "user_name": user_name,
            "user_image": user_image,
        }
        messages.error(request, "NO Subscription Available")
        return render(request, "payment_success.html", context)


def isPaymentSuccess(user_email):
    try:
        userPayment = PaymentRecord.objects.get(user_email=user_email, pyament_status="succeeded",
                                                type="payment_intent.succeeded")
        return True
    except:
        return False


class CouponAPI(APIView):
    permission_classes = [AllowAny]

    def get(self, request, id=None):
        # coupon_code = request.GET.get('code', None)
        try:
            if id is not None:

                coupon = Coupon.objects.filter(id=id)
            else:
                coupon = Coupon.objects.all().order_by("-id")

            serializer = GetCouponssSerializer(coupon, many=True)
            count = len(coupon)

            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            print(e)
            count = None
            return Response('exception_message', status=status.HTTP_400_BAD_REQUEST)

    def post(self, request, *args, **kwargs):
        try:
            print("print 1")
            code = request.data.get("code", "").lower()
            trial_period = request.data.get("trial_period", None)
            add_coupon = GetCouponssSerializer(data=request.data)
            # stripe.api_key = settings.STRIPE_SECRET_KEY

            try:
                print("print 2")
                if add_coupon.is_valid():
                    print("print 3")
                    try:
                        product_price_str = request.data['price']
                        price_in_dollars = float(product_price_str)
                        price_in_cents = int(price_in_dollars * 100)

                        if price_in_dollars == 0:
                            # Save coupon details directly without involving Stripe
                            coupon_product_detail_instance = Coupon_Product_detail(
                                code=code,
                                product_name=request.data['title'],
                                product_description=request.data['description'],
                                price=0  # Save price as 0
                            )
                            coupon_product_detail_instance.save()
                            coupons_detail = add_coupon.save()
                            coupon_product_detail_instance.coupon_id = coupons_detail.id
                            coupon_product_detail_instance.save()

                            return Response('Coupon details saved successfully', status=status.HTTP_200_OK)

                        print("product price", price_in_dollars)
                        product = stripe.Product.create(
                            name=request.data['title'],
                            description=request.data['description'],
                            metadata={
                                'product_name': request.data['title'],
                                'product_price': price_in_dollars,
                                'product_status': "active",
                                'product_description': request.data['description'],
                            },
                        )

                        # Create a subscription plan with a trial period
                        price = stripe.Price.create(
                            product=product.id,
                            nickname=request.data['title'],
                            unit_amount=price_in_cents,  # amount in cents
                            currency="usd",
                            recurring={"interval": "month"},
                        )

                        coupon_product_detail_instance = Coupon_Product_detail(
                            product_id=product.id,
                            price_id=price.id,
                            code=code,
                            product_name=product.name,
                            product_description=product.description + " and code is " + code,
                            price=price_in_dollars
                        )
                        print(price_in_dollars)
                        coupon_product_detail_instance.save()

                        print("print 7")
                    except Exception as e:
                        print("print 3", e)
                        return Response({'exception': str(e)}, status=status.HTTP_400_BAD_REQUEST)
                    print("print 8")
                    coupons_detail = add_coupon.save()
                    print("print 9")
                    coupon_product_detail_instance.coupon_id = coupons_detail.id
                    print("print 10")
                    coupon_product_detail_instance.save()
                    print("print 11")

                    return Response(GetCouponssSerializer(coupons_detail).data, status=status.HTTP_200_OK)
                else:
                    print("print 2.1")
                    return Response('coupon with this code already exists', status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                print("print 3", e)
                return Response('exception_message', status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:  # Added this line for the missing except block
            print("print 4", e)
            return Response('exception_message', status=status.HTTP_400_BAD_REQUEST)


class CouponsDeleteAPI(APIView):
    permission_classes = [AllowAny]
    def delete(self, request,product_id, *args, **kwargs):
        try:

            coupon_product_detail_instance = Coupon_Product_detail.objects.get(product_id=product_id)

            # Delete corresponding product from Stripe
            stripe.api_key = settings.STRIPE_SECRET_KEY
            stripe.Product.modify(product_id, active=False)
            coupon_product_detail_instance.delete()
            return Response('Coupon deleted successfully', status=status.HTTP_204_NO_CONTENT)
        except Coupon_Product_detail.DoesNotExist:
            return Response('Coupon not found', status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            print("Exception:", e)
            return Response('exception_message', status=status.HTTP_400_BAD_REQUEST)




class VerifyCouponCode(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        try:
            code = request.data.get("code")  # Use request.data to access POST data in DRF

            # Check if the code exists in the database
            coupon_exists = Coupon.objects.filter(code=code).exists()

            # Return the result as True or False
            return Response(coupon_exists)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)