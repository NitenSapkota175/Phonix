"""
Accounts URL configuration (template views).
"""
from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('register/', views.RegisterView.as_view(), name='register'),
    path('verify-email/<str:token>/', views.VerifyEmailView.as_view(), name='verify_email'),
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('change-password/', views.ChangePasswordView.as_view(), name='change_password'),
    path('set-transaction-password/', views.SetTransactionPasswordView.as_view(), name='set_txn_password'),
    path('resend-verification/', views.ResendVerificationView.as_view(), name='resend_verification'),
]
