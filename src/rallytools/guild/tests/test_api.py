from django.urls import reverse
from django.test import override_settings
from rest_framework import status
from rest_framework.test import APITestCase
from guild.models import Guild, Team, Character, Application
from gamedata.models import Recipe, PlayableClass, PlayableRace, PlayableSpecialization, Profession # Added Profession

# It's good practice to create some test data
def create_test_guild(name="Test Guild", realm="Test Realm", faction="Horde", region="us", id=1):
    return Guild.objects.create(id=id, name=name, realm=realm, faction=faction, region=region)

def create_test_team(name="Test Team", guild=None, id=1):
    if guild is None:
        guild = create_test_guild()
    return Team.objects.create(id=id, name=name, short_name=name[:7], guild=guild)

def create_test_profession(name="Alchemy", id=1):
    # Profession model fields are id, name, icon
    return Profession.objects.get_or_create(id=id, defaults={'name': name, 'icon': 'http://fake.icon/alchemy.jpg'})[0]

def create_test_recipe(name="Test Recipe", blizzard_id=123, id=1, profession=None): # blizzard_id is not on Recipe model, icon is.
    if profession is None:
        profession = create_test_profession()
    # Recipe model fields: id, name, icon, profession, profession_skill_tier, crafted_quantity
    # Assuming blizzard_id was meant for something else or is not part of Recipe model directly.
    # For now, creating with available fields. 'link' is also not on Recipe model.
    return Recipe.objects.create(id=id, name=name, icon="http://fake.icon/testrecipe.jpg", profession=profession)

def create_test_playable_class(name="Warrior", id=1):
    # PlayableClass model fields: id, name, icon
    return PlayableClass.objects.get_or_create(id=id, defaults={'name': name, 'icon': 'http://fake.icon/warrior.jpg'})[0]

def create_test_playable_race(name="Orc", faction="Horde", id=1): # Faction and blizzard_id are not on the model
    # PlayableRace model fields: id, name
    return PlayableRace.objects.get_or_create(id=id, defaults={'name': name})[0]

def create_test_playable_spec(name="Fury", playable_class=None, id=1):
    # PlayableSpecialization model fields: id, name, icon, playable_class, role
    if playable_class is None:
        playable_class = create_test_playable_class()
    return PlayableSpecialization.objects.get_or_create(id=id, defaults={'name': name, 'playable_class': playable_class, 'icon': 'http://fake.icon/fury.jpg', 'role': 'DPS'})[0]


def create_test_character(name="Test Char", guild=None, team=None, realm="Test Realm", id=1,
                          level=70, playable_class=None, playable_race=None, active_spec=None,
                          achievement_points=1000, average_item_level=300, equipped_item_level=290):
    if guild is None:
        guild = create_test_guild(id=99) # Use a different ID to avoid conflicts
    if team is None:
        team = create_test_team(name="CharTeam", guild=guild, id=99)

    final_playable_class = playable_class if playable_class else create_test_playable_class()
    final_playable_race = playable_race if playable_race else create_test_playable_race()
    final_active_spec = active_spec if active_spec else create_test_playable_spec(playable_class=final_playable_class)

    return Character.objects.create(
        id=id, name=name, realm=realm, guild=guild, team=team, level=level,
        playable_class=final_playable_class, playable_race=final_playable_race, active_spec=final_active_spec,
        achievement_points=achievement_points, average_item_level=average_item_level, equipped_item_level=equipped_item_level
    )

def create_test_application(name="Test App", discord_name="TestDiscord#1234", guild=None, team=None, id=1):
    if guild is None:
        guild = create_test_guild(id=98)
    if team is None:
        team = create_test_team(name="AppTeam", guild=guild, id=98)
    return Application.objects.create(id=id, name=name, discord_name=discord_name, guild=guild, team=team, app_data="Some details")


