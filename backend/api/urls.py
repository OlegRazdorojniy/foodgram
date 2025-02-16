from api.views import IngredientViewSet, UserViewSet
from django.urls import include, path
from recipes.views import RecipeViewSet, TagViewSet
from rest_framework.routers import DefaultRouter

app_name = 'api'

router = DefaultRouter()
router.register('users', UserViewSet)
router.register('recipes', RecipeViewSet, basename='recipes')
router.register('tags', TagViewSet, basename='tags')
router.register('ingredients', IngredientViewSet, basename='ingredients')

urlpatterns = [
    path('', include(router.urls)),
]
