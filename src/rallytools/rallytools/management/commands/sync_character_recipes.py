from django.core.management.base import BaseCommand, CommandError
from guild.jobs import GuildDataImporter


class Command(BaseCommand):
    """
    """
    help = "Synchronizes character recipes"

    def handle(self, *args, **options):
        """
        """

        gdi = GuildDataImporter()
        results = gdi.sync_character_recipes()

        self.stdout.write(self.style.SUCCESS(results))
