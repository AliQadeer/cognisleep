from django.db import models
from django.utils import timezone

from django.core.validators import RegexValidator

from accounts.models import User
from datetime import  date


# Create your models here.

class TakeTester_questions(models.Model):
    question = models.TextField()
    question_slug = models.TextField(default='')
    timestamp = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.question


class TakeTester_answers(models.Model):
    question = models.ForeignKey(TakeTester_questions, on_delete=models.CASCADE)
    answer = models.CharField(max_length=200)
    timestamp = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.answer





class DealBreakerQuestions(models.Model):
    question = models.TextField()
    deal_breaker_id = models.IntegerField(default=0)
    type = models.IntegerField(default=0)
    timestamp = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.question


class DealBreakerNotes(models.Model):
    title = models.ForeignKey(DealBreakerQuestions, on_delete=models.CASCADE)
    message = models.CharField(max_length=200)
    timestamp = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.message


class Guest_User(models.Model):
    alphanumeric = RegexValidator(r'[a-zA-Z][a-zA-Z ]+', 'Only alpha characters are allowed.')

    first_name = models.CharField(max_length=200, validators=[alphanumeric])
    last_name = models.CharField(max_length=200, validators=[alphanumeric])
    email = models.EmailField()
    phone = models.CharField(max_length=15)
    txt_insomnia_points = models.CharField(max_length=200)
    txt_insomnia_msg = models.CharField(max_length=500)
    result_value = models.IntegerField(null=True)
    timestamp = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.first_name




class Question(models.Model):
    qid = models.CharField(max_length=4, primary_key=True, editable=False)
    question = models.TextField()
    option1 = models.TextField()
    option2 = models.TextField()
    option3 = models.TextField()
    option4 = models.TextField()
    year = models.IntegerField()


class PatientAnswer(models.Model):
    patient_id = models.ForeignKey(User,on_delete=models.CASCADE)
    qid = models.CharField(max_length=4, primary_key=True, editable=False)
    pre_answer = models.TextField()
    post_answer = models.TextField()
    result = models.TextField()

class Question_new(models.Model):
    name = models.TextField()
    is_pre = models.BooleanField(default=False)
    is_post = models.BooleanField(default=False)
    year = models.IntegerField()

class Options_new(models.Model):
    question_new = models.ForeignKey(Question_new,on_delete=models.CASCADE)
    name = models.CharField(max_length=100, null=True, blank=True)

class UserAnswer(models.Model):
    user = models.ForeignKey(User,on_delete=models.CASCADE)
    question = models.ForeignKey(Question_new,on_delete=models.CASCADE)
    option_selected = models.ForeignKey(Options_new,on_delete=models.CASCADE)
    date = models.DateField(default=date.today, blank=True)
