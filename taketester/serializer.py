from rest_framework.serializers import (ChoiceField, BooleanField, ModelSerializer, DateField, ValidationError,
                                        SerializerMethodField, ImageField, CharField, EmailField, IntegerField,FloatField,)

from rest_framework import serializers

from taketester.models import Question_new, Options_new, UserAnswer


class OptionsSerializer(ModelSerializer):

    class Meta:
        model = Options_new
        fields = ["id","name"]
class QuestionSerializer(ModelSerializer):
    options = SerializerMethodField('get_options',required=False)

    def get_options(self, obj):
        try:
            options = Options_new.objects.filter(question_new_id = obj.id)
            options_serialzier = OptionsSerializer(options, many=True)
            return options_serialzier.data
        except Exception as e:
            print(e)
            return None
    class Meta:
        model = Question_new
        fields = ["id","name","is_pre","is_post","options"]

class UserAnswerSerializer(ModelSerializer):

    class Meta:
        model = UserAnswer
        fields = '__all__'



class OptionsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Options_new
        fields = '__all__'

class SaveQuestionSerializer(serializers.ModelSerializer):



    class Meta:
        model = Question_new
        fields = ["id","name","is_pre","is_post","year"]