from decimal import Decimal
from django.conf import settings
from store.models import Book

class Cart:
    def __init__(self, request):
        """Initialise the cart."""
        self.session = request.session
        cart = self.session.get(settings.CART_SESSION_ID)
        if not cart:
            cart = self.session[settings.CART_SESSION_ID] = {}
        self.cart = cart

    def add(self, book, quantity=1, override_quantity=False):
        """Add a book to the cart."""
        book_id = str(book.id)
        if override_quantity not in self.cart:
            self.cart[book_id] = {
                'quantity': 0,
                'price': str(book.price)
            }
        if override_quantity:
            self.cart[book_id]['quantity'] = quantity
        else:
            self.cart[book_id]['quantity'] += quantity

    def remove(self, book):
        """Remove a book from the cart."""
        book_id = str(book.id)
        if book_id in self.cart:
            del self.cart[book_id]
            self.save()

    def clear(self):
        """Remove all items from the cart."""
        del self.session[settings.CART_SESSION_ID]
        self.save()

    def save(self):
        """Save the cart."""
        self.session.modified = True

    def __iter__(self):
        """Iterate over the cart."""
        books_ids = self.cart.keys()
        books = Book.objects.filter(id__in=books_ids)
        cart = self.cart.copy()
        for book in books:
            cart[str(book.id)]['book'] = book

        for item in cart.values():
            item['price'] = Decimal(item['price'])
            item['total_price'] = item['price'] * item['quantity']
            yield item

    def __len__(self):
        """Return the number of items in the cart."""
        return sum(item['quantity'] for item in self.cart.values())

    def get_total_price(self):
        """Return the total price of the cart."""
        return sum(Decimal(item['price']) * item['quantity'] for item in self.cart.values())
