from django.urls import path, reverse
from . import views as permission_views

urlpatterns = [
    path('userrolelist/', permission_views.UserRoleList.as_view(), name='role-list'),
    path('userrolelist/<int:pk>', permission_views.UserRoleList.as_view(), name='role-list'),
    path('userroledetails/<int:pk>', permission_views.UserRoleDetail.as_view(), name='role-detail'),
    #     -----------------------------
    path('permissions/', permission_views.PermissionList.as_view()),
    path('roles/<int:pk>/permissions/', permission_views.RolePermissionList.as_view()),
    path('users/<int:pk>/', permission_views.UserPermissionList.as_view()),
    # Permission Assignment
    # path('roles/<int:pk>/add-permission/', permission_views.AddRolePermission.as_view()),
    # path('users/<int:pk>/add-permission/', permission_views.AddUserPermission.as_view()),
    path('add/user/', permission_views.AddUser.as_view()),
    path('edit/user/', permission_views.EditUser.as_view()),
    path('delete/user/<int:id>', permission_views.DeleteUser.as_view()),
    path('all/users/', permission_views.AllUsers.as_view()),
    path('api/users/<int:user_id>/update_role/', permission_views.UpdateUserRole.as_view(), name='update-user-role'),]
