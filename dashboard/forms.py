from django import forms
from django.contrib.auth.forms import ReadOnlyPasswordHashField, UserCreationForm
from .models import User, SleepDiary


class SleepDiaruForm(forms.ModelForm):
    class Meta:
        model = SleepDiary
        widgets = {
            'date': forms.DateInput(attrs={
                'class': '',
                'data-date-format': 'yyyy-mm-dd',
                'type': 'text',
                'autocomplete': 'off'
            }),
            'time_went_to_bed': forms.DateInput(attrs={
                'class': '',
                'data-time-format': 'hh:mm p',
                'name':'time',
                'type': 'time',
                'autocomplete': 'off'
            }),
            #'total_gotup_time': forms.DateInput(attrs={
            #    'class': '',
            #    'data-time-format': 'hh:mm p',
            #    'name': 'time',
            #    'type': 'time',
            #    'autocomplete': 'off'
            #}),
            'lights_out': forms.DateInput(attrs={
                'class': '',
                'data-time-format': 'hh:mm p',
                'name': 'time',
                'type': 'time',
                'autocomplete': 'off'
            }),
            #'time_fell_asleep': forms.DateInput(attrs={
            #   'class': '',
            #    'data-time-format': 'hh:mm p',
            #    'name': 'time',
            #   'type': 'time',
            #   'autocomplete': 'off'
            #}),
            'time_got_up': forms.DateInput(attrs={
                'class': '',
                'data-time-format': 'hh:mm p',
                'name': 'time',
                'type': 'time',
                'autocomplete': 'off'
            }),
            'desire_wakeup_time': forms.DateInput(attrs={
                'class': '',
                'data-time-format': 'hh:mm p',
                'name': 'time',
                'type': 'time',
                'autocomplete': 'off'
            }),
            'out_of_bed': forms.DateInput(attrs={
                'class': '',
                'data-time-format': 'hh:mm p',
                'name': 'time',
                'type': 'time',
                'autocomplete': 'off'
            })
        }
        fields = [
            'patient',
            'date',
            #'total_gotup_time',
            'time_went_to_bed',
            'lights_out',
            'minutes_fall_asleep',
            #'time_fell_asleep',
            'time_got_up',
            'desire_wakeup_time',
            'number_of_naps',
            'totlatime_napping_minutes',
            'minutes_fellback_sleep',
            'no_of_times_awakend',
            'out_of_bed',
            'total_time_awakened'
        ]
        labels = {
            #'date': "Date <span style='font-size: 12px;'>(Please select the day from the menu above.)</span>",
            'date': "Date",
            'time_went_to_bed': "Time Went To Bed",
            #'total_gotup_time': "Total Gotup Time",
            #'time_fell_asleep': "Time you fell asleep (estimate)",
            'time_got_up': "Time you woke up",
            'no_of_times_awakend': "How Many Times You Woke Up",
            'out_of_bed': "Got Up From Bed",
            'total_time_awakened' : "Total Minutes Awake During The Night",
            'lights_out' : "Lights Out",
            'minutes_fall_asleep' : "Minutes To Fall Asleep",
            'desire_wakeup_time' : "Desired Wake Up Time",
            'number_of_naps' : "Number Of Naps",
            'totlatime_napping_minutes' : "Total Time Napping In Minutes",
            'minutes_fellback_sleep' : "Minutes You Fell Back To Sleep"
        }

    