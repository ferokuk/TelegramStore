from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup
from store.models import CartItem, Product


def build_cart_view(items: list[CartItem]) -> tuple[str, InlineKeyboardMarkup]:
    """
    Возвращает пару (текст корзины, InlineKeyboardMarkup) с кнопками удаления,
    очистки, оформления и перехода в каталог.
    """
    kb = InlineKeyboardBuilder()
    if not items:
        text = "🛒 Ваша корзина пуста."
    else:
        total = 0
        lines = []
        # Строки текста и кнопки удаления
        for ci in items:
            p: Product = ci.product
            cost = p.price * ci.quantity
            total += cost
            lines.append(f"• {p.description}\n  {ci.quantity} × {p.price}₽ = {cost}₽")
            kb.button(
                text=f"❌ Удалить {p.description}",
                callback_data=f"remove_item_{ci.id}"
            )
        lines.append(f"\n<b>Итого: {total}₽</b>")
        text = "\n".join(lines)

        # Управляющие кнопки
        kb.button(text="🗑 Очистить корзину", callback_data="clear_cart")
        kb.button(text="💳 Оформить заказ", callback_data="order")

    # Всегда даём кнопку «назад в каталог»
    kb.button(text="⬅️ Продолжить покупки", callback_data="catalog")

    # Упорядочиваем: сначала столько строк, сколько айтемов, потом 2 колонки
    if items:
        kb.adjust(*( [1] * len(items) + [2,] ))
    else:
        kb.adjust(1)

    return text, kb.as_markup(parse_mode="HTML")
