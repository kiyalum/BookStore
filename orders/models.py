from django.db import models
from store.models import CustomUser, Book


class Order(models.Model):
    STATUS_CHOICES = (
        ('created', 'Created'),
        ('paid', 'Paid'),
        ('shipped', 'Shipped'),
        ('completed', 'Completed'),
        ('canceled', 'Canceled'),
    )
    customer = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='orders',
                                 null=True, blank=True, verbose_name="User")
    first_name = models.CharField(max_length=50, verbose_name="First Name")
    last_name = models.CharField(max_length=50, verbose_name="Last Name")
    email = models.EmailField(verbose_name="Email")
    address = models.CharField(max_length=250, verbose_name="Address")
    city = models.CharField(max_length=100, verbose_name="City")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")
    status = models.CharField(verbose_name="Status", choices=STATUS_CHOICES, max_length=20, default="created")
    paid = models.BooleanField(default=False, verbose_name="Paid")
    stripe_id = models.CharField(max_length=250, blank=True, null=True, verbose_name="Stripe ID")

    class Meta:
        verbose_name = "Order"
        verbose_name_plural = "Orders"
        ordering = ['-created_at']

    def __str__(self):
        return f"Order #{self.id}"

    def get_total_cost(self):
        return sum(item.get_cost() for item in self.items.all())


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE, verbose_name="Order")
    book = models.ForeignKey(Book, related_name='order_items', on_delete=models.PROTECT, verbose_name="Book")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Price")
    quantity = models.PositiveIntegerField(default=1, verbose_name="Quantity")

    class Meta:
        verbose_name = "Order Item"
        verbose_name_plural = "Order Items"

    def __str__(self):
        return f"Book #{self.id} in order #{self.order.id}"

    def get_cost(self):
        return self.price * self.quantity
