import asyncio
from decimal import Decimal

from aiogram.types import (
    Message,
    PreCheckoutQuery,
    LabeledPrice,
)
from aiogram import Router, types, F
from django.db import transaction
from asgiref.sync import sync_to_async

from src.exceptions.insufficient_product import InsufficientStockError
from src.logger import logger
from ..config import YOOKASSA_PROVIDER_TOKEN, ORDERS_CSV_PATH
from src.utils.address import format_address
from src.utils.export_orders import save_to_csv_async
from store.models import Cart, CartItem, Order, OrderItem, Product
from users.models import TelegramUser

router = Router()


@sync_to_async
def reserve_items(items: list[CartItem]):
    with transaction.atomic():
        for item in items:
            # Блокируем строку продукта
            product = Product.objects.select_for_update().get(pk=item.product.pk)

            # Правильный расчет доступного количества
            available = product.quantity - product.reserved

            # Проверяем достаточно ли товара
            if available < item.quantity:
                raise InsufficientStockError(
                    product,
                    available=available,
                    requested=item.quantity
                )

            # Резервируем товар
            product.reserved += item.quantity
            product.save(update_fields=['reserved'])
            logger.debug(f"Зарезервировано {item.quantity} шт. {product.description} для заказа")


@sync_to_async
def cancel_reservation(order: Order):
    with transaction.atomic():
        items = OrderItem.objects.filter(order=order).select_related('product')
        for item in items:
            product = item.product
            product.reserved -= item.quantity
            if product.reserved < 0:
                product.reserved = 0
            product.save(update_fields=['reserved'])


@sync_to_async
def confirm_order(order: Order):
    with transaction.atomic():
        # Получаем все товары заказа
        items = OrderItem.objects.filter(order=order).select_related('product')

        for item in items:
            product = item.product

            # Списание товара
            product.quantity -= item.quantity
            product.reserved -= item.quantity
            product.in_stock = product.quantity > 0
            product.save(update_fields=['quantity', 'reserved', 'in_stock'])


@router.callback_query(F.data == 'order')
async def checkout(call: types.CallbackQuery):
    if call.from_user.is_bot:
        return
    user, _ = await TelegramUser.objects.aupdate_or_create(chat_id=call.message.chat.id, defaults={
        'username': call.message.chat.username,
        'first_name': call.message.chat.first_name,
        'last_name': call.message.chat.last_name
    })
    logger.info(f"Пользователь {call.from_user.id} хочет оформить заказ")
    cart = await Cart.objects.filter(user__chat_id=call.message.chat.id, is_ordered=False).aget()
    items = [ci async for ci in CartItem.objects.filter(cart=cart).select_related('product').all()]
    total = int(sum(Decimal(item.product.price) * item.quantity for item in items) * 100)  # в копейках

    active_order = await Order.objects.filter(
        cart__user__chat_id=call.message.chat.id,
        status='pending'
    ).aget()

    if active_order:
        # Отменяем предыдущий резерв
        await cancel_reservation(active_order)
        # Помечаем заказ как отмененный
        active_order.status = 'canceled'
        await active_order.asave()
        logger.info(f"Отменен предыдущий заказ #{active_order.id}")

    new_order, created = await Order.objects.aupdate_or_create(
        cart=cart,
        defaults={
            'status': 'pending',
            'total_amount': total / 100
        }
    )

    if not created:
        await OrderItem.objects.filter(order=new_order).adelete()
    logger.info(f"Создан заказ #{new_order.id} на сумму {total / 100} руб.")
    #
    try:
        # Резервируем товары
        await reserve_items(items)
        logger.info(f"Товары зарезервированы для заказа #{new_order.id}")

        # Создаем позиции заказа
        order_items = [
            OrderItem(
                order=new_order,
                product=item.product,
                quantity=item.quantity,
                price=item.product.price
            )
            for item in items
        ]
        await OrderItem.objects.abulk_create(order_items)
        #     # Отправляем счет на оплату
        await call.message.bot.send_invoice(
            chat_id=call.message.chat.id,
            title='Ваш заказ',
            description=f'Оплата заказа #{new_order.id}',
            payload=f'order_{new_order.id}',
            provider_token=YOOKASSA_PROVIDER_TOKEN,
            currency='RUB',
            prices=[LabeledPrice(label='Товары', amount=total)],
            need_name=True,
            need_phone_number=True,
            need_shipping_address=True,
            is_flexible=False,
        )


    except InsufficientStockError as e:
        error_msg = (
            f"❌ Не удалось зарезервировать товар:\n"
            f"• {e.product.description}\n"
            f"Доступно: {e.available}, Заказано: {e.requested}"
        )
        await call.answer(error_msg, show_alert=True)
        logger.warning(str(e))
    except Exception as e:
        logger.exception(f"Ошибка при создании заказа: {str(e)}")
        if 'new_order' in locals():
            await cancel_reservation(new_order)
            await call.answer("❌ Не удалось оформить заказ. Скорее всего, слишком большая стоимость. Попробуйте снова.")


