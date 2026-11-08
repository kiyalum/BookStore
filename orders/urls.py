from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    path('create/', views.order_create, name='order_create'),
    path('process/<int:order_id>/', views.payment_process, name='payment_process'),
    path('completed/<int:order_id>/', views.payment_completed, name='payment_completed'),
    path('canceled/<int:order_id>/', views.payment_canceled, name='payment_canceled'),
    path('webhook/', views.payment_webhook, name='stripe_webhook'),
]
