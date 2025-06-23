class InsufficientStockError(Exception):
    def __init__(self, product, available, requested):
        self.product = product
        self.available = available
        self.requested = requested
        super().__init__(
            f"❌ Недостаточно товара: {product.description}. "
            f"Доступно: {available}, Запрошено: {requested}"
        )
