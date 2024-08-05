from django.contrib import admin
from .models import TakeTester_questions
from .models import TakeTester_answers

# Register your models here.

admin.site.register(TakeTester_questions)
admin.site.register(TakeTester_answers)