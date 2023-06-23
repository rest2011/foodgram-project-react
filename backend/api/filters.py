from django.db.models import Exists, OuterRef
from django_filters import rest_framework as filters

from recipes.models import Ingredient, Recipe, Favorite, ShoppingCart


class RecipeFilter(filters.FilterSet):
    """
    Класс для фильтр рецептов.
    """
    is_favorited = filters.BooleanFilter(
        field_name='is_favorited',
        method='favorite_filter'
    )
    is_in_shopping_cart = filters.BooleanFilter(
        field_name='is_in_shopping_cart',
        method='shopping_cart_filter'
    )
    tags = filters.AllValuesMultipleFilter(field_name='tags__slug')

    def favorite_filter(self, queryset, name, value):
        user = self.request.user
        if user.is_authenticated:
            queryset = queryset.annotate(
                is_favorited=Exists(
                    Favorite.objects.filter(user=user, recipe=OuterRef('pk'))
                )
            )
            return queryset.filter(favorite__user=user)

    def shopping_cart_filter(self, queryset, name, value):
        user = self.request.user
        if user.is_authenticated:
            queryset = queryset.annotate(
                is_in_shopping_cart=Exists(
                    ShoppingCart.objects.filter(
                        user=user, recipe=OuterRef('pk')
                    )
                )
            )
            return queryset.filter(shopping_cart__user=user)

    class Meta:
        model = Recipe
        fields = ('is_favorited', 'author', 'tags', 'is_in_shopping_cart',)


class IngredientFilter(filters.FilterSet):
    """
    Класс для фильтра ингридиентов.
    """
    name = filters.CharFilter(
        field_name='name',
        lookup_expr='istartswith',
    )

    class Meta:
        model = Ingredient
        fields = ('name',)
