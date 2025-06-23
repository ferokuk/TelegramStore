import asyncio
from pathlib import Path


async def save_to_csv_async(order, path: Path):
    from store.models import Order
    """Асинхронно добавляет заказ в CSV"""
    loop = asyncio.get_running_loop()

    # Загружаем связанные объекты для заказа
    order = await Order.objects.select_related('cart__user').aget(id=order.id)

    lines = []
    # Получаем элементы заказа с продуктами
    async for item in order.items.select_related('product'):
        line = (
            f"{order.id},{order.cart.user.chat_id},"
            f"\"{order.cart.user.username}\",{order.status},"
            f"{order.total_amount},{order.created_at.isoformat()},"
            f"{item.product.id},\"{item.product.description}\","
            f"{item.quantity},{item.price},{item.quantity * item.price}\n"
        )
        lines.append(line)

    await loop.run_in_executor(
        None,
        lambda: save_csv_sync(path, lines)  # Убрали лишний аргумент
    )


def save_csv_sync(path: Path, lines: list):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'a', encoding='utf-8') as f:
        if path.stat().st_size == 0:  # Если файл новый
            headers = (
                "order_id,user_chat_id,user_username,status,total_amount,"
                "created_at,product_id,product_name,quantity,price,line_total\n"
            )
            f.write(headers)
        f.writelines(lines)
