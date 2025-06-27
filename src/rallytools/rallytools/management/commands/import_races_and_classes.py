from django.core.management.base import BaseCommand, CommandError
from gamedata.jobs import GameDataImporter


class Command(BaseCommand):
    """
    """
    help = "Imports all Race, Class, and Specialization data.  You should only need to run this during installation"

    def handle(self, *args, **options):
        """
        """

        gdi = GameDataImporter()

        race_results = gdi.import_playable_races()
        class_results = gdi.import_playable_classes()
        spec_results = gdi.import_playable_specializations()

        results = f"""
        Added Races: {race_results}
        Added Classes: {class_results}
        Added Specializations: {spec_results}
        """

        self.stdout.write(self.style.SUCCESS(results))



