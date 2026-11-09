from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from .models import Book, Category, UserCart
from .forms import BookForm, UserRegistrationForm
from cart.forms import CartAddBookForm



class UserRegisterView(CreateView):
    form_class = UserRegistrationForm
    template_name = 'store/register.html'
    success_url = reverse_lazy('store:login')


class CustomLoginView(LoginView):
    template_name = 'store/login.html'
    redirect_authenticated_user = True

    def form_valid(self, form):
        response = super().form_valid(form)
        user = self.request.user
        session_cart = self.request.session.get('cart', {})
        if session_cart:
            user_cart, created = UserCart.objects.get_or_create(user=user)
            for book_id, item_data in session_cart.items():
                try:
                    book = Book.objects.get(id=int(book_id))
                except Book.DoesNotExist:
                    continue

                guest_quantity = item_data['quantity']

                if book_id in user_cart.cart_data:
                    current_quantity = user_cart.cart_data[book_id]['quantity']
                    new_quantity = current_quantity + guest_quantity
                    user_cart.cart_data[book_id]['quantity'] = min(new_quantity, book.stock)
                else:
                    item_data['quantity'] = min(guest_quantity, book.stock)
                    user_cart.cart_data[book_id] = item_data
            user_cart.save()
            if 'cart' in self.request.session:
                del self.request.session['cart']
        return response


class CustomLogoutView(LogoutView):
    next_page = reverse_lazy('store:book_list')

    def dispatch(self, request, *args, **kwargs):
        cart_data = request.session.get('cart')
        response = super().dispatch(request, *args, **kwargs)
        if cart_data:
            request.session['cart'] = cart_data
            request.session.modified = True
        return response


class BookListView(ListView):
    model = Book
    template_name = "store/book_list.html"
    context_object_name = "books"
    paginate_by = 4

    def get_queryset(self):
        queryset = super().get_queryset().filter(is_active=True).select_related("category")
        query = self.request.GET.get("q")
        if query:
            queryset = queryset.filter(title__icontains=query)

        category_id = self.request.GET.get("category")
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["categories"] = Category.objects.all()
        return context


class BookDetailView(DetailView):
    model = Book
    template_name = "store/book_detail.html"
    context_object_name = "book"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['cart_product_form'] = CartAddBookForm(initial={'quantity': 1, 'override': False})
        return context


class BookCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Book
    form_class = BookForm
    template_name = "store/book_form.html"
    success_url = reverse_lazy("store:book_list")
    permission_required = 'store.add_book'


class BookUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Book
    form_class = BookForm
    template_name = "store/book_form.html"
    success_url = reverse_lazy("store:book_list")
    permission_required = 'store.change_book'

    def get_initial(self):
        initial = super().get_initial()
        if self.object.category:
            initial["category_name"] = self.object.category.name
        return initial


class BookDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Book
    template_name = "store/book_confirm_delete.html"
    success_url = reverse_lazy("store:book_list")
    permission_required = 'store.delete_book'

    def form_valid(self, form):
        self.object = self.get_object()
        self.object.is_active = False
        self.object.save()

        category = self.object.category
        if category:
            active_books_count = category.books.filter(is_active=True).count()
            if active_books_count == 0:
                category.delete()

        return redirect(self.success_url)
