from django.contrib import admin

from users.models import TelegramUser


@admin.register(TelegramUser)
class TelegramUserAdmin(admin.ModelAdmin):
    list_display = ('id', 'username', 'first_name', 'last_name', 'joined_at', 'chat_id')
    search_fields = ('username', 'first_name', 'last_name', 'joined_at', 'chat_id')
    ordering = ('joined_at',)
