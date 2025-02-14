from datetime import datetime

from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404

from django_filters.rest_framework import DjangoFilterBackend

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from recipes.filters import RecipeFilter, IngredientFilter
from recipes.models import Favorite, Recipe, ShoppingCart, Tag, Ingredient
from recipes.serializers import (
    RecipeSerializer,
    RecipeShortLinkSerializer,
    RecipeShortSerializer,
    TagSerializer,
    IngredientSerializer,
    RecipeCreateSerializer,
)
from recipes.permissions import IsAdminOrReadOnly, IsAuthorOrReadOnly


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    permission_classes = [IsAuthorOrReadOnly]
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    http_method_names = ['get', 'post', 'patch', 'delete']

    def get_serializer_class(self):
        if self.action in ('create', 'partial_update'):
            return RecipeCreateSerializer
        return RecipeSerializer

    def get_queryset(self):
        return Recipe.objects.all().prefetch_related(
            'tags',
            'ingredients',
            'recipe_ingredients',
        ).select_related('author')

    def get_permissions(self):
        if self.action in ['create']:
            return [IsAuthenticated()]
        if self.action in ['update', 'partial_update', 'destroy']:
            return [IsAuthorOrReadOnly()]
        return super().get_permissions()

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def _handle_m2m_action(self, request, pk, model_class, error_message):
        recipe = get_object_or_404(Recipe, id=pk)
        if request.method == 'POST':
            obj, created = model_class.objects.get_or_create(
                user=request.user,
                recipe=recipe,
            )
            if not created:
                return Response(
                    {'error': error_message},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            serializer = RecipeShortSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        obj = get_object_or_404(
            model_class,
            user=request.user,
            recipe=recipe,
        )
        obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated],
    )
    def favorite(self, request, pk=None):
        return self._handle_m2m_action(
            request,
            pk,
            Favorite,
            'Рецепт уже в избранном',
        )

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated],
        url_path='favorites',
    )
    def favorites(self, request):
        user = request.user
        queryset = Recipe.objects.filter(in_favorites=user)
        
        tags = self.request.query_params.getlist('tags')
        if tags:
            queryset = queryset.filter(tags__slug__in=tags).distinct()

        queryset = queryset.order_by('-pub_date')
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(
                page,
                many=True,
                context={'request': request},
            )
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(
            queryset,
            many=True,
            context={'request': request},
        )
        return Response(serializer.data)

    @action(
        detail=True,
        methods=['get'],
        url_path='get-link',
    )
    def get_short_link(self, request, pk=None):
        recipe = get_object_or_404(Recipe, id=pk)
        serializer = RecipeShortLinkSerializer(recipe)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(
        detail=False,
        methods=['get'],
        url_path='by-uuid/(?P<uuid>[^/.]+)',
    )
    def get_by_uuid(self, request, uuid):
        recipe = get_object_or_404(Recipe, short_link=uuid)
        serializer = self.get_serializer(recipe)
        return Response(serializer.data)

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated],
    )
    def shopping_cart(self, request, pk=None):
        return self._handle_m2m_action(
            request,
            pk,
            ShoppingCart,
            'Рецепт уже в списке покупок',
        )

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated],
    )
    def download_shopping_cart(self, request):
        ingredients = (
            Recipe.objects.filter(in_shopping_cart=request.user)
            .values(
                'ingredients__name',
                'ingredients__measurement_unit',
            )
            .annotate(total=Sum('recipe_ingredients__amount'))
            .order_by('ingredients__name')
        )

        shopping_list = [
            'Список покупок\n',
            '=============\n\n',
            'Дата: {}\n'.format(
                datetime.now().strftime('%d.%m.%Y')
            ),
            'Пользователь: {} {}\n\n'.format(
                request.user.first_name,
                request.user.last_name,
            ),
            'Ингредиенты:\n',
            '------------\n\n',
        ]

        for i, ingredient in enumerate(ingredients, 1):
            shopping_list.append(
                '{}. {} ({}) — {}\n'.format(
                    i,
                    ingredient['ingredients__name'],
                    ingredient['ingredients__measurement_unit'],
                    ingredient['total'],
                )
            )

        shopping_list.append(
            '\nВсего ингредиентов: {}'.format(len(ingredients))
        )

        response = HttpResponse(
            ''.join(shopping_list),
            content_type='text/plain; charset=utf-8'
        )
        response['Content-Disposition'] = (
            'attachment; filename="shopping_list.txt"'
        )
        return response


class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [IsAdminOrReadOnly]
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all().order_by('name')
    serializer_class = IngredientSerializer
    permission_classes = [IsAdminOrReadOnly]
    pagination_class = None

    def get_queryset(self):
        name = self.request.query_params.get('name')
        queryset = super().get_queryset()
        
        if name:
            queryset = queryset.filter(name__istartswith=name)
        
        return queryset
