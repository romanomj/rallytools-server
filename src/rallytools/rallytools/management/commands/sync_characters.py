from django.core.management.base import BaseCommand, CommandError
from guild.jobs import GuildDataImporter


class Command(BaseCommand):
    """
    """
    help = "Synchronizes character data"

    def handle(self, *args, **options):
        """
        """

        gdi = GuildDataImporter()
        results = gdi.sync_characters()

        self.stdout.write(self.style.SUCCESS(results))
