import csv

from django.contrib import admin, messages
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import path, reverse

from .forms import IngredientImportForm
from .models import (
    Favorite,
    ImportIngredient,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingСart,
    Tag,
)


@admin.register(ImportIngredient)
class ImportIngredient(admin.ModelAdmin):
    list_display = ('csv_file', 'date_added')


class IngredientAdmin(admin.ModelAdmin):
    """Админка ингридиентов и импорт-CSV"""

    model = Ingredient
    list_display = ('pk', 'name', 'measurement_unit')
    search_fields = ('name', 'measurement_unit')

    def get_urls(self):
        urls = super().get_urls()
        urls.insert(-1, path('csv-upload/', self.upload_csv))
        return urls

    def upload_csv(self, request):
        if request.method == 'POST':
            form = IngredientImportForm(request.POST, request.FILES)
            if form.is_valid():
                form_object = form.save()
                with open(
                    form_object.csv_file.path, encoding='utf-8'
                ) as csv_file:
                    rows = csv.reader(csv_file, delimiter=',')
                    if next(rows) != ['name', 'measurement_unit']:
                        messages.warning(request, 'Неверные заголовки у файла')
                        return HttpResponseRedirect(request.path_info)
                    Ingredient.objects.bulk_create(
                        Ingredient(
                            name=row[0],
                            measurement_unit=row[1],
                        )
                        for row in rows
                    )
                url = reverse('admin:index')
                messages.success(request, 'Файл успешно импортирован')
                return HttpResponseRedirect(url)
        form = IngredientImportForm()
        return render(request, 'admin/csv_import_page.html', {'form': form})


class IngredientsInline(admin.TabularInline):
    """
    Админ-зона для интеграции добавления ингридиентов в рецепты.
    Сразу доступно добавление 3х ингрдиентов.
    """
    model = RecipeIngredient
    extra = 3


class FollowAdmin(admin.ModelAdmin):
    """
    Админ-зона подписок.
    """
    list_display = ('user', 'author')
    list_filter = ('author',)
    search_fields = ('user',)


class FavouriteAdmin(admin.ModelAdmin):
    """
    Админ-зона избранных рецептов.
    """
    list_display = ('pk', 'user', 'recipe')
    list_editable = ('user', 'recipe')


class ShoppingCartAdmin(admin.ModelAdmin):
    """
    Админ-зона покупок.
    """
    list_display = ('pk', 'user', 'recipe')
    list_editable = ('user', 'recipe')


class IngredientRecipeAdmin(admin.ModelAdmin):
    """
    Админ-зона ингридентов для рецептов.
    """
    list_display = ('id', 'recipe', 'ingredient', 'amount',)
    list_filter = ('recipe', 'ingredient')
    search_fields = ('name',)


class RecipeAdmin(admin.ModelAdmin):
    """
    Админ-зона рецептов.
    Добавлен просмотр кол-ва добавленных рецептов в избранное.
    """
    list_display = (
        'id',
        'author',
        'name',
    )
    fields = ('name', 'author', 'text', 'image', 'tags')
    search_fields = ('name', 'author', 'tags')
    list_filter = ('name', 'author', 'tags')
    inlines = (IngredientsInline,)
    empty_value_display = '- пусто -'
    filter_horizontal = ("tags",)

    def in_favorite(self, obj):
        return obj.favorite.all().count()

    in_favorite.short_description = 'Добавленные рецепты в избранное'


class TagAdmin(admin.ModelAdmin):
    """
    Админ-зона тегов.
    """
    prepopulated_fields = {'slug': ('name',)}
    list_display = ('name', 'color', 'slug')
    list_editable = ('color',)
    empty_value_display = '-пусто-'


admin.site.register(Recipe, RecipeAdmin)
admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(Tag, TagAdmin)
admin.site.register(RecipeIngredient, IngredientRecipeAdmin)
admin.site.register(Favorite, FavouriteAdmin)
admin.site.register(ShoppingСart, ShoppingCartAdmin)
