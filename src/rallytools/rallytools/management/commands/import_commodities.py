from django.core.management.base import BaseCommand, CommandError
from auctionhouse.jobs import AuctionHouseImporter


class Command(BaseCommand):
    """
    """
    help = "Imports all Auction House commodities data from a battlenet snapshot"

    def handle(self, *args, **options):
        """
        """

        ahi = AuctionHouseImporter()

        results = ahi.import_commodities()

        self.stdout.write(self.style.SUCCESS(results))



