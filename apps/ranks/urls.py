"""
Ranks URL configuration.
"""
from django.urls import path
from . import views

app_name = 'ranks'

urlpatterns = [
    path('', views.RankOverviewView.as_view(), name='overview'),
    path('payouts/', views.RankPayoutListView.as_view(), name='payouts'),
]
