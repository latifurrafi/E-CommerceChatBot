from django.urls import path
from . import views

urlpatterns = [
    path('api/message/', views.process_message, name='process_message'),
]