from django.db import transaction
from django.forms import ValidationError
from djoser.serializers import UserCreateSerializer
from drf_extra_fields.fields import Base64ImageField
from rest_framework.serializers import (
    IntegerField,
    ModelSerializer,
    PrimaryKeyRelatedField,
    ReadOnlyField,
    SerializerMethodField,
)
from rest_framework.validators import UniqueTogetherValidator

from foodgram.constants import (
    MAX_NUMBER_INGR,
    MAX_VALUE_COUNT,
    MIN_VALUE_COUNT,
)
from recipes.models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
    Tag,
)
from users.models import Subscribed, User


class TagSerializer(ModelSerializer):
    """Сериалайзер Тэгов."""

    class Meta:
        model = Tag
        fields = '__all__'


class RecipeSerializer(ModelSerializer):
    """Сериалайзер Рецепта"""

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class IngredienSerializer(ModelSerializer):
    """Сериалайзер ингредиентов."""

    class Meta:
        model = Ingredient
        fields = (
            'id',
            'name',
            'measurement_unit'
        )


class RecipeIngredientSerializer(ModelSerializer):
    """Сериалайзер для рецепта с ингредиентами"""

    id = ReadOnlyField(source='ingredient.id')
    name = ReadOnlyField(source='ingredient.name')
    measurement_unit = ReadOnlyField(source='ingredient.measurement_unit')

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class BaseRelationSerializer(ModelSerializer):
    """Базовый сериализатор для связей"""

    def validate(self, attrs):
        user = attrs['user']
        recipe = attrs['recipe']

        # Проверяем уникальность записи
        if self.Meta.model.objects.filter(user=user, recipe=recipe).exists():
            raise ValidationError('У вас уже есть эта запись')

        return attrs

    def to_representation(self, instance):
        return RecipeSerializer(instance, context=self.context).data


class FavoriteSerializer(BaseRelationSerializer):
    """Сереалайзер избранного"""

    class Meta:
        model = Favorite
        fields = ('user', 'recipe')


class ShoppingCartSerializer(BaseRelationSerializer):
    """Сериалайзер модели Cart."""

    class Meta:
        model = ShoppingCart
        fields = ('user', 'recipe')


class HowIngredientSerilizer(ModelSerializer):
    """Сереалайзер колличества ингредиентов в рецепте."""

    id = PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all()
    )
    amount = IntegerField(
        min_value=MIN_VALUE_COUNT,
        max_value=MAX_NUMBER_INGR,
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')


class UserSerializer(ModelSerializer):
    """Сериалайзер Юзера."""
    is_subscribed = SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed'
        )

    def get_is_subscribed(self, obj):
        user = self.context.get('request').user
        return (
            user.is_authenticated
            and obj.subscribing.filter(user=user).exists()
        )


class RecipeListSerializer(ModelSerializer):
    """
    Serializer для модели Recipe - чтение данных.
    Находится ли рецепт в избранном, списке покупок.
    Получение списка ингредиентов с добавленным полем
    amount из промежуточной модели.
    """
    author = UserSerializer()
    tags = TagSerializer(
        many=True,
        read_only=True)
    ingredients = RecipeIngredientSerializer(
        many=True,
        source='recipes',
        read_only=True)
    is_favorited = SerializerMethodField()
    is_in_shopping_cart = SerializerMethodField()

    class Meta:
        model = Recipe
        fields = ('id', 'tags', 'author', 'ingredients',
                  'is_favorited', 'is_in_shopping_cart',
                  'name', 'image', 'text', 'cooking_time')

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        return (
            request
            and request.user.is_authenticated
            and request.user.favorite
        )

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        return (
            request
            and request.user.is_authenticated
            and request.user.shoppingcart
        )


