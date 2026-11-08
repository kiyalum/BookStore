from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from django.contrib import messages
from store.models import Book
from .cart import Cart
from .forms import CartAddBookForm


@require_POST
def cart_add(request, book_id):
    cart = Cart(request)
    book = get_object_or_404(Book, id=book_id)
    form = CartAddBookForm(request.POST or None, book=book)
    if request.method == 'POST':
        if not request.POST.get('quantity') or form.is_valid():
            quantity = form.cleaned_data['quantity'] if form.is_valid() else 1
            override = form.cleaned_data.get('override', False) if form.is_valid() else False
            try:
                cart.add(
                    book=book,
                    quantity=quantity,
                    override_quantity=override
                )
            except ValueError as ex:
                messages.error(request, str(ex))
        else:
            messages.error(request, "Error adding product.")

    return redirect('cart:cart_detail')


@require_POST
def cart_remove(request, book_id):
    cart = Cart(request)
    book = get_object_or_404(Book, id=book_id)
    cart.remove(book)
    return redirect('cart:cart_detail')


def cart_detail(request):
    cart = Cart(request)
    return render(request, 'cart/cart_detail.html', {'cart': cart})


@require_POST
def cart_clear(request):
    cart = Cart(request)
    cart.clear()
    return redirect('cart:cart_detail')
