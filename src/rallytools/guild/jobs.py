from datetime import datetime, timedelta
import logging
from rallytools import settings
from .models import *
from gamedata.models import PlayableClass, PlayableRace, PlayableSpecialization, Recipe
from gamedata.jobs import GameDataImporter
from lib import battlenet


logger = logging.getLogger(__name__)

class GuildDataImportError(Exception):
    """
    Base exception class for jobs related to Guild Data Imports
    """
    pass

class GuildDataImporter(object):
    def __init__(self):
        self.battlenet_client = battlenet.BattleNetAPI(settings.BATTLENET_CLIENT_ID, settings.BATTLENET_CLIENT_SECRET)
        self.gdi = GameDataImporter()

    def import_guild(self, realm, name):
        num_success = 0
        try:
            response = self.battlenet_client.get_guild(realm, name)
            entry, created = Guild.objects.get_or_create(
                id=response['id'],
                name=response['name'],
                realm=response['realm']['slug'],
                region=self.battlenet_client.region,
                faction=response['faction']['name']
            )
            num_success += 1

        except Exception as e:
            raise GuildDataImportError(f"Failed to import guild: {e}")

        return {"num_success": num_success} 


    def sync_guild_roster(self, realm, name):
        """
        """

        #NOTE: ADD some checks in here to fast track characters that already exist
        num_added = 0
        num_skipped = 0
        num_removed = 0

        try:
            guild = Guild.objects.filter(name=name,realm=realm)
            if not guild:
                raise GuildDataImportError(f"No existing guild named {name} on realm {realm}.  Check the name or run import_guild first")

            existing_member_ids = guild.values_list('character__id', flat=True) #Use this to skip redundant checks
            added_or_skipped = set([])
            response = self.battlenet_client.get_guild_roster(realm, name)

            # Handle additions & skip those already existing
            for member in response['members']:
                if member['character']['id'] in existing_member_ids: 
                    #Skip, they're already in the roster, and specific character sync will have a more complete data set
                    num_skipped += 1
                    added_or_skipped.update([member['character']['id']])
                    continue

                playable_class = PlayableClass.objects.get(id=member['character']['playable_class']['id']) 
                playable_race = PlayableRace.objects.get(id=member['character']['playable_race']['id'])

                entry, created = Character.objects.get_or_create(
                    id=member['character']['id'],
                    name=member['character']['name'],
                    level=member['character']['level'],
                    guild=guild[0],
                    guild_rank=member['rank'],
                    realm=member['character']['realm']['slug'],
                    playable_class=playable_class,
                    playable_race=playable_race,
                )
                added_or_skipped.update([member['character']['id']])
                num_added += 1

            # Handle members removed from guild
            member_ids_to_remove = set(existing_member_ids) - added_or_skipped
            logger.info(f"INFO: have members to remove: {len(member_ids_to_remove)}")
            for member_id in member_ids_to_remove:
                member = Character.objects.filter(id=member_id)
                member.guild = None
                member.save()
                num_removed += 1


        except Exception as e:
            raise GuildDataImportError(f"Failed to sync guild roster: {e}")

        results = {
            "num_added": num_added,
            "num_skipped": num_skipped,
            "num_removed": num_removed
        }

        return results


    def sync_characters(self):
        """
        """
        num_success = 0
        characters_not_found = []

        yesterday = datetime.now() - timedelta(days=1)
        characters = Character.objects.all() #filter(last_updated__lte=yesterday)
        logger.debug(f"DEBUG: need to sync {len(characters)} characters")

        def extract_character_icons(character_media_response):
            """
            Checks through a list of dictionaries to return the correct icons associated with a character
            """
            icons = {
                'icon': "",
                "inset_icon": "",
                "character_model": ""
            }
            assets = character_media_response['assets']
            for asset in assets:
                if asset['key'] == 'avatar':
                    icons['icon'] = asset['value']
                elif asset['key'] == 'inset':
                    icons['inset_icon'] = asset['value']
                elif asset['key'] == 'main-raw':
                    icons['character_model'] = asset['value']
            return icons

                    
        for character in characters:

            try:
                character_response = self.battlenet_client.get_character_summary(character.realm, character.name)
                character_media_response =  self.battlenet_client.get_character_media(character.realm, character.name)
                icons = extract_character_icons(character_media_response)
            except battlenet.BattleNetAPINotFoundError as e:
                logger.warning(f"WARNING: character {character.id} not found. skipping")
                characters_not_found.append(character.id)
                continue

             
            active_spec = PlayableSpecialization.objects.get(id=character_response['active_spec']['id']) 
            character.icon = icons['icon']
            character.inset_icon = icons['inset_icon']
            character.character_model = icons['character_model']
            character.active_spec = active_spec
            character.achievement_points = character_response['achievement_points']
            character.average_item_level = character_response['average_item_level']
            character.equipped_item_level = character_response['equipped_item_level']
            character.save()

            num_success += 1

        return {"num_success": num_success, 'characters_not_found': characters_not_found}




    def sync_character_recipes(self):
        """
        """

        num_added = 0
        num_removed = 0
        characters_not_found = []
        extra_results = {} #Used if we call downstream additions

        characters = Character.objects.all()
        for character in characters:
            try:
                profession_response = self.battlenet_client.get_character_professions(character.realm, character.name)
            except battlenet.BattleNetAPINotFoundError as e:
                # Some characters actually 404 ?
                logger.warning(f"WARNING: character {character.id} not found. skipping")
                characters_not_found.append(character.id)
                continue

            known_recipes = character.known_recipes.all().values_list('id', flat=True)
            known_recipes = set(known_recipes)
            discovered_recipes = set([])

            has_changes = False #Track if we need to save

            # Handle Additions
            for profession_type in ['primaries', 'secondaries']:
                for tiers in profession_response.get(profession_type, []):
                    for tier in tiers.get('tiers', []): #Some professions such as Archaeology don't have tiers
                        for recipe_response in tier.get('known_recipes', []): # People may have picked up a profession but have 0 known recipes
                            discovered_recipes.update([recipe_response['id']])
                            if recipe_response['id'] in known_recipes:
                                logger.debug(f"DEBUG: skip already known recipe {recipe_response['id']}")
                                # Skip professions already known
                                continue

                            has_changes = True

                            logger.debug(f"DEBUG: query recipe {recipe_response['id']}")
                            try:
                                recipe = Recipe.objects.get(id=recipe_response['id'])
                            except Recipe.DoesNotExist:
                                # Interesting edge case
                                local_results = self.gdi.sync_recipe(recipe_response['id'], skill_tier=tier['tier']['id'])
                                for key in local_results:
                                    if key not in extra_results:
                                        extra_results.update({key: 0})
                                    extra_results[key] += local_results[key]

                                recipe = Recipe.objects.get(id=recipe_response['id'])

                            logging.info(f"INFO: Add recipe {recipe_response['id']} to {character.id}")
                            num_added += 1
                            character.known_recipes.add(recipe)

            # Handle removals
            recipes_to_remove = known_recipes - discovered_recipes
            for recipe_to_remove in recipes_to_remove:
                has_changes = True
                logging.info(f"INFO: Remove recipe {recipe_to_remove} from {character.id}")
                recipe = Recipe.objects.get(id=recipe_to_remove)
                character.known_recipes.remove(recipe)
                num_removed += 1

            if has_changes:
                logging.info(f"INFO: Save character {character.id}")
                character.save()

        results = {"num_added": num_added, "num_removed": num_removed, 'characters_not_found': characters_not_found}
        if extra_results:
            results.update(**extra_results)
        return results




