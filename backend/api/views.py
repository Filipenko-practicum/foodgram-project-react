from datetime import datetime as dt
from django.db.models import Sum
from django.http import FileResponse
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import response, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import (
    AllowAny,
    IsAuthenticated,
    IsAuthenticatedOrReadOnly,
)
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from api.serializers import (
    AddSubscribedSerializer,
    FavoriteSerializer,
    IngredienSerializer,
    RecipeCreateSerializer,
    RecipeListSerializer,
    ShoppingCartSerializer,
    SubscribedSerializer,
    TagSerializer,
    UserSerializer,
)
from foodgram.constants import FILE_NAME
from recipes.models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
    Tag,
)
from users.models import Subscribed, User
from .filters import IngredientSearchFilter, RecipeFilter
from .pagination import LimitPageNumberPagination
from .permissions import IsOwnerOrAdminOrReadOnly


class TagViewSet(ReadOnlyModelViewSet):
    """Вьюсет тегов."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AllowAny,)
    pagination_class = None


class IngredientViewSet(ReadOnlyModelViewSet):
    """Вьюсет ингридеентов."""

    queryset = Ingredient.objects.all()
    serializer_class = IngredienSerializer
    permission_classes = (AllowAny,)
    pagination_class = None
    filter_backends = [DjangoFilterBackend]
    filterset_class = IngredientSearchFilter


class RecipeViewSet(ModelViewSet):
    """Вью сет для рецептов."""

    queryset = Recipe.objects.all().select_related(
        'author'
    ).prefetch_related(
        'tags', 'ingredients'
    )
    permission_classes = (IsOwnerOrAdminOrReadOnly,)
    filter_backends = [DjangoFilterBackend]
    filterset_class = RecipeFilter
    pagination_class = LimitPageNumberPagination

    def get_serializer_class(self):
        """Метод определения сереолайзера."""

        if self.action in ('list', 'retrieve'):
            return RecipeListSerializer
        return RecipeCreateSerializer

    @staticmethod
    def adding_recipe(add_serializer, model, request, recipe_id):
        """Кастомный метод добавления и удаления рецепта."""
        user = request.user
        data = {'user': user.id, 'recipe': recipe_id}
        serializer = add_serializer(data=data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return response.Response(
            serializer.data, status=status.HTTP_201_CREATED
        )

    @staticmethod
    def create_shopping_cart_file(self, request, ingredients):
        """Кастомный метод создания списка покупок."""
        user = self.request.user
        filename = f'{user.username}_{FILE_NAME}'
        today = dt.today()
        shopping_list = (
            f'Список покупок для пользователя: {user.username}\n\n'
            f'Дата: {today:%Y-%m-%d}\n\n'
        )
        shopping_list += '\n'.join(
            [
                f'- {ingredient["ingredient__name"]} '
                f'({ingredient["ingredient__measurement_unit"]})'
                f' - {ingredient["amount"]}'
                for ingredient in ingredients
            ]
        )
        shopping_list += f'\n\nFoodgram ({today:%Y})'
        response = FileResponse(
            shopping_list, content_type='text.txt; charset=utf-8'
        )
        response['Content-Disposition'] = f'attachment; filename={filename}'
        return response

    @action(
        detail=True, methods=['post'], permission_classes=(IsAuthenticated,)
    )
    def favorite(self, request, pk):
        return self.adding_recipe(FavoriteSerializer, Favorite, request, pk)

    @favorite.mapping.delete
    def remove_from_favorite(self, request, pk):
        """Метод удаления избраного."""
        favorite_delete = Favorite.objects.filter(user=request.user, recipe=pk)
        if favorite_delete.exists():
            favorite_delete.delete()
            return response.Response(status=status.HTTP_204_NO_CONTENT)
        return response.Response(status=status.HTTP_400_BAD_REQUEST)

    @action(
        detail=True,
        methods=['post'],
        permission_classes=(IsAuthenticated,),
        pagination_class=None,
    )
    def shopping_cart(self, request, pk):
        """Метод добавления рецепта в корзину."""
        return self.adding_recipe(
            ShoppingCartSerializer, ShoppingCart, request, pk
        )

    @shopping_cart.mapping.delete
    def remove_from_shopping_cart(self, request, pk):
        """Метод удаления из корзины."""
        delete_shop_cart = ShoppingCart.objects.filter(
            user=request.user, recipe=pk
        )
        if delete_shop_cart.exists():
            delete_shop_cart.delete()
            return response.Response(status=status.HTTP_204_NO_CONTENT)
        return response.Response(status=status.HTTP_400_BAD_REQUEST)

    @action(
        detail=False, methods=['get'], permission_classes=(IsAuthenticated,)
    )
    def download_shopping_cart(self, request):
        """Метод получения списка покупок."""
        ingredients = (
            RecipeIngredient.objects.filter(
                recipe__shoppingcart__user=self.request.user
            )
            .values('ingredient__name', 'ingredient__measurement_unit')
            .order_by('ingredient__name')
            .annotate(amount=Sum('amount'))
        )
        return self.create_shopping_cart_file(self, request, ingredients)


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    permission_classes = (IsAuthenticatedOrReadOnly,)
    serializer_class = UserSerializer
    pagination_class = LimitPageNumberPagination

    def get_permissions(self):
        if self.action == 'me':
            return [IsAuthenticated()]
        return super().get_permissions()

    @action(
        detail=False, methods=['get'], permission_classes=(IsAuthenticated,)
    )
    def subscriptions(self, request):
        """Возвращает пользователей, на которых подписан текущий пользователь.
        В выдачу добавляются рецепты.
        """
        return self.get_paginated_response(
            SubscribedSerializer(
                self.paginate_queryset(
                    User.objects.filter(subscribing__user=request.user)
                ),
                many=True,
                context={'request': request},
            ).data
        )

    @action(
        detail=True, methods=['post'], permission_classes=[IsAuthenticated]
    )
    def subscribe(self, request, id):
        """Подписываем пользователя.
            Доступно только авторизованным пользователям."""
        user = request.user
        data = {'user': user.id, 'author': id}
        serializer = AddSubscribedSerializer(
            data=data, context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            serializer.to_representation(serializer.instance),
            status=status.HTTP_201_CREATED,
        )

    @subscribe.mapping.delete
    def delete_subscribe(self, request, id):
        """Отписываемся от пользователя."""
        subscribed_user = Subscribed.objects.filter(
            user=request.user,
            author=id,
        )
        if subscribed_user.exists():
            subscribed_user.delete()
            return Response(
                {'detail': 'Отписались от пользователя'},
                status=status.HTTP_204_NO_CONTENT
            )
        else:
            return Response(
                {'detail': 'Подписка не найдена'},
                status=status.HTTP_400_BAD_REQUEST
            )
