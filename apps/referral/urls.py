"""
Referral URL configuration.
"""
from django.urls import path
from . import views

app_name = 'referral'

urlpatterns = [
    path('', views.ReferralDashboardView.as_view(), name='dashboard'),
    path('team/', views.TeamListView.as_view(), name='team'),
]
