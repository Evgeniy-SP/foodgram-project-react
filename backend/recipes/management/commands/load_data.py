import json

from django.core.management import call_command
from django.core.management.base import BaseCommand

from recipes.models import Ingredient


class Command(BaseCommand):
    """
    Пополнения базы данных информацией по продуктам.
    """

    def handle(self, *args, **options):
        call_command('loaddata', 'fixtures/ingredients.json')