class RecipeCreateSerializer(ModelSerializer):
    """Serializer для модели Recipe - запись / обновление / удаление данных."""

    author = UserSerializer(read_only=True)
    tags = PrimaryKeyRelatedField(many=True, queryset=Tag.objects.all())
    cooking_time = IntegerField(
        min_value=MIN_VALUE_COUNT, max_value=MAX_VALUE_COUNT
    )
    ingredients = HowIngredientSerilizer(
        many=True,
    )
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'image',
            'tags',
            'ingredients',
            'name',
            'text',
            'cooking_time',
            'author',
        )

    def validate_image(self, image):
        """Именной валидатор для проверки картинки"""
        if not image:
            raise ValidationError(
                {'error': 'Нужна картинка, пустым не должно быть!'}
            )
        return image

    def validate(self, data):
        """Метод валидации для создания рецепта"""
        ingredients = data.get('ingredients')
        tags = data.get('tags')

        if not ingredients:
            raise ValidationError(
                {'error': 'Выберите ингредиенты!'}
            )

        if not tags:
            raise ValidationError(
                {'error': 'Укажите тэг!'}
            )

        ingredient_ids = [ingredient['id'] for ingredient in ingredients]
        if len(set(ingredient_ids)) != len(ingredient_ids):
            raise ValidationError('Ингредиенты не должны повторяться.')

        if len(set(tags)) != len(tags):
            raise ValidationError('Тэги не должны повторяться.')

        return data

    def add_ingredients_and_tags(self, tags, ingredients, recipe):
        recipe.tags.set(tags)
        ingredients_list = []
        for ingredient in ingredients:
            new_ingredient = RecipeIngredient(
                recipe=recipe,
                ingredient_id=ingredient['id'],
                amount=ingredient['amount'],
            )
            ingredients_list.append(new_ingredient)
        RecipeIngredient.objects.bulk_create(ingredients_list)

    @transaction.atomic
    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        author = self.context.get('request').user
        recipe = Recipe.objects.create(author=author, **validated_data)
        self.add_ingredients_and_tags(tags, ingredients, recipe)
        return recipe

    def update(self, instance, validated_data):
        """Редактирование рецепта."""

        instance.ingredients.clear()
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        return RecipeListSerializer(instance, context={
            'request': self.context.get('request')
        }).data


class SubscribedSerializer(UserSerializer):
    """Сереалайзер Подписок. для GET запроса"""

    recipes = SerializerMethodField(method_name='get_recipes', read_only=True)
    recipes_count = SerializerMethodField(
        method_name='get_recipes_count', read_only=True
    )

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + (
            'recipes',
            'recipes_count',
        )
        read_only_fields = (
            'email',
            'username',
            'last_name',
            'first_name',
        )

    def get_recipes_count(self, obj):
        """Метод получения колличества рецепта."""
        return obj.recipes.count()

    def get_recipes(self, object):
        """Метод получение рецепта."""
        try:
            limit = int(
                self.context['request'].query_params.get(
                    'recipes_limit',
                )
            )
        except (ValueError, KeyError):
            raise ValueError('Неверное значение параметра recipes_limit')
        except AttributeError:
            raise AttributeError('Отсутствует объект запроса')
        author_recipes = object.recipes.all()[:limit]
        return RecipeSerializer(author_recipes, many=True).data


class AddSubscribedSerializer(ModelSerializer):
    """Сереалайзер добавления подписки"""

    class Meta:
        model = Subscribed
        fields = ('user', 'author')
        validators = [
            UniqueTogetherValidator(
                queryset=Subscribed.objects.all(),
                fields=['user', 'author'],
                message='Вы уже подписались!',
            )
        ]

    def validate(self, attrs):
        user = attrs.get('user')
        author = attrs.get('author')

        if user == author:
            raise ValidationError('Нельзя подписаться на самого себя!')

        return attrs

    def to_representation(self, instance):
        request = self.context.get('request')
        return SubscribedSerializer(
            instance.author, context={'request': request}
        ).data


class UserRegistrationSerializer(UserCreateSerializer):
    """Сереалайзер регистрации."""

    class Meta(UserCreateSerializer.Meta):
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'password',
        )
