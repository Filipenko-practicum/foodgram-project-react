from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet as UserViewSet
from rest_framework import response, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly

from api.serializers import AddSubscribedSerializer, SubscribedSerializer
from api.pagination import LimitPageNumberPagination
from .serializers import UserSerializer
from .models import Subscribed, User


class UserViewSet(UserViewSet):
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
        serializer = AddSubscribedSerializer(data=data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return response.Response(
            serializer.to_representation(serializer.instance),
            status=status.HTTP_201_CREATED,
        )

    @subscribe.mapping.delete
    def delete_subscribe(self, request, id):
        """Отписываемся от пользователя."""
        try:
            subscribed_user = Subscribed.objects.get(user=request.user, author=id)
            subscribed_user.delete()
            return response.Response(
                {'detail': 'Отписались от пользователя'},
                status=status.HTTP_204_NO_CONTENT
            )
        except Subscribed.DoesNotExist:
            return response.Response(
                {'detail': 'Подписка не найдена'},
                status=status.HTTP_400_BAD_REQUEST
            )
