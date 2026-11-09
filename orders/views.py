import stripe
from django.conf import settings
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.mail import send_mail
from cart.cart import Cart
from .forms import OrderCreateForm
from .models import Order, OrderItem

stripe.api_key = settings.STRIPE_SECRET_KEY


def order_create(request):
    cart = Cart(request)

    if not cart:
        messages.error(request, "Your cart is empty.")
        return redirect('cart:cart_detail')

    for item in cart:
        book = item['book']
        cart_quantity = item['quantity']

        if cart_quantity > book.stock:
            if book.stock == 0:
                messages.error(request, f"Unfortunately, the book '{book.title}' is sold out and no longer available.")
            else:
                messages.error(
                    request,
                    f"Unfortunately, the book '{book.title}' is only available in stock in quantity {book.stock} pieces."
                )
            cart.add(book=book, quantity=book.stock, override_quantity=True, check_stock=False)
            return redirect('cart:cart_detail')

    if request.method == 'POST':
        form = OrderCreateForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    order = form.save(commit=False)
                    if request.user.is_authenticated:
                        order.user = request.user
                    order.save()
                    line_items = []
                    for item in cart:
                        book = item['book']
                        quantity = item['quantity']
                        OrderItem.objects.create(
                            order=order,
                            book=book,
                            price=item['price'],
                            quantity=quantity
                        )
                        line_items.append({
                            'price_data': {
                                'currency': 'UAH',
                                'product_data': {
                                    'name': book.title,
                                },
                                'unit_amount': int(item['price'] * 100),
                            },
                            'quantity': quantity,
                        })
                    request.session['order_id'] = order.id
                    checkout_session = stripe.checkout.Session.create(
                        line_items=line_items,
                        mode='payment',
                        success_url=request.build_absolute_uri(reverse('orders:payment_completed', args=[order.id])),
                        cancel_url=request.build_absolute_uri(reverse('orders:payment_canceled', args=[order.id])),
                    )
                return redirect(checkout_session.url, code=303)
            except Exception as ex:
                messages.error(request, f"An error occurred while creating the order: {ex}")
                return redirect('cart:cart_detail')
    else:
        initial_data = {}
        if request.user.is_authenticated:
            initial_data = {
                'first_name': getattr(request.user, 'first_name', ''),
                'last_name': getattr(request.user, 'last_name', ''),
                'email': getattr(request.user, 'email', ''),
                'phone': getattr(request.user, 'phone', ''),
                'address': getattr(request.user, 'address', ''),
                'city': getattr(request.user, 'city', ''),
            }
        form = OrderCreateForm(initial=initial_data)

    return render(request, 'orders/order_create.html', {'cart': cart, 'form': form})


def payment_process(request, order_id):
    """Create session for paid in Stripe Checkout"""
    order = get_object_or_404(Order, id=order_id)
    if request.method == 'POST':
        success_url = request.build_absolute_uri(reverse("orders:payment_completed", args=[order.id]))
        cancel_url = request.build_absolute_uri(reverse("orders:payment_canceled", args=[order.id]))

        session_data = {
            'line_items': [],
            'mode': 'payment',
            'client_reference_id': order.id,
            'success_url': success_url,
            'cancel_url': cancel_url,
        }

        for item in order.items.all():
            session_data['line_items'].append({
                'price_data': {
                    'unit_amount': int(item.price * 100),
                    'currency': "UAH",
                    'product_data': {
                        'name': item.book.title,
                    },
                },
                'quantity': item.quantity,
            })

        try:
            session = stripe.checkout.Session.create(**session_data)
            order.stripe_id = session.id
            order.save()
            return redirect(session.url, code=303)
        except Exception as ex:
            return render(request, 'orders/payment_errors.html', {'error': str(ex)})

    return render(request, 'orders/process.html', {'order': order})


def payment_completed(request, order_id):
    """Page for success_url"""
    order = get_object_or_404(Order, id=order_id)
    if not order.paid:
        with transaction.atomic():
            order.paid = True
            order.status = 'paid'
            order.save()
            for item in order.items.all():
                book = item.book
                book.stock = max(0, book.stock - item.quantity)
                book.save()

        send_mail(
            subject=f'Order #{order.id} Successful',
            message=f'Hi {order.first_name},\n\nThank you for your purchase! Your order ID is {order.id}.',
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@store.com'),
            recipient_list=[order.email],
            fail_silently=True,
        )

    Cart(request).clear()
    return render(request, 'orders/completed.html', {'order': order})


def payment_canceled(request, order_id=None):
    """Page for cancel_url"""
    return render(request, 'orders/canceled.html', {'order_id': order_id})


@csrf_exempt
def payment_webhook(request):
    """Safety handler for Stripe webhooks"""
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    event = None

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError:
        return HttpResponse(status=400)

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        if session.get('mode') == 'payment' and session.get('payment_status') == 'paid':
            order_id = session.get('client_reference_id')
            if order_id:
                try:
                    order = Order.objects.get(id=order_id)
                    if not order.paid:
                        order.paid = True
                        order.status = 'paid'
                        order.save(update_fields=['paid', 'status'])
                        send_mail(
                            subject=f'Order #{order.id} Successful',
                            message=f'Hi {order.first_name},\n\nThank you for your purchase! Your order ID is {order.id}.',
                            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@store.com'),
                            recipient_list=[order.email],
                            fail_silently=True,
                        )
                except Order.DoesNotExist:
                    return HttpResponse(status=404)

    return JsonResponse({'status': 'success'})
