import os

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management.base import BaseCommand

from recipes.models import Ingredient, Recipe, RecipeIngredient, Tag
from users.models import User


class Command(BaseCommand):
    help = 'Loads test data for Foodgram project'

    def handle(self, *args, **options):
        test_tags = [
            {'name': 'Завтрак', 'color': '#E26C2D', 'slug': 'breakfast'},
            {'name': 'Обед', 'color': '#49B64E', 'slug': 'lunch'},
            {'name': 'Ужин', 'color': '#8775D2', 'slug': 'dinner'},
            {'name': 'Десерт', 'color': '#FFC107', 'slug': 'dessert'},
            {'name': 'Первое', 'color': '#E52037', 'slug': 'first-course'},
        ]

        for tag_data in test_tags:
            Tag.objects.get_or_create(**tag_data)

        test_users = [
            {
                'email': 'user@example.com',
                'username': 'user',
                'first_name': 'Иван',
                'last_name': 'Иванов',
                'password': 'testpass123',
            },
            {
                'email': 'chef@example.com',
                'username': 'chef',
                'first_name': 'Петр',
                'last_name': 'Петров',
                'password': 'testpass123',
            },
        ]

        users = []
        for user_data in test_users:
            user, created = User.objects.get_or_create(
                email=user_data['email'],
                username=user_data['username'],
                defaults={
                    'first_name': user_data['first_name'],
                    'last_name': user_data['last_name'],
                }
            )
            if created:
                user.set_password(user_data['password'])
                user.save()
            users.append(user)

        test_recipes = [
            {
                'name': 'Омлет с сыром',
                'text': 'Классический омлет с сыром на завтрак',
                'cooking_time': 15,
                'tags': ['breakfast'],
                'ingredients': [
                    {'name': 'Яйцо куриное', 'amount': 3},
                    {'name': 'Молоко', 'amount': 100},
                    {'name': 'Сыр', 'amount': 50},
                    {'name': 'Соль', 'amount': 5},
                ],
            },
            {
                'name': 'Борщ',
                'text': 'Традиционный украинский борщ',
                'cooking_time': 120,
                'tags': ['lunch', 'first-course'],
                'ingredients': [
                    {'name': 'Свекла', 'amount': 300},
                    {'name': 'Картофель', 'amount': 400},
                    {'name': 'Капуста белокочанная', 'amount': 300},
                    {'name': 'Морковь', 'amount': 100},
                    {'name': 'Лук репчатый', 'amount': 100},
                ],
            },
            {
                'name': 'Паста Карбонара',
                'text': 'Итальянская паста с беконом и сыром',
                'cooking_time': 30,
                'tags': ['lunch', 'dinner'],
                'ingredients': [
                    {'name': 'Спагетти', 'amount': 200},
                    {'name': 'Бекон', 'amount': 150},
                    {'name': 'Сыр пармезан', 'amount': 50},
                    {'name': 'Яйцо куриное', 'amount': 2},
                ],
            },
            {
                'name': 'Тирамису',
                'text': 'Классический итальянский десерт',
                'cooking_time': 60,
                'tags': ['dessert'],
                'ingredients': [
                    {'name': 'Печенье савоярди', 'amount': 200},
                    {'name': 'Маскарпоне', 'amount': 500},
                    {'name': 'Кофе', 'amount': 200},
                    {'name': 'Яйцо куриное', 'amount': 3},
                ],
            },
            {
                'name': 'Греческий салат',
                'text': 'Легкий салат с фетой и оливками',
                'cooking_time': 15,
                'tags': ['lunch'],
                'ingredients': [
                    {'name': 'Помидоры', 'amount': 200},
                    {'name': 'Огурцы', 'amount': 200},
                    {'name': 'Сыр фета', 'amount': 100},
                    {'name': 'Маслины', 'amount': 50},
                    {'name': 'Лук красный', 'amount': 50},
                ],
            },
            {
                'name': 'Куриный суп',
                'text': 'Легкий куриный суп с вермишелью',
                'cooking_time': 60,
                'tags': ['lunch', 'first-course'],
                'ingredients': [
                    {'name': 'Курица', 'amount': 500},
                    {'name': 'Морковь', 'amount': 100},
                    {'name': 'Лук репчатый', 'amount': 100},
                    {'name': 'Вермишель', 'amount': 100},
                ],
            },
            {
                'name': 'Блины',
                'text': 'Классические русские блины',
                'cooking_time': 45,
                'tags': ['breakfast', 'dessert'],
                'ingredients': [
                    {'name': 'Мука пшеничная', 'amount': 200},
                    {'name': 'Молоко', 'amount': 500},
                    {'name': 'Яйцо куриное', 'amount': 2},
                    {'name': 'Сахар', 'amount': 50},
                ],
            },
            {
                'name': 'Цезарь с курицей',
                'text': 'Популярный салат с курицей и соусом цезарь',
                'cooking_time': 30,
                'tags': ['lunch'],
                'ingredients': [
                    {'name': 'Куриное филе', 'amount': 300},
                    {'name': 'Салат романо', 'amount': 200},
                    {'name': 'Сыр пармезан', 'amount': 50},
                    {'name': 'Хлеб белый', 'amount': 100},
                ],
            },
            {
                'name': 'Пицца Маргарита',
                'text': 'Классическая итальянская пицца',
                'cooking_time': 45,
                'tags': ['lunch', 'dinner'],
                'ingredients': [
                    {'name': 'Тесто для пиццы', 'amount': 300},
                    {'name': 'Томатный соус', 'amount': 100},
                    {'name': 'Сыр моцарелла', 'amount': 200},
                    {'name': 'Базилик', 'amount': 20},
                ],
            },
            {
                'name': 'Чизкейк',
                'text': 'Нью-Йоркский чизкейк',
                'cooking_time': 90,
                'tags': ['dessert'],
                'ingredients': [
                    {'name': 'Сыр сливочный', 'amount': 500},
                    {'name': 'Печенье песочное', 'amount': 200},
                    {'name': 'Сливки', 'amount': 200},
                    {'name': 'Яйцо куриное', 'amount': 4},
                ],
            },
        ]

        img_path = os.path.join(
            settings.BASE_DIR,
            'recipes/fixtures/test_image.jpg'
        )
        with open(img_path, 'rb') as img:
            image = SimpleUploadedFile(
                name='test_image.jpg',
                content=img.read(),
                content_type='image/jpeg'
            )

        for i, recipe_data in enumerate(test_recipes):
            recipe = Recipe.objects.create(
                author=users[i % len(users)],
                name=recipe_data['name'],
                text=recipe_data['text'],
                cooking_time=recipe_data['cooking_time'],
                image=image,
            )

            for tag_slug in recipe_data['tags']:
                tag = Tag.objects.get(slug=tag_slug)
                recipe.tags.add(tag)

            for ingredient_data in recipe_data['ingredients']:
                ingredient = Ingredient.objects.get(
                    name=ingredient_data['name']
                )
                RecipeIngredient.objects.create(
                    recipe=recipe,
                    ingredient=ingredient,
                    amount=ingredient_data['amount'],
                )

        self.stdout.write(
            self.style.SUCCESS('Successfully loaded test data')
        )
