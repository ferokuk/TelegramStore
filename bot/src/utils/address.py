from aiogram.types.shipping_address import ShippingAddress


def format_address(
        address: ShippingAddress
) -> str:
    parts = []
    country_code = address.country_code
    state = address.state
    city = address.city
    street_line1 = address.street_line1
    street_line2 = address.street_line2
    post_code = address.post_code

    # Добавляем страну (если есть)
    if country_code:
        country = country_code.upper()
        if country == 'RU':
            parts.append('Россия')
        elif country == 'KZ':
            parts.append('Казахстан')
        elif country == 'BY':
            parts.append('Беларусь')
        else:
            parts.append(country)

    # Добавляем регион (если указан и не дублирует город)
    if state and state != city:
        parts.append(state)

    # Город всегда добавляем
    parts.append(city)

    # Улица (первая линия)
    if street_line1:
        parts.append(f"ул. {street_line1}")

    # Улица (вторая линия - дом, квартира)
    if street_line2:
        parts.append(street_line2)

    # Почтовый индекс
    if post_code:
        parts.append(f"индекс: {post_code}")

    # Собираем в одну строку
    return ", ".join(parts)
