from http import HTTPStatus

from django.db.models import Sum
from django.http import HttpResponse
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from recipes.models import (AmountIngredient, Favorite, Ingredient, Recipe,
                            ShoppingCart, Tag)
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from users.models import Follow, User

from .filters import IngredientFilter, RecipeFilter
from .pagination import LimitPageNumberPagination
from .permissions import AdminAndUserOrReadOnly, AdminOrAuthorOrReadOnly
from .serializers import (FollowSerializer, IngredientSerializer,
                          ListUserSerializer, RecipeCreateSerializer,
                          RecipeForFollowersSerializer, RecipeSerializer,
                          TagSerializer)

NOT_SELF_SUBSCRIBE = 'На себя подписаться нельзя'
DOUBLE_SUBSCRIBE = "Вы уже подписаны на этого автора"
NOT_SUBSCRIBED = 'Вы не подписаны на автора и отписка от него невозможна'


class UsersViewSet(UserViewSet):
    """
    Вьюсет для пользователей.
    """
    queryset = User.objects.all()
    serializer_class = ListUserSerializer
    filter_backends = (DjangoFilterBackend, filters.SearchFilter,)
    permission_classes = (AllowAny,)
    search_fields = ('username', 'email')

    def get_permissions(self):
        if self.action == 'me' or self.action == 'retrieve':
            self.permission_classes = [IsAuthenticated]
        return super().get_permissions()

    @action(
        methods=['GET'],
        detail=False,
        permission_classes=(IsAuthenticated,)
    )
    def subscriptions(self, request):
        user = request.user
        queryset = Follow.objects.filter(user=user)
        page = self.paginate_queryset(queryset)
        serializer = FollowSerializer(
            page, many=True, context={'request': request}
        )
        return self.get_paginated_response(serializer.data)

    @action(
        methods=['POST', 'DELETE'], detail=True,
        permission_classes=(IsAuthenticated,)
    )
    def subscribe(self, request, id):
        author = get_object_or_404(User, id=id)
        if request.method == 'POST':
            if request.user.id == author.id:
                return Response(
                    {"errors": NOT_SELF_SUBSCRIBE},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if Follow.objects.filter(
                user=request.user, author=author
            ).exists():
                return Response(
                    {"errors": DOUBLE_SUBSCRIBE},
                    status=status.HTTP_400_BAD_REQUEST
                )
            serializer = FollowSerializer(
                Follow.objects.create(user=request.user, author=author),
                context={'request': request},
            )
            return Response(
                serializer.data, status=status.HTTP_201_CREATED
            )
        elif request.method == 'DELETE':
            if Follow.objects.filter(
                    user=request.user, author=author
            ).exists():
                Follow.objects.filter(
                    user=request.user, author=author
                ).delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response(
                {"errors": NOT_SUBSCRIBED}, status=status.HTTP_400_BAD_REQUEST,
            )


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    pagination_class = LimitPageNumberPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    permission_classes = (AdminOrAuthorOrReadOnly,)

    def get_permissions(self):
        if (self.action in ('create', 'update', 'delete')):
            self.permission_classes = (IsAuthenticated,)
        return super().get_permissions()

    def get_serializer_class(self):
        if self.action in ('retrieve', 'list'):
            return RecipeSerializer
        if self.action in ('create', 'partial_update'):
            return RecipeCreateSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def add_recipe(self, model, request, pk):
        recipe = get_object_or_404(Recipe, id=pk)
        if model.objects.filter(recipe=recipe, user=request.user).exists():
            return Response({"errors": "Данный рецепт уже был добавлен"},
                            status=HTTPStatus.BAD_REQUEST)
        model.objects.create(recipe=recipe, user=request.user)
        serializer = RecipeForFollowersSerializer(recipe)
        return Response(data=serializer.data, status=HTTPStatus.CREATED)

    def delete_recipe(self, model, request, pk):
        recipe = get_object_or_404(Recipe, id=pk)
        if model.objects.filter(user=request.user, recipe=recipe).exists():
            model.objects.filter(user=request.user, recipe=recipe).delete()
            return Response(status=HTTPStatus.NO_CONTENT)
        return Response({"errors": "Такой рецепт не добавлялся"},
                        status=HTTPStatus.BAD_REQUEST)

    @action(
        detail=True, methods=['DELETE', 'POST'],
        permission_classes=(IsAuthenticated,)
    )
    def favorite(self, request, pk=None):
        return self.add_recipe(
            Favorite, request, pk
        ) if request.method == 'POST' else self.delete_recipe(
            Favorite, request, pk
        )

    @action(
        detail=True, methods=['DELETE', 'POST'],
        permission_classes=(IsAuthenticated,)
    )
    def shopping_cart(self, request, pk):
        return self.add_recipe(
            ShoppingCart, request, pk
        ) if request.method == 'POST' else self.delete_recipe(
            ShoppingCart, request, pk
        )

    @action(
        detail=False, methods=['GET'],
        permission_classes=(IsAuthenticated,)
    )
    def download_shopping_cart(self, request):
        user = request.user
        file = 'shopping_products.txt'
        if not user.shopping_cart.exists():
            return Response(status=HTTPStatus.BAD_REQUEST)
        ingredients = AmountIngredient.objects.filter(
            recipe__shopping_cart__user=user
        ).values(
            'ingredients__name', 'ingredients__measurement_unit'
        ).annotate(value=Sum('amount')).order_by('ingredients__name')
        response = HttpResponse(content_type='text/plain', charset='utf-8')
        response['Content-Disposition'] = f'attachment; filename={file}'
        response.write('Продукты к покупке:\n')
        for ingredient in ingredients:
            response.write(
                f'- {ingredient["ingredients__name"]} '
                f'- {ingredient["value"]} '
                f'{ingredient["ingredients__measurement_unit"]}\n'
            )
        return response


class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AdminAndUserOrReadOnly,)
    pagination_class = None


class IngredientViewSet(viewsets.ModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (DjangoFilterBackend, filters.SearchFilter,)
    filterset_class = IngredientFilter
    pagination_class = None
    permission_classes = (AdminAndUserOrReadOnly,)
