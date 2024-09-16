import json

from django.http import Http404
from django.shortcuts import render
from rest_framework.renderers import JSONRenderer

from . import serializers as permission_serializers, models as permission_models
from Permissions import utils as backend_utils
from rest_framework import status
from django.contrib.auth import authenticate
# from django.contrib.auth.models import User
from accounts.models import User
from rest_framework.generics import get_object_or_404
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from django.db.models import Q

#
#
# # Create your views here.
# class Role(APIView):
#     serializer_class = permission_serializers.RoleSerializer
#     permission_classes = (AllowAny,)
#
#     def post(self, request, format=None):
#         serializer = self.serializer_class(data=request.data)
#         serializer.is_valid(raise_exception=True)
#         if serializer.is_valid():
#             serializer.save()
#         return Response(
#             backend_utils.success_response(status_code=status.HTTP_200_OK, data=None,
#                                            msg='Role Added Successfully'))
#
#     def get(self, request, format=None):
#         roles = permission_models.UserRole.objects.all()
#         serializer = permission_serializers.RoleSerializer(roles, many=True)
#         return Response(
#             backend_utils.success_response(status_code=status.HTTP_200_OK, data=serializer.data,
#                                            msg='Roles Retrieved Successfully'))
#
#     def patch(self, request, pk, format=None):
#         role = permission_models.UserRole.objects.get(pk=pk)
#         serializer = permission_serializers.RoleSerializer(role, data=request.data, partial=True)
#         serializer.is_valid(raise_exception=True)
#         serializer.save()
#         return Response(
#             backend_utils.success_response(status_code=status.HTTP_200_OK, data=None,
#                                            msg='Role Updated Successfully'))
#
#     def delete(self, request, pk, format=None):
#         role = permission_models.UserRole.objects.get(pk=pk)
#         role.delete()
#         return Response(
#             backend_utils.success_response(status_code=status.HTTP_200_OK, data=None,
#                                            msg='Role Deleted Successfully'))
#
#
# class Permission(APIView):
#     serializer_class = permission_serializers.PermissionSerializer
#     permission_classes = (AllowAny,)
#
#     def post(self, request, format=None):
#         serializer = self.serializer_class(data=request.data)
#         serializer.is_valid(raise_exception=True)
#         serializer.save()
#         return Response(
#             backend_utils.success_response(status_code=status.HTTP_200_OK, data=None,
#                                            msg='Permission Added Successfully'))
#
#     def get(self, request, format=None):
#         permissions = permission_models.Module.objects.all()
#         serializer = permission_serializers.ModuleSerializer(permissions, many=True)
#         return Response(
#             backend_utils.success_response(status_code=status.HTTP_200_OK, data=serializer.data,
#                                            msg='Permissions Retrieved Successfully'))
#
#     def patch(self, request, pk, format=None):
#         permission = permission_models.Permission.objects.get(pk=pk)
#         serializer = permission_serializers.PermissionSerializer(permission, data=request.data, partial=True)
#         serializer.is_valid(raise_exception=True)
#         serializer.save()
#         return Response(
#             backend_utils.success_response(status_code=status.HTTP_200_OK, data=None,
#                                            msg='Permission Updated Successfully'))
#
#     def delete(self, request, pk, format=None):
#         permission = permission_models.Permission.objects.get(pk=pk)
#         permission.delete()
#         return Response(
#             backend_utils.success_response(status_code=status.HTTP_200_OK, data=None,
#                                            msg='Permission Deleted Successfully'))


from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import UserRole, ModulePermission, UserRolePermission
from .serializers import UserRoleSerializer, PermissionSerializer, GetUserRoleSerializer
from accounts import models as account_models
from . import permission as all_permissions, utils as permission_utils


