# serializers.py
from django.contrib.auth.models import User
from rest_framework import serializers
from .models import Subject, Question, Answer, MatchingPair, TestResult, SubjectResult, CustomUser


class AnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Answer
        fields = ['id', 'text']

class MatchingPairSerializer(serializers.ModelSerializer):
    class Meta:
        model = MatchingPair
        fields = '__all__'

class QuestionSerializer(serializers.ModelSerializer):
    answers = AnswerSerializer(many=True, read_only=True)
    matching_pairs = MatchingPairSerializer(many=True, read_only=True)

    class Meta:
        model = Question
        fields = ['id', 'text', 'question_type', 'answers', 'matching_pairs']

class SubjectSerializer(serializers.ModelSerializer):
    questions = QuestionSerializer(many=True, read_only=True)

    class Meta:
        model = Subject
        fields = ['id', 'name', 'variant', 'questions']

class SubjectResultSerializer(serializers.ModelSerializer):
    subject = SubjectSerializer(read_only=True)

    class Meta:
        model = SubjectResult
        fields = ['subject', 'score']

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'iin', 'full_name']

class TestResultSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    subject_results = SubjectResultSerializer(many=True, read_only=True)

    class Meta:
        model = TestResult
        fields = ['id', 'user', 'date_taken', 'total_score', 'subject_results']