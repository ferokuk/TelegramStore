from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models

from users.models import TelegramUser


class Category(models.Model):
    name = models.CharField(max_length=255, verbose_name='Название')
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='children',
                               verbose_name='Родительская категория')

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'

    def clean(self):
        if self.parent and self.parent.parent:
            raise ValidationError(
                f'Максимальная глубина вложенности категорий — 1 уровень. '
                f'У категории {self.parent} уже есть родительская категория {self.parent.parent}.')

    def save(self, *args, **kwargs):
        self.full_clean()
        # чтобы категория не стала сама себе родителем
        if self.id and self.parent and self.id == self.parent.id:
            self.parent = None
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Product(models.Model):
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='products', verbose_name='Категория')
    description = models.TextField(blank=True, verbose_name='Описание', max_length=2000)
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Цена, руб.',
                                validators=[MinValueValidator(Decimal('0.01'))])
    image = models.ImageField(upload_to='products/', blank=True, null=True, verbose_name='Изображение')
    quantity = models.PositiveIntegerField(default=0, verbose_name='Количество')
    reserved = models.PositiveIntegerField(default=0, verbose_name='Зарезервировано')
    in_stock = models.BooleanField(default=False, verbose_name='В наличии')

    def save(self, *args, **kwargs):
        self.in_stock = self.quantity > 0
        super().save(*args, **kwargs)

    class Meta:
        ordering = ['id']
        verbose_name = 'Товар'
        verbose_name_plural = 'Товары'

    def __str__(self):
        return self.description


class Cart(models.Model):
    user = models.ForeignKey(TelegramUser, null=True, blank=True, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')
    is_ordered = models.BooleanField(default=False, verbose_name='Заказ создан')

    class Meta:
        verbose_name = 'Корзина'
        verbose_name_plural = 'Корзины'

    def __str__(self):
        return f'Cart {self.id}' if self.user is None else f'Cart of {self.user}'


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items', verbose_name='Корзина')
    product = models.ForeignKey(Product, on_delete=models.PROTECT, verbose_name='Товар')
    quantity = models.PositiveIntegerField(default=1, verbose_name='Количество')
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Цена',
                                validators=[MinValueValidator(Decimal('0.01'))])

    class Meta:
        unique_together = ('cart', 'product')
        verbose_name = 'Товар в корзине'
        verbose_name_plural = 'Товары в корзине'

    def __str__(self):
        return f'{self.quantity} x {self.product.description}'


class Order(models.Model):
    cart = models.OneToOneField(Cart, on_delete=models.PROTECT, related_name='order', verbose_name='Корзина')
    full_name = models.CharField(max_length=255, verbose_name='Полное имя')
    phone = models.CharField(max_length=20, verbose_name='Телефон')
    address = models.TextField(max_length=200, verbose_name='Адрес')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Общая сумма',
                                       validators=[MinValueValidator(Decimal('0.01'))])
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    payment_id = models.CharField(max_length=255, null=True, blank=True, verbose_name='ID платежа')
    status = models.CharField(
        max_length=20,
        choices=[('new', 'New'), ('paid', 'Paid'), ('shipped', 'Shipped'), ('cancelled', 'Cancelled')],
        default='new',
        verbose_name='Статус'
    )

    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'

    @property
    def user(self):
        return self.cart.user

    def __str__(self):
        return f'Order {self.id} - {self.status}'


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items', verbose_name='Заказ')
    product = models.ForeignKey(Product, on_delete=models.PROTECT, verbose_name='Товар')
    quantity = models.PositiveIntegerField(verbose_name='Количество')
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Цена',
                                validators=[MinValueValidator(Decimal('0.01'))])

    class Meta:
        verbose_name = 'Товар в заказе'
        verbose_name_plural = 'Товары в заказе'

    def __str__(self):
        return f'{self.quantity} x {self.product.description}'


class FAQ(models.Model):
    question = models.CharField(max_length=255, db_index=True, verbose_name='Вопрос')
    answer = models.TextField(verbose_name='Ответ')

    class Meta:
        verbose_name = 'Часто задаваемый вопрос'
        verbose_name_plural = 'Часто задаваемые вопросы'

    def __str__(self):
        return self.question[:20]
