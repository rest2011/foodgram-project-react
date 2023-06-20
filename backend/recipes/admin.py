from django.contrib import admin

from .models import (AmountIngredient, Favorite, Ingredient, Recipe,
                     ShoppingCart, Tag)


class RecipeIngredientsAdmin(admin.StackedInline):
    model = AmountIngredient
    autocomplete_fields = ('ingredients',)


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'name', 'author', 'text',
        'cooking_time', 'pub_date', 'favorite_counter'
    )
    search_fields = (
        'name', 'cooking_time', 'author__username', 'ingredients__name'
    )
    list_filter = ('author', 'name', 'tags',)
    inlines = (RecipeIngredientsAdmin,)
    empty_value_display = '-пусто-'

    @admin.display(description='В избранном')
    def favorite_counter(self, obj):
        return obj.favorite.count()


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'color', 'slug',)
    search_fields = ('name', 'slug',)
    empty_value_display = '-пусто-'


@admin.register(Favorite)
class FavoritesAdmin(admin.ModelAdmin):
    list_display = ('id', 'user',)
    empty_value_display = '-пусто-'


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ('id', 'user')
    empty_value_display = '-пусто-'


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'measurement_unit',)
    search_fields = ('name',)
    list_filter = ('name',)
    empty_value_display = '-пусто-'
