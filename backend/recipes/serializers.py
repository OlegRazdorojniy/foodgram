from django.db import transaction
from recipes.fields import Base64ImageField
from recipes.models import Ingredient, Recipe, RecipeIngredient, Tag
from rest_framework import serializers
from users.serializers import UserSerializer


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug')


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class RecipeIngredientSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        source='ingredient.id',
        queryset=Ingredient.objects.all(),
    )
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)
    author = UserSerializer(read_only=True)
    ingredients = RecipeIngredientSerializer(
        source='recipe_ingredients',
        many=True,
        read_only=True,
    )
    image = Base64ImageField()
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'name',
            'image',
            'text',
            'cooking_time',
            'is_favorited',
            'is_in_shopping_cart',
        )

    def get_is_favorited(self, obj):
        user = self.context.get('request').user
        if user.is_anonymous:
            return False
        return obj.in_favorites.filter(id=user.id).exists()

    def get_is_in_shopping_cart(self, obj):
        user = self.context.get('request').user
        if user.is_anonymous:
            return False
        return obj.in_shopping_cart.filter(id=user.id).exists()

    def validate(self, attrs):
        ingredients = self.initial_data.get('ingredients')
        if not ingredients:
            raise serializers.ValidationError(
                {'ingredients': 'Нужен хотя бы один ингредиент'}
            )

        ingredient_list = []
        for ingredient_item in ingredients:
            ingredient = ingredient_item['id']
            if ingredient in ingredient_list:
                raise serializers.ValidationError(
                    {'ingredients': 'Ингредиенты не должны повторяться'}
                )
            ingredient_list.append(ingredient)
            amount = ingredient_item['amount']
            if int(amount) <= 0:
                raise serializers.ValidationError(
                    {
                        'amount':
                        'Количество ингредиента должно быть больше нуля'
                    }
                )

        tags = self.initial_data.get('tags')
        if not tags:
            raise serializers.ValidationError(
                {'tags': 'Нужен хотя бы один тег'}
            )
        tags_list = []
        for tag in tags:
            if tag in tags_list:
                raise serializers.ValidationError(
                    {'tags': 'Теги не должны повторяться'}
                )
            tags_list.append(tag)

        cooking_time = attrs.get('cooking_time')
        if cooking_time <= 0:
            raise serializers.ValidationError(
                {'cooking_time': 'Время приготовления должно быть больше нуля'}
            )

        return attrs

    @transaction.atomic
    def create(self, validated_data):
        tags = self.initial_data.get('tags')
        ingredients = self.initial_data.get('ingredients')

        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)

        recipe_ingredients = [
            RecipeIngredient(
                recipe=recipe,
                ingredient_id=ingredient['id'],
                amount=ingredient['amount'],
            )
            for ingredient in ingredients
        ]
        RecipeIngredient.objects.bulk_create(recipe_ingredients)

        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        tags = self.initial_data.get('tags')
        ingredients = self.initial_data.get('ingredients')

        instance.tags.clear()
        instance.tags.set(tags)

        instance.ingredients.clear()
        recipe_ingredients = [
            RecipeIngredient(
                recipe=instance,
                ingredient_id=ingredient['id'],
                amount=ingredient['amount'],
            )
            for ingredient in ingredients
        ]
        RecipeIngredient.objects.bulk_create(recipe_ingredients)

        return super().update(instance, validated_data)


class RecipeShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class RecipeShortLinkSerializer(serializers.ModelSerializer):
    short_link = serializers.CharField(source='get_short_link', read_only=True)

    class Meta:
        model = Recipe
        fields = ('short_link',)


class RecipeIngredientCreateSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all()
    )
    amount = serializers.IntegerField(min_value=1)

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')


class RecipeIngredientReadSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeCreateSerializer(serializers.ModelSerializer):
    image = Base64ImageField()
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
    )
    ingredients = RecipeIngredientCreateSerializer(many=True)
    author = UserSerializer(read_only=True)

    class Meta:
        model = Recipe
        fields = (
            'id',
            'name',
            'image',
            'text',
            'ingredients',
            'tags',
            'cooking_time',
            'author',
        )

    def to_representation(self, instance):
        serializer = RecipeSerializer(instance, context=self.context)
        return serializer.data

    def validate(self, data):
        required_fields = [
            'name', 'text', 'cooking_time', 'tags', 'ingredients'
        ]
        errors = {}

        for field in required_fields:
            if field not in data:
                errors[field] = ['Обязательное поле.']
            elif not data[field]:
                errors[field] = ['Это поле не может быть пустым.']

        if 'ingredients' in data:
            if not data['ingredients']:
                errors['ingredients'] = ['Добавьте хотя бы один ингредиент.']
            else:
                ingredients_set = set()
                for ingredient in data['ingredients']:
                    ingredient_id = ingredient['id'].id
                    if ingredient_id in ingredients_set:
                        errors['ingredients'] = [
                            'Ингредиенты не должны повторяться.'
                        ]
                        break
                    ingredients_set.add(ingredient_id)

        if 'tags' in data:
            if not data['tags']:
                errors['tags'] = ['Добавьте хотя бы один тег.']
            else:
                tags_set = set()
                for tag in data['tags']:
                    if tag in tags_set:
                        errors['tags'] = ['Теги не должны повторяться.']
                        break
                    tags_set.add(tag)

        if 'cooking_time' in data:
            if data['cooking_time'] <= 0:
                errors['cooking_time'] = [
                    'Время приготовления должно быть больше нуля.'
                ]

        if errors:
            raise serializers.ValidationError(errors)

        return data

    def create(self, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)

        recipe_ingredients = [
            RecipeIngredient(
                recipe=recipe,
                ingredient=ingredient['id'],
                amount=ingredient['amount']
            )
            for ingredient in ingredients
        ]
        RecipeIngredient.objects.bulk_create(recipe_ingredients)

        return recipe

    def update(self, instance, validated_data):
        tags = validated_data.pop('tags', None)
        ingredients = validated_data.pop('ingredients', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if tags is not None:
            instance.tags.clear()
            instance.tags.set(tags)

        if ingredients is not None:
            instance.recipe_ingredients.all().delete()
            recipe_ingredients = [
                RecipeIngredient(
                    recipe=instance,
                    ingredient=ingredient['id'],
                    amount=ingredient['amount']
                )
                for ingredient in ingredients
            ]
            RecipeIngredient.objects.bulk_create(recipe_ingredients)

        instance.save()
        return instance
