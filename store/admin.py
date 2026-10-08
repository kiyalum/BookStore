from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Book, Category, CustomUser


class BookInline(admin.TabularInline):
    model = Book
    extra = 1


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name",)
    inlines = [BookInline]


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ("title", "author", "price", "stock", "category")
    list_filter = ("category", "author")
    search_fields = ("title", "author", "description")
    list_editable = ("price", "stock")
    list_per_page = 20


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ("email", "username", "phone", "is_staff", "is_superuser")
    search_fields = ("email", "username", "phone")
    list_filter = ("is_staff", "is_superuser", "is_active")

    # Додаємо поле phone у форму редагування користувача в адмінці
    fieldsets = UserAdmin.fieldsets + (
        ("Additional Info", {"fields": ("phone",)}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ("Additional Info", {"fields": ("email", "phone",)}),
    )
