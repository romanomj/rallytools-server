from django.core.management.base import BaseCommand, CommandError
from gamedata.jobs import GameDataImporter


class Command(BaseCommand):
    """
    """
    help = "Imports all Profession information and icon media.  Does not include recipes"

    def handle(self, *args, **options):
        """
        """

        gdi = GameDataImporter()

        p_results = gdi.import_professions()
        st_results = gdi.import_profession_skill_tiers()

        results = f"""
        Profession Results: {p_results}
        Skill Tier Results: {st_results}
        """

        self.stdout.write(self.style.SUCCESS(results))



