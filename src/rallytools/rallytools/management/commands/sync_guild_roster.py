from django.core.management.base import BaseCommand, CommandError
from guild.jobs import GuildDataImporter


class Command(BaseCommand):
    """
    """
    help = "Synchronizes a guild roster"

    def add_arguments(self, parser):
        """
        """
        parser.add_argument(
            "--guild",
            action="store",
            required=True,
            help="Guild name"
        )

        parser.add_argument(
            "--realm",
            action="store",
            required=True,
            help="Realm name/slug"
        )

    def handle(self, *args, **options):
        """
        """

        gdi = GuildDataImporter()
        results = gdi.sync_guild_roster(options['realm'], options['guild'])

        self.stdout.write(self.style.SUCCESS(results))
