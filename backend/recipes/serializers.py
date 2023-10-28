from django.forms import ValidationError
from drf_extra_fields.fields import Base64ImageField
from rest_framework.serializers import (
    IntegerField,
    ModelSerializer,
    PrimaryKeyRelatedField,
    ReadOnlyField,
    SerializerMethodField,
)
from rest_framework.validators import UniqueTogetherValidator

from users.models import Subscribed
from users.serializers import UserSerializer

from .models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
    Tag,
)


class TagSerializer(ModelSerializer):
    """Сериалайзер Тэгов."""

    class Meta:
        model = Tag
        fields = '__all__'


class RecipeSerializer(ModelSerializer):
    """Сериалайзер Рецепта"""

    image = ReadOnlyField(source='image.url')
    name = ReadOnlyField()
    cooking_time = ReadOnlyField()

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class IngredienSerializer(ModelSerializer):
    """Сериалайзер ингредиентов."""

    class Meta:
        model = Ingredient
        fields = '__all__'


class RecipeIngredientSerializer(ModelSerializer):
    """Сериалайзер для рецепта с ингредиентами"""

    id = ReadOnlyField(source='ingredient.id')
    name = ReadOnlyField(source='ingredient.name')
    measurement_unit = ReadOnlyField(source='ingredient.measurement_unit')

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class FavoriteSerializer(ModelSerializer):
    """Сереалайзер избранного"""

    class Meta:
        model = Favorite
        fields = ('user', 'recipe')
        validators = [
            UniqueTogetherValidator(
                queryset=Favorite.objects.all(),
                fields=['user', 'recipe'],
                message='У вас уже есть это рецепт',
            )
        ]

    def to_representation(self, instance):
        request = self.context.get('request')
        return RecipeSerializer(
            instance.recipe, context={'request': request}
        ).data


class ShoppingCartSerializer(ModelSerializer):
    """Сериалайзер модели Cart."""

    class Meta:
        model = ShoppingCart
        fields = ('user', 'recipe')
        validators = [
            UniqueTogetherValidator(
                queryset=ShoppingCart.objects.all(),
                fields=['user', 'recipe'],
                message='Добавлен уже в корзину!',
            )
        ]

    def to_representation(self, instance):
        request = self.context.get('request')
        return RecipeSerializer(
            instance.recipe, context={'request': request}
        ).data


class HowIngredientSerilizer(ModelSerializer):
    """Сереалайзер колличества ингредиентов в рецепте."""

    id = PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all().values_list('id', flat=True)
    )
    amount = IntegerField(min_value=1, max_value=1000)

    class Meta:
        model = Ingredient
        fields = ('id', 'amount')


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
        source='recipeingredients_set',
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
        return bool(
            request
            and request.user.is_authenticated
            and request.user.favorite.filter(
                recipe=obj, user=request.user
            ).exists()
        )

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        return bool(
            request
            and request.user.is_authenticated
            and request.user.shoppingcart.filter(
                recipe=obj, user=request.user
            ).exists()
        )


class RecipeCreateSerializer(ModelSerializer):
    """Serializer для модели Recipe - запись / обновление / удаление данных."""

    tags = PrimaryKeyRelatedField(many=True, queryset=Tag.objects.all())
    cooking_time = IntegerField(min_value=1, max_value=1000)
    ingredients = HowIngredientSerilizer(many=True)
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
        )

    def validate(self, data):
        """Метод валидации для создания рецепта"""
        ingredients = data.get('ingredients')
        tags = data.get('tags')
        image = data.get('image')

        if not ingredients:
            raise ValidationError('Выберите ингредиенты!')

        if not tags:
            raise ValidationError('Укажите тэг!')

        if not image:
            raise ValidationError('Нужна картинка,пустым не должно быть!')

        ingredient_ids = [ingredient['id'] for ingredient in ingredients]
        if len(set(ingredient_ids)) != len(ingredient_ids):
            raise ValidationError('Ингредиенты не должны повторяться.')

        tag_ids = [tag.id for tag in tags]
        if len(set(tag_ids)) != len(tag_ids):
            raise ValidationError('Тэги не должны повторяться.')

        return data

    @staticmethod
    def create_recipe_ingredients(recipe, ingredients_data):
        recipe.ingredients.clear()
        recipe_ingredients = []
        for ingredient_data in ingredients_data:
            ingredient_id = ingredient_data['id']
            amount = ingredient_data['amount']
            recipe_ingredients.append(
                RecipeIngredient(
                    recipe=recipe, ingredient_id=ingredient_id, amount=amount
                )
            )
        RecipeIngredient.objects.bulk_create(recipe_ingredients)

    def create(self, validated_data):
        """Создание рецепта."""

        tags_data = validated_data.pop('tags', None)
        ingredients_data = validated_data.pop('ingredients', None)
        author = self.context.get('request').user
        recipe = Recipe.objects.create(author=author, **validated_data)
        recipe.tags.set(tags_data)
        self.create_recipe_ingredients(recipe, ingredients_data)
        return recipe

    def update(self, instance, validated_data):
        """Редактирование рецепта."""
        tags_data = validated_data.pop('tags', None)
        instance.tags.set(tags_data)
        ingredients_data = validated_data.pop('ingredients', None)
        self.create_recipe_ingredients(instance, ingredients_data)
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        return RecipeListSerializer(instance, context=self.context).data


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
                    'recipes_limit', default=0
                )
            )
        except ValueError:
            raise ValueError('должно быть целым числом')
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
