from django.db import models


class TelegramUser(models.Model):
    chat_id = models.BigIntegerField(unique=True, verbose_name='Telegram Chat ID')
    username = models.CharField(max_length=32, blank=True, verbose_name='Telegram Username')
    first_name = models.CharField(max_length=64, blank=True, verbose_name='Имя', null=True)
    last_name = models.CharField(max_length=64, blank=True, verbose_name='Фамилия', null=True)
    joined_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата регистрации')

    class Meta:
        verbose_name = 'Клиент'
        verbose_name_plural = 'Клиенты'

    def __str__(self):
        return self.username or str(self.chat_id)
