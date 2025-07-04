from django.contrib import admin

from .forms import CategoryForm
from .models import Category, Product, Cart, CartItem, Order, OrderItem, FAQ


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    form = CategoryForm
    ordering = ('id', '-parent',)
    search_fields = ('name',)
    search_help_text = 'Поиск по названию категории'


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('id', 'description', 'category', 'price', 'in_stock', 'quantity', 'reserved')
    list_filter = ('in_stock', 'category')
    search_fields = ('description',)
    search_help_text = 'Поиск по описанию товара'


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'is_ordered', 'updated_at')
    list_filter = ('is_ordered',)
    search_fields = ('user__username',)
    search_help_text = 'Поиск по имени пользователя'
    inlines = (CartItemInline,)


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'cart', 'product', 'quantity', 'price')
    list_filter = ('cart', 'product')
    search_fields = ('product__description',)
    search_help_text = 'Поиск по описанию товара'


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'full_name', 'status', 'total_amount', 'created_at')
    list_filter = ('status',)
    ordering = ('-created_at',)
    search_fields = ('full_name', 'address', 'phone', 'cart__user__username')
    search_help_text = 'Поиск по ФМО, почте, адресу, телефону или имени пользователя в Telegram'
    inlines = (OrderItemInline,)


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'order', 'product', 'quantity', 'price')
    list_filter = ('order',)
    search_fields = ('product__description',)
    search_help_text = 'Поиск по описанию товара'


@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ('question', 'answer')
    search_fields = ('question', 'answer')
    search_help_text = 'Поиск по вопросу или ответу'
