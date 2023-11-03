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

    def get_recipe_count(self, obj):
        return obj.recipe_set.count()

    def get_subscriber_count(self, obj):
        return obj.subscribe_set.count()


class SubscribedAdmin(admin.ModelAdmin):
    """
    Админ-зона подписок.
    """
    list_display = ('user', 'author')
    list_filter = ('author',)
    search_fields = ('user',)


admin.site.register(User, UserAdmin)
admin.site.register(Subscribed, SubscribedAdmin)
