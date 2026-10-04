from django.urls import path
from . import views

app_name = 'store'

urlpatterns = [
    path('', views.book_list, name='book_list'),
    path("book/add/", views.book_create, name="book_create"),
    path('book/<int:pk>/delete/', views.book_delete, name='book_delete'),
]
