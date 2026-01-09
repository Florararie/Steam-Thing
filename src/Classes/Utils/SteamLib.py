import os
import re
import json
import random
import requests
from pathlib import Path



def is_valid_steam_id(steam_id):
    """Check if the provided Steam ID is a valid 17-digit integer."""
    return isinstance(steam_id, str) and steam_id.isdigit() and len(steam_id) == 17


def is_valid_api_key(api_key):
    """Check if the provided API key is a valid 32-character hexadecimal string."""
    return isinstance(api_key, str) and len(api_key) == 32 and all(c in '0123456789abcdefABCDEF' for c in api_key)



class GameLibrary:
    def __init__(self, steam_path, api_key, steam_id):
        self.steam_path = Path(steam_path)
        self.api_key = api_key
        self.steam_id = steam_id


    def load_excluded_apps(self, json_file):
        """Load excluded app ids from a JSON file."""
        try:
            with open(json_file, 'r') as file:
                excluded_data = json.load(file)
                return {appid: name for name, appid in excluded_data.items()}
        except Exception as e:
            print(f"Error loading excluded apps from {json_file}: {e}")
            return {}


    def get_library_paths(self):
        """Retrieve Steam library folders from libraryfolders.vdf."""
        library_file = self.steam_path / 'steamapps' / 'libraryfolders.vdf'
        if not library_file.is_file():
            print(f"Could not find {library_file}. Ensure Steam is installed and the path is correct.")
            return []

        try:
            with library_file.open('r', encoding='utf-8') as file:
                content = file.read()
                paths = re.findall(r'"path"\s+"(.*?)"', content)
                return [path.replace('\\\\', '\\') for path in paths if os.path.isdir(path)]
        except Exception as e:
            print(f"Error reading {library_file}: {e}")
            return []


    def get_installed_games(self, excluded_apps_file=None):
        games = []
        excluded_apps = {}
        if excluded_apps_file is not None:
            excluded_apps = self.load_excluded_apps(excluded_apps_file)

        for library in self.get_library_paths():
            steamapps_path = Path(library) / 'steamapps'
            if not steamapps_path.is_dir():
                continue

            for acf_file in steamapps_path.glob('*.acf'):
                try:
                    with acf_file.open('r', encoding='utf-8') as file:
                        appid, name, last_played, last_updated, size_on_disk = None, None, 0, 0, 0
                        for line in file:
                            if '"appid"' in line:
                                appid = re.search(r'"appid"\s+"(\d+)"', line).group(1)
                            elif '"name"' in line:
                                name = line.split('"')[3]
                            elif '"LastPlayed"' in line:
                                last_played = int(re.search(r'"LastPlayed"\s+"(\d+)"', line).group(1))
                            elif '"lastupdated"' in line:
                                last_updated = int(re.search(r'"lastupdated"\s+"(\d+)"', line).group(1))
                            elif '"SizeOnDisk"' in line:
                                size_on_disk = int(re.search(r'"SizeOnDisk"\s+"(\d+)"', line).group(1))

                        # Exclude SteamWorks Common Redistributables
                        if appid == "228980":
                            continue

                        if appid and name and appid not in excluded_apps and name not in excluded_apps.values():
                            games.append((name, appid, last_played, last_updated, size_on_disk, True))
                except Exception as e:
                    print(f"Error reading {acf_file}: {e}")
        return games


    def get_owned_games(self, excluded_apps_file=None):
        # Load excluded apps from the file if provided
        owned_games = []
        excluded_apps = {}
        if excluded_apps_file is not None:
            excluded_apps = self.load_excluded_apps(excluded_apps_file)

        # Fetch owned games from the Steam API
        url = "https://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/"
        params = {
            "key": self.api_key,
            "steamid": self.steam_id,
            "include_appinfo": 1,
            "format": "json"
        }
        response = requests.get(url, params=params)
        data = response.json()
        
        # Filter games based on the exclusion list
        for game in data.get("response", {}).get("games", []):
            appid = str(game['appid'])
            name = game.get("name", "Unknown")
            
            # Exclude the game if its appid or name is in the exclusion list
            if appid in excluded_apps or name in excluded_apps.values():
                continue
            
            # Add the game to the list if it's not excluded
            owned_games.append(game)

        return owned_games


    def get_all_games(self, excluded_apps_file=None):
        # Attempt to fetch owned games
        try:
            owned_games = self.get_owned_games(excluded_apps_file)
        except Exception as e:
            self.install_filter = False
            owned_games = []  # If fetching fails, treat it as empty

        # Retrieve installed games as you already do
        installed_games = self.get_installed_games(excluded_apps_file)
        installed_appids = {game[1] for game in installed_games}

        # Create a set to hold unique appids to avoid duplicates
        seen_appids = set()

        # Create a list to hold game tuples
        games_list = []

        # Create a dictionary to hold games by appid for easy lookup
        installed_games_dict = {game[1]: game for game in installed_games}

        # Update the list with installed game details, ensuring no duplicates
        for game in installed_games:
            appid = game[1]
            if appid not in seen_appids:  # Check for duplicates
                seen_appids.add(appid)
                games_list.append((
                    game[0],  # name
                    appid,
                    game[2],  # last_played
                    game[3],  # last_updated
                    game[4],  # size_on_disk
                    True,     # installed
                    0         # playtime_forever (initialize as 0)
                ))

        # Only add owned games if the fetch was successful
        if owned_games:
            for game in owned_games:
                appid = str(game['appid'])
                if appid not in seen_appids:  # Check for duplicates
                    seen_appids.add(appid)
                    games_list.append((
                        game.get("name", "Unknown"),
                        appid,
                        game.get("rtime_last_played", 0),
                        0,  # last_updated
                        0,  # size_on_disk
                        appid in installed_appids,
                        game.get('playtime_forever', 0)  # Add playtime_forever from the API
                    ))
                else:
                    # If the game is already in the installed list, update its details with the API data
                    installed_game = installed_games_dict.get(appid)
                    if installed_game:
                        # Find the index of the game in the games_list
                        game_index = next((index for index, item in enumerate(games_list) if item[1] == appid), None)
                        if game_index is not None:
                            # Update the playtime_forever in the existing game entry
                            games_list[game_index] = (
                                installed_game[0],  # name
                                appid,
                                installed_game[2],  # last_played
                                installed_game[3],  # last_updated
                                installed_game[4],  # size_on_disk
                                True,                # installed
                                game.get('playtime_forever', 0)  # playtime_forever from API
                            )

        # Return the merged list as tuples with the new field
        if installed_games and owned_games:
            self.install_filter = True
        return games_list


    def get_game_description(self, app_id):
        """Fetch the game description using requests and regex."""
        url = f"https://store.steampowered.com/app/{app_id}"
        try:
            response = requests.get(url)
            if response.status_code == 200:
                #match = re.search(r'<div class="game_description_snippet">(.*?)</div>', response.text, re.DOTALL)
                match = re.search(r'<meta property="og:description" content="(.*?)"', response.text)
                return match.group(1).strip() if match else "Description not available."
        except Exception as e:
            print(f"Error fetching description for app ID {app_id}: {e}")
        return "Error fetching description."