from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import Subscribed, User


class UserAdmin(BaseUserAdmin):
    """
    Админ-зона пользователя.
    """
    list_display = ('id', 'username', 'first_name',
                    'last_name', 'email',
                    'get_recipe_count',
                    'get_subscriber_count',)
    search_fields = ('username', 'email')
    list_filter = ('username', 'email',)
    empty_value_display = '-пусто-'

    @admin.display(description='Количество рецептов')
    def get_recipe_count(self, obj):
        return obj.recipes.count()

    @admin.display(description='Количество подписчиков')
    def get_subscriber_count(self, obj):
        return obj.subscriber.count()


class SubscribedAdmin(admin.ModelAdmin):
    """
    Админ-зона подписок.
    """
    list_display = ('user', 'author')
    list_filter = ('author',)
    search_fields = ('user',)


admin.site.register(User, UserAdmin)
admin.site.register(Subscribed, SubscribedAdmin)
