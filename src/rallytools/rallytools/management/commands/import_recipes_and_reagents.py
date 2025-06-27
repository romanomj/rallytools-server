from django.core.management.base import BaseCommand, CommandError
from gamedata.jobs import GameDataImporter


class Command(BaseCommand):
    """
    """
    help = "Imports all Recipes and related Reagents"


    def handle(self, *args, **options):
        """
        """

        gdi = GameDataImporter()
        print(options)
        results = gdi.import_recipes_and_reagents()

        self.stdout.write(self.style.SUCCESS(results))



