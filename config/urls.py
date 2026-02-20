"""
Root URL configuration for Phonix platform.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect


urlpatterns = [
    path('admin/', admin.site.urls),

    # App URLs
    path('', lambda request: redirect('dashboard:index'), name='home'),
    path('accounts/', include('apps.accounts.urls', namespace='accounts')),
    path('dashboard/', include('apps.dashboard.urls', namespace='dashboard')),
    path('wallets/', include('apps.wallets.urls', namespace='wallets')),
    path('trading/', include('apps.trading.urls', namespace='trading')),
    path('referral/', include('apps.referral.urls', namespace='referral')),
    path('incomes/', include('apps.incomes.urls', namespace='incomes')),
    path('transactions/', include('apps.transactions.urls', namespace='transactions')),
    path('ranks/', include('apps.ranks.urls', namespace='ranks')),
    path('kyc/', include('apps.kyc.urls', namespace='kyc')),
    path('support/', include('apps.support.urls', namespace='support')),
    path('reports/', include('apps.reports.urls', namespace='reports')),

    # DRF API token endpoints
    path('api/token/', include('apps.accounts.api_urls')),
]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Custom error handlers
handler404 = 'apps.core.views.error_404'
handler500 = 'apps.core.views.error_500'
handler403 = 'apps.core.views.error_403'
