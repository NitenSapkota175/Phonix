"""
Wallets URL configuration.
"""
from django.urls import path
from . import views

app_name = 'wallets'

urlpatterns = [
    path('', views.WalletOverviewView.as_view(), name='overview'),
    path('deposit/', views.DepositView.as_view(), name='deposit'),
    path('withdraw/', views.WithdrawView.as_view(), name='withdraw'),
    path('swap/', views.SwapView.as_view(), name='swap'),
    path('transfer/', views.TransferView.as_view(), name='transfer'),
]
