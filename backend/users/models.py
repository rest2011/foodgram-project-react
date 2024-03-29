from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models

VALID_USERNAME = 'Введите корректное значение поля "username"'
NOT_SELF_SUBSCRIBE = 'На себя подписаться нельзя'


class User(AbstractUser):
    username = models.CharField(
        'Ник пользователя',
        max_length=150,
        unique=True,
        validators=(RegexValidator(
            regex=r'^[\w.@+-]+\Z', message=VALID_USERNAME
        ),)
    )
    email = models.EmailField(
        'Электронная почта',
        max_length=254,
        unique=True,
    )
    first_name = models.CharField(
        'Имя пользователя',
        max_length=150,
    )
    last_name = models.CharField(
        'Фамилия пользователя',
        max_length=150,
    )

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.username


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        verbose_name='Подписчик',
        related_name='follower',
        on_delete=models.CASCADE,
    )
    author = models.ForeignKey(
        User,
        verbose_name='Автор',
        related_name='following',
        on_delete=models.CASCADE,
    )

    def clean(self):
        if self.user == self.author:
            raise ValidationError(NOT_SELF_SUBSCRIBE)

    class Meta:
        ordering = ['author', ]
        verbose_name = 'Подписчик'
        verbose_name_plural = 'Подписчики'
        constraints = (
            models.UniqueConstraint(
                fields=('user', 'author'),
                name='follow_user_author_constraint'
            ),
        )

    def __str__(self):
        return (
            f'Пользователь {self.user} подписался на автора {self.author}'
        )
