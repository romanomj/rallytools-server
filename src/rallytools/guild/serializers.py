from rest_framework import serializers
from .models import Guild, Team, Character, Application
from gamedata.models import Recipe # Recipe is in gamedata app

class RecipeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        # Valid fields from Recipe model: id, name, icon, profession, profession_skill_tier, crafted_quantity
        fields = ['id', 'name', 'icon', 'profession', 'profession_skill_tier', 'crafted_quantity']
        read_only_fields = fields

class TeamSerializer(serializers.ModelSerializer):
    # The Team model doesn't have faction, type, active, discord_channel_id, discord_role_id
    # It has name, short_name, color, guild
    class Meta:
        model = Team
        fields = ['id', 'name', 'short_name', 'color', 'guild']
        read_only_fields = fields

class CharacterSerializer(serializers.ModelSerializer):
    known_recipes = RecipeSerializer(many=True, read_only=True)
    team = TeamSerializer(read_only=True)
    guild = serializers.StringRelatedField(read_only=True)
    playable_class = serializers.StringRelatedField(read_only=True)
    # active_spec is the field name in the model for playable_spec
    playable_spec = serializers.StringRelatedField(read_only=True, source='active_spec')
    # player_name, faction, race, thumbnail_url, is_main are not in the Character model
    # Model fields: id, name, level, guild, guild_rank, realm, playable_class, playable_race, active_spec, icon, achievement_points, average_item_level, equipped_item_level, known_recipes, team, last_updated

    class Meta:
        model = Character
        fields = [
            'id', 'name', 'level', 'guild', 'guild_rank', 'realm', 'playable_class',
            'playable_race', 'playable_spec', 'icon', 'achievement_points',
            'average_item_level', 'equipped_item_level', 'team', 'known_recipes', 'last_updated'
        ]
        read_only_fields = fields

class GuildSerializer(serializers.ModelSerializer):
    # related_name for Team.guild is not explicitly set, so it defaults to 'team_set'
    teams = TeamSerializer(many=True, read_only=True, source='team_set')

    class Meta:
        model = Guild
        # Model fields: id, name, realm, icon, timezone, region, faction
        fields = ['id', 'name', 'realm', 'icon', 'timezone', 'region', 'faction', 'teams']
        read_only_fields = fields

class ApplicationSerializer(serializers.ModelSerializer):
    team = TeamSerializer(read_only=True)
    guild = serializers.StringRelatedField(read_only=True)
    # The request was to search by name, discord name, and team name.
    # Model fields: id, name, discord_name, guild, team, app_data, delivered
    # Other fields from initial plan (battlenet_name, age, etc.) are not in the Application model.
    # app_data likely contains more details, but is not directly queryable for specific fields unless parsed.

    class Meta:
        model = Application
        fields = [
            'id', 'name', 'discord_name', 'guild', 'team', 'app_data', 'delivered'
        ]
        read_only_fields = fields
