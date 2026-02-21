"""
KYC URL configuration.
"""
from django.urls import path
from . import views

app_name = 'kyc'

urlpatterns = [
    path('', views.KYCView.as_view(), name='upload'),
]