class UserRoleList(APIView):
    permission_classes = [AllowAny]
    """
    API view to get all user roles or create a new role.
    """

    def get(self, request, format=None):
            search_query = request.query_params.get('search', None)
            print(f"Search Query: {search_query}")  # Log the search query

            if search_query:
                user_roles = UserRole.objects.filter(name__icontains=search_query)
            else:
                user_roles = UserRole.objects.all()

            serializer = GetUserRoleSerializer(user_roles, many=True)
            return Response(
                backend_utils.success_response(status_code=status.HTTP_200_OK, data=serializer.data,
                                            msg='Action Successful')
            )

    def post(self, request, format=None):
        try:
            alloted_permissions = request.data.get('permissions')
            role_name = request.data.get('name')
            role_obj = UserRole.objects.filter(name=role_name, actual_roles=True).first()
            if role_obj:
                return Response(
                    backend_utils.failure_response(status_code=status.HTTP_400_BAD_REQUEST,
                                                   msg="Role Name Already Exist"))
            role_obj = UserRole.objects.create(name=role_name, actual_roles=True)
            for permission_segment in alloted_permissions:
                module_obj = ModulePermission.objects.create(module_name=permission_segment['module_name'],
                                                             can_add=permission_segment['can_add'],
                                                             can_edit=permission_segment['can_edit'],
                                                             can_delete=permission_segment['can_delete'],
                                                             can_view=permission_segment['can_view'],
                                                             can_access=permission_segment['can_access'])
                role_obj.permissions.add(module_obj)
            return Response(
                backend_utils.success_response(status_code=status.HTTP_200_OK, data=[],
                                               msg='Role Add Action Successful'))
        except:
            return Response(
                backend_utils.failure_response(status_code=status.HTTP_400_BAD_REQUEST,
                                               msg="Failed"))

    def patch(self, request, pk, format=None):
        role = UserRole.objects.get(pk=pk)
        alloted_permissions = request.data.get('permissions', None)
        role_name = request.data.get('name', None)
        if not role_name and not alloted_permissions:
            return Response(
                backend_utils.failure_response(status_code=status.HTTP_400_BAD_REQUEST,
                                               msg="Please enter either role name or permissions"))
        if role_name:
            if role_name != role.name:
                role_obj = UserRole.objects.filter(name=role_name).first()
                if role_obj:
                    return Response(
                        backend_utils.failure_response(status_code=status.HTTP_400_BAD_REQUEST,
                                                       msg="Role Name Already Exist"))
                role.name = role_name
                role.save()
        if alloted_permissions:
            role.permissions.all().delete()
            for permission_segment in alloted_permissions:
                module_obj = ModulePermission.objects.create(module_name=permission_segment['module_name'],
                                                             can_add=permission_segment['can_add'],
                                                             can_edit=permission_segment['can_edit'],
                                                             can_delete=permission_segment['can_delete'],
                                                             can_view=permission_segment['can_view'],
                                                             can_access=permission_segment['can_access'])
                role.permissions.add(module_obj)
        return Response(
            backend_utils.success_response(status_code=status.HTTP_200_OK, data=[],
                                           msg='Role Edit Action Successful'))

    def delete(self, request, pk, format=None):
        role = UserRole.objects.get(pk=pk, actual_roles=True)
        role.permissions.all().delete()
        role.delete()
        return Response(
            backend_utils.success_response(status_code=status.HTTP_200_OK, data=[],
                                           msg='Role Delete Action Successful'))


class UserRoleDetail(APIView):
    permission_classes = [AllowAny]
    """
    API view to retrieve, update or delete a specific user role.
    """

    def get_object(self, pk):
        try:
            return UserRole.objects.get(pk=pk)
        except UserRole.DoesNotExist:
            raise Http404

    def get(self, request, pk, format=None):
        user_role = self.get_object(pk)
        serializer = UserRoleSerializer(user_role)
        json_data = permission_utils.convert_serialized_data_to_json(serializer.data)
        returning_data = permission_utils.compare_and_update_permissions(json_data)
        return Response(
            backend_utils.success_response(status_code=status.HTTP_200_OK, data=returning_data,
                                           msg='Action Successful'))

    def put(self, request, pk, format=None):
        user_role = self.get_object(pk)
        serializer = UserRoleSerializer(user_role, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                backend_utils.success_response(status_code=status.HTTP_200_OK, data=serializer.data,
                                               msg='Action Successful'))
        return Response(
            backend_utils.failure_response(status_code=status.HTTP_400_BAD_REQUEST,
                                           msg=serializer.errors))

    def delete(self, request, pk, format=None):
        user_role = self.get_object(pk)
        user_role.delete()
        return Response(
            backend_utils.success_response(status_code=status.HTTP_200_OK, data=[],
                                           msg='Action Successful'))


