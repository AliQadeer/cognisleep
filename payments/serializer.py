from .models import Coupon
from rest_framework import serializers

class GetCouponssSerializer(serializers.ModelSerializer):
    class Meta:
        model = Coupon
        fields = '__all__'