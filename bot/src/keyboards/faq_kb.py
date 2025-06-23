from aiogram.utils.keyboard import InlineKeyboardBuilder

from store.models import FAQ


def faq_kb(faqs: list[FAQ]):
    kb = InlineKeyboardBuilder()
    for faq in faqs:
        kb.button(text=faq.question, callback_data=f'question_{faq.id}')
    kb.button(text='Назад', callback_data='back_to_start')
    kb.adjust(2)
    return kb.as_markup()


def back_to_faq_kb():
    kb = InlineKeyboardBuilder()
    kb.button(text='Назад', callback_data='faq')
    return kb.as_markup()
