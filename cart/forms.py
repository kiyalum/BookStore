from django import forms


class CartAddBookForm(forms.Form):
    quantity = forms.IntegerField(
        min_value=1,
        initial=1,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'style': 'width: 100px;'})
    )
    override = forms.BooleanField(required=False, initial=False, widget=forms.HiddenInput)

    def __init__(self, *args, **kwargs):
        self.book = kwargs.pop('book', None)
        super().__init__(*args, **kwargs)

    def clean_quantity(self):
        quantity = self.cleaned_data['quantity']
        if self.book and quantity > self.book.stock:
            raise forms.ValidationError(
                f"Unfortunately, there are only {self.book.stock} copies of this book in stock."
            )
        return quantity
