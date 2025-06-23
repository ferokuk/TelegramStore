from aiogram import Dispatcher, types, Router, F
from aiogram.types import InlineQuery, InlineQueryResultArticle, InputTextMessageContent
from store.models import FAQ
from ..keyboards.catalog_kb import main_menu_kb
from ..keyboards.faq_kb import faq_kb, back_to_faq_kb

router = Router()


@router.callback_query(lambda c: c.data == 'faq')
@router.message(F.text == '/faq')
async def show_faq(update: types.CallbackQuery | types.Message):
    if isinstance(update, types.CallbackQuery):
        message = update.message
        is_callback = True
    else:
        message = update
        is_callback = False
    text = 'Вы можете задать свой вопрос в чат, упомянув бота. \nЧасто задаваемые вопросы:'
    items = [f async for f in FAQ.objects.all()]

    if is_callback:
        await message.edit_text(
            text,
            reply_markup=faq_kb(items),
            parse_mode="HTML"
        )
        await update.answer()
    else:
        await message.answer(
            text,
            reply_markup=faq_kb(items),
            parse_mode="HTML"
        )


@router.inline_query
async def handle_faq_inline(query: InlineQuery):
    text = query.query.strip().lower()
    if text:
        faqs = FAQ.objects.filter(question__icontains=text)[:10]
    else:
        faqs = FAQ.objects.all()[:10]
    results = []
    async for faq in faqs:
        message_text = (
            f"<b>{faq.question}</b>\n"
            f"{faq.answer}"
        )
        results.append(
            InlineQueryResultArticle(
                id=str(faq.id),
                title=faq.question,
                input_message_content=InputTextMessageContent(
                    message_text=message_text,
                    parse_mode="HTML"
                )
            )
        )
    await query.answer(results, cache_time=1, is_personal=True)


@router.callback_query(lambda c: c.data.startswith('question_'))
async def show_question_details(call: types.CallbackQuery):
    faq_id = call.data.split('_', 1)[1]
    faq = await FAQ.objects.aget(id=faq_id)
    await call.message.edit_text(
        f"<b>{faq.question}</b>\n"
        f"{faq.answer}",
        parse_mode="HTML",
        reply_markup=back_to_faq_kb()
    )


@router.callback_query(lambda c: c.data == 'back_to_start')
async def back_to_start(call: types.CallbackQuery):
    await call.message.edit_text(
        'Добро пожаловать! Выберите раздел:',
        reply_markup=main_menu_kb()
    )
    await call.answer()
