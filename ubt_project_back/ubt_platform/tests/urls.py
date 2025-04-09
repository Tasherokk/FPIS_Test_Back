# urls.py
from django.urls import path
from rest_framework.authtoken.views import obtain_auth_token

from .views import GenerateTestView, SubmitAnswersView, CustomAuthToken

urlpatterns = [
    path('generate_test/', GenerateTestView.as_view(), name='generate_test'),
    path('submit_answers/', SubmitAnswersView.as_view(), name='submit_answers'),
    path('login/', CustomAuthToken.as_view(), name='api_token_auth'),
]