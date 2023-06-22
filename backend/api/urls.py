from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (FollowUnfollow, IngredientViewSet,
                    RecipeViewSet, TagViewSet, UsersViewSet)

app_name = 'api'

router_v1 = DefaultRouter()

router_v1.register('users', UsersViewSet, basename='users')
router_v1.register('recipes', RecipeViewSet, basename='recipes')
router_v1.register('ingredients', IngredientViewSet, basename='ingredients')
router_v1.register('tags', TagViewSet, basename='tags')

urlpatterns = [
    path(
          'users/<int:user_id>/subscribe/',
          FollowUnfollow.as_view(),
          name='follow'),
    path('', include(router_v1.urls)),
    path('', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
]