@override_settings(SECRET_KEY='a-test-secret-key-for-development-only')
class GuildAPITests(APITestCase):
    def setUp(self):
        self.guild1 = create_test_guild(name="Alpha Guild", realm="Sargeras", faction="Alliance", id=1)
        self.guild2 = create_test_guild(name="Beta Guild", realm="Area 52", faction="Horde", id=2)
        self.team1_g1 = create_test_team(name="Raiders", guild=self.guild1, id=1)
        self.team2_g1 = create_test_team(name="PvPers", guild=self.guild1, id=2)

    def test_list_guilds(self):
        url = reverse('guild-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Check pagination structure
        self.assertIn('count', response.data)
        self.assertIn('next', response.data)
        self.assertIn('previous', response.data)
        self.assertIn('results', response.data)
        self.assertEqual(response.data['count'], 2)
        self.assertEqual(len(response.data['results']), 2)
        self.assertEqual(response.data['results'][0]['name'], self.guild1.name)
        self.assertEqual(len(response.data['results'][0]['teams']), 2) # Check nested teams

    def test_retrieve_guild(self):
        url = reverse('guild-detail', kwargs={'pk': self.guild1.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], self.guild1.name)
        self.assertEqual(len(response.data['teams']), 2)
        self.assertEqual(response.data['teams'][0]['name'], self.team1_g1.name)


@override_settings(SECRET_KEY='a-test-secret-key-for-development-only')
class TeamAPITests(APITestCase):
    def setUp(self):
        self.guild = create_test_guild(id=100) # Unique ID
        self.team1 = create_test_team(name="The A Team", guild=self.guild, id=101)
        self.team2 = create_test_team(name="The B Team", guild=self.guild, id=102)
        self.team3 = create_test_team(name="Another Team", guild=self.guild, id=103)


    def test_list_teams(self):
        url = reverse('team-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Check pagination structure
        self.assertIn('count', response.data)
        self.assertIn('next', response.data)
        self.assertIn('previous', response.data)
        self.assertIn('results', response.data)
        self.assertEqual(response.data['count'], 3)
        self.assertEqual(len(response.data['results']), 3)

    def test_team_pagination_works_with_many_teams(self):
        # Create more than 50 teams to test pagination
        for i in range(4, 55): # Existing 3 + 51 new = 54 total
            create_test_team(name=f"Team {i}", guild=self.guild, id=i)

        url = reverse('team-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 54)
        self.assertEqual(len(response.data['results']), 50) # Default PAGE_SIZE
        self.assertIsNotNone(response.data['next'])
        self.assertIsNone(response.data['previous'])

        # Test second page
        response_page2 = self.client.get(response.data['next'])
        self.assertEqual(response_page2.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_page2.data['results']), 4)
        self.assertIsNone(response_page2.data['next'])
        self.assertIsNotNone(response_page2.data['previous'])


    def test_search_team_by_name(self):
        url = reverse('team-list')
        response = self.client.get(url, {'search': 'A Team'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 3) # "The A Team", "The B Team", and "Another Team"
        self.assertEqual(len(response.data['results']), 3)
        # Check that names match, order might vary
        names_in_response = sorted([item['name'] for item in response.data['results']])
        self.assertEqual(names_in_response, sorted([self.team1.name, self.team2.name, self.team3.name]))

    def test_filter_team_by_exact_name(self):
        url = reverse('team-list')
        response = self.client.get(url, {'name': 'The B Team'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['name'], self.team2.name)


@override_settings(SECRET_KEY='a-test-secret-key-for-development-only')
class CharacterAPITests(APITestCase):
    def setUp(self):
        self.guild = create_test_guild(id=200) # Unique ID
        self.team = create_test_team(name="Heroic Raiders", guild=self.guild, id=200) # Unique ID
        self.recipe1 = create_test_recipe(name="Flask of the Titans", id=201) # Unique ID
        self.recipe2 = create_test_recipe(name="Greater Healing Potion", id=202) # Unique ID

        self.char1_pclass = create_test_playable_class(name="Paladin", id=220) # Unique ID range
        self.char1_pspec = create_test_playable_spec(name="Retribution", playable_class=self.char1_pclass, id=220) # Unique ID range

        self.char1 = create_test_character(
            name="Palador", guild=self.guild, team=self.team, realm="Stormrage", id=201, # Unique ID
            achievement_points=15000, average_item_level=350, equipped_item_level=345,
            playable_class=self.char1_pclass, active_spec=self.char1_pspec
        )
        self.char1.known_recipes.add(self.recipe1)

        self.char2_pclass = create_test_playable_class(name="Mage", id=221) # Unique ID range
        self.char2_pspec = create_test_playable_spec(name="Frost", playable_class=self.char2_pclass, id=221) # Unique ID range
        self.char2 = create_test_character(
            name="Magicka", guild=self.guild, team=self.team, realm="Stormrage", id=202, # Unique ID
            achievement_points=10000, average_item_level=330, equipped_item_level=325,
            playable_class=self.char2_pclass, active_spec=self.char2_pspec
        )
        self.char2.known_recipes.add(self.recipe1, self.recipe2)

        self.char3_pclass = create_test_playable_class(name="Warrior", id=222) # Unique ID range
        self.char3_pspec = create_test_playable_spec(name="Arms", playable_class=self.char3_pclass, id=222) # Unique ID range
        self.char3 = create_test_character(
            name="Warrick", guild=self.guild, team=self.team, realm="Area 52", id=203, # Unique ID, Different realm
            achievement_points=20000, average_item_level=360, equipped_item_level=355,
            playable_class=self.char3_pclass, active_spec=self.char3_pspec
        )


    def test_list_characters(self):
        url = reverse('character-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Check pagination structure
        self.assertIn('count', response.data)
        self.assertIn('next', response.data)
        self.assertIn('previous', response.data)
        self.assertIn('results', response.data)
        self.assertEqual(response.data['count'], 3)
        self.assertEqual(len(response.data['results']), 3)

    def test_filter_character_by_player_name_partial(self):
        url = reverse('character-list')
        response = self.client.get(url, {'player_name': 'lado'}) # Palador
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['name'], self.char1.name)

    def test_filter_character_by_guild_name(self):
        url = reverse('character-list')
        response = self.client.get(url, {'guild_name': self.guild.name})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 3) # All are in the same guild
        self.assertEqual(len(response.data['results']), 3)

    def test_filter_character_by_realm(self):
        url = reverse('character-list')
        response = self.client.get(url, {'realm_name': 'Stormrage'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)
        self.assertEqual(len(response.data['results']), 2)

    def test_filter_character_by_playable_class_name(self):
        url = reverse('character-list')
        response = self.client.get(url, {'playable_class_name': 'Paladin'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['name'], self.char1.name)

    def test_filter_character_by_playable_spec_name(self):
        url = reverse('character-list')
        response = self.client.get(url, {'playable_spec_name': 'Frost'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['name'], self.char2.name)

    def test_filter_character_achievement_points_gt(self):
        url = reverse('character-list')
        response = self.client.get(url, {'achievement_points_gt': 12000})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2) # Char1 (15k) and Char3 (20k)
        self.assertEqual(len(response.data['results']), 2)
        names = sorted([c['name'] for c in response.data['results']])
        self.assertEqual(names, sorted([self.char1.name, self.char3.name]))


    def test_filter_character_achievement_points_lt(self):
        url = reverse('character-list')
        response = self.client.get(url, {'achievement_points_lt': 16000})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2) # Char1 (15k) and Char2 (10k)
        self.assertEqual(len(response.data['results']), 2)
        names = sorted([c['name'] for c in response.data['results']])
        self.assertEqual(names, sorted([self.char1.name, self.char2.name]))

    def test_filter_character_avg_ilvl_gt(self):
        url = reverse('character-list')
        response = self.client.get(url, {'average_item_level_gt': 340})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2) # Char1 (350) and Char3 (360)
        self.assertEqual(len(response.data['results']), 2)

    def test_filter_character_equipped_ilvl_lt(self):
        url = reverse('character-list')
        response = self.client.get(url, {'equipped_item_level_lt': 330})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1) # Char2 (325)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['name'], self.char2.name)

    def test_filter_character_by_team_name(self):
        url = reverse('character-list')
        response = self.client.get(url, {'team_name': 'Heroic Raiders'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 3) # All chars are in this team
        self.assertEqual(len(response.data['results']), 3)

# Removed test_filter_character_by_known_recipe_partial and test_filter_character_by_known_recipe_exact_on_potion


@override_settings(SECRET_KEY='a-test-secret-key-for-development-only')
class ApplicationAPITests(APITestCase):
    def setUp(self):
        self.guild = create_test_guild(id=300) # Unique ID
        self.team1 = create_test_team(name="Mythic Team", guild=self.guild, id=301) # Unique ID
        self.team2 = create_test_team(name="Casual Team", guild=self.guild, id=302) # Unique ID

        self.app1 = create_test_application(name="ApplicantOne", discord_name="AppOne#1111", team=self.team1, guild=self.guild, id=301) # Unique ID
        self.app2 = create_test_application(name="ApplicantTwo", discord_name="AppTwo#2222", team=self.team2, guild=self.guild, id=302) # Unique ID
        self.app3 = create_test_application(name="ThirdApply", discord_name="AppOne#3333", team=self.team1, guild=self.guild, id=303) # Unique ID

    def test_list_applications(self):
        url = reverse('application-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Check pagination structure
        self.assertIn('count', response.data)
        self.assertIn('next', response.data)
        self.assertIn('previous', response.data)
        self.assertIn('results', response.data)
        self.assertEqual(response.data['count'], 3)
        self.assertEqual(len(response.data['results']), 3)

    def test_filter_application_by_name(self):
        url = reverse('application-list')
        response = self.client.get(url, {'name': 'ApplicantOne'}) # Exact match from filterset
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Check pagination structure (response.data is the paginated dict)
        self.assertIn('count', response.data)
        self.assertIn('results', response.data)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['name'], self.app1.name)

    def test_search_application_by_name_partial(self):
        url = reverse('application-list')
        response = self.client.get(url, {'search': 'Applicant'}) # Partial from search_fields
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)
        self.assertEqual(len(response.data['results']), 2)
        names = sorted([c['name'] for c in response.data['results']])
        self.assertEqual(names, sorted([self.app1.name, self.app2.name]))


    def test_filter_application_by_discord_name(self):
        url = reverse('application-list')
        response = self.client.get(url, {'discord_name': 'AppOne#1111'}) # Exact from filterset
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['discord_name'], self.app1.discord_name)

    def test_search_application_by_discord_name_partial(self):
        url = reverse('application-list')
        response = self.client.get(url, {'search': 'AppOne'}) # Partial from search_fields
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2) # App1 and App3
        self.assertEqual(len(response.data['results']), 2)
        discord_names = sorted([c['discord_name'] for c in response.data['results']])
        self.assertEqual(discord_names, sorted([self.app1.discord_name, self.app3.discord_name]))


    def test_filter_application_by_team_name(self):
        url = reverse('application-list')
        response = self.client.get(url, {'team_name': 'Mythic Team'}) # Uses team_name from ApplicationFilter
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)
        self.assertEqual(len(response.data['results']), 2)
        names = sorted([c['name'] for c in response.data['results']])
        self.assertEqual(names, sorted([self.app1.name, self.app3.name]))

    def test_filter_application_by_team_id(self):
        url = reverse('application-list')
        response = self.client.get(url, {'team__id': self.team2.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['name'], self.app2.name)


@override_settings(SECRET_KEY='a-test-secret-key-for-development-only')
class RecipeCharacterSearchAPITests(APITestCase):
    def setUp(self):
        self.guild = create_test_guild(id=400)
        self.team = create_test_team(name="Recipe Testers", guild=self.guild, id=400)

        self.recipe_flask = create_test_recipe(name="Super Flask of Power", id=401)
        self.recipe_potion = create_test_recipe(name="Minor Healing Potion", id=402)
        self.recipe_elixir = create_test_recipe(name="Elixir of Giants", id=403)

        self.char1 = create_test_character(name="Alchemist Al", guild=self.guild, team=self.team, id=401)
        self.char2 = create_test_character(name="Herbalist Herb", guild=self.guild, team=self.team, id=402)
        self.char3 = create_test_character(name="Scribe Sky", guild=self.guild, team=self.team, id=403)
        self.char4 = create_test_character(name="NoRecipes Ned", guild=self.guild, team=self.team, id=404)

        self.char1.known_recipes.add(self.recipe_flask)
        self.char2.known_recipes.add(self.recipe_flask, self.recipe_potion)
        self.char3.known_recipes.add(self.recipe_potion)
        # Char4 knows no recipes from this set

        self.url = reverse('recipe-character-search')

    def test_search_by_full_recipe_name(self):
        response = self.client.get(self.url, {'name': "Super Flask of Power"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2) # Al and Herb
        character_names = sorted([item['name'] for item in response.data])
        self.assertEqual(character_names, sorted([self.char1.name, self.char2.name]))

    def test_search_by_partial_recipe_name_flask(self):
        response = self.client.get(self.url, {'name': "Flask"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2) # Al and Herb
        character_names = sorted([item['name'] for item in response.data])
        self.assertEqual(character_names, sorted([self.char1.name, self.char2.name]))

    def test_search_by_partial_recipe_name_potion(self):
        response = self.client.get(self.url, {'name': "Potion"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2) # Herb and Sky
        character_names = sorted([item['name'] for item in response.data])
        self.assertEqual(character_names, sorted([self.char2.name, self.char3.name]))

    def test_search_returns_only_names_structure(self):
        response = self.client.get(self.url, {'name': "Super Flask of Power"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)
        # Expecting list of dicts: [{'name': 'CharName1'}, ...]
        self.assertIsInstance(response.data[0], dict)
        self.assertIn('name', response.data[0])
        # Ensure no other character fields are present
        self.assertEqual(len(response.data[0].keys()), 1)


    def test_search_no_match(self):
        response = self.client.get(self.url, {'name': "Unknown Recipe"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_search_no_recipe_name_param(self):
        response = self.client.get(self.url) # No 'name' query parameter
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0) # View returns Character.objects.none()

    def test_search_is_case_insensitive(self):
        response = self.client.get(self.url, {'name': "super flask of power"}) # Lowercase
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        character_names = sorted([item['name'] for item in response.data])
        self.assertEqual(character_names, sorted([self.char1.name, self.char2.name]))
