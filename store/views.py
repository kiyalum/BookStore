from django.shortcuts import render, redirect, get_object_or_404
from .forms import BookForm
from .models import Book, Category


def book_list(request):
    books = Book.objects.select_related("category").all()
    categories = Category.objects.all()

    context = {
        "books": books,
        "categories": categories,
    }
    return render(request, "store/book_list.html", context)

def book_create(request):
    if request.method == "POST":
        form = BookForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("store:book_list")
    else:
        form = BookForm()
    return render(request, "store/book_form.html", {"form": form})


def book_delete(request, pk):
    book = get_object_or_404(Book, pk=pk)
    if request.method == 'POST':
        book.delete()
        return redirect('store:book_list')
    return render(request, 'store/book_confirm_delete.html', {'book': book})
