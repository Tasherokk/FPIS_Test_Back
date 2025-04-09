import re
from django.utils import timezone

from ckeditor.fields import RichTextField
from django.contrib.auth.base_user import BaseUserManager, AbstractBaseUser
from django.contrib.auth.models import User, AbstractUser, PermissionsMixin
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models
from markdownx.models import MarkdownxField
from tinymce.models import HTMLField

from django.conf import settings


class Subject(models.Model):
    HISTORY = 'HIS'
    MATH = 'MAT'
    PHYSICS = 'PHY'
    CHEMISTRY = 'CHE'
    READING_LITERACY = 'RL'
    MATH_LITERACY = 'ML'
    WORLDWIDE_HISTORY = 'WHI'
    GEOGRAPHY = 'GEO'
    LAW_FUNDAMENTALS = 'LF'
    FOREIGN_LANGUAGE = 'FL'
    BIOLOGY = 'BIO'
    KAZAKH_LANGUAGE = 'KZ'
    KAZAKH_LITERATURE = 'KL'
    INFORMATICS = 'INF'
    RUSSIAN_LANGUAGE = 'RU'
    RUSSIAN_LITERATURE = 'RUL'

    SUBJECT_CHOICES = [
        (HISTORY, 'Тарих'),
        (MATH, 'Математика'),
        (PHYSICS, 'Физика'),
        (CHEMISTRY, 'Химия'),
        (READING_LITERACY, 'Оқу сауаттылығы'),
        (MATH_LITERACY, 'Математикалық сауаттылық'),
        (WORLDWIDE_HISTORY, 'Дүниежүзі тарихы'),
        (GEOGRAPHY, 'География'),
        (LAW_FUNDAMENTALS, 'Құқық негіздері'),
        (FOREIGN_LANGUAGE, 'Шет тілі'),
        (BIOLOGY, 'Биология'),
        (KAZAKH_LANGUAGE, 'Қазақ тілі'),
        (KAZAKH_LITERATURE, 'Қазақ әдебиеті'),
        (INFORMATICS, 'Информатика'),
        (RUSSIAN_LANGUAGE, 'Русский язык'),
        (RUSSIAN_LITERATURE, 'Русская литература'),
    ]

    name = models.CharField(max_length=3, choices=SUBJECT_CHOICES)
    variant = models.IntegerField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f'{self.get_name_display()} - Variant {self.variant}'


class Question(models.Model):
    SINGLE_CHOICE = 'SC'
    MULTIPLE_CHOICE = 'MC'
    MATCHING = 'MT'

    QUESTION_TYPES = [
        (SINGLE_CHOICE, 'Single Choice'),
        (MULTIPLE_CHOICE, 'Multiple Choice'),
        (MATCHING, 'Matching'),
    ]

    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='questions')
    text = models.TextField()
    question_type = models.CharField(max_length=2, choices=QUESTION_TYPES)

    def __str__(self):
        return self.text


class Answer(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='answers')
    text = models.TextField(blank=False, null=False)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return self.text

class MatchingPair(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='matching_pairs')
    left_side_1 = models.TextField(blank=False, null=False, help_text="Первая неизменяемая левая часть")
    left_side_2 = models.TextField(blank=False, null=False, help_text="Вторая неизменяемая левая часть")
    # left_side_1 = models.CharField(max_length=200, help_text="Первая неизменяемая левая часть")
    # left_side_2 = models.CharField(max_length=200, help_text="Вторая неизменяемая левая часть")
    right_option_1 = models.TextField(blank=False, null=False, help_text="Первый вариант для выбора")
    right_option_2 = models.TextField(blank=False, null=False, help_text="Второй вариант для выбора")
    right_option_3 = models.TextField(blank=False, null=False, help_text="Третий вариант для выбора")
    right_option_4 = models.TextField(blank=False, null=False, help_text="Четвёртый вариант для выбора")

    # Теперь правильные варианты хранятся как int (от 1 до 4)
    correct_for_left_1 = models.IntegerField(choices=[(1, 'Первый'), (2, 'Второй'), (3, 'Третий'), (4, 'Четвертый')])
    correct_for_left_2 = models.IntegerField(choices=[(1, 'Первый'), (2, 'Второй'), (3, 'Третий'), (4, 'Четвертый')])

    def __str__(self):
        return f'{self.left_side_1}, {self.left_side_2}'


class TestResult(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='test_results')
    date_taken = models.DateTimeField(auto_now_add=True)
    total_score = models.IntegerField()

    def __str__(self):
        return f'Имя: {self.user}, Баллы: {self.total_score}'

class SubjectResult(models.Model):
    test_result = models.ForeignKey(TestResult, on_delete=models.CASCADE, related_name='subject_results')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    score = models.IntegerField()

    def __str__(self):
        return f'{self.subject} - {self.score}'


class School(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class CustomUserManager(BaseUserManager):
    def create_user(self, full_name, iin, **extra_fields):
        if not full_name:
            raise ValueError("The FIO field must be set")
        if not iin:
            raise ValueError("The IIN field must be set")
        user = self.model(full_name=full_name, iin=iin, **extra_fields)
        user.save(using=self._db)
        return user

    def create_superuser(self, full_name, iin, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        user = self.create_user(full_name, iin, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

class CustomUser(AbstractBaseUser, PermissionsMixin):
    USAGE_TYPE_CHOICES = [
        ('single', 'Single'),
        ('subscription', 'Subscription'),
    ]

    full_name = models.CharField(max_length=255, verbose_name="ФИО")
    iin = models.CharField(max_length=12, unique=True, validators=[RegexValidator(r'^\d{12}$', 'IIN must be 12 digits')], verbose_name="ИИН")

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    # Новые поля
    created_at = models.DateTimeField(default=timezone.now, verbose_name="Дата создания")
    usage_type = models.CharField(max_length=20, choices=USAGE_TYPE_CHOICES, default='single',
                                  verbose_name="Тип использования")

    school = models.ForeignKey(
        School,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='users'
    )

    USERNAME_FIELD = 'iin'
    REQUIRED_FIELDS = ['full_name']

    objects = CustomUserManager()

    def __str__(self):
        return self.full_name
