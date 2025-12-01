from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    # API endpoints
    path('api/count/', views.notification_count, name='count'),
    path('api/list/', views.notification_list, name='list'),
    path('api/<int:notification_id>/read/', views.mark_as_read, name='mark_read'),
    path('api/mark-all-read/', views.mark_all_as_read, name='mark_all_read'),
    
    # Page view
    path('', views.notification_page, name='page'),
]
