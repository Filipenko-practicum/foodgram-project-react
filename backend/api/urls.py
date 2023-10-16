from django.urls import include, path, re_path
from rest_framework.routers import DefaultRouter

from users.views import UserViewSet

from .views import IngredientViewSet, RecipeViewSet, TagViewSet

app_name = 'api'

router = DefaultRouter()

router.register('users', UserViewSet, basename='users')
router.register('tags', TagViewSet, basename='tags')
router.register('recipes', RecipeViewSet, basename='recipes')
router.register('ingredients', IngredientViewSet, basename='ingredients')

urlpatterns = [
    path('', include(router.urls)),
    re_path('auth/', include('djoser.urls.authtoken')),
]
