import hashlib
import random
import string

import discord
import requests
from discord.ext import commands
from urllib3.exceptions import InsecureRequestWarning

#disable ssl warning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# Replace 'your-token-here' with your actual Discord bot token
TOKEN = 'MTA5NTkwODk4ODQ4ODUyNzg5Mg.G_3qUi.AboiIK-ASDipT3SrVY7vLxUEMeSnSK9fdCgkDc'

# Replace 'your-airsonic-url' with your actual Airsonic URL
# Replace 'your-airsonic-username' and 'your-airsonic-password' with your actual Airsonic credentials
AIRSONIC_URL = 'http://aud-con1.rocketwerkz.net'
AIRSONIC_USERNAME = 'admin'
AIRSONIC_PASSWORD = 'admin'
AIRSONIC_API_VERSION = '1.15.0'
AIRSONIC_CLIENT_NAME = 'my_discord_airsonic_bot'

intents = discord.Intents.default()
intents.typing = False
intents.presences = False
intents.message_content = True

bot = commands.Bot(command_prefix='?', intents=intents)
def generate_salt(length=6):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

AIRSONIC_SALT = generate_salt()

def generate_airsonic_token(password, salt):
    md5 = hashlib.md5()
    md5.update((password + salt).encode('utf-8'))
    return md5.hexdigest()

AIRSONIC_TOKEN = generate_airsonic_token(AIRSONIC_PASSWORD, AIRSONIC_SALT)
def generate_salt():
    return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(6))

def generate_token(password, salt):
    return hashlib.md5((password + salt).encode('utf-8')).hexdigest()

def get_airsonic_api_url(method, extra_params=None):
    params = {
        'u': AIRSONIC_USERNAME,
        't': AIRSONIC_TOKEN,
        's': AIRSONIC_SALT,
        'v': AIRSONIC_API_VERSION,
        'c': AIRSONIC_CLIENT_NAME,
        'f': 'json'
    }

    if extra_params:
        params.update(extra_params)

    query_string = '&'.join([f'{key}={value}' for key, value in params.items()])
    return f"{AIRSONIC_URL}/rest/{method}?{query_string}"


@bot.event
async def on_ready():
    print(f'{bot.user} is connected!')

# Add this function to your bot code:

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandError):
        await ctx.send(f'Error: {str(error)}')
    else:
        raise error

@bot.command(name='ping', help='Check the bot connection')
async def ping(ctx):
    await ctx.send('Pong!')

@bot.command(name='airsonic', help='Check if the Airsonic server is reachable')
async def airsonic(ctx):
    try:
        response = requests.get(get_airsonic_api_url('ping.view'), verify=False)
        if response.status_code == 200:
            await ctx.send('Airsonic server is reachable.')
        else:
            await ctx.send(f'Error {response.status_code}: Unable to reach Airsonic server.')
    except Exception as e:
        await ctx.send(f'Error: {str(e)}')

@bot.command(name='change_song', help='Change the song on the specified Airsonic player')
async def change_song(ctx, player_id: str):
    try:
        response = requests.get(get_airsonic_api_url('skip', extra_params={'playerId': player_id}), verify=False)
        if response.status_code == 200:
            await ctx.send('Song changed successfully.')
        else:
            await ctx.send(f'Error {response.status_code}: Unable to change the song.')
    except Exception as e:
        await ctx.send(f'Error: {str(e)}')

@bot.command(name='list_playlists', help='List all Airsonic playlists')
async def list_playlists(ctx):
    try:
        response = requests.get(get_airsonic_api_url('getPlaylists'), verify=False)
        data = response.json()
        if response.status_code != 200 or data['subsonic-response']['status'] != 'ok':
            await ctx.send(f'Error {response.status_code}: Unable to retrieve playlists.')
            return
        for playlist in data['subsonic-response']['playlists']['playlist']:
            await ctx.send(f'Playlist ID: {playlist["id"]}, Playlist: {playlist["name"]}')
    except Exception as e:
        await ctx.send(f'Error: {str(e)}')

