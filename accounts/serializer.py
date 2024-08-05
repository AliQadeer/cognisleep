from rest_framework import serializers
from django.contrib.auth import get_user_model, authenticate

from .models import Provider_type, Provider,RefPatient
from payments.models import Product_detail

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'email', 'first_login', 'is_active', 'is_admin')


class CreateUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('email', 'password')
        extra_kwargs = {'password': {'write_only': True}, }

        def create(self, validated_data):
            user = User.objects.create(**validated_data)
            user.set_password(validated_data['password'])
            return user


class LoginSerializer(serializers.Serializer):
    email = serializers.CharField()
    password = serializers.CharField(
        style={'input_type': 'password'}, trim_whitespace=False)

    def validate(self, data):
        print(data)
        email = data.get('email')
        password = data.get('password')

        if email and password:
            if User.objects.filter(email=email).exists():

                user = authenticate(request=self.context.get('request'), email=email, password=password)
                print(user)

            else:
                msg = {
                    'detail': 'Email not found.',
                    'status': False

                }
                raise serializers.ValidationError(msg)

            if not user:
                msg = {
                    'detail': 'Email and password is not matching, Try again.',
                    'status': False
                }

                raise serializers.ValidationError(msg, code='autherization')

        else:

            msg = {
                'detail': 'Email and password is not found in request, Try again.',
                'status': False

            }
            raise serializers.ValidationError(msg, code='autherization')

        data['user'] = user
        return data


class LoginFormSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()

    def validate(self, data):
        email = data.get('email')
        password = data.get('password')

        if not email or not password:
            raise serializers.ValidationError('Email and password are required.')

        return data


class PasswordChangeSerializer(serializers.Serializer):
    password1 = serializers.CharField(required=True)
    password2 = serializers.CharField(required=True)
    email = serializers.EmailField()
    role_id = serializers.IntegerField()


class LoginFormProviderSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(max_length=128)


class SignupProviderSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    contact_no = serializers.CharField()
    providertype = serializers.ChoiceField(choices=["Associated PA, APRN", "MD/DO", "PHD", "Independent PA, APRN"])
    doctor_ref_number = serializers.CharField(required=False)
    primary_care_doctor_name = serializers.CharField(required=False)
    flag = serializers.IntegerField()


class ProviderTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product_detail
        fields = ["id", "product_name"]


class UserDetailSerializer(serializers.ModelSerializer):
    first_name = serializers.SerializerMethodField('get_firstName')
    last_name = serializers.SerializerMethodField('get_lastName')
    contact_no = serializers.SerializerMethodField('get_contact')
    package_type = serializers.SerializerMethodField('get_package_type')
    provider_id = serializers.SerializerMethodField('get_provider_id')

    def get_provider_id(self, obj):
        try:
            provider_id = Provider.objects.get(user_id=obj.id).id
        except:
            provider_id = None

        return provider_id

    def get_firstName(self, obj):
        try:
            first_name = Provider.objects.get(user_id=obj.id).first_name
        except:
            first_name = None

        return first_name

    def get_lastName(self, obj):
        try:
            last_name = Provider.objects.get(user_id=obj.id).last_name
        except:
            last_name = None

        return last_name

    def get_contact(self, obj):
        try:
            contact_no = Provider.objects.get(user_id=obj.id).contact_no
        except:
            contact_no = None

        return contact_no

    def get_package_type(self, obj):
        try:
            contact_no = Provider.objects.get(user_id=obj.id).package_type
        except:
            contact_no = None

        return contact_no

    class Meta:
        model = User
        fields = ["first_name", "last_name", "contact_no", "email", "package_type"]


class ProviderRegSerializer(serializers.ModelSerializer):
    def update(self, instance, validated_data):
        instance.practice_name = validated_data.get('email', instance.practice_name)
        instance.practice_phone_number = validated_data.get('content', instance.practice_phone_number)
        instance.practice_address = validated_data.get('created', instance.practice_address)
        instance.fax_no = validated_data.get('created', instance.fax_no)
        return instance

    class Meta:
        model = Provider
        fields = ('practice_name', 'practice_phone_number', 'practice_address', 'fax_no')




class RefpatientSerializer(serializers.ModelSerializer):
    class Meta:
        model = RefPatient
        fields = ['user', 'provider_id', 'first_name','last_name','driving_license_front_img',
                  'driving_license_back_img']

# class SignupProviderSerializer(serializers.Serializer):
#     email = serializers.EmailField()
#     password = serializers.CharField()
#     first_name = serializers.CharField()
#     last_name = serializers.CharField()
#     contact_no = serializers.CharField()
#     providertype = serializers.ChoiceField(choices=["Associated PA, APRN", "MD/DO", "PHD", "Independent PA, APRN"])
#     doctor_ref_number = serializers.CharField(required=False)
#     primary_care_doctor_name = serializers.CharField(required=False)
#     flag = serializers.IntegerField()
class SignupProviderSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    contact_no = serializers.CharField()
    providertype = serializers.ChoiceField(choices=["Associated PA, APRN", "MD/DO", "PHD", "Independent PA, APRN"])
    package_type = serializers.CharField()
    doctor_ref_number = serializers.CharField(required=False)
    primary_care_doctor_name = serializers.CharField(required=False)
    flag = serializers.IntegerField()