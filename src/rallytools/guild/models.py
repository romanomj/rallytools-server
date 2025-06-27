from django.db import models
from gamedata.models import *

class Guild(models.Model):
    """
    Guild in WoW
    """
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=128, blank=False, null=False, db_index=True, help_text="Guild name")
    realm = models.CharField(max_length=128, blank=False, null=False, db_index=True, help_text="Guild Server/Realm")
    icon = models.CharField(max_length=255, blank=True, null=True, help_text="Guild icon (not emblem)")
    timezone = models.CharField(max_length=64, default='US/Eastern')
    region = models.CharField(max_length=2, blank=False, null=False,
            choices = [
                ('us', 'us'),
                ('eu', 'eu')
                ],
            help_text="Region to retrieve guild data")
    faction = models.CharField(max_length=8, blank=False, null=False,
            choices = [
                ('Horde', 'Horde'),
                ('Alliance', 'Alliance')
                ],
        help_text="Horde/Alliance")

    def __str__(self):
        return self.name


class Team(models.Model):
    """
    Raid/Dungeon/PvP/etc Team in WoW.  Not a standard tracked entity
    """
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=32, unique=True, db_index=True)
    short_name = models.CharField(max_length=7, unique=True, db_index=True)
    color = models.CharField(max_length=7, default='#000000', help_text="Color used for display purposes")
    guild = models.ForeignKey(Guild, on_delete=models.SET_NULL, null=True, db_index=True)

    class Meta:
        unique_together = ("guild", "name")

    def __str__(self):
        return f"{self.name} ({self.guild.name})"


class Character(models.Model):
    """
    Player character in WoW
    """
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=32, blank=False, db_index=True, help_text="Character Name")
    level = models.IntegerField()
    guild = models.ForeignKey(Guild, on_delete=models.SET_NULL, null=True, db_index=True)
    guild_rank = models.IntegerField(null=True)
    realm = models.CharField(max_length=32, db_index=True)

    playable_class = models.ForeignKey(PlayableClass, on_delete=models.PROTECT, related_name='characters', help_text="Character's Class")
    playable_race = models.ForeignKey(PlayableRace, on_delete=models.PROTECT, related_name='characters', help_text="Character's Race")
    active_spec = models.ForeignKey(PlayableSpecialization, on_delete=models.PROTECT, related_name='characters', help_text="Character's Active Specialization", null=True)

    icon = models.CharField(max_length=128, help_text="Wow Avatar Render Image", blank=True)
    achievement_points = models.IntegerField(default=0)

    average_item_level = models.IntegerField(default=0)
    equipped_item_level = models.IntegerField(default=0)

    known_recipes = models.ManyToManyField(Recipe)

    team = models.ForeignKey(Team, on_delete=models.SET_NULL, null=True, db_index=True)

    last_updated = models.DateField(auto_now=True)

    def __str__(self):
        return f"{self.name} - {self.realm}"



class Application(models.Model):
    """
    Recuitment purposes.  Tracks applicants to a guild
    """
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=32, db_index=True, help_text="WoW character name")
    discord_name = models.CharField(max_length=32, help_text="Discord name")
    guild = models.ForeignKey(Guild, on_delete=models.CASCADE)
    team = models.ForeignKey(Team, null=True, on_delete=models.SET_NULL)
    app_data = models.TextField()
    delivered = models.BooleanField(default=False, help_text="Track state of application.  Has it been delivered to the guild?")

    def __str__(self):
        return f"{self.name} - {self.discord_name}"