class PermissionList(APIView):
    permission_classes = [AllowAny]
    """
    API view to retrieve all permissions.
    """

    def get(self, request, format=None):
        permissions = all_permissions.all_permissions
        return Response(
            backend_utils.success_response(status_code=status.HTTP_200_OK, data=permissions,
                                           msg='Action Successful'))


class RolePermissionList(APIView):
    """
    API view to retrieve permissions associated with a specific role.
    """

    def get(self, request, pk, format=None):
        try:
            user_role = UserRole.objects.get(pk=pk)
            permissions = user_role.permissions.all()
            serializer = PermissionSerializer(permissions, many=True)
            # Assuming PermissionSerializer exists
            json_data = permission_utils.convert_serialized_data_to_json(serializer.data)
            returning_data = permission_utils.compare_and_update_permissions(json_data)
            return Response(
                backend_utils.success_response(status_code=status.HTTP_200_OK, data=returning_data,
                                               msg='Action Successful'))
        except UserRole.DoesNotExist:
            return Response(
                backend_utils.failure_response(status_code=status.HTTP_400_BAD_REQUEST,
                                               msg='Role not found'))


def get_user_permissions(user):
    default_permission = UserRolePermission.objects.filter(user=user).first()
    print("these are the default permission=====", default_permission)
    role_permissions = None
    user_permissions = None
    if default_permission:
        permissions = UserRole.objects.filter(name=default_permission.user_role).first()
    else:
        permissions = UserRole.objects.filter(name=user.role).first()
    if permissions:
        print("these are the permissions=====", permissions)
        print("these are the permissions=====222", permissions.permissions.all())
        serializer = PermissionSerializer(permissions.permissions.all(),
                                          many=True)
        json_data = permission_utils.convert_serialized_data_to_json(serializer.data)
        returning_data = permission_utils.compare_and_update_permissions(json_data)
        return returning_data
    return "EMPTY"


class UserPermissionList(APIView):
    permission_classes = [AllowAny]

    def get(self, request, pk, format=None):
        try:
            if not pk:
                return Response(
                    backend_utils.failure_response(
                        status_code=status.HTTP_200_OK,
                        msg='field please add id'
                    )
                )

            user = account_models.User.objects.get(id=pk)

            if user.user_role:  # Check if user has a role
                role_data = {
                    'role_id': user.user_role.id,
                    'role_name': user.user_role.name,
                    'actual_roles': user.user_role.actual_roles,
                }
            else:
                role_data = {}

            data = {
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'city': user.city,
                'state': user.state,
                'zip': user.zip,
                'birthdate': user.birthdate,
                'role': role_data,
            }

            return Response(
                backend_utils.success_response(
                    status_code=status.HTTP_200_OK,
                    data=data,
                    msg='Action Successful'
                )
            )

        except account_models.User.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

# class AddRolePermission(APIView):
#     """
#     API view to add a permission to a specific role.
#     """
#
#     def post(self, request, pk, format=None):
#         try:
#             user_role = UserRole.objects.get(pk=pk)
#             permissions = request.data.get('permissions')
#             if not permissions:
#                 return Response({'error': 'Missing permission field in request data'},
#                                 status=status.HTTP_400_BAD_REQUEST)
#             permission = ModulePermission.objects.get(pk=permissions)
#             user_role.permissions.add(permission)
#             return Response(
#                 backend_utils.success_response(status_code=status.HTTP_200_OK, data=[],
#                                                msg='Action Successful'))
#         except (UserRole.DoesNotExist, ModulePermission.DoesNotExist):
#             return Response(status=status.HTTP_404_NOT_FOUND)


# class AddUserPermission(APIView):
#     """
#     API view to assign a specific permission to a user, overriding default role permissions.
#     """
#
#     def post(self, request, pk, format=None):
#         try:
#             user = User.objects.get(pk=pk)
#             permission_id = request.data.get('permission_id')
#             if not permission_id:
#                 return Response({'error': 'Missing permission_id field in request data'},
#                                 status=status.HTTP_400_BAD_REQUEST)
#             permission = ModulePermission.objects.get(pk=permission_id)
#             # Check if permission already exists for the user (overrides default role permissions)
#             existing_permission = UserRolePermission.objects.filter(user=user,
#                                                                     user_role__permissions=permission).exists()
#             if existing_permission:
#                 return Response({'error': 'Permission already assigned to user'}, status=status.HTTP_400_BAD_REQUEST)
#             # Create a new UserRolePermission for the user and permission
#             user_role_permission = UserRolePermission.objects.create(user=user, user_role=None, permission=permission,
#                                                                      default_permission=False)
#             return Response(
#                 backend_utils.success_response(status_code=status.HTTP_200_OK, data=[],
#                                                msg='Action Successful'))
#         except (User.DoesNotExist, ModulePermission.DoesNotExist):
#             return Response(status=status.HTTP_404_NOT_FOUND)


