import stripe
from django.conf import settings
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.db import transaction
from django.core.mail import send_mail
from cart.cart import Cart
from .forms import OrderCreateForm
from .models import Order, OrderItem

stripe.api_key = settings.STRIPE_SECRET_KEY


def order_create(request):
    cart = Cart(request)
    if not cart:
        return redirect('cart:cart_detail')

    if request.method == 'POST':
        form = OrderCreateForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                order = form.save(commit=False)
                if request.user.is_authenticated:
                    order.customer = request.user
                order.status = 'created'
                order.paid = False
                order.save()

                for item in cart:
                    OrderItem.objects.create(
                        order=order,
                        book=item['book'],
                        price=item['price'],
                        quantity=item['quantity']
                    )

            success_url = request.build_absolute_uri(reverse('orders:payment_success', args=[order.id])) + f'?order_id={order.id}'
            cancel_url = request.build_absolute_uri(reverse('orders:payment_cancel', args=[order.id]))

            session_data = {
                'payment_method_types': ['card'],
                'line_items': [],
                'mode': 'payment',
                'success_url': success_url,
                'cancel_url': cancel_url,
            }

            for item in cart:
                session_data['line_items'].append({
                    'price_data': {
                        'currency': 'UAH',
                        'product_data': {
                            'name': item['book'].title,
                        },
                        'unit_amount': int(item['price'] * 100),
                    },
                    'quantity': item['quantity'],
                })

            checkout_session = stripe.checkout.Session.create(**session_data)
            order.stripe_id = checkout_session.id
            order.save()

            return redirect(checkout_session.url, code=303)
    else:
        form = OrderCreateForm()

    return render(request, 'orders/order_create.html', {'cart': cart, 'form': form})


def payment_success(request):
    order_id = request.GET.get('order_id')
    if order_id:
        order = get_object_or_404(Order, id=order_id)
        order.paid = True
        order.status = 'paid'
        order.save()

        send_mail(
            subject=f'Order #{order.id} Successful',
            message=f'Hi {order.first_name},\n\nThank you for your purchase! Your order ID is {order.id}.',
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@store.com'),
            recipient_list=[order.email],
            fail_silently=True,
        )

        Cart(request).clear()
        return render(request, 'orders/success.html', {'order': order})
    return redirect('store:book_list')


def payment_cancel(request):
    return render(request, 'orders/cancel.html')
