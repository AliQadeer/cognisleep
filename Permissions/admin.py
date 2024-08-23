from django.contrib import admin
from .models import *

# Register your models here.
# admin.site.register(Action)
# admin.site.register(UserRole)
# admin.site.register(Module)
# admin.site.register(Permission)

admin.site.register(UserRole)
admin.site.register(ModulePermission)
admin.site.register(UserRolePermission)

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
#         permissions = permission_models.Permission.objects.all()
#         serializer = permission_serializers.PermissionSerializer(permissions, many=True)
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
