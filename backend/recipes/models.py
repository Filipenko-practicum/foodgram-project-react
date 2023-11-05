from colorfield.fields import ColorField
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import UniqueConstraint

from foodgram.constants import (
    DEFAULT_COLOR,
    DIRICTORY_PATH,
    MAX_AMOUNT,
    MAX_INGREDIENT,
    MAX_LENGTH,
    MAX_LENGTH_COLOR,
    MAX_TIME_COOK,
    MAX_VALUE_COUNT,
    MIN_INGREDIENT,
    MIN_TIME_COOK,
    MIN_VALUE_COUNT,
)
from users.models import User


class ImportIngredient(models.Model):
    """Модель импорта ингридиентов."""

    csv_file = models.FileField(upload_to='uploads/')
    date_added = models.DateTimeField(auto_now_add=True)


class ImportTag(ImportIngredient):
    """Модель импорта ингридиентов."""


class Tag(models.Model):
    """Модель Тегов."""

    name = models.CharField(
        'Название Тега',
        max_length=MAX_LENGTH,
        unique=True,
        error_messages={
            'unique': 'Тег с таким именем уже существует.',
        },
    )
    color = ColorField(
        'Цвет в HeX',
        max_length=MAX_LENGTH_COLOR,
        unique=True,
        error_messages={
            'unique': 'Такой цвет уже существует.',
        },
        default=DEFAULT_COLOR,
    )
    slug = models.CharField(
        'Уникальный Тег',
        max_length=MAX_LENGTH,
        unique=True,
        error_messages={
            'unique': 'Такой Slug уже существует.',
        },
    )

    class Meta:
        ordering = ('name',)
        verbose_name = "Тег"
        verbose_name_plural = "Теги"

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    """Модель ингредиент"""

    name = models.CharField(
        'Название',
        max_length=MAX_LENGTH,
        db_index=True,
        error_messages={
            'unique': 'Такой ингредиент уже есть.',
        },
    )
    measurement_unit = models.CharField(
        'Единица измерения',
        max_length=MAX_LENGTH,
    )

    class Meta:
        ordering = ('name',)
        verbose_name = "ингредиент"
        verbose_name_plural = "ингредиенты"
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'measurement_unit'],
                name='ingredient_name_unit_unique'
            ),
        ]

    def __str__(self):
        return f'{self.name},в {self.measurement_unit}'


class Recipe(models.Model):
    """Модель рецептов."""

    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
        verbose_name='Ингредиенты',
    )
    tags = models.ManyToManyField(
        Tag,
        verbose_name='Теги',
    )
    image = models.ImageField(
        'Изображение блюда',
        upload_to=DIRICTORY_PATH,
    )
    name = models.CharField(
        'Название блюда',
        max_length=MAX_LENGTH,
    )
    text = models.TextField(
        'Описание',
    )
    cooking_time = models.PositiveSmallIntegerField(
        'Время приготовления, мин',
        default=MIN_VALUE_COUNT,
        validators=[
            MinValueValidator(MIN_VALUE_COUNT, message=MIN_TIME_COOK),
            MaxValueValidator(MAX_VALUE_COUNT, message=MAX_TIME_COOK),
        ],
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Автор рецепта',
    )
    pub_date = models.DateTimeField(
        auto_now_add=True, verbose_name='Дата публикации'
    )

    class Meta:
        ordering = ('-pub_date',)
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        constraints = [
            UniqueConstraint(
                fields=('name', 'author'),
                name="unique_for_author"
            ),
        ]

    def __str__(self):
        return self.name


class RecipeIngredient(models.Model):
    """Модель связывает Recipe и Ingredient с
    указанием количества ингредиентов.
    """

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Рецепт',
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='ingredients',
        verbose_name='Ингредиенты',
    )
    amount = models.PositiveSmallIntegerField(
        'Количество',
        default=MIN_VALUE_COUNT,
        validators=[
            MinValueValidator(MIN_VALUE_COUNT, message=MIN_INGREDIENT),
            MaxValueValidator(MAX_AMOUNT, message=MAX_INGREDIENT),
        ],
    )

    class Meta:
        ordering = ('recipe',)
        verbose_name = 'Ингредиенты в рецепте'
        verbose_name_plural = 'Ингредиенты в рецептах'
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'ingredient'],
                name='recipe_ingredient_unique',
            ),
        ]

    def __str__(self):
        return f'{self.recipe} содержит ингредиенты {self.ingredient}'


class UserRecipeRelation(models.Model):
    """
    Модель, представляющая связь подписок между пользователем и рецептом.
    Поля:
    - user: внешний ключ к модели User, представляющий пользователя,
            который подписан на рецепт.
    - recipe: внешний ключ к модели Recipe, представляющий рецепт,
              на который пользователь подписан."""

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, verbose_name='Пользователь'
    )
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE, verbose_name='Рецепт'
    )

    class Meta:
        abstract = True
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'], name='unique_%(class)s'
            )
        ]

    def __str__(self):
        return f'{self.user.username} - {self.recipe.id}'


class Favorite(UserRecipeRelation):
    """Подписка на избранное."""

    class Meta(UserRecipeRelation.Meta):
        default_related_name = 'favorite'
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'


class ShoppingCart(UserRecipeRelation):
    """Рецепты в корзине покупок.
    Модель связывает Recipe и User
    """

    class Meta(UserRecipeRelation.Meta):
        default_related_name = 'shoppingcart'
        verbose_name = 'Корзина'
        verbose_name_plural = 'Корзина'
