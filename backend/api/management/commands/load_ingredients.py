import csv
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from recipes.models import Ingredient


class Command(BaseCommand):
    """Добавляем ингредиенты из файла CSV."""

    def add_arguments(self, parser):
        parser.add_argument('--path', type=str,
                            help='Path to the CSX file')

    def handle(self, *args, **options):
        csv_path = options['path'] or str(
            Path(settings.BASE_BIR) / 'data',
        )

        self.import_csv_data(
            csv_path,
            'ingredients.csv',
            self.import_ingredients
        )
        self.stdout.write(
            self.style.SUCCESS('=== Ингредиенты успешно загружены ===')
        )

    def import_csv_data(self, csv_path, filename, import_func):
        file_path = Path(csv_path) / filename
        with open(file_path, 'r') as file:
            csv_data = csv.DictReader(file)
            import_func(csv_data)

    def import_ingredients(self, csv_data):
        ingredients = [Ingredient(
            name=row['name'],
            measurement_unit=row.get('measurement_unit', '')
        )for row in csv_data
        ]
        Ingredient.objects.bulk_create(ingredients)
