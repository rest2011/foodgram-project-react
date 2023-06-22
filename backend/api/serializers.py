from django.db import transaction
from djoser.serializers import (UserSerializer as DjoserUserSerializer,
                                UserCreateSerializer)
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from recipes.models import (MINIMUM_COOKING_TIME, MINIMUM_OF_INGREDIENTS,
                            AmountIngredient, Ingredient, Recipe, Tag,
                            ShoppingCart, Favorite)
from users.models import Follow, User

NEED_TAGS_FOR_INGREDIENT = 'Для рецепта нужен минимум 1 тэг'
NEED_UNIQUE_INGREDIENT = 'В рецепт уже добавлен ингредиент "{value}"'


class UserSerialiser(DjoserUserSerializer):
    """
    Сериализатор для операций с пользователями.
    """
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "email", "id", "username", "first_name",
            "last_name", "is_subscribed",
        )

    def get_is_subscribed(self, obj):
        return (self.context.get('request').user.is_authenticated
                and Follow.objects.filter(
                    user=self.context.get('request').user,
                    author=obj).exists())


class CreateUserSerializer(UserCreateSerializer):
    """
    Сериализатор для создания пользователей.
    """

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username', 'first_name', 'last_name', 'password',
        )
        extra_kwargs = {
            'password': {'required': True, 'write_only': True}
        }


class IngredientSerializer(serializers.ModelSerializer):
    """
    Сериализатор для ингредиентов.
    """

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit',)


class IngredientCreateSerializer(serializers.ModelSerializer):
    """
    Сериализатор создания ингредиентов при добавлении рецепта.
    """
    id = serializers.IntegerField(required=True)
    amount = serializers.IntegerField(required=True)

    class Meta:
        model = AmountIngredient
        fields = ('id', 'amount')

    def validate_amount(self, value):
        if value < 1:
            raise serializers.ValidationError(MINIMUM_OF_INGREDIENTS)
        return value


class ReadIngredientsRecipeSerializer(serializers.ModelSerializer):
    """
    Сериализатор для просматривания ингредиентов в рецепте.
    """
    id = serializers.ReadOnlyField(source='ingredients.id')
    name = serializers.ReadOnlyField(source='ingredients.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredients.measurement_unit'
    )

    class Meta:
        model = AmountIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount',)
        validators = [UniqueTogetherValidator(
            queryset=AmountIngredient.objects.all(),
            fields=['recipe', 'ingredient'])]


class TagSerializer(serializers.ModelSerializer):
    """
    Сериализатор для тегов.
    """

    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug',)


class RecipeSerializer(serializers.ModelSerializer):
    """
    Сериализатор для рецептов.
    """
    tags = TagSerializer(many=True)
    author = UserSerialiser(read_only=True)
    ingredients = ReadIngredientsRecipeSerializer(
        many=True,
        read_only=True,
        source='amount_ingredient',
    )
    is_favorited = serializers.SerializerMethodField(read_only=True)
    is_in_shopping_cart = serializers.SerializerMethodField(read_only=True)
    image = Base64ImageField(use_url=True, )

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'author', 'ingredients',
            'is_favorited', 'is_in_shopping_cart',
            'name', 'image', 'text', 'cooking_time',
        )

    def get_is_in_shopping_cart(self, obj):
        user = self.context.get('request').user
        return ShoppingCart.objects.filter(
            user=user, recipe=obj
        ).exists() if all(
            [user.is_authenticated, self.context.get('request') is not None]
        ) else False

    def get_is_favorited(self, obj):
        user = self.context.get('request').user
        return Favorite.objects.filter(user=user, recipe=obj).exists() if all(
            [user.is_authenticated, self.context.get('request') is not None]
        ) else False


class RecipeCreateSerializer(serializers.ModelSerializer):
    """
    Сериализатор для добавления рецептов.
    """
    author = UserSerialiser(read_only=True)
    ingredients = IngredientCreateSerializer(many=True)
    image = Base64ImageField(use_url=True, required=True)
    cooking_time = serializers.IntegerField(required=True)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True
    )

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'author', 'ingredients',
            'name', 'image', 'text', 'cooking_time',
        )

    def validate_cooking_time(self, value):
        """
        Валидация времени приготовления блюда.
        """
        if value <= 0:
            raise serializers.ValidationError(MINIMUM_COOKING_TIME)
        return value

    def validate_tags(self, value):
        if not value:
            raise serializers.ValidationError(
                "Список тегов не может быть пустым"
            )
        return value

    def validate_ingredients(self, value):
        if not value:
            raise serializers.ValidationError(
                "Список ингредиентов не может быть пустым"
            )
        return value

    def create_ingredients(self, ingredients, recipe):
        ingredient_objs = []
        for ingredient in ingredients:
            ingredient_obj, created = Ingredient.objects.get_or_create(
                id=ingredient['id']
            )
            amount_ingredient = AmountIngredient(
                ingredients=ingredient_obj,
                recipe=recipe,
                amount=ingredient['amount']
            )
            ingredient_objs.append(amount_ingredient)
        AmountIngredient.objects.bulk_create(ingredient_objs)

    @transaction.atomic
    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)
        self.create_ingredients(ingredients, recipe)
        return recipe

    def update(self, instance, validated_data):
        if 'ingredients' in validated_data:
            ingredients = validated_data.pop('ingredients')
            instance.ingredients.clear()
            self.create_ingredients(ingredients, instance)
        if 'tags' in validated_data:
            instance.tags.set(
                validated_data.pop('tags'))
        return super().update(
            instance, validated_data)

    def to_representation(self, recipe):
        return RecipeSerializer(
            recipe, context={'request': self.context.get('request')}
        ).data


class RecipeForFollowersSerializer(serializers.ModelSerializer):
    """
    Сериализатор для показа рецептов в подписке.
    """
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time',)


class FollowSerializer(serializers.ModelSerializer):
    """
    Сериализатор подписок пользователей.
    """
    is_subscribed = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField(read_only=True)
    first_name = serializers.ReadOnlyField(source='author.first_name')
    email = serializers.ReadOnlyField(source='author.email')
    username = serializers.ReadOnlyField(source='author.username')
    last_name = serializers.ReadOnlyField(source='author.last_name')
    id = serializers.ReadOnlyField(source='author.id')
    recipes = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username', 'first_name',
            'last_name', 'is_subscribed',
            'recipes', 'recipes_count'
        )

    def get_is_subscribed(self, obj):
        return Follow.objects.filter(user=obj.user, author=obj.author).exists()

    def get_recipes_count(self, obj):
        return Recipe.objects.filter(author=obj.author).count()

    def get_recipes(self, obj):
        request = self.context.get('request')
        recipes_limit = request.GET.get('recipes_limit')
        recipes = Recipe.objects.filter(author=obj.author)
        if recipes_limit:
            recipes = recipes[:int(recipes_limit)]
        serializer = RecipeForFollowersSerializer(recipes, many=True)
        return serializer.data
