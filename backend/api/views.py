from http import HTTPStatus

from django.db.models import Sum, Exists, OuterRef
from django.http import HttpResponse
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from rest_framework import filters, generics, status, viewsets
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.response import Response


from .filters import IngredientFilter, RecipeFilter
from .permissions import IsAuthor, IsUser
from .serializers import (FollowSerializer, IngredientSerializer,
                          UserSerialiser, RecipeCreateSerializer,
                          RecipeForFollowersSerializer, RecipeSerializer,
                          TagSerializer)
from recipes.models import (AmountIngredient, Favorite, Ingredient,
                            Recipe, ShoppingCart, Tag)
from users.models import Follow, User

NOT_SELF_SUBSCRIBE = 'На себя подписаться нельзя'
DOUBLE_SUBSCRIBE = 'Вы уже подписаны на этого автора'
NOT_SUBSCRIBED = 'Вы не подписаны на автора и отписка от него невозможна'


class UsersViewSet(UserViewSet):
    """
    Вьюсет для пользователей.
    """
    queryset = User.objects.all()
    serializer_class = UserSerialiser
    filter_backends = (DjangoFilterBackend, filters.SearchFilter,)
    permission_classes = (AllowAny,)
    search_fields = ('username', 'email')

    def get_permissions(self):
        if self.action == 'me' or self.action == 'retrieve':
            self.permission_classes = [IsUser]
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


class FollowUnfollow(generics.RetrieveDestroyAPIView,
                     generics.ListCreateAPIView):
    """
    Вьюсет для управления подпиской и отпиской.
    """
    permission_classes = (IsAuthenticated,)
    serializer_class = FollowSerializer

    def get_queryset(self):
        return self.request.user.follower.all()

    def get_object(self):
        user_id = self.kwargs['user_id']
        user = get_object_or_404(User, id=user_id)
        return user

    def create(self, request, *args, **kwargs):
        instance = self.get_object()
        if request.user.id == instance.id:
            return Response({'errors': NOT_SELF_SUBSCRIBE},
                            status=status.HTTP_400_BAD_REQUEST)
        if request.user.follower.filter(author=instance).exists():
            return Response(
                {'errors': DOUBLE_SUBSCRIBE},
                status=status.HTTP_400_BAD_REQUEST)
        subs = request.user.follower.create(author=instance)
        serializer = self.get_serializer(subs)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def perform_destroy(self, instance):
        if self.request.user.follower.filter(author=instance).exists():
            self.request.user.follower.filter(author=instance).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(
            {'errors': NOT_SUBSCRIBED}, status=status.HTTP_400_BAD_REQUEST,
        )


class RecipeViewSet(viewsets.ModelViewSet):
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    permission_classes = (AllowAny,)

    def get_permissions(self):
        if self.action in ['create']:
            self.permission_classes = (AllowAny,)
        if self.action in ['update', 'delete']:
            self.permission_classes = (IsAdminUser | IsAuthor)
        return super().get_permissions()

    def get_serializer_class(self):
        if self.action in ['retrieve', 'list']:
            return RecipeSerializer
        if self.action in ['create', 'partial_update']:
            return RecipeCreateSerializer

    def get_queryset(self):
        if self.request.user.is_authenticated:
            user_id = self.request.user.id
            return Recipe.objects.annotate(
                is_favorited=Exists(
                    Favorite.objects.filter(
                        user_id=user_id, recipe=OuterRef('pk')
                    )
                ),
                is_in_shopping_cart=Exists(
                    ShoppingCart.objects.filter(
                        user_id=user_id, recipe=OuterRef('pk')
                    )
                )
            )
        return Recipe.objects.all()

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def add_recipe(self, model, request, pk):
        recipe = get_object_or_404(Recipe, id=pk)
        obj, created = model.objects.get_or_create(
            recipe=recipe, user=request.user
        )
        if not created:
            return Response({'errors': 'Данный рецепт уже был добавлен'},
                            status=HTTPStatus.BAD_REQUEST)
        serializer = RecipeForFollowersSerializer(recipe)
        return Response(data=serializer.data, status=HTTPStatus.CREATED)

    def delete_recipe(self, model, request, pk):
        recipe = get_object_or_404(Recipe, id=pk)
        if model.objects.filter(user=request.user, recipe=recipe).exists():
            model.objects.filter(user=request.user, recipe=recipe).delete()
            return Response(status=HTTPStatus.NO_CONTENT)
        return Response({'errors': 'Такой рецепт не добавлялся'},
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

    def generate_shopping_cart_text(self, ingredients):
        text = 'Продукты к покупке:\n'
        for ingredient in ingredients:
            text += f'- {ingredient["ingredients__name"]} - '
            text += f'{ingredient["value"]} '
            text += f'{ingredient["ingredients__measurement_unit"]}\n'
        return text

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
        response.write(self.generate_shopping_cart_text(ingredients))
        return response


class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AllowAny,)
    pagination_class = None


class IngredientViewSet(viewsets.ModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (DjangoFilterBackend, filters.SearchFilter,)
    filterset_class = IngredientFilter
    pagination_class = None
    permission_classes = (AllowAny,)
