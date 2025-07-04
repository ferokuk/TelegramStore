from typing import List, Tuple
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton


class Paginator:
    def __init__(self, data: list, page_size: int = 5):
        self.data = data
        self.page_size = page_size
        self.total_pages = (len(data) + page_size - 1) // page_size

    def get_page(self, page: int) -> Tuple[List, int]:
        """Возвращает элементы для страницы и номер страницы"""
        page = max(1, min(page, self.total_pages))
        start = (page - 1) * self.page_size
        end = start + self.page_size
        return self.data[start:end], page

    def build_pagination_kb(self, prefix: str, current_page: int, parent_id=None) -> InlineKeyboardBuilder:
        """Строит клавиатуру с пагинацией"""
        builder = InlineKeyboardBuilder()

        # Кнопки навигации
        if current_page > 1:
            builder.button(
                text="⬅️ Пред.",
                callback_data=f"{prefix}_page_{current_page - 1}_{parent_id or ''}"
            )

        builder.button(
            text=f"{current_page}/{self.total_pages}",
            callback_data="no_action"
        )

        if current_page < self.total_pages:
            builder.button(
                text="След. ➡️",
                callback_data=f"{prefix}_page_{current_page + 1}_{parent_id or ''}"
            )

        # Кнопка "Назад"
        if parent_id:
            builder.button(
                text="⬅️ Назад",
                callback_data=f"category_{parent_id}"
            )
        else:
            builder.button(
                text="⬅️ Главное меню",
                callback_data="back_to_start"
            )

        builder.adjust(3, 1)  # 3 кнопки в первом ряду, 1 во втором
        return builder