class AddUser(APIView):
    permission_classes = [AllowAny]
    """
    API view to assign a specific permission to a user, overriding default role permissions.
    """

    def post(self, request, format=None):
        user = None
        first_name = request.data.get('first_name', None)
        last_name = request.data.get('last_name', None)
        email = request.data.get('email', None)
        city = request.data.get('city', None)
        state = request.data.get('state', None)
        zip = request.data.get('zip', None)
        birthdate = request.data.get('birthdate', None)
        default_role = request.data.get('default_role', None)
        password = request.data.get('password', None)
        role_id = request.data.get('role_id', None)
        role_name = request.data.get('role_name', None)
        # check if email already exists
        try:
            user = User.objects.get(email=email)
        except Exception as e:
            print(e)
        if user:
            return Response(
                backend_utils.failure_response(status_code=status.HTTP_400_BAD_REQUEST,
                                               msg="Email already exists"))
        if default_role and not role_id:
            return Response(
                backend_utils.failure_response(status_code=status.HTTP_400_BAD_REQUEST,
                                               msg="When Selecting Default Role then Role ID is required"))
        # if not default_role and role_name:
        role_obj = UserRole.objects.filter(name=role_name, actual_roles=True).first()
        if role_obj:
            return Response(
                backend_utils.failure_response(status_code=status.HTTP_400_BAD_REQUEST,
                                               msg="Role Name Already Exist"))
        user = User.objects.create_user(email=email, password=password)

        user_role = UserRole.objects.get(id=role_id)
        # user_profile = account_models.User.objects.create(user=user, city=city, state=state, zip=zip,
        #                                                          birth_date=birthdate, first_name=first_name, last_name=last_name)
        user.city = city
        user.state = state
        user.zip = zip
        user.birthdate = birthdate
        user.first_name = first_name
        user.last_name = last_name
        user.role_name = role_name
        user.user_role = user_role
        user.set_password(password)
        user.save()
        print("default===", default_role)
        if default_role:
            user_role_obj = UserRole.objects.get(pk=role_id)
            user.role = user_role_obj.name
            user.save()
            UserRolePermission.objects.create(user=user, user_role=user_role_obj,
                                              default_permission=True)
        elif role_name and not default_role:
            alloted_permissions = request.data.get('permissions')
            role_obj = UserRole.objects.create(name=role_name, actual_roles=False)
            for permission_segment in alloted_permissions:
                module_obj = ModulePermission.objects.create(module_name=permission_segment['module_name'],
                                                             can_add=permission_segment['can_add'],
                                                             can_edit=permission_segment['can_edit'],
                                                             can_delete=permission_segment['can_delete'],
                                                             can_view=permission_segment['can_view'],
                                                             can_access=permission_segment['can_access'])
                role_obj.permissions.add(module_obj)
            user.role = role_name
            user.save()
            UserRolePermission.objects.create(user=user, user_role=role_obj,
                                              default_permission=False)
        else:
            print("rlse===========", role_name, default_role)
        return Response(
            backend_utils.success_response(status_code=status.HTTP_200_OK, data=[],
                                           msg='User Added Successfully'))


