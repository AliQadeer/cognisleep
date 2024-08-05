from rest_framework import serializers
from .models import Providerhandbooks

class ProviderhandbooksSerializer(serializers.ModelSerializer):
    class Meta:
        model = Providerhandbooks
        fields = '__all__'
