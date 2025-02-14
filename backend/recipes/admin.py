from django.contrib import admin
from django.db.models import Count

from recipes.models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
    Tag,
)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'color', 'slug')
    search_fields = ('name', 'slug')
    list_filter = ('name',)
    empty_value_display = '-пусто-'


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit')
    search_fields = ('name',)
    list_filter = ('name',)
    empty_value_display = '-пусто-'


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    min_num = 1
    extra = 1
    verbose_name = 'Ингредиент'
    verbose_name_plural = 'Ингредиенты'


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'author',
        'get_favorites_count',
        'get_ingredients_display',
    )
    search_fields = ('name', 'author__username', 'author__email')
    list_filter = ('tags', 'author', 'name')
    inlines = (RecipeIngredientInline,)
    empty_value_display = '-пусто-'

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.annotate(
            favorites_count=Count('in_favorites')
        )

    def get_favorites_count(self, obj):
        return obj.favorites_count

    get_favorites_count.short_description = 'В избранном'

    def get_ingredients_display(self, obj):
        return ', '.join([
            f'{ingredient.name} - '
            f'{ingredient.recipe_ingredients.get(recipe=obj).amount}'
            f' {ingredient.measurement_unit}'
            for ingredient in obj.ingredients.all()
        ])

    get_ingredients_display.short_description = 'Ингредиенты'


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe')
    search_fields = ('user__username', 'recipe__name')
    list_filter = ('user', 'recipe')
    empty_value_display = '-пусто-'


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe')
    search_fields = ('user__username', 'recipe__name')
    list_filter = ('user', 'recipe')
    empty_value_display = '-пусто-'