class EditUser(APIView):
    """
    API view to assign a specific permission to a user, overriding default role permissions.
    """

    def post(self, request, format=None):
        first_name = request.data.get('first_name', None)
        last_name = request.data.get('last_name', None)
        email = request.data.get('email', None)
        city = request.data.get('city', None)
        state = request.data.get('state', None)
        zip = request.data.get('zip', None)
        birthdate = request.data.get('birthdate', None)
        default_role = request.data.get('default_role', None)
        password = request.data.get('password', None)
        role_id = request.data.get('role_id', None)
        role_name = request.data.get('role_name', None)
        # check if email already exists
        user = User.objects.filter(email=email).first()
        if user:
            return Response(
                backend_utils.failure_response(status_code=status.HTTP_400_BAD_REQUEST,
                                               msg="Email already exists"))
        if default_role and not role_id:
            return Response(
                backend_utils.failure_response(status_code=status.HTTP_400_BAD_REQUEST,
                                               msg="When Selecting Default Role then Role ID is required"))
        if not default_role and role_name:
            role_obj = UserRole.objects.filter(name=role_name, actual_roles=True).first()
            if role_obj:
                return Response(
                    backend_utils.failure_response(status_code=status.HTTP_400_BAD_REQUEST,
                                                   msg="Role Name Already Exist"))
        user = User.objects.create_user(email=email, password=password, username=email, first_name=first_name,
                                        last_name=last_name)
        user_profile = account_models.UserProfile.objects.create(user=user, city=city, state=state, zip=zip,
                                                                 birth_date=birthdate)
        user.set_password(password)
        user.save()
        print("default===", default_role)
        if default_role:
            user_role_obj = UserRole.objects.get(pk=role_id)
            user_profile.role = user_role_obj.name
            user_profile.save()
            UserRolePermission.objects.create(user=user_profile, user_role=user_role_obj,
                                              default_permission=True)
        elif role_name and not default_role:
            alloted_permissions = request.data.get('permissions')
            role_obj = UserRole.objects.create(name=role_name, actual_roles=False)
            for permission_segment in alloted_permissions:
                module_obj = ModulePermission.objects.create(module_name=permission_segment['module_name'],
                                                             can_add=permission_segment['can_add'],
                                                             can_edit=permission_segment['can_edit'],
                                                             can_delete=permission_segment['can_delete'],
                                                             can_view=permission_segment['can_view'],
                                                             can_access=permission_segment['can_access'])
                role_obj.permissions.add(module_obj)
            user_profile.role = role_name
            user_profile.save()
            UserRolePermission.objects.create(user=user_profile, user_role=role_obj,
                                              default_permission=False)
        else:
            print("rlse===========", role_name, default_role)
        return Response(
            backend_utils.success_response(status_code=status.HTTP_200_OK, data=[],
                                           msg='User Added Successfully'))


class DeleteUser(APIView):
    permission_classes = [AllowAny]
    """
    API view to assign a specific permission to a user, overriding default role permissions.
    """

    def delete(self, request, id, format=None):
        user = User.objects.get(pk=id)
        UserRolePermission.objects.filter(user=user).delete()
        user.delete()
        return Response(
            backend_utils.success_response(status_code=status.HTTP_200_OK, data=[],
                                           msg='User Deleted Successfully'))


class AllUsers(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        # Get search parameters
        search_query = request.query_params.get('search', None)

        # Initial queryset
        users = account_models.User.objects.filter(role__isnull=False)

        # Apply filter based on search query
        if search_query:
            users = users.filter(
                Q(first_name__icontains=search_query) |
                Q(last_name__icontains=search_query) |
                Q(role__icontains=search_query)
            )

        # Serialize the filtered queryset
        serializer = permission_serializers.AllUserSerializer(users, many=True)
        return Response(
            backend_utils.success_response(status_code=status.HTTP_200_OK, data=serializer.data,
                                           msg='Action Successful')
        )

class UpdateUserRole(APIView):
    permission_classes = [AllowAny]

    def patch(self, request, user_id, format=None):
        try:
            # Fetch the user by user_id
            user = account_models.User.objects.get(pk=user_id)
        except account_models.User.DoesNotExist:
            return Response(
                backend_utils.failure_response(
                    status_code=status.HTTP_404_NOT_FOUND,
                    msg="User not found"
                )
            )

        # Get the role name from the request data
        role_name = request.data.get('name', None)

        if not role_name:
            return Response(
                backend_utils.failure_response(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    msg="Please enter a role name"
                )
            )

        # Check if the role exists in UserRole model
        try:
            role = UserRole.objects.get(name=role_name)
        except UserRole.DoesNotExist:
            return Response(
                backend_utils.failure_response(
                    status_code=status.HTTP_404_NOT_FOUND,
                    msg="Role not found"
                )
            )

        # Update the user's role field
        user.role = role_name
        user.save()

        # Serialize the updated user data
        serializer = permission_serializers.AllUserSerializer(user)

        return Response(
            backend_utils.success_response(
                status_code=status.HTTP_200_OK,
                data=serializer.data,
                msg='Role updated successfully for the user'
            )
        )