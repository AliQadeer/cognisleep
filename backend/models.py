from django.db import models
from django.utils import timezone
from accounts.admin import User

# Create your models here.
class Subscriptionpackage(models.Model):
    date = models.DateField(default=timezone.now)
    package_name = models.CharField(max_length=80, null=True)
    no_free_months = models.IntegerField(default=0)
    no_discounted_months = models.IntegerField(default=0)
    discounted_price = models.IntegerField(default=0)
    base_price = models.IntegerField(default=0)
    package_detail = models.CharField(max_length=500, null=True)

    class Meta:
        db_table = 'subscription_package'

class StripeCustomer(models.Model):
    user = models.OneToOneField(to=User, on_delete=models.CASCADE)
    stripeCustomerId = models.CharField(max_length=255)
    stripeSubscriptionId = models.CharField(max_length=255)

    class Meta:
        db_table = 'stripe_customer'
    def __str__(self):
        return self.user.username