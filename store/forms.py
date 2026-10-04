from django import forms
from django.utils.text import slugify
from .models import Book, Category


class BookForm(forms.ModelForm):
    category_name = forms.CharField(
        max_length=255,
        label="Category",
        widget=forms.TextInput(
            attrs={
                  "class": "form-control",
                  "placeholder": "Enter category name",
            }
        ),
    )

    class Meta:
        model = Book
        fields = ["title", "author", "price", "description", "stock"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "author": forms.TextInput(attrs={"class": "form-control"}),
            "price": forms.NumberInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
            "stock": forms.NumberInput(attrs={"class": "form-control"}),
        }

    def save(self, commit=True):
        cat_name = self.cleaned_data["category_name"].strip()

        cat_slug = slugify(cat_name)

        category, created = Category.objects.get_or_create(
            name__iexact=cat_name, defaults={"name": cat_name, "slug": cat_slug}
        )

        book = super().save(commit=False)
        book.category = category
        if commit:
            book.save()
        return book
