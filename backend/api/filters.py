from django_filters import rest_framework as filters

from recipes.models import Ingredient, Recipe, Tag
from users.models import User


class IngredientSearchFilter(filters.FilterSet):
    name = filters.CharFilter(lookup_expr='startswith')

    class Meta:
        model = Ingredient
        fields = ('name',)


class RecipeFilter(filters.FilterSet):
    tags = filters.ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        queryset=Tag.objects.all(),
    )
    is_favorited = filters.BooleanFilter(method='filter_is_favorited')
    is_in_shoppingcart = filters.BooleanFilter(
        method='filter_is_in_shopping_cart'
    )

    def filter_is_favorited(self, queryset, name, value):
        if value and self.request.user.is_authenticated:
            return queryset.filter(favorite__user=self.request.user)
        return queryset

    def filter_is_in_shopping_cart(self, queryset, name, value):
        if value and self.request.user.is_authenticated:

            return queryset.filter(shopping_cart__user=self.request.user)
        return queryset

    class Meta:
        model = Recipe
        fields = (
            'tags',
            'author',
        )
