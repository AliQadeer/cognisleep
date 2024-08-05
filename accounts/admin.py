from django.contrib.auth import get_user_model
from django.contrib import admin

User = get_user_model()

from django.contrib.auth.models import Group
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .forms import UserAdminCreationForm, UserAdminChangeForm
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import PatientProfile , User
from django.contrib.admin import AdminSite
from django.utils.translation import gettext_lazy


# class MyUserCreationForm(UserCreationForm):
#     class Meta:
#         model = User

class MyAdminSite(AdminSite):
    # Text to put at the end of each page's <title>.
    site_title = gettext_lazy('My site admin')

    # Text to put in each page's <h1> (and above login form).
    site_header = gettext_lazy('My administration')

    # Text to put at the top of the admin index page.
    index_title = gettext_lazy('Site administration')

admin_site = MyAdminSite()



# class ProfileInLine(admin.StackedInline):
#     model = Profile
#     can_delete= False
#     verbose_name_plural = 'profile'
#     fk_name = 'user'

#class UserAdmin(BaseUserAdmin):
class UserAdmin(BaseUserAdmin):
    # The forms to add and change user instances
    form = UserAdminChangeForm
    add_form = UserAdminCreationForm

    # The fields to be used in displaying the User model.
    # These override the definitions on the base UserAdmin
    # that reference specific fields on auth.User.
    list_display = ('email', 'admin')
    list_filter = ('admin',)
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('username', )}),
        ('Permissions', {'fields': ('admin','isprovider','active')}),
    )
    # add_fieldsets is not a standard ModelAdmin attribute. UserAdmin
    # overrides get_fieldsets to use this attribute when creating a user.
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2','isprovider')}
        ),
    )
    search_fields = ('email',)
    ordering = ('email',)
    filter_horizontal = ()

admin.site.register(User, UserAdmin)
admin.site.register(PatientProfile)

admin.site.unregister(Group)

# @admin.register(AccessToken)
# class AccessTokenAdmin(admin.ModelAdmin):
#     list_display = ('token', 'created_at')
#     search_fields = ('token',)
#     readonly_fields = ('created_at',)
#     ordering = ('-created_at',)