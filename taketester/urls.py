from django.urls import path, include, re_path
from .views import (
    thankyou, cogni_questionsv2, cogni_questions, cogni_answer, is_submited,create_ciq_report ,save_question
, add_question, ciq_report, ciq_report_by_provider, custom_fax_send
)

urlpatterns = [
    path('cogni_questionsv2', cogni_questionsv2, name='cogni-questionsv2-home'),
    path('thankyou/', thankyou, name='thankyou'),
    path('cogni_questions', cogni_questions, name='cogni_questions'),
    path('cogni_answer', cogni_answer, name='cogni_answer'),
    path('is_submited_quest/<int:id>/<str:flg>/', is_submited, name='is_submited_quest'),
    path('report/<int:pid>', create_ciq_report, name='create_ciq_report'),
    path('is_submited_quest/<int:id>', is_submited, name='is_submited_quest'),
    path('save_question', save_question, name='save_question'),
    path('add_question/',add_question ),
    path('ciq_report/', ciq_report),
    path('view_ciq/<int:pid>/', ciq_report_by_provider),
    path('custom_fax_send/<int:id>/<int:start_week>/<int:fromDay>/<int:end_week>/<int:toDay>', custom_fax_send),

]
