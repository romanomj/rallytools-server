import requests
import time
import random
import logging

logger = logging.getLogger(__name__)

RETRY_STATUS_CODES = [429, 502]
NOT_FOUND_STATUS_CODES = [404]
MAX_RETRIES = 3
BASE_BACKOFF_SECONDS = 1

# Define a custom exception class for the API
class BattleNetAPIError(Exception):
    """Base exception class for BattleNetAPI errors."""
    pass

class BattleNetAPINotFoundError(Exception):
    """
    Exception for 404s
    Sometimes useful for items not publicly tracked, such as junk quality items
    """
    pass

class BattleNetAPI:
    """
    A Python class to interact with the Blizzard Battle.net API.
    This class handles authentication and provides methods to access
    World of Warcraft game data and profile data.
    """

    def __init__(self, client_id, client_secret, region='us'):
        """
        Initializes the BattleNetAPI client.

        Args:
            client_id (str): Your Blizzard application client ID.
            client_secret (str): Your Blizzard application client secret.
            region (str, optional): The API region to use. Defaults to 'us'.
                                    Other options include 'eu', 'kr', 'tw'.
        """
        if not client_id or not client_secret:
            raise ValueError("Client ID and Client Secret cannot be empty.")

        self.client_id = client_id
        self.client_secret = client_secret
        self.region = region
        self.api_host = f"https://{self.region}.api.blizzard.com"
        self.token_url = f"https://{self.region}.battle.net/oauth/token"
        self.access_token = None
        self.token_expiry = 0

    def _get_access_token(self):
        """
        Retrieves an OAuth access token from the Blizzard API.
        It caches the token and renews it only when it has expired.
        
        Raises:
            BattleNetAPIError: If there's an issue obtaining the access token.
        """
        # If we have a token and it hasn't expired, reuse it
        if self.access_token and time.time() < self.token_expiry:
            return

        try:
            data = {'grant_type': 'client_credentials'}
            response = requests.post(self.token_url, data=data, auth=(self.client_id, self.client_secret))
            response.raise_for_status()  # Raise an exception for bad status codes

            token_data = response.json()
            self.access_token = token_data['access_token']
            # Set expiry time with a small buffer
            self.token_expiry = time.time() + token_data['expires_in'] - 180

        except requests.exceptions.RequestException as e:
            # Wrap the original exception in our custom exception
            raise BattleNetAPIError(f"Error obtaining access token: {e}") from e

    def _make_request(self, endpoint, namespace, params=None):
        """
        A helper function to make authenticated requests to the API.

        Args:
            endpoint (str): The API endpoint to request (e.g., '/data/wow/realm/index').
            namespace (str): The required namespace for the endpoint.
            params (dict, optional): A dictionary of query parameters. Defaults to None.

        Returns:
            dict: The JSON response from the API.
            
        Raises:
            BattleNetAPIError: If the request fails due to authentication, network issues, or an API error.
        """
        self._get_access_token()
        if not self.access_token:
            # This case is now more theoretical since _get_access_token will raise an exception if it fails.
            # However, it's good practice to keep it as a safeguard.
            raise BattleNetAPIError("Cannot make request: No valid access token and failed to retrieve a new one.")

        endpoint = endpoint.lower() #Battlenet requires lowercase
        url = f"{self.api_host}{endpoint}"
        headers = {
            'Authorization': f'Bearer {self.access_token}'
        }
        
        # Add the namespace to the parameters
        if params is None:
            params = {}
        params['namespace'] = namespace
        params['locale'] = params.get('locale', 'en_US') # Default locale

        last_exception = None #Track exceptions in case we deal with backoff
        for attempt in range(MAX_RETRIES):

            try:
                response = requests.get(url, headers=headers, params=params)
                response.raise_for_status()
                return response.json()
            except requests.exceptions.HTTPError as e:
                if e.response.status_code in RETRY_STATUS_CODES: 
                    last_exception = e
                    if attempt < MAX_RETRIES - 1:
                        wait_time = BASE_BACKOFF_SECONDS * (2 ** attempt)
                        jitter = random.uniform(0, wait_time * 0.1)
                        logger.warning(f"INFO: Received status {e.response.status_code}. Retrying in {wait_time + jitter:.2f} seconds... (Attempt {attempt + 1}/{MAX_RETRIES})")
                        time.sleep(wait_time + jitter) # Sleep briefly
                        continue
                    else:
                        logger.error(f"ERROR: Final attempt failed with status {e.response.status_code}.")
                        break
                elif e.response.status_code in NOT_FOUND_STATUS_CODES:
                    raise BattleNetAPINotFoundError(f"HTTP Error: Not Found: {e}")
                else:
                    # Include more context in the raised exception
                    error_message = f"HTTP Error for {url}: {e.response.status_code} - {e.response.text}"
                    raise BattleNetAPIError(error_message) from e

            except requests.exceptions.RequestException as e:
                raise BattleNetAPIError(f"Request failed for {url}: {e}") from e

    # --- World of Warcraft Game Data APIs ---

    def get_guild(self, realm, name, locale='en_US'):
        """
        Retrieves data for a Guild
        """
        namespace = f'profile-{self.region}'
        endpoint = f'/data/wow/guild/{realm}/{name}'
        return self._make_request(endpoint, namespace)

    def get_guild_roster(self, realm, name, locale='en_US'):
        """
        Retrieves a character roster for a Guild
        """
        namespace = f'profile-{self.region}'
        endpoint = f'/data/wow/guild/{realm}/{name}/roster'
        return self._make_request(endpoint, namespace)

    def get_character_summary(self, realm, name):
        """
        Retrieves a character summary
        """
        namespace = f'profile-{self.region}'
        endpoint = f'/profile/wow/character/{realm}/{name}'
        return self._make_request(endpoint, namespace)

    def get_character_professions(self, realm, name):
        """
        Retrieves a character's profession data
        """
        namespace = f'profile-{self.region}'
        endpoint = f'/profile/wow/character/{realm}/{name}/professions'
        return self._make_request(endpoint, namespace)


    def get_playable_races(self, id=None):
        """
        Retrieves a list of playable races and their associated metadata
        """
        namespace = f'static-{self.region}'
        if id:
            endpoint = f'/data/wow/playable-race/{id}'
        else:
            endpoint = '/data/wow/playable-race/index'
        return self._make_request(endpoint, namespace)

    def get_playable_classes(self, id=None):
        """
        Retrieves a list of playable classes and their associated metadata
        """
        namespace = f'static-{self.region}'
        if id:
            endpoint = f'/data/wow/playable-class/{id}'
        else:
            endpoint = '/data/wow/playable-class/index'
        return self._make_request(endpoint, namespace)

    def get_playable_class_media(self, id):
        """
        Retrieves a list of playable classes media
        """
        namespace = f'static-{self.region}'
        endpoint = f'/data/wow/media/playable-class/{id}'
        return self._make_request(endpoint, namespace)

    def get_playable_specializations(self, id=None):
        """
        Retrieves a list of playable specializations and their associated metadata
        """
        namespace = f'static-{self.region}'
        if id:
            endpoint = f'/data/wow/playable-specialization/{id}'
        else:
            endpoint = '/data/wow/playable-specialization/index'
        return self._make_request(endpoint, namespace)

    def get_playable_specialization_media(self, id):
        """
        Retrieves a list of playable specialization media
        """
        namespace = f'static-{self.region}'
        endpoint = f'/data/wow/media/playable-specialization/{id}'
        return self._make_request(endpoint, namespace)

    def get_professions(self, id=None):
        """
        Retrieves a list of professions and their associated metadata.
        If an ID is provided, it returns a detail view for the specific id
        """
        namespace = f'static-{self.region}'
        if id:
            endpoint = f'/data/wow/profession/{id}'
        else:
            endpoint = '/data/wow/profession/index'
        return self._make_request(endpoint, namespace)

    def get_profession_media(self, id):
        """
        Retrieves a list of profession media/icons
        """
        namespace = f'static-{self.region}'
        endpoint = f'/data/wow/media/profession/{id}'
        return self._make_request(endpoint, namespace)

    def get_profession_skill_tier(self, profession_id, skill_tier_id):
        """
        Retrieves a list of profession skill tier data
        """
        namespace = f'static-{self.region}'
        endpoint = f'/data/wow/profession/{profession_id}/skill-tier/{skill_tier_id}'
        return self._make_request(endpoint, namespace)

    def get_recipe(self, id):
        """
        Retrieves a data for a given recipe id
        """
        namespace = f'static-{self.region}'
        endpoint = f'/data/wow/recipe/{id}'
        return self._make_request(endpoint, namespace)

    def get_recipe_media(self, id):
        """
        Retrieves a list of recipe media/icons
        """
        namespace = f'static-{self.region}'
        endpoint = f'/data/wow/media/recipe/{id}'
        return self._make_request(endpoint, namespace)

    def get_commodities(self):
        """
        Retrieves a list of all current actions.
        Note: This is a snapshot in time generated every hour
        """
        namespace = f'dynamic-{self.region}'
        endpoint = '/data/wow/auctions/commodities'
        return self._make_request(endpoint, namespace)

    def get_item(self, id):
        """
        Retrieves data about a specific in game item
        """
        namespace = f'static-{self.region}'
        endpoint = f'/data/wow/item/{id}'
        return self._make_request(endpoint, namespace)

    def get_item_media(self, id):
        """
        Retrieves media data about a specific in game item
        """
        namespace = f'static-{self.region}'
        endpoint = f'/data/wow/media/item/{id}'
        return self._make_request(endpoint, namespace)

