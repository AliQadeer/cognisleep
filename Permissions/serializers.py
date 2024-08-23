from rest_framework import serializers
from .models import UserRole, ModulePermission, UserRolePermission
from accounts import models as account_models


class GetUserRoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserRole
        fields = ('id', 'name', 'actual_roles')


class UserRolePermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserRolePermission
        fields = '__all__'


class PermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModulePermission
        fields = '__all__'


class UserRoleSerializer(serializers.ModelSerializer):
    permissions = serializers.SerializerMethodField('get_permissions', read_only=True)

    def get_permissions(self, obj):
        permissions = obj.permissions.all()
        serializers_data = PermissionSerializer(permissions, many=True).data
        return serializers_data

    class Meta:
        model = UserRole
        fields = '__all__'


class AllUserSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField('get_user', read_only=True)
    role_id = serializers.SerializerMethodField('get_role_id', read_only=True)

    def get_user(self, obj):
        user = obj.username
        return user

    def get_role_id(self, obj):
        role_id = obj.role
        return role_id

    class Meta:
        model = account_models.User
        fields = ['id', 'user', 'role', 'role_id','email','first_name','last_name',]
