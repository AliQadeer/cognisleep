from django.db import models
from accounts.admin import User

# Create your models here.
#from accounts.admin import User

class PaymentRecord(models.Model):

  #  user_id = models.ForeignKey(User, on_delete=models.CASCADE)
    session_id = models.TextField()
    user_id = models.IntegerField()
    payment_id = models.TextField()
    paid = models.TextField()
    user_name = models.TextField()
    pyament_status = models.TextField()
    amount = models.TextField()
    user_email = models.TextField()
    user_package = models.TextField()
    customer_id = models.TextField()
    type = models.TextField()
    created = models.TextField()

    class Meta:
        db_table = 'payment'

    def __str__(self):
        return self.session_id

class Product_detail(models.Model):
  product_id = models.CharField(max_length=100, null=False)
  price_id = models.CharField(max_length=100, null=False)
  # plan_id = models.CharField(max_length=100, null=False)
  product_name = models.CharField(max_length=100 ,null=False)
  product_description= models.CharField(max_length=1000, null=True)
  price = models.CharField(max_length=3, null=False)

  class Meta:
    db_table = "product_detail"

class Coupon(models.Model):
  title = models.CharField(max_length=250, null=True, blank=True)
  description = models.TextField(null=True, blank=True)
  code = models.CharField(max_length=250, null=True, blank=True, unique=True)
  trial_period = models.CharField(max_length=250, null=True, blank=True)
  price = models.CharField(max_length=250, null=True, blank=True)
  expires = models.CharField(max_length=250, null=True, blank=True)
  type = models.CharField(max_length=250, null=True, blank=True)
  unlimited = models.BooleanField(default=False)

  def __str__(self):
    return self.title


class Coupon_Product_detail(models.Model):
  product_id = models.CharField(max_length=100, null=False)
  price_id = models.CharField(max_length=100, null=False)
  code = models.CharField(max_length=100, null=False)
  product_name = models.CharField(max_length=100 ,null=False)
  product_description= models.CharField(max_length=1000, null=True)
  price = models.CharField(max_length=50, null=False)

  class Meta:
    db_table = "Coupon_Product_detail"