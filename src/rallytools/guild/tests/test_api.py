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
        self.assertEqual(len(response.data), 2)
        self.assertEqual(response.data[0]['name'], self.guild1.name)
        self.assertEqual(len(response.data[0]['teams']), 2) # Check nested teams

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
        self.guild = create_test_guild()
        self.team1 = create_test_team(name="The A Team", guild=self.guild, id=1)
        self.team2 = create_test_team(name="The B Team", guild=self.guild, id=2)
        self.team3 = create_test_team(name="Another Team", guild=self.guild, id=3)


    def test_list_teams(self):
        url = reverse('team-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)

    def test_search_team_by_name(self):
        url = reverse('team-list')
        response = self.client.get(url, {'search': 'A Team'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3) # "The A Team", "The B Team", and "Another Team"
        # Check that names match, order might vary
        names_in_response = sorted([item['name'] for item in response.data])
        self.assertEqual(names_in_response, sorted([self.team1.name, self.team2.name, self.team3.name]))

    def test_filter_team_by_exact_name(self):
        url = reverse('team-list')
        response = self.client.get(url, {'name': 'The B Team'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], self.team2.name)


@override_settings(SECRET_KEY='a-test-secret-key-for-development-only')
class CharacterAPITests(APITestCase):
    def setUp(self):
        self.guild = create_test_guild(id=10)
        self.team = create_test_team(name="Heroic Raiders", guild=self.guild, id=10)
        self.recipe1 = create_test_recipe(name="Flask of the Titans", id=1)
        self.recipe2 = create_test_recipe(name="Greater Healing Potion", id=2)

        self.char1_pclass = create_test_playable_class(name="Paladin", id=20)
        self.char1_pspec = create_test_playable_spec(name="Retribution", playable_class=self.char1_pclass, id=20)

        self.char1 = create_test_character(
            name="Palador", guild=self.guild, team=self.team, realm="Stormrage", id=1,
            achievement_points=15000, average_item_level=350, equipped_item_level=345,
            playable_class=self.char1_pclass, active_spec=self.char1_pspec
        )
        self.char1.known_recipes.add(self.recipe1)

        self.char2_pclass = create_test_playable_class(name="Mage", id=21)
        self.char2_pspec = create_test_playable_spec(name="Frost", playable_class=self.char2_pclass, id=21)
        self.char2 = create_test_character(
            name="Magicka", guild=self.guild, team=self.team, realm="Stormrage", id=2,
            achievement_points=10000, average_item_level=330, equipped_item_level=325,
            playable_class=self.char2_pclass, active_spec=self.char2_pspec
        )
        self.char2.known_recipes.add(self.recipe1, self.recipe2)

        self.char3_pclass = create_test_playable_class(name="Warrior", id=22) # Different class for filtering
        self.char3_pspec = create_test_playable_spec(name="Arms", playable_class=self.char3_pclass, id=22)
        self.char3 = create_test_character(
            name="Warrick", guild=self.guild, team=self.team, realm="Area 52", id=3, # Different realm
            achievement_points=20000, average_item_level=360, equipped_item_level=355,
            playable_class=self.char3_pclass, active_spec=self.char3_pspec
        )


    def test_list_characters(self):
        url = reverse('character-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)

    def test_filter_character_by_player_name_partial(self):
        url = reverse('character-list')
        response = self.client.get(url, {'player_name': 'lado'}) # Palador
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], self.char1.name)

    def test_filter_character_by_guild_name(self):
        url = reverse('character-list')
        response = self.client.get(url, {'guild_name': self.guild.name})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3) # All are in the same guild

    def test_filter_character_by_realm(self):
        url = reverse('character-list')
        response = self.client.get(url, {'realm_name': 'Stormrage'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_filter_character_by_playable_class_name(self):
        url = reverse('character-list')
        response = self.client.get(url, {'playable_class_name': 'Paladin'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], self.char1.name)

    def test_filter_character_by_playable_spec_name(self):
        url = reverse('character-list')
        response = self.client.get(url, {'playable_spec_name': 'Frost'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], self.char2.name)

    def test_filter_character_achievement_points_gt(self):
        url = reverse('character-list')
        response = self.client.get(url, {'achievement_points_gt': 12000})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2) # Char1 (15k) and Char3 (20k)
        names = sorted([c['name'] for c in response.data])
        self.assertEqual(names, sorted([self.char1.name, self.char3.name]))


    def test_filter_character_achievement_points_lt(self):
        url = reverse('character-list')
        response = self.client.get(url, {'achievement_points_lt': 16000})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2) # Char1 (15k) and Char2 (10k)
        names = sorted([c['name'] for c in response.data])
        self.assertEqual(names, sorted([self.char1.name, self.char2.name]))

    def test_filter_character_avg_ilvl_gt(self):
        url = reverse('character-list')
        response = self.client.get(url, {'average_item_level_gt': 340})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2) # Char1 (350) and Char3 (360)

    def test_filter_character_equipped_ilvl_lt(self):
        url = reverse('character-list')
        response = self.client.get(url, {'equipped_item_level_lt': 330})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1) # Char2 (325)
        self.assertEqual(response.data[0]['name'], self.char2.name)

    def test_filter_character_by_team_name(self):
        url = reverse('character-list')
        response = self.client.get(url, {'team_name': 'Heroic Raiders'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3) # All chars are in this team

    def test_filter_character_by_known_recipe_partial(self):
        url = reverse('character-list')
        # Search for "Flask" - should match "Flask of the Titans"
        response = self.client.get(url, {'known_recipes_name': 'Flask'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2) # Char1 and Char2 know "Flask of the Titans"
        names = sorted([c['name'] for c in response.data])
        self.assertEqual(names, sorted([self.char1.name, self.char2.name]))

    def test_filter_character_by_known_recipe_exact_on_potion(self):
        url = reverse('character-list')
        response = self.client.get(url, {'known_recipes_name': 'Greater Healing Potion'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1) # Only Char2 knows "Greater Healing Potion"
        self.assertEqual(response.data[0]['name'], self.char2.name)


@override_settings(SECRET_KEY='a-test-secret-key-for-development-only')
class ApplicationAPITests(APITestCase):
    def setUp(self):
        self.guild = create_test_guild(id=30)
        self.team1 = create_test_team(name="Mythic Team", guild=self.guild, id=30)
        self.team2 = create_test_team(name="Casual Team", guild=self.guild, id=31)

        self.app1 = create_test_application(name="ApplicantOne", discord_name="AppOne#1111", team=self.team1, guild=self.guild, id=1)
        self.app2 = create_test_application(name="ApplicantTwo", discord_name="AppTwo#2222", team=self.team2, guild=self.guild, id=2)
        self.app3 = create_test_application(name="ThirdApply", discord_name="AppOne#3333", team=self.team1, guild=self.guild, id=3) # Same discord prefix, diff team

    def test_list_applications(self):
        url = reverse('application-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)

    def test_filter_application_by_name(self):
        url = reverse('application-list')
        response = self.client.get(url, {'name': 'ApplicantOne'}) # Exact match from filterset
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], self.app1.name)

    def test_search_application_by_name_partial(self):
        url = reverse('application-list')
        response = self.client.get(url, {'search': 'Applicant'}) # Partial from search_fields
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        names = sorted([c['name'] for c in response.data])
        self.assertEqual(names, sorted([self.app1.name, self.app2.name]))


    def test_filter_application_by_discord_name(self):
        url = reverse('application-list')
        response = self.client.get(url, {'discord_name': 'AppOne#1111'}) # Exact from filterset
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['discord_name'], self.app1.discord_name)

    def test_search_application_by_discord_name_partial(self):
        url = reverse('application-list')
        response = self.client.get(url, {'search': 'AppOne'}) # Partial from search_fields
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2) # App1 and App3
        discord_names = sorted([c['discord_name'] for c in response.data])
        self.assertEqual(discord_names, sorted([self.app1.discord_name, self.app3.discord_name]))


    def test_filter_application_by_team_name(self):
        url = reverse('application-list')
        response = self.client.get(url, {'team_name': 'Mythic Team'}) # Uses team_name from ApplicationFilter
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        names = sorted([c['name'] for c in response.data])
        self.assertEqual(names, sorted([self.app1.name, self.app3.name]))

    def test_filter_application_by_team_id(self):
        url = reverse('application-list')
        response = self.client.get(url, {'team__id': self.team2.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], self.app2.name)
