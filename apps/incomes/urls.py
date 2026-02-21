"""
Incomes URL configuration.
"""
from django.urls import path
from . import views

app_name = 'incomes'

urlpatterns = [
    path('', views.IncomeListView.as_view(), name='list'),
]
