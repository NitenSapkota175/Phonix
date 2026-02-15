from django.urls import path
from . import views

app_name = 'investment'

urlpatterns = [
    path('', views.subscription_list, name='list'),
    path('buy/', views.buy_subscription, name='buy'),
]
