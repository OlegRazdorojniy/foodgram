import json

from django.core.management.base import BaseCommand

from recipes.models import Ingredient


class Command(BaseCommand):
    help = 'Load ingredients from ingredients.json'

    def handle(self, *args, **options):
        with open('data/ingredients.json', 'r', encoding='utf-8') as file:
            ingredients = json.load(file)

            for ingredient in ingredients:
                Ingredient.objects.get_or_create(
                    name=ingredient['name'],
                    measurement_unit=ingredient['measurement_unit']
                )

        self.stdout.write(
            self.style.SUCCESS('Successfully loaded ingredients')
        )
