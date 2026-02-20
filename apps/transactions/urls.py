"""
Transactions URL configuration.
"""
from django.urls import path
from . import views

app_name = 'transactions'

urlpatterns = [
    path('', views.TransactionListView.as_view(), name='list'),
    path('<int:pk>/', views.TransactionDetailView.as_view(), name='detail'),
]
