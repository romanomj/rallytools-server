import logging
from rallytools import settings
from .models import *
from lib import battlenet

logger = logging.getLogger('__name__')

class GameDataImportError(Exception):
    """
    Base exception class for jobs related to Game Data Imports
    """
    pass

class GameDataImporter(object):
    def __init__(self):
        self.battlenet_client = battlenet.BattleNetAPI(settings.BATTLENET_CLIENT_ID, settings.BATTLENET_CLIENT_SECRET)

    def import_playable_races(self):
        num_success = 0
        try:
            response = self.battlenet_client.get_playable_races()

            # Get All Race Data
            for playable_race in response['races']:
                entry, created = PlayableRace.objects.get_or_create(
                    id=playable_race['id'],
                    name=playable_race['name']
                )
                num_success += 1

        except Exception as e:
            raise GameDataImportError(f"Failed to get playable races: {e}")

        return {"num_success": num_success} 


    def import_playable_classes(self):
        """
        """
        num_success = 0
        try:
            response = self.battlenet_client.get_playable_classes()
            
            # Get all playable class data at the top level first
            for playable_class in response['classes']:
                # Then look for associated media - the icon for example
                media_response = self.battlenet_client.get_playable_class_media(playable_class['id'])
                icon = media_response['assets'][0]['value'] # Always first item in the array
            
                entry, created = PlayableClass.objects.get_or_create(
                    id=playable_class['id'],
                    name=playable_class['name'],
                    icon=icon
                )
                num_success += 1

        except Exception as e:
            raise GameDataImportError(f"Failed to get playable classes: {e}")

        return {"num_success": num_success} 


    def import_playable_specializations(self):
        """
        """
        num_success = 0
        try:
            response = self.battlenet_client.get_playable_specializations()

            # Get all playable specialization data at the top level first
            for playable_specialization in response['character_specializations']:
                # Then get specialization specifics
                specialization_response = self.battlenet_client.get_playable_specializations(playable_specialization['id'])
                playable_class_id = specialization_response['playable_class']['id']

                media_response = self.battlenet_client.get_playable_specialization_media(playable_specialization['id'])
                icon = media_response['assets'][0]['value']

                playable_class = PlayableClass.objects.get(id=playable_class_id)

                entry, created = PlayableSpecialization.objects.get_or_create(
                    id=playable_specialization['id'],
                    name=playable_specialization['name'],
                    icon=icon,
                    playable_class=playable_class,
                    role=specialization_response['role']['name']
                )
                num_success += 1


        except Exception as e:
            raise GameDataImportError(f"Failed to get playable specializations: {e}")

        return {"num_success": num_success} 


    def import_professions(self):
        """
        """
        num_success = 0
        try:
            response = self.battlenet_client.get_professions()

            for profession in response['professions']:
                media_response = self.battlenet_client.get_profession_media(profession['id'])

                entry, created = Profession.objects.get_or_create(
                    id=profession['id'],
                    name=profession['name'],
                    icon=media_response['assets'][0]['value']
                )
                num_success += 1

        except Exception as e:
            logger.error(f"ERROR: failed to import profession data for profession {profession['id']}: {e}")
            raise GameDataImportError(f"Failed to import profession data: {e}")

        return {"num_success": num_success}

    def import_profession_skill_tiers(self):
        """
        """
        num_success = 0
        try:
            professions = Profession.objects.all()
            for profession in professions:
                profession_response = self.battlenet_client.get_professions(id=profession.id)
                if 'skill_tiers' not in profession_response:
                    continue #This is a profession without a specialization or tier

                for tier in profession_response['skill_tiers']:
                    entry, created = ProfessionSkillTier.objects.get_or_create(
                        id=tier['id'],
                        name=tier['name'],
                        profession=profession
                    )
                    num_success += 1
        except Exception as e:
            raise GameDataImportError(f"Failed to import profession skill tier data: {tier['id']} {tier['name']}: {e}")

        return {"num_success": num_success}

    def sync_recipe(self, id, skill_tier):
        """
        """

        logger.debug(f"DEBUG: sync recipe {id}")

        if isinstance(skill_tier, int):
            # if we only have an instead of a class instance, fetch the class
            skill_tier = ProfessionSkillTier.objects.get(id=skill_tier)

        num_recipes_added = 0
        num_reagents_added = 0

        recipe_media_response = self.battlenet_client.get_recipe_media(id=id)

        recipe_response = self.battlenet_client.get_recipe(id=id)
        crafted_quantity = self.extract_crafted_quantity(recipe_response)

        recipe_entry, recipe_created = Recipe.objects.get_or_create(
            id=id,
            name=recipe_response['name'],
            icon=recipe_media_response['assets'][0]['value'],
            profession=skill_tier.profession,
            profession_skill_tier=skill_tier,
            crafted_quantity=crafted_quantity
        )
        num_recipes_added += 1

        if 'reagents' in recipe_response:
            logger.debug(f"Recipe {id} has reagents")
            for reagent in recipe_response['reagents']:
                logger.info(f"INFO: Add reagent {reagent['reagent']['id']}")
                reagent_entry, reagent_created = Reagent.objects.get_or_create(
                    id=reagent['reagent']['id'],
                    name=reagent['reagent']['name'],
                )

                reagent_recipe_entry, recipe_reagent_created = RecipeReagent.objects.get_or_create(
                    reagent=reagent_entry,
                    quantity=reagent['quantity'],
                    recipe=recipe_entry
                )
                num_reagents_added += 1

        return {'num_recipes_added': num_recipes_added, 'num_reagents_added': num_reagents_added}

    def extract_crafted_quantity(self, recipe_response):
        """
        """
        if 'crafted_quantity' not in recipe_response:
            return 1
        if 'value' in recipe_response['crafted_quantity']:
            return recipe_response['crafted_quantity']['value']
        if 'minimum' in recipe_response['crafted_quantity'] and 'maximum' in recipe_response['crafted_quantity']:
            minimum = recipe_response['crafted_quantity']['minimum'] 
            maximum = recipe_response['crafted_quantity']['maximum']
            return ((minimum+maximum) / 2)
        return 1



    def import_recipes_and_reagents(self):
        """
        """

        num_recipes_added = 0
        num_reagents_added = 0

        logger.debug("DEBUG: Init import recipes and reagents")
       
        skill_tiers = ProfessionSkillTier.objects.all()

        # Get some ids for caching, skipping redundant work
        known_recipes = Recipe.objects.all().values_list('id', flat=True)
        logger.debug("DEBUG: pulled known recipes")

           

        for skill_tier in skill_tiers:
            try:
                skill_tier_response = self.battlenet_client.get_profession_skill_tier(profession_id=skill_tier.profession.id, skill_tier_id=skill_tier.id)
                for category in skill_tier_response.get('categories', []):
                    #Get categories or default to blank - some professions like gathering professions have no crafts

                    # Get the High level Recipe, then get and set the details
                    for recipe in category['recipes']:

                        if recipe['id'] in known_recipes:
                            logger.debug(f"DEBUG: Skip recipe {recipe['id']} - already known")
                            continue # Already tracked

                        logger.info(f"INFO: Add recipe {recipe['id']}")

                        # First set the recipe + media
                        results = self.sync_recipe(recipe['id'], skill_tier)
                        num_recipes_added += results['num_recipes_added']
                        num_reagents_added += results['num_reagents_added']
       

            except Exception as e:
                logger.error(f"ERROR: Failed to import profession recipe data for skill tier {skill_tier.id}: {e}")
                raise GameDataImportError(f"Failed to import profession recipe data for skill tier {skill_tier.id}: {e}")

        return {"num_recipes_added": num_recipes_added, "num_reagents_added": num_reagents_added}

