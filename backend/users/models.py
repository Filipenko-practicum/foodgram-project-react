from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import CheckConstraint, F, Q

from foodgram.constants import MAX_VALUE_LENGTH_USER
from users.validate import validate_username


class User(AbstractUser):
    """Абстрактная модель пользователя."""

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = (
        'username',
        'first_name',
        'last_name',
    )

    username = models.CharField(
        'Ваш логин',
        max_length=MAX_VALUE_LENGTH_USER,
        unique=True,
        error_messages={
            'unique': 'Пользователь с таким username уже существует.',
        },
        help_text='введите username',
        validators=(validate_username,),
    )
    email = models.EmailField(
        'Почта',
        unique=True,
        error_messages={
            'unique': 'e-mail уже занят.',
        },
    )
    first_name = models.CharField(
        'Имя', max_length=MAX_VALUE_LENGTH_USER
    )
    last_name = models.CharField(
        'Фамилия', max_length=MAX_VALUE_LENGTH_USER
    )

    class Meta:
        ordering = ('email',)
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.username


class Subscribed(models.Model):
    """Модель подписки."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscriber',
        verbose_name='Подписчик',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name='Автор',
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'], name='unique_subscribe'
            ),
            CheckConstraint(
                check=~Q(author=F('user')), name='No self sibscription'
            ),
        ]

    def __str__(self):
        return (
            f'Пользователь  {self.user} подписался на автора {self.author}'
        )
