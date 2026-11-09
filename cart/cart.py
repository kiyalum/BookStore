from decimal import Decimal
from django.conf import settings
from store.models import Book, UserCart


class Cart:
    def __init__(self, request):
        """Initialise the cart (database for authenticated users, session for guests)."""
        self.request = request
        self.session = request.session
        self.user = request.user

        if self.user.is_authenticated:
            user_cart, created = UserCart.objects.get_or_create(user=self.user)
            self.cart = user_cart.cart_data
        else:
            cart = self.session.get(settings.CART_SESSION_ID)
            if not cart:
                cart = self.session[settings.CART_SESSION_ID] = {}
            self.cart = cart

    def add(self, book, quantity=1, override_quantity=False):
        """Add a book to the cart."""
        book_id = str(book.id)
        if book_id not in self.cart:
            self.cart[book_id] = {'quantity': 0, 'price': str(book.price)}

        current_quantity = self.cart[book_id]['quantity']

        if override_quantity:
            target_quantity = quantity
        else:
            target_quantity = current_quantity + quantity

        if target_quantity > book.stock:
            if current_quantity >= book.stock:
                raise ValueError("There are no more books available.")
            else:
                raise ValueError(f"Unfortunately, there are only {book.stock} copies of this book in stock.")

        self.cart[book_id]['quantity'] = target_quantity
        self.save()

    def remove(self, book):
        """Remove a book from the cart."""
        book_id = str(book.id)
        if book_id in self.cart:
            if self.cart[book_id]['quantity'] > 1:
                self.cart[book_id]['quantity'] -= 1
            else:
                del self.cart[book_id]
            self.save()

    def remove_completely(self, book):
        """Completely remove a book from the cart."""
        book_id = str(book.id)
        if book_id in self.cart:
            del self.cart[book_id]
            self.save()

    def clear(self):
        """Remove all items from the cart."""
        self.cart = {}
        self.save()

    def save(self):
        """Save the cart (to DB if user is auth, otherwise to session)."""
        if self.user.is_authenticated:
            user_cart, created = UserCart.objects.get_or_create(user=self.user)
            user_cart.cart_data = self.cart
            user_cart.save()
        else:
            self.session[settings.CART_SESSION_ID] = self.cart
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
