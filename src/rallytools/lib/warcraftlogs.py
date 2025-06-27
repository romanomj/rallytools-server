import requests
import json

class WarcraftLogsAPI:
    """
    A Python wrapper for the Warcraft Logs V2 GraphQL API.

    This library provides a simplified interface for making authenticated requests 
    to the Warcraft Logs API, allowing you to fetch data such as reports, fights, 
    and character rankings.

    Attributes:
        client_id (str): Your Warcraft Logs API client ID.
        client_secret (str): Your Warcraft Logs API client secret.
        access_token (str): The access token for making authenticated requests.
        api_endpoint (str): The URL of the Warcraft Logs GraphQL API endpoint.
    """

    def __init__(self, client_id, client_secret):
        """
        Initializes the WarcraftLogsAPI client.

        Args:
            client_id (str): Your Warcraft Logs API client ID.
            client_secret (str): Your Warcraft Logs API client secret.
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = None
        self.api_endpoint = "https://www.warcraftlogs.com/api/v2/client"

    def get_access_token(self):
        """
        Retrieves an access token from the Warcraft Logs API.

        This method uses your client ID and secret to request an access token,
        which is then stored in the `access_token` attribute for subsequent API calls.
        """
        token_url = "https://www.warcraftlogs.com/oauth/token"
        data = {
            "grant_type": "client_credentials"
        }
        try:
            response = requests.post(token_url, data=data, auth=(self.client_id, self.client_secret))
            response.raise_for_status()  # Raise an exception for bad status codes
            self.access_token = response.json().get("access_token")
            print("Successfully obtained access token.")
        except requests.exceptions.RequestException as e:
            print(f"Error obtaining access token: {e}")
            self.access_token = None


    def execute_query(self, query, variables=None):
        """
        Executes a GraphQL query against the Warcraft Logs API.

        Args:
            query (str): The GraphQL query string.
            variables (dict, optional): A dictionary of variables for the query.

        Returns:
            dict: The JSON response from the API, or None if an error occurs.
        """
        if not self.access_token:
            self.get_access_token()
            if not self.access_token:
                print("Cannot execute query without a valid access token.")
                return None

        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        payload = {"query": query}
        if variables:
            payload["variables"] = variables

        try:
            response = requests.post(self.api_endpoint, headers=headers, data=json.dumps(payload))
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"API request failed: {e}")
            return None
        except json.JSONDecodeError:
            print("Failed to decode JSON response.")
            return None


    def get_report(self, report_code):
        """
        Fetches a specific report by its code.

        Args:
            report_code (str): The unique code of the report (e.g., 'aBcDeFg123456789').

        Returns:
            dict: The report data, or None if the report is not found or an error occurs.
        """
        query = """
            query($report_code: String!) {
                reportData {
                    report(code: $report_code) {
                        code
                        title
                        owner {
                            name
                        }
                        startTime
                        endTime
                        zone {
                            name
                        }
                    }
                }
            }
        """
        variables = {"report_code": report_code}
        return self.execute_query(query, variables)


    def get_fight(self, report_code, fight_id):
        """
        Fetches a specific fight from a report.

        Args:
            report_code (str): The code of the report.
            fight_id (int): The ID of the fight within the report.

        Returns:
            dict: The fight data, or None if not found or an error occurs.
        """
        query = """
            query($report_code: String!, $fight_id: [Int]!) {
                reportData {
                    report(code: $report_code) {
                        fights(fightIDs: $fight_id) {
                            id
                            name
                            startTime
                            endTime
                            bossPercentage
                            keystoneLevel
                        }
                    }
                }
            }
        """
        variables = {"report_code": report_code, "fight_id": [fight_id]}
        return self.execute_query(query, variables)

    def get_character_rankings(self, character_name, server_name, server_region):
        """
        Fetches character rankings for a specific character.

        Args:
            character_name (str): The name of the character.
            server_name (str): The server name of the character.
            server_region (str): The region of the server (e.g., 'US', 'EU').

        Returns:
            dict: The character ranking data, or None if not found or an error occurs.
        """
        query = """
            query($character_name: String!, $server_name: String!, $server_region: String!) {
                characterData {
                    character(name: $character_name, serverSlug: $server_name, serverRegion: $server_region) {
                        id
                        name
                        classID
                        zoneRankings
                    }
                }
            }
        """
        variables = {
            "character_name": character_name,
            "server_name": server_name.lower().replace(" ", "-"), # Server slug format
            "server_region": server_region
        }
        return self.execute_query(query, variables)
