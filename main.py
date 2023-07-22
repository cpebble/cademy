import click
import requests
from collections import Counter
import json
from pprint import pprint
import time
from flask import Flask, render_template
import threading
import os
app = Flask(__name__)


def fetch_game(game: str):
    r = requests.get(f"https://academy.beer/api/games/{game}/")
    if r.status_code != 200:
        raise Exception(f"Error in request: {str(r.text)}")
    d = r.json()
    return d


def parse_game(game: str):
    data = fetch_game(game)
    return {
            "players": 
                    [(p['username'], p['total_sips']) for p in data['player_stats']],
            "chugs":[(data['players'][i % len(data['players'])]['username'], c) 
                     for i, c in enumerate(data['cards']) 
                     if c['chug_duration_ms'] != None
                    ],
            }

@click.group()
def cli():
    pass


def parse_collected(games):
    c = Counter()
    for g in games:
        for p in g['players']:
            c[p[0]] += p[1]
    return {
                "totals": list(sorted(c.items(), reverse=True, key=lambda e: e[1]))#, key=lambda pl: c[pl]))
            }

@cli.command()
@click.option('--hostname', default='127.0.0.1',
              help='The hostname to run the server on. Defaults to 127.0.0.1.')
@click.option('--port', default=5000, 
              help='The port to run the server on. Defaults to 5000.')
@click.option('--tail/--no-tail', default=True)
@click.option('--fetch_time', default=10)
#@click.argument('games')
def server_command(hostname, port, tail, fetch_time):
    games_list = [g.strip() for g in os.getenv("GAMES", "").split(',')]
    game_data = [parse_game(g) for g in games_list]
    threading.Thread(target=app.run, kwargs={'host':hostname, 'port':port}).start()

    while tail:
        try:
            game_data = {g: parse_game(g) for g in games_list}
            app.config['GAMES'] = game_data
            app.config['COLL'] = parse_collected(game_data.values())
        except Exception as ex:
            print("Error in fetch", ex)
            
        time.sleep(fetch_time)

@cli.command()
@click.option('--games', help='The games you are interested in.', default="")
#@click.option('--tail/--no-tail', help='Should we continually perform requests?', default=False) 
def fetch_games(games):
    games_list = [g.strip() for g in games.split(',')]
    try:
        game_data = {g: parse_game(g) for g in games_list}
    except Exception as ex:
        print("Error in fetch", ex)
        raise ex
    pprint(game_data)
    return 0



def process(games):
    if games:  
        return [game.strip() for game in games.split(',')]
    return []

@app.route('/')
def home():
    return render_template('index.html', games=app.config['GAMES'], collected=app.config['COLL'])




if __name__ == "__main__":
    cli()
