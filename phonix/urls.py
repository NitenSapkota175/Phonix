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
    path('ranks/', include('ranks.urls')),
    path('', lambda request: redirect('dashboard:index')),
]

# Custom error handlers
handler404 = 'phonix.views.error_404'
handler500 = 'phonix.views.error_500'
handler403 = 'phonix.views.error_403'
