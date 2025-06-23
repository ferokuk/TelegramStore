from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardMarkup
from aiogram.types import InlineKeyboardButton
from store.models import Category, Product
from typing import Optional

# Константы
CATEGORIES_PER_PAGE = 8
PRODUCTS_PER_PAGE = 5


def main_menu_kb() -> InlineKeyboardMarkup:
    """Клавиатура главного меню"""
    kb = InlineKeyboardBuilder()
    kb.button(text='📦 Каталог', callback_data='catalog')
    kb.button(text='🛒 Корзина', callback_data='cart')
    kb.button(text='❓ FAQ', callback_data='faq')
    kb.adjust(2)
    return kb.as_markup()


def categories_kb(
        categories: list[Category],
        parent_id: Optional[int] = None,
        current_page: int = 1,
        total_pages: int = 1
) -> InlineKeyboardMarkup:
    """Клавиатура категорий с пагинацией"""
    kb = InlineKeyboardBuilder()

    # Кнопки категорий
    for category in categories:
        kb.button(text=category.name, callback_data=f'category_{category.id}')

    if total_pages > 1:
        if current_page > 1:
            kb.button(text="⬅️", callback_data=f"cat_page_{current_page - 1}_{parent_id or ''}")
        kb.button(text=f"{current_page}/{total_pages}", callback_data="no_action")
        if current_page < total_pages:
            kb.button(text="➡️", callback_data=f"cat_page_{current_page + 1}_{parent_id or ''}")

    # Кнопка возврата
    if parent_id:
        kb.button(text="⬅️ Назад", callback_data='catalog')
    else:
        kb.button(text="⬅️ В начало", callback_data='back_to_start')

    # Распределение кнопок
    kb.adjust(1, repeat=True)  # Категории по одной в строке

    return kb.as_markup()


def products_kb(
        products: list[Product],
        category_id: int,
        parent_category_id: int,
        current_page: int = 1,
        total_pages: int = 1
) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()

    # 1) Кнопки товаров — по одной в строке
    for product in products:
        kb.button(
            text=product.description,
            callback_data=f"product_{product.id}"
        )
    kb.adjust(1, repeat=True)

    if total_pages > 1:
        page_buttons = []
        if current_page > 1:
            page_buttons.append(
                InlineKeyboardButton(text="⬅️", callback_data=f"prod_page_{category_id}_{current_page - 1}")
            )
        page_buttons.append(
            InlineKeyboardButton(text=f"{current_page}/{total_pages}", callback_data="no_action")
        )
        if current_page < total_pages:
            page_buttons.append(
                InlineKeyboardButton(text="➡️", callback_data=f"prod_page_{category_id}_{current_page + 1}")
            )
        kb.row(*page_buttons)

    kb.row(
        InlineKeyboardButton(text="⬅️ К категориям", callback_data=f"category_{parent_category_id}")
    )

    return kb.as_markup()


def product_detail_kb(product_id: int) -> InlineKeyboardMarkup:
    """Клавиатура для детального просмотра товара"""
    kb = InlineKeyboardBuilder()
    kb.button(text="🛒 Добавить в корзину", callback_data=f"add_item_{product_id}")
    kb.adjust(1, 2)
    return kb.as_markup()

def out_of_stock_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="Нет в наличии", callback_data=f"no_action")
    kb.adjust(1, 2)
    return kb.as_markup()
