import http.client, urllib

from bs4 import BeautifulSoup
from cloudscraper import create_scraper
from pandas import read_html

api_key = "ayms1wvxify8f526b241pqjpqqdbfp"
user_key = "uowz7obrxytt94tai7zyt1wpzd3vw6"
daily_url = "https://www.espn.com/nba/scoreboard"

conn = http.client.HTTPSConnection("api.pushover.net:443")

# Translate abbreviated name into full player name
def get_full_name(abbreviated_name, game_link):
    url = game_link
    scraper = create_scraper(delay=10, browser={"custom": "ScraperBot/1.0"})
    req = scraper.get(url)
    soup = BeautifulSoup(req.content, "html.parser")
    for link in soup.find_all('a', href=True, text=abbreviated_name):
        return link["href"]
    return ("Invalid: " + abbreviated_name)

# get game ids
def get_games(daily_url):
    scraper = create_scraper(delay=10, browser={"custom": "ScraperBot/1.0"})
    req = scraper.get(daily_url)
    soup = BeautifulSoup(req.content, "html.parser")

    for daily_url in soup.find_all("a"):
        try:
            href = daily_url.get("href")
            if not href.startswith("/nba/game/_/gameId/"):
                continue
            print("HREF: " + href)
            game_id = href.rsplit('/', 1)[-1]
            print("Game ID: " + game_id)
            get_players(game_id)

        except:
            continue

# get individual player stats
def get_players(game_id):
    url = 'https://www.espn.com/nba/boxscore/_/gameId/' + game_id
    tables = read_html(url)  # Returns list of all tables on page
    player_table_1, player_table_2 = tables[1], tables[3]  # Select tables of interest
    stats_1, stats_2 = tables[2], tables[4]
    players_1, players_2 = [], []

    for index, row in player_table_1.iterrows():
        players_1.append(row[0])
    for index, row in player_table_2.iterrows():
        players_2.append(row[0])

    process_team(stats_1, players_1, url)
    process_team(stats_2, players_2, url)

def process_team(stats, players, game_link):
    i = 0
    for index, row in stats.iterrows():
        if str(row[0]).startswith("DNP"):
            print("DNP")
            continue
        if row[0] is None or str(row[0]) == "nan":
            print("INVALID")
            continue
        if players[i] == "bench" or players[i] == "starters":
          i += 1
          continue
        player_name = extract_player_name_from_url(get_full_name(remove_position_suffix(players[i]), game_link))
        try:
            minutes = str(row[0])
            fg = str(row[1])
            three_pt = str(row[2])
            ft = str(row[3])
            oreb = str(row[4])
            dreb = str(row[5])
            reb = str(row[6])
            ast = str(row[7])
            stl = str(row[8])
            blk = str(row[9])
            to = str(row[10])
            pf = str(row[11])
            plus_minus = str(row[12])
            pts = str(row[13])
            if int(pts) > 25:
                send_notification(player_name + " has accumulated " + pts + " points!")
        except ValueError:
            pass
        i += 1

def remove_position_suffix(input_string):
    suffixes = [" C", " PF", " F", " SF", " SG", " PG", " G"]

    for suffix in suffixes:
        if input_string.endswith(suffix):
            return input_string[:-len(suffix)].strip()

    return input_string

def extract_player_name_from_url(url):
    # Parse the URL to extract the path
    parsed_url = urllib.parse.urlparse(url)
    path = parsed_url.path

    # Split the path and remove any empty segments
    path_segments = [segment for segment in path.split('/') if segment]

    # Extract the last segment (which should be the player's name)
    if path_segments:
        player_name = path_segments[-1]
        # Replace '-' with space and capitalize the name
        return player_name.replace('-', ' ').upper()

    return None  # Return None if the URL doesn't match the expected format

def send_notification(message):
    conn.request("POST", "/1/messages.json",
                 urllib.parse.urlencode({
                     "token": api_key,
                     "user": user_key,
                     "message": message,
                 }), {"Content-type": "application/x-www-form-urlencoded"})
    conn.getresponse()

get_games(daily_url)