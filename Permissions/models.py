from django.contrib.auth.models import User
from django.db import models
from accounts import models as account_models


class UserRole(models.Model):
    name = models.CharField(max_length=50, unique=True)
    permissions = models.ManyToManyField('ModulePermission')
    actual_roles = models.BooleanField(default=False)

    # users = models.ManyToManyField(User)

    def __str__(self):
        return self.name


class ModulePermission(models.Model):
    module_name = models.CharField(max_length=50)
    can_access = models.BooleanField(default=False)
    can_add = models.BooleanField(default=False)
    can_edit = models.BooleanField(default=False)
    can_delete = models.BooleanField(default=False)
    can_view = models.BooleanField(default=False)
    can_view_sub = models.BooleanField(default=False)
    can_view_agreement = models.BooleanField(default=False)
    send_Custom_Fax_Report = models.BooleanField(default=False)
    conditions_Legend = models.BooleanField(default=False)
    update_Package = models.BooleanField(default=False)
    update_Price = models.BooleanField(default=False)




    def __str__(self):
        return f"{self.module_name}---{', '.join(permission.name for permission in self.userrole_set.all())}"


class UserRolePermission(models.Model):
    user_role = models.ForeignKey(UserRole, on_delete=models.CASCADE)
    user = models.ForeignKey(account_models.User, on_delete=models.CASCADE, unique=True, null=True, blank=True)
    default_permission = models.BooleanField(default=False)

    def __str__(self):
        if not self.default_permission:
            try:
                return self.user.role + "-------" + self.user_role.name
            except:
                return 'No ROLE Defined In UserProfile MOdel for this user' + "-------" + self.user_role.name
        else:
            return self.user.user.get_full_name() + "-------" + self.user_role.name
