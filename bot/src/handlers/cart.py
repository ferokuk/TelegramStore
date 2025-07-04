import asyncio

from aiogram import types, F

from store.models import CartItem, Product, Cart
from users.models import TelegramUser
from ..keyboards.cart_kb import build_cart_view
from aiogram import Router
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from ..logger import logger
from ..states.states import CartStates

router = Router()


async def get_cart_items(chat_id: int) -> list[CartItem]:
    cart = await Cart.objects.filter(user__chat_id=chat_id, is_ordered=False).afirst()
    if not cart:
        return []
    return [ci async for ci in CartItem.objects.filter(cart=cart).select_related('product')]


@router.callback_query(F.data.startswith('add_item_'))
async def ask_quantity(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    product_id = int(callback.data.split('_')[2])
    await state.update_data(
        product_id=product_id,
        origin_chat_id=callback.message.chat.id,
        origin_message_id=callback.message.message_id
    )
    sent = await callback.message.answer("Введите количество товара:")
    await state.update_data(prompt_msg_id=sent.message_id)
    await state.set_state(CartStates.waiting_for_quantity)


@router.message(CartStates.waiting_for_quantity)
async def process_quantity(message: Message, state: FSMContext):
    data = await state.get_data()
    product_id = data['product_id']
    prompt_id = data.get('prompt_msg_id')
    try:
        quantity = int(message.text)
        if quantity < 1:
            raise ValueError
    except ValueError:
        msg = await message.reply("Пожалуйста, введите корректное число (больше 0).")
        await asyncio.sleep(1)
        await msg.delete()
        return
    user_id = message.from_user.id
    user = await TelegramUser.objects.aget(chat_id=user_id)
    cart, _ = await Cart.objects.aget_or_create(user=user, is_ordered=False)
    try:
        item = await CartItem.objects.aget(cart=cart, product_id=product_id)

        item.quantity += quantity
        await item.asave(update_fields=['quantity'])

    except CartItem.DoesNotExist:
        product = await Product.objects.aget(pk=product_id)
        await CartItem.objects.acreate(
            cart=cart,
            product=product,
            quantity=quantity,
            price=product.price
        )

    sent: Message = await message.answer(f"✅ Добавлено в корзину")
    await state.clear()
    await asyncio.sleep(1)
    try:
        await message.bot.delete_messages(
            chat_id=message.chat.id,
            message_ids=[prompt_id, message.message_id, sent.message_id]
        )
    except Exception:
        logger.exception(
            "Ошибка при удалении одного из сообщений: "
            f"prompt_id={prompt_id}, "
            f"user_msg={message.message_id}, "
            f"bot_msg={sent.message_id}"
        )


@router.callback_query(F.data.startswith('remove_item_'))
async def remove_item(call: types.CallbackQuery):
    item_id = int(call.data.split('_')[2])
    cart = await Cart.objects.filter(user__chat_id=call.message.chat.id, is_ordered=False).aget()
    item = await CartItem.objects.filter(id=item_id, cart=cart).aget()
    await item.adelete()
    items = await get_cart_items(call.message.chat.id)
    text, kb = build_cart_view(items)
    await call.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    await call.answer("✅ Товар удалён")


@router.callback_query(F.data == 'cart')
@router.message(F.text == '/cart')
async def show_cart(update: types.CallbackQuery | types.Message):
    if isinstance(update, types.CallbackQuery):
        message = update.message
    else:
        message = update
    items = await get_cart_items(message.chat.id)
    text, kb = build_cart_view(items)
    if isinstance(update, types.CallbackQuery):
        await message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    else:
        await message.answer(text, reply_markup=kb, parse_mode="HTML")


@router.callback_query(F.data == 'clear_cart')
async def clear_cart(call: types.CallbackQuery):
    # Никаких операций с TelegramUser здесь!
    await CartItem.objects. \
        filter(
        cart__user__chat_id=call.message.chat.id,
        cart__is_ordered=False
    ).adelete()
    _, res = build_cart_view([])
    await call.message.edit_text(
        'Корзина очищена',
        reply_markup=res
    )
    await call.answer("✅ Корзина очищена")
