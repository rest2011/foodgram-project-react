from django.core.validators import MinValueValidator, RegexValidator
from django.db import models
from users.models import User

VALID_TAG_SLUG = 'Введите корректное значение поля "slug"'
MINIMUM_COOKING_TIME = 'Время готовки не может быть меньше 1 минуты'
MINIMUM_OF_INGREDIENTS = 'Нужно добавить как минимум 1 ингредиент'


class Ingredient(models.Model):
    name = models.CharField(
        'Ингредиент',
        max_length=200,
        blank=False,
    )
    measurement_unit = models.CharField(
        'Единицы измерения',
        max_length=200,
        blank=False,
    )

    class Meta:
        ordering = ['id', ]
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self):
        return self.name


class Tag(models.Model):
    name = models.CharField(
        'Тэг',
        max_length=200,
        unique=True,
    )
    color = models.CharField(
        'Цвет',
        max_length=7,
        unique=True,
    )
    slug = models.SlugField(
        'Идентификатор',
        max_length=200,
        unique=True,
        validators=(RegexValidator(
            regex=r'^[-a-zA-Z0-9_]+$', message=VALID_TAG_SLUG
        ),)
    )

    class Meta:
        ordering = ['id', ]
        verbose_name = 'Тэг'
        verbose_name_plural = 'Тэги'

    def __str__(self):
        return self.name[:15]


class Recipe(models.Model):
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Автор',
        null=True
    )
    name = models.CharField(
        'Название рецепта',
        max_length=200,
    )
    image = models.ImageField(
        'Изображение рецепта',
        upload_to='recipe/',
    )
    text = models.TextField(
        'Описание рецепта',
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        verbose_name='Список ингредиентов',
        through='AmountIngredient',
        related_name='recipes',
    )
    tags = models.ManyToManyField(
        Tag,
        verbose_name='Тэги',
        related_name='recipes',
    )
    cooking_time = models.PositiveIntegerField(
        'Время приготовления (в минутах)',
        validators=[
            MinValueValidator(
                1, message=MINIMUM_COOKING_TIME
            ),
        ],
    )
    pub_date = models.DateTimeField(
        'Дата публикации рецепта',
        auto_now_add=True,
    )

    class Meta:
        ordering = ['-pub_date', ]
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return self.name[:15]


class AmountIngredient(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
        related_name='amount_ingredient',
    )
    ingredients = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        verbose_name='Ингредиент',
        related_name='amount_ingredient',
    )
    amount = models.PositiveSmallIntegerField(
        'Колличество ингредиентов',
        validators=[
            MinValueValidator(
                1, message=MINIMUM_OF_INGREDIENTS
            ),
        ]
    )

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Количество ингредиентов'
        constraints = [
            models.UniqueConstraint(
                fields=('ingredients', 'recipe',),
                name='recipe_ingredient_constraint'
            )
        ]


class Favorite(models.Model):
    user = models.ForeignKey(
        User,
        verbose_name='Пользователь',
        on_delete=models.CASCADE,
        related_name='favorite',
    )
    recipe = models.ForeignKey(
        Recipe,
        verbose_name='Избранный рецепт',
        on_delete=models.CASCADE,
        related_name='favorite',
    )

    class Meta:
        verbose_name = 'Избранный рецепт'
        verbose_name_plural = 'Избранные рецепты'
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'user'],
                name='unique_favorite_user_recipe',
            ),
        ]

    def __str__(self):
        return f'Пользователь {self.user} добавил в избранное {self.recipe}'


class ShoppingCart(models.Model):
    user = models.ForeignKey(
        User,
        verbose_name='Пользователь',
        on_delete=models.CASCADE,
        related_name='shopping_cart',
    )
    recipe = models.ForeignKey(
        Recipe,
        verbose_name='Рецепт',
        on_delete=models.CASCADE,
        related_name='shopping_cart',
    )

    class Meta:
        verbose_name = 'Корзина'
        verbose_name_plural = 'Корзины'
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'user'],
                name='unique_shoppinglist_recipe_user',
            ),
        ]