@bot.command(name='play_playlist', help='Start playing a playlist')
async def play_playlist(ctx, playlist_id: str):
    try:
        # First, clear the current playlist
        params = {'action': 'stop'}
        response = requests.get(get_airsonic_api_url('jukeboxControl', extra_params=params), verify=False)
        data = response.json()

        # Then, load the new playlist
        params = {'action': 'set', 'id': playlist_id}
        response = requests.get(get_airsonic_api_url('jukeboxControl', extra_params=params), verify=False)
        data = response.json()

        # Finally, start playing the new playlist
        params = {'action': 'start'}
        response = requests.get(get_airsonic_api_url('jukeboxControl', extra_params=params), verify=False)
        data = response.json()

        if response.status_code != 200 or data['subsonic-response']['status'] != 'ok':
            await ctx.send(f'Error {response.status_code}: Unable to start playlist.')
            return

        await ctx.send('Successfully started playlist.')
    except Exception as e:
        await ctx.send(f'Error: {str(e)}')


@bot.command(name='playing', help='Displays the songs currently playing on Airsonic by all users')
async def playing(ctx):
    try:
        # Request the current jukebox status
        response = requests.get(get_airsonic_api_url('getNowPlaying'), verify=False)
        data = response.json()

        # Check the status of the response
        if response.status_code != 200 or data['subsonic-response']['status'] != 'ok':
            await ctx.send(f'Error {response.status_code}: Unable to fetch currently playing songs.')
            return

        # Check if any song is playing
        now_playing_list = data['subsonic-response'].get('nowPlaying', {}).get('entry', [])
        if not now_playing_list:
            await ctx.send('No song is currently playing.')
            return

        # Retrieve and display details of all playing songs
        for i, song in enumerate(now_playing_list, start=1):
            await ctx.send(f'{i}. "{song["title"]}" by {song["artist"]}')
    except Exception as e:
        await ctx.send(f'Error: {str(e)}')



@bot.command(name='play_on_player', help='Play a playlist on a specific player')
async def play_on_player(ctx, player_id: str, playlist_id: str):
    try:
        # Set the player to use
        params = {'action': 'set', 'id': player_id}
        response = requests.get(get_airsonic_api_url('jukeboxControl', extra_params=params), verify=False)
        data = response.json()

        if response.status_code != 200 or data['subsonic-response']['status'] != 'ok':
            await ctx.send(f'Error setting player: {data["subsonic-response"].get("error", {}).get("message", "")}')
            return

        # Load the playlist
        params = {'action': 'set', 'id': playlist_id}
        response = requests.get(get_airsonic_api_url('jukeboxControl', extra_params=params), verify=False)
        data = response.json()

        if response.status_code != 200 or data['subsonic-response']['status'] != 'ok':
            await ctx.send(f'Error loading playlist: {data["subsonic-response"].get("error", {}).get("message", "")}')
            return

        # Play the playlist
        params = {'action': 'start'}
        response = requests.get(get_airsonic_api_url('jukeboxControl', extra_params=params), verify=False)
        data = response.json()

        if response.status_code != 200 or data['subsonic-response']['status'] != 'ok':
            await ctx.send(f'Error starting playback: {data["subsonic-response"].get("error", {}).get("message", "")}')
            return

        await ctx.send(f'Successfully started playing playlist {playlist_id} on player {player_id}.')
    except Exception as e:
        await ctx.send(f'Error: {str(e)}')



@bot.command(name='get_player_id', help='Get player ID')
async def get_player_id(ctx):
    try:
        # Send a request to the Airsonic server
        response = requests.get(get_airsonic_api_url('getNowPlaying'), verify=False)
        data = response.json()

        # Check the status of the response
        if response.status_code != 200:
            await ctx.send(f'Error {response.status_code}: Unable to fetch now playing.')
            return

        if data['subsonic-response']['status'] != 'ok':
            await ctx.send(f'Error: {data["subsonic-response"]["error"]["message"]}')
            return

        now_playing_entries = data['subsonic-response']['nowPlaying']['entry']

        if not now_playing_entries:
            await ctx.send('No songs currently playing.')
            return

        player_id = now_playing_entries[0]['playerId']
        await ctx.send(f'Player ID: {player_id}')
    except Exception as e:
        await ctx.send(f'Error: {str(e)}')

if __name__ == '__main__':
    bot.run(TOKEN)
