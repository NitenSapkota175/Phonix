"""
Reports URL configuration.
"""
from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('', views.UserReportView.as_view(), name='user_report'),
    path('admin/', views.AdminReportView.as_view(), name='admin_report'),
]