@router.pre_checkout_query(F.invoice_payload.startswith('order_'))
async def pre_checkout(pre_checkout_query: PreCheckoutQuery):
    # Подтверждаем оплату
    logger.info(f"Пользователь {pre_checkout_query.from_user.id} хочет оплатить заказ")

    try:
        payload = pre_checkout_query.invoice_payload
        order_id = int(payload.split('_')[1])

        order = await Order.objects.select_related('cart').aget(id=order_id)

        if order.status != 'pending':
            raise ValueError("Заказ уже обработан")

        # Обновляем данные доставки
        shipping = pre_checkout_query.order_info.shipping_address
        order.full_name = pre_checkout_query.order_info.name
        order.phone = pre_checkout_query.order_info.phone_number
        order.address = format_address(shipping)
        await order.asave(update_fields=['full_name', 'phone', 'address'])
        logger.info(f"Данные доставки обновлены для заказа #{order_id}")
        async for item in order.items.select_related('product'):
            product = item.product
            available = product.quantity - (product.reserved - item.quantity)
            if available < item.quantity:
                raise InsufficientStockError(product, product.quantity, product.reserved)

        # Подтверждаем оплату
        await pre_checkout_query.answer(ok=True)
        logger.info(f"Заказ #{order_id} оплачен")

    except (Order.DoesNotExist, ValueError, InsufficientStockError) as e:
        error_message = "❌ Ошибка при оплате заказа"
        if isinstance(e, InsufficientStockError):
            error_message = f"❌ Товара '{e.product.description}' недостаточно на складе. Осталось {e.product.quantity - e.product.reserved}"
        logger.error(f"Ошибка pre_checkout: {error_message}")
        if 'order' in locals():
            await cancel_reservation(order)
        await pre_checkout_query.answer(ok=False, error_message=error_message[:200])
    except Exception as e:
        logger.exception("Неизвестная ошибка в pre_checkout")
        await pre_checkout_query.answer(
            ok=False,
            error_message="❌ Внутренняя ошибка сервера"
        )


@router.message(F.successful_payment)
async def successful_payment(message: Message):
    payment = message.successful_payment
    order_id = int(payment.invoice_payload.split('_')[1])
    logger.info(f"Счет #{order_id} оплачен, подтверждаем заказ")
    try:
        order = await Order.objects.select_related('cart').aget(id=order_id)

        # 1. Подтверждаем заказ и списываем товары
        await confirm_order(order)

        # 2. Обновляем статус заказа
        order.status = 'paid'
        order.payment_id = payment.provider_payment_charge_id
        await order.asave(update_fields=['status', 'payment_id'])

        # 3. Помечаем корзину как оплаченную
        order.cart.is_ordered = True
        await order.cart.asave(update_fields=['is_ordered'])

        # 4. Сохраняем в CSV
        asyncio.create_task(save_to_csv_async(order, ORDERS_CSV_PATH))

        await message.answer("✅ Заказ успешно оплачен!")
        logger.info(f"Заказ #{order_id} полностью обработан")

    except Exception as e:
        logger.exception(f"Ошибка при обработке оплаты заказа #{order_id}")
        await message.answer("❌ Произошла ошибка при обработке заказа")
