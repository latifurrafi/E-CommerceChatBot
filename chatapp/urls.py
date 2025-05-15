from django.urls import path 
from . import views

urlpatterns = [
    path('', views.chat_view, name='chat'),
    path('api/message/', views.process_message, name='process_message')
]