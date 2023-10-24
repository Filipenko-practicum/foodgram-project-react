from django.contrib.auth import get_user_model
from django_filters import rest_framework as filters

# from rest_framework.filters import SearchFilter
# FilterSet
from recipes.models import Ingredient, Recipe, Tag

# from django_filters.rest_framework import filters


# class IngredientSearchFilter(SearchFilter):
#     """Фильтр ингридиентов."""

#     name = filters.CharFilter(lookup_expr='icontains')

#     class Meta:
#         model = Ingredient
#         fields = ('name',)


# class RecipeFilter(FilterSet):
#     tags = filters.AllValuesMultipleFilter(field_name='tags__slug')
#     is_favorited = filters.BooleanFilter(method='is_favorited_filter')
#     is_in_shopping_cart = filters.BooleanFilter(
#         method='is_in_shopping_cart_filter'
#     )

#     class Meta:
#         model = Recipe
#         fields = ('tags', 'author')

#     def is_favorited_filter(self, queryset, name, value):
#         user = self.request.user.pk
#         if value:
#             return queryset.filter(favorite__user=user)
#         return queryset

#     def is_in_shopping_cart_filter(self, queryset, name, value):
#         user = self.request.user.pk
#         if value:
#             return queryset.filter(shoppingcart__user=user)
#         return queryset
User = get_user_model()


class IngredientFilter(filters.FilterSet):
    name = filters.CharFilter(lookup_expr='startswith')

    class Meta:
        model = Ingredient
        fields = ('name',)


class RecipeFilter(filters.FilterSet):
    tags = filters.ModelMultipleChoiceFilter(
        field_name='tagsslug',
        to_field_name='slug',
        queryset=Tag.objects.all(),
    )
    author = filters.ModelChoiceFilter(queryset=User.objects.all())
    is_favorited = filters.BooleanFilter(method='filter_is_favorited')
    is_in_shopping_cart = filters.BooleanFilter(
        method='filter_is_in_shopping_cart'
    )

    def filter_is_favorited(self, queryset, name, value):
        if value and not self.request.user.is_anonymous:
            return queryset.filter(favoritesuser=self.request.user)
        return queryset

    def filter_is_in_shopping_cart(self, queryset, name, value):
        if value and not self.request.user.is_anonymous:

            return queryset.filter(shopping_cart__user=self.request.user)
        return queryset

    class Meta:
        model = Recipe
        fields = (
            'tags',
            'author',
        )
