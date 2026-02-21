"""
Trading URL configuration.
"""
from django.urls import path
from . import views

app_name = 'trading'

urlpatterns = [
    path('', views.TradeListView.as_view(), name='list'),
    path('activate/', views.TradeActivateView.as_view(), name='activate'),
]
