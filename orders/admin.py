from django.contrib import admin
from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    raw_id_fields = ['book']
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'first_name', 'last_name', 'email', 'address', 'city', 'paid', 'created_at']
    list_filter = ['paid', 'created_at', 'updated_at']
    search_fields = ['first_name', 'last_name', 'email']
    inlines = [OrderItemInline]
