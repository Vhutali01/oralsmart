from django.urls import path
from . import views

app_name = 'tips'

urlpatterns = [
    path('', views.tips_list, name='tips_list'),  # Public access
]