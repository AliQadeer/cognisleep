from django.db import models
from django.conf import settings
from django.utils import timezone
# Create your models here.
from accounts.admin import User
from datetime import  date


class SleepDiary(models.Model):
    patient = models.ForeignKey(User, on_delete=models.CASCADE)
    week_day = models.CharField(max_length=10, null=True)
    date = models.DateField(null=True, blank=True)
    time_went_to_bed = models.CharField(max_length=10, null=True)
    lights_out = models.CharField(max_length=10, null=True)
    minutes_fall_asleep = models.IntegerField(null=True)
    out_of_bed = models.CharField(max_length=10, null=True)
    # nap_time_asleep = models.CharField(max_length=10, null=True)
    time_fell_asleep = models.CharField(max_length=10, null=True)
    time_got_up = models.CharField(max_length=10, null=True)
    minutes_fellback_sleep = models.IntegerField(null=True)
    desire_wakeup_time = models.CharField(max_length=10, null=True)
    no_of_times_awakend = models.IntegerField(null=True)
    total_time_awakened = models.IntegerField(null=True)
    number_of_naps = models.IntegerField(null=True)
    totlatime_napping_minutes = models.IntegerField(null=True)
    day_avg = models.CharField(max_length=10, null=True)
    is_updated = models.BooleanField(default=True)
    time_in_bed = models.CharField(max_length=8, null=True)
    total_sleep_time = models.CharField(max_length=8, null=True)
    sleep_efficiency = models.CharField(max_length=8, null=True)
    problem_falling_asleep = models.CharField(max_length=8, blank=True)
    overslept = models.CharField(max_length=10, blank=True)
    awake_during_night = models.CharField(max_length=8, blank=True)
    awake_too_early = models.CharField(max_length=8, blank=True)
    delayed_getting_up = models.CharField(max_length=8, blank=True)
    total_gotup_time = models.CharField(max_length=10, null=True)
    comment = models.TextField(max_length=2000, null=True)

    def __str__(self):
        return self.week_day


class VideoSessions(models.Model):
    # user_id = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.TextField()
    url = models.TextField()
    content = models.TextField()
    review_content = models.TextField()
    status = models.IntegerField()

    class Meta:
        db_table = 'video_sessions'

    def __str__(self):
        return self.title


class VideoSessionsCompleted(models.Model):
    # user_id = models.ForeignKey(User, on_delete=models.CASCADE)
    patient_id = models.IntegerField()
    completed = models.BooleanField()
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'video_session_patients'

    def __str__(self):
        return self.title


class VideoQuestions(models.Model):
    video_sessions = models.ForeignKey(VideoSessions, on_delete=models.CASCADE)
    question = models.TextField()
    main_question = models.TextField()
    correct_ans = models.TextField()
    options = models.TextField()
    status = models.IntegerField()
    type = models.IntegerField(default=1)

    class Meta:
        db_table = 'video_questions'

    def __str__(self):
        return self.question


class VideoAnswers(models.Model):
    video_questions = models.ForeignKey(VideoQuestions, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    answer = models.TextField()

    class Meta:
        db_table = 'video_answers'

    def __str__(self):
        return self.answer


class VideoViews(models.Model):
    patient_id = models.IntegerField()
    view_video = models.IntegerField()

    class Meta:
        db_table = 'patient_video_view'


class ProviderCard(models.Model):
    provider_id = models.CharField(max_length=5, null=False)
    subscription_date = models.DateTimeField(default=timezone.now)
    name_on_card = models.CharField(max_length=40, null=False)
    exp_date = models.DateField(null=False)
    cvc_code = models.CharField(max_length=3, null=False)
    card_number = models.CharField(max_length=18, null=False)

    class Meta:
        db_table = 'provider_card_detail'


class PatientEfficiency(models.Model):
    patient_id = models.CharField(max_length=5, null=False)
    week_no = models.CharField(max_length=2, null=False)
    sleep_efficiency = models.CharField(max_length=10, null=True)
    bed_time = models.CharField(max_length=10, null=True)
    sugg_wake_up = models.CharField(max_length=10, null=True)
    base_time = models.CharField(max_length=10, null=True)

    class Meta:
        db_table = 'patient_efficieny'


class SendFax(models.Model):
    patient_id = models.IntegerField(max_length=2, default=0)
    weekno = models.IntegerField(default=0)
    pre_ciq = models.BooleanField(default=False)
    post_ciq = models.BooleanField(default=False)

    class Meta:
        db_table = 'fax_send'


class Logfile(models.Model):
    user_id = models.CharField(max_length=5, null=False)
    entry_date = models.DateField(default=date.today, null=False)
    sleep_diary_date = models.DateField(null=False)
    patient_id = models.CharField(max_length=5, null=False)
    user_type = models.CharField(max_length=10, null=False)

    class Meta:
        db_table = 'log_detail'


class Providerhandbooks(models.Model):
    patient = models.ForeignKey(User, on_delete=models.CASCADE)
    patient_remark = models.CharField(max_length=2000)
    provider_remark = models.CharField(max_length=2000)
    week_number = models.IntegerField()
    date = models.DateField(auto_now_add=True)

    class Meta:
        db_table = 'provider_handbooks'