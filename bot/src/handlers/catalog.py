from pathlib import Path

from aiogram import Router, F

from ..config import CATEGORIES_PER_PAGE, PRODUCTS_PER_PAGE
from store.models import Category, Product
from ..keyboards.catalog_kb import categories_kb, products_kb, main_menu_kb, product_detail_kb, out_of_stock_kb
from aiogram.types import FSInputFile, CallbackQuery, Message, InputMediaPhoto
from ..init_django import MEDIA_ROOT_BOT
from aiogram.exceptions import TelegramBadRequest

from ..logger import logger
from ..utils.paginator import Paginator

router = Router()


async def get_categories(parent_id: None | int = None):
    if parent_id:
        categories = [c async for c in Category.objects.filter(parent_id=parent_id).all()]
    else:
        categories = [c async for c in Category.objects.filter(parent__isnull=True).all()]
    return categories


@router.message(F.text == '/start')
@router.callback_query(F.data == 'back_to_start')
async def cmd_start(message_or_callback: Message | CallbackQuery):
    """Обработчик команды /start и возврата в начало"""
    text = "Добро пожаловать в наш магазин!\nВыберите нужный раздел:"
    kb = main_menu_kb()

    if isinstance(message_or_callback, Message):
        await message_or_callback.answer(text, reply_markup=kb)
    else:
        await message_or_callback.message.edit_text(text, reply_markup=kb)


@router.callback_query(F.data == 'catalog')
async def show_catalog(cb: CallbackQuery):
    cats = await get_categories(None)
    pag = Paginator(cats, CATEGORIES_PER_PAGE)
    items, page = pag.get_page(1)
    await cb.message.edit_text(
        "Выберите категорию:",
        reply_markup=categories_kb(items, None, page, pag.total_pages)
    )


@router.callback_query(F.data.startswith('cat_page_'))
async def paginate_categories(cb: CallbackQuery):
    rest = cb.data[len('cat_page_'):]
    page_str, parent = rest.split('_', 1)
    parent_id = int(parent) if parent.isdigit() else None
    cats = await get_categories(parent_id)
    pag = Paginator(cats, CATEGORIES_PER_PAGE)
    items, page = pag.get_page(int(page_str))
    await cb.message.edit_text(
        "Выберите категорию:",
        reply_markup=categories_kb(items, parent_id, page, pag.total_pages)
    )


@router.callback_query(F.data.startswith('category_'))
async def show_subcategories_or_products(cb: CallbackQuery):
    # удаляем карточку товара, если была
    chat_id = cb.from_user.id
    if m := last_detail_message.pop(chat_id, None):
        try:
            await cb.bot.delete_message(chat_id, m)
        except:
            pass

    cat_id = int(cb.data.split('_')[1])
    subcats = await get_categories(cat_id)
    if subcats:
        pag = Paginator(subcats, CATEGORIES_PER_PAGE)
        items, page = pag.get_page(1)
        await cb.message.edit_text(
            f"Категория: {(await Category.objects.aget(id=cat_id)).name}",
            reply_markup=categories_kb(items, cat_id, page, pag.total_pages)
        )
    else:
        await _show_products(cb, await Category.objects.aget(id=cat_id), 1)


async def _show_products(cb: CallbackQuery, category: Category, page: int):
    prods = [p async for p in Product.objects.filter(category=category)]
    pag = Paginator(prods, PRODUCTS_PER_PAGE)
    items, page = pag.get_page(page)
    parent = await Category.objects.aget(id=category.parent_id) if category.parent_id else None

    await cb.message.edit_text(
        f"Товары: {(parent.name + ' → ') if parent else ''}{category.name} (стр. {page}/{pag.total_pages})",
        reply_markup=products_kb(items, category.id, parent.id if parent else 0, page, pag.total_pages)
    )


@router.callback_query(F.data.startswith('prod_page_'))
async def paginate_products(cb: CallbackQuery):
    rest = cb.data[len('prod_page_'):]
    cat_str, page_str = rest.split('_', 1)
    cat = await Category.objects.aget(id=int(cat_str))
    await _show_products(cb, cat, int(page_str))


@router.callback_query(F.data.startswith('product_'))
async def handle_product_detail(cb: CallbackQuery):
    await cb.answer()
    prod = await Product.objects.aget(id=int(cb.data.split('_')[1]))
    path = MEDIA_ROOT_BOT / Path(prod.image.name)
    in_stock_mark = "✅" if prod.in_stock else "❌"
    text = f"<b>{prod.description}</b>\n💵 {prod.price}₽\n В наличии: {prod.quantity} шт. {in_stock_mark}"
    media = InputMediaPhoto(media=FSInputFile(path),
                            caption=text,
                            parse_mode="HTML")

    chat_id = cb.from_user.id
    if not prod.in_stock:
        kb = out_of_stock_kb()
    else:
        kb = product_detail_kb(prod.id)
    if msg_id := last_detail_message.get(chat_id):
        try:
            await cb.bot.edit_message_media(chat_id=chat_id, message_id=msg_id, media=media,
                                            reply_markup=kb)
            return
        except TelegramBadRequest:
            try:
                await cb.bot.delete_message(chat_id, msg_id)
            except:
                logger.error(f"Не удалось удалить сообщение {msg_id}")
    sent = await cb.message.answer_photo(media.media, caption=media.caption, parse_mode="HTML",
                                         reply_markup=kb)
    last_detail_message[chat_id] = sent.message_id


last_detail_message: dict[int, int] = {}
