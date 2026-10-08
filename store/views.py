from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from .models import Book, Category
from .forms import BookForm, UserRegistrationForm


class UserRegisterView(CreateView):
    form_class = UserRegistrationForm
    template_name = 'store/register.html'
    success_url = reverse_lazy('store:login')


class CustomLoginView(LoginView):
    template_name = 'store/login.html'
    redirect_authenticated_user = True


class CustomLogoutView(LogoutView):
    next_page = reverse_lazy('store:book_list')


class BookListView(ListView):
    model = Book
    template_name = "store/book_list.html"
    context_object_name = "books"
    paginate_by = 4

    def get_queryset(self):
        queryset = super().get_queryset().select_related("category")
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
        category = self.object.category
        response = super().form_valid(form)
        if category and not category.books.exists():
            category.delete()
        return response
