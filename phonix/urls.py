"""
URL configuration for phonix project.
"""
from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect

urlpatterns = [
    path('admin/', admin.site.urls),
    path('dashboard/', include('dashboard.urls')),
    path('investment/', include('investment.urls')),
    path('wallet/', include('wallet.urls')),
    path('', lambda request: redirect('dashboard:index')),
]
