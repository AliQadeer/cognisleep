# Generated by Django 3.2.9 on 2024-08-19 17:27

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ModulePermission',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('module_name', models.CharField(max_length=50)),
                ('can_access', models.BooleanField(default=False)),
                ('can_add', models.BooleanField(default=False)),
                ('can_edit', models.BooleanField(default=False)),
                ('can_delete', models.BooleanField(default=False)),
                ('can_view', models.BooleanField(default=False)),
                ('can_view_sub', models.BooleanField(default=False)),
                ('can_view_agreement', models.BooleanField(default=False)),
                ('send_Custom_Fax_Report', models.BooleanField(default=False)),
                ('conditions_Legend', models.BooleanField(default=False)),
                ('update_Package', models.BooleanField(default=False)),
                ('update_Price', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='UserRole',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, unique=True)),
                ('actual_roles', models.BooleanField(default=False)),
                ('permissions', models.ManyToManyField(to='Permissions.ModulePermission')),
            ],
        ),
        migrations.CreateModel(
            name='UserRolePermission',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('default_permission', models.BooleanField(default=False)),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, unique=True)),
                ('user_role', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='Permissions.userrole')),
            ],
        ),
    ]
