from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet
from recipes.serializers import AddSubscribedSerializer, SubscribedSerializer
from rest_framework import response, status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from users.pagination import LimitPageNumberPagination

from .models import Subscribed, User


class UserViewSet(UserViewSet):
    from .serializers import UserSerializer
    queryset = User.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = UserSerializer
    pagination_class = LimitPageNumberPagination

    @staticmethod
    def adding_author(add_serializer, model, request, author_id):
        """Кастомный метод добавления author и получения данных"""
        user = request.user
        data = {'user': user.id, 'author': author_id}
        serializer = add_serializer(data=data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return response.Response(
            serializer.to_representation(serializer.instance),
            status=status.HTTP_201_CREATED,
        )

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
        Доступно только авторизованным пользователям.
        """
        return self.adding_author(
            AddSubscribedSerializer, Subscribed, request, id
        )

    @subscribe.mapping.delete
    def delete_subscribe(self, request, id):
        """Отписываемся от пользователя."""
        get_object_or_404(Subscribed, user=request.user, author=id).delete()
        return response.Response(
            {'detail': 'Отписались от пользователя'},
            status=status.HTTP_204_NO_CONTENT
        )
