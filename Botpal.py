from dotenv import load_dotenv
import os
from twitchio.ext import commands
from twitchio import Message
import time
import re
import random
import requests
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from flask import Flask, redirect, request, jsonify, session
import threading
import webbrowser
import pickle
from AnswersAI import answer_question
from BotpalUtils import get_alertus, time_format, getTranslation, is_question, is_mod, is_vip, language
from BotpalTTS import change_voice

# https://id.twitch.tv/oauth2/authorize?response_type=token&client_id=4rbssd4gv3vpwike8d0jjl29v41t19&redirect_uri=https://localhost:3000&scope=channel%3Abot+channel%3Amanage%3Amoderators+channel%3Amanage%3Aredemptions

# get the environment variables
load_dotenv()
idSpotify = os.getenv("SPOTIFY_CLIENT_ID")
secretSpotify = os.getenv("SPOTIFY_CLIENT_SECRET")

twitch_token = os.getenv("TWITCH_TOKEN")
twitch_client_id = os.getenv("TWITCH_CLIENT_ID")
twitch_client_secret = os.getenv("TWITCH_CLIENT_SECRET")
reward_id = os.getenv("REWARD_ID")
weather_key = os.getenv("WEATHER_API_KEY")

# variables
klonoa = 0
deaths = 0
tts_enabled = False
whoWantsSkip = []
whenSkip = 0
listOfIms = ["ich bin ein ", "i'm a ", "i am an ", "i am the ", "ich bin der ", "i'm the ", "im the ", "i am the ", "ich bin die ", "i bims der ", "i bims ", "ich heiße ", "i'm called ", "i'm named ", "i'm known as ", "mein name ist ", "i am ", "ich bin ", "i'm "]
regex_pattern = "|".join(map(re.escape, listOfIms))
channels = ["lordzaros_"]
lurks = {}
twitch_client_tokens = {"lordzaros_": os.getenv("TWITCH_TOKEN_ZAROS")}
channel_ids = {}
blacklist = []
blacklistedUsers = []
    
# create the bot
bot = commands.Bot(
    token=twitch_token,
    client_id=twitch_client_id,
    nick='fritzbotpal',
    prefix='!',
    initial_channels=channels
)

# get twitch api headers
def get_twitch_headers():
    return {
        "Client-ID": twitch_client_id,
        "Authorization": "Bearer " + twitch_token
    }

# get twitch client headers
def get_twitch_client_headers(channel):
    global twitch_client_tokens
    if channel not in twitch_client_tokens:
        return get_twitch_headers()
    return {
        "Client-ID": twitch_client_id,
        "Authorization": "Bearer " + twitch_client_tokens[channel]
    }

# event listener for chat messages
@bot.event()
async def event_message(message: Message):
    # ignore messages without author aka bot messages
    if not message.author:
        print("null: ", message.content)
        return
    
    # check if the message is a redemption of the songrequest reward
    if is_redemption(message.raw_data):
        if message.author.name in blacklistedUsers:
            await message.channel.send("@" + message.author.name + " du bist permanent vom Songrequest ausgeschlossen")
            return
        await process_redeem(message.content, message.channel)
        return
    
    # print the message to the console
    print("chat:(" + message.author.channel.name + ") " + message.author.name,":", message.content)
    
    # 1% chance to tell someone they stink
    if random.random() < 0.002:
        await message.channel.send("@" + message.author.name + getTranslation("stink"))
        
    # check if the message is a greeting and respond with troll
    match = re.search(regex_pattern, message.content.lower())
    if match:
        nameString = message.content[match.end():].strip()
        split = nameString.split(" ")
        print(match, split)
        if len(split) > 0 and len(split) <= 3:
            name = []
            for word in split:
                if word.endswith(",") or word.endswith(".") or word.endswith("!") or word.endswith("?"):
                    name.append(word[:-1])
                    break
                else:
                    name.append(word)
            await message.channel.send(getTranslation("hallo") + " ".join(name) + getTranslation("iam"))

    # check if the message is a question and respond with the AI
    if ("botpal" in message.content.lower() or "fritzbot" in message.content.lower()) and is_question(message.content.lower()):
        await answer_question(message, getTranslation, get_alertus, tts_enabled)
    
    # check if klonoa is on the toilet and respond with the time
    global klonoa
    if message.author.name == "klonoaofthewind":
        if klonoa > 0:
            await message.channel.send("/me Klonoa war " + time_format(round(time.time() - klonoa)) + " auf dem Klo")
            klonoa = 0
    
    # check if chatter was lurking and respond with the time
    if message.author.name in lurks:
        lurktime = time_format(round(time.time() - lurks[message.author.name]))
        if lurktime:
            await message.channel.send("/me " + message.author.name + " war " + lurktime + " im lurk!")
            lurks.pop(message.author.name)
            serialize_lurks()
        
    # echo emotes
    if message.author.name == "streamelements" and message.content == "DieStimmen":
        await message.channel.send("frfr")
    if message.author.name != "fritzbotpal" and message.content == get_alertus(message.author.channel.name):
        await message.channel.send(get_alertus(message.author.channel.name))

# command test
@bot.command(name='test')
async def test_command(ctx):
    await ctx.send(getTranslation("test"))

# command klo
@bot.command(name='klo')
async def pipi_command(ctx):
    global klonoa
    if klonoa == 0:
        klonoa = time.time()
        await ctx.send("/me Klonoa muss aufs Klo " + get_alertus(ctx.author.channel.name))
        
# command lurk
@bot.command(name='lurk')
async def lurk_command(ctx):
    if ctx.author.name in lurks:
        return
    lurks[ctx.author.name] = time.time()
    serialize_lurks()
    await ctx.send("/me " + ctx.author.name + " ist jetzt im lurk! " + get_alertus(ctx.author.channel.name))

# command play
@bot.command(name='play')
async def play_command(ctx):
    if ctx.author.name != "fritzpal":
        return
    await ctx.send("!play")
    
# voice command
@bot.command(name='voice')
async def voice_command(ctx, amount=None):
    if not is_mod(ctx):
        return
    if not amount:
        await ctx.send("/me Usage: !voice <0-2>")
        return
    try:
        amount = int(amount)
        change_voice(amount)
        await ctx.send("/me Voice changed to " + str(amount))
    except:
        await ctx.send("/me Usage: !voice <0-2>")

# command tts
@bot.command(name='enabletts')
async def tts_command(ctx):
    global tts_enabled
    if not is_mod(ctx):
        return
    tts_enabled = not tts_enabled
    await ctx.send("/me TTS " + ("enabled" if tts_enabled else "disabled"))

# command elo
@bot.command(name='elo')
async def elo_command(ctx, name=None):
    # headers
    headers = {
        "User-Agent": "Botpal/1.0"
    }
    # get name from context
    if name:
        subject = name
    else:
        subject = ctx.author.name
    
    response = requests.get("https://api.chess.com/pub/player/" + subject + "/stats", headers=headers)
    if response.status_code == 200:
        data = response.json()
    else:
        if response.status_code == 404:
            await ctx.send(f"/me {subject} not found")
            return
        print("Error:", response.status_code)
        await ctx.send("/me Something went wrong trying to reach the API")
        return
    if 'chess_rapid' not in data:
        await ctx.send(f"/me {subject} has no rapid elo")
        return
    await ctx.send(f"/me {subject}'s rapid elo: {data['chess_rapid']['last']['rating']}")

# command weather
@bot.command(name='weather')
async def weather_command(ctx, *, city):
    if not city:
        await ctx.send("/me Usage: !weather <city>")
        return
    response = requests.get(f"https://api.weatherapi.com/v1/current.json?q={city}&lang={language}&key={weather_key}")
    if not response:
        await ctx.send("/me Error fetching weather data")
        print("Response null")
        return
    if response.status_code != 200:
        print("Error:", response.status_code, response.json())
        if response.status_code == 400 and response.json()["code"] == 1006:
            await ctx.send("/me Location not found")
            return
        await ctx.send("/me Error fetching weather data")
        return
    if language == "de":
        msg = f"/me Das Wetter in {response.json()["location"]["name"]} - {response.json()["location"]["country"]} ist {response.json()["current"]["condition"]["text"]} bei {response.json()["current"]["temp_c"]}°C. Die Windgeschwindigkeit beträgt {response.json()["current"]["wind_kph"]} km/h."
    elif language == "en":
        msg = f"/me The weather in {response.json()["location"]["name"]} - {response.json()["location"]["country"]} is {response.json()["current"]["condition"]["text"]} at {response.json()["current"]["temp_c"]}°C. The wind speed is {response.json()["current"]["wind_kph"]} km/h."
    if not response.json()["location"]["tz_id"].startswith("Europe"):
        msg += f" Es ist gerade {response.json()["location"]["localtime"].split()[1]} Uhr in {response.json()["location"]["name"]}."
    await ctx.send(msg)

# command death 
@bot.command(name='death')
async def death_command(ctx, amount = None):
    global deaths
    if not is_mod(ctx) and not is_vip(ctx):
        return
    if amount:
        try:
            deaths = int(amount)
        except:
            deaths += 1
    else:
        deaths += 1
    await ctx.send(f"/me {ctx.author.channel.name} ist bisher {deaths} mal gestorben.")

# environment variables for spotify
load_dotenv()
idSpotify = os.getenv("SPOTIFY_CLIENT_ID")
secretSpotify = os.getenv("SPOTIFY_CLIENT_SECRET")

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY")

# links for spotify
redirect_uri = "https://localhost:3000/callback"
auth_url = "https://accounts.spotify.com/authorize"
token_url = "https://accounts.spotify.com/api/token"
api_base_url = "https://api.spotify.com/v1"

token_info = None
expires_at = 0

# create the spotify oauth object
def create_spotify_oauth():
    return SpotifyOAuth(
        client_id=idSpotify,
        client_secret=secretSpotify,
        redirect_uri=redirect_uri,
        scope="user-read-playback-state user-modify-playback-state user-read-currently-playing user-read-playback-position user-read-recently-played user-top-read user-read-playback-position user-read-private user-read-email user-library-read user-library-modify playlist-read-private playlist-modify-public playlist-modify-private playlist-read-collaborative user-follow-read user-follow-modify user-read-recently-played",
    )

# authentication sites for spotify oauth
@app.route("/")
def index():
    global token_info
    if token_info:
        return "Du bist eingeloggt"
    if session.get("token_info"):
        token_info = session.get("token_info")
        return redirect("/success")
    return "Mit Spotify <a href='/login'>einloggen</a>"

@app.route("/login")
def login():
    auth_url = create_spotify_oauth().get_authorize_url()
    return redirect(auth_url)

@app.route("/callback")
def callback():
    if "error" in request.args:
        return jsonify({"error": request.args["error"]})
    if "code" not in request.args:
        return jsonify({"error": "No code in request"})
    code = request.args.get('code')
    global token_info
    global expires_at
    token_info = create_spotify_oauth().get_access_token(code)
    session["token_info"] = token_info
    expires_at = int(time.time()) + token_info["expires_in"]
    return redirect("/success")

# fuctions to get spotipy object
def get_spotify():
    global token_info
    if not token_info:
        redirect("/login")
    
    global expires_at
    is_expired = expires_at - int(time.time()) < 60
    if(is_expired):
        spotify_oauth = create_spotify_oauth()
        token_info = spotify_oauth.refresh_access_token(token_info['refresh_token'])

    return spotipy.Spotify(auth=token_info["access_token"])

# returns the device id of the first device of the user
def get_device():
    if not get_spotify().devices()["devices"]:
        return None
    return get_spotify().devices()["devices"][0]["id"]

# returns the currently playing song or that nothing is playing
def get_currently_playing():
    try:
        playback = get_spotify().current_playback()
        if not playback:
            return getTranslation("noSong")
        return playback["item"]["name"] + " - " + playback["item"]["artists"][0]["name"]
    except:
        print(playback)
        return "Error fetching song"

# add a song to the queue by uri
def add_track_to_queue(track_uri):
    get_spotify().add_to_queue(track_uri)
    return 

# return queue
def get_queue():
    return get_spotify().queue()

# set the volume of the current device
def set_volume(volume):
    device_id = get_device()
    if not device_id:
        return False
    get_spotify().volume(volume, device_id)
    return True

# search for a song by query
def get_search_results(query):
    return get_spotify().search(query, 10, 0, "track")

# get the info of a song by uri
def get_song_info(track_uri):
    return get_spotify().track(track_uri)

# get the info of an artist by uri
def get_artist_info(artist_uri):
    return get_spotify().artist(artist_uri)

# skip the current song
def skip_song():
    device_id = get_device()
    if not device_id:
        return False
    get_spotify().next_track(device_id)
    return True

# get view count of a channel
def get_view_count(channel):
    global channel_ids
    response = requests.get("https://api.twitch.tv/helix/streams?user_id=" + channel_ids[channel], headers=get_twitch_headers())
    if response.status_code == 200:
        data = response.json()
        if data["data"]:
            return data["data"][0]["viewer_count"]
        return 0
    else:
        print("Error:", response.status_code)
        return 0
        
# get all mods of a channel
def get_mods(channel):
    response = requests.get("https://api.twitch.tv/helix/moderation/moderators?broadcaster_id=" + channel_ids[channel], headers=get_twitch_client_headers(channel))
    if response.status_code == 200:
        data = response.json()
        mods = []
        for mod in data["data"]:
            mods.append(mod["user_name"])
        return mods
    else:
        print("Error:", response.status_code)
        return []
    
# get list of custom rewards
def get_custom_rewards(channel):
    response = requests.get("https://api.twitch.tv/helix/channel_points/custom_rewards?broadcaster_id=" + channel_ids[channel], headers=get_twitch_client_headers(channel))
    if response.status_code == 200:
        return response.json()["data"]
    else:
        print("Error:", response)
        return []
    
# get redemptions of a custom reward
def get_redemptions(channel, reward_id):
    response = requests.get("https://api.twitch.tv/helix/channel_points/custom_rewards/redemptions?broadcaster_id=" + channel_ids[channel] + "&reward_id=" + reward_id + "&status=UNFULFILLED", headers=get_twitch_client_headers(channel))
    if response.status_code == 200:
        data = response.json()
        return data["data"]
    else:
        print("Error:", response)
        return []
    
# create reward
def create_custom_reward(channel):
    data = {
        "title": "Botpal-Songrequest",
        "cost": 1,
        "prompt": "Requeste einen Song mit einem Spotify-Link oder dem Namen des Songs",
        "is_enabled": True,
        "background_color": "#1e90ff",
        "is_user_input_required": True,
        "should_redemptions_skip_request_queue": True
    }
    response = requests.post("https://api.twitch.tv/helix/channel_points/custom_rewards?broadcaster_id=" + channel_ids[channel], headers=get_twitch_client_headers(channel), json=data)
    if response.status_code == 200:
        return response.json()
    else:
        print("Error:", response)
        return None
    
# delete reward
def delete_custom_reward(channel, reward_id):
    response = requests.delete("https://api.twitch.tv/helix/channel_points/custom_rewards?broadcaster_id=" + channel_ids[channel] + "&id=" + reward_id, headers=get_twitch_client_headers(channel))
    if response.status_code == 200:
        return response.json()
    else:
        print("Error:", response)
        return None

# bot command to create the songrequest reward
@bot.command(name='createreward')
async def createreward_command(ctx):
    if not ctx.author.channel.name == ctx.author.name and not ctx.author.name == "fritzpal":
        return
    reward = create_custom_reward(ctx.author.channel.name)
    if not reward:
        await ctx.send("/me Error creating reward")
        return
    await ctx.send("/me Reward successfully created: " + reward["data"][0]["id"])

# bot command to see mods
@bot.command(name='mods')
async def mods_command(ctx):
    mods = get_mods(ctx.author.channel.name)
    if not mods:
        await ctx.send("/me no mods")
        return
    await ctx.send("/me Mods: " + ", ".join(mods))  

# bot commands to get currently playing song
@bot.command(name='song')
async def song_command(ctx):
    if not token_info:
        await ctx.send("/me spotify not authenticated")
        return
    song = get_currently_playing()
    await ctx.send("@" + ctx.author.name + " -> Song: " + song)
    
# bot command to see the queue
@bot.command(name='queue', aliases=['q'])
async def queue_command(ctx):
    if not token_info:
        await ctx.send("/me spotify not authenticated")
        return
    queue = get_queue()
    if not queue["queue"]:
        await ctx.send("/me queue is empty")
        return
    songs = []
    for item in queue["queue"]:
        songs.append(item["name"] + " - " + item["artists"][0]["name"])
    # add the first 3 songs to the message
    msg = "/me " + getTranslation("queue") + ": "
    for i in range(3):
        if i < len(songs):
            msg += songs[i] + " -> "
    msg = msg[:-4]
    if len(msg) > 500:
        msg = msg[:500]
    await ctx.send(msg)
    
# bot command to change volume
@bot.command(name='volume', aliases=['vol'])
async def volume_command(ctx, volume=None):
    if not is_mod(ctx):
        return
    if not token_info:
        await ctx.send("/me spotify not authenticated")
        return
    if not volume:
        await ctx.send("/me Usage: !volume <0-100>")
        return
    try:
        volume = int(volume)
        if volume < 0 or volume > 100:
            await ctx.send("/me Usage: !volume <0-100>")
            return
        if set_volume(volume):
            await ctx.send(getTranslation("volumeSet") + str(volume) + "%")
        else:
            await ctx.send("/me No active device")
    except:
        await ctx.send("/me Usage: !volume <0-100>")
    
# bot command to vote skip the current song
@bot.command(name='skip', aliases=['voteskip'])
async def skip_command(ctx):
    global whenSkip
    global whoWantsSkip
    if not token_info:
        await ctx.send("/me spotify not authenticated")
        return
    if time.time() - whenSkip > 30:
        whoWantsSkip.clear()
    if ctx.author.name in whoWantsSkip:
        return
    whoWantsSkip.append(ctx.author.name)
    viewcount = get_view_count(ctx.author.channel.name)
    needed = int(viewcount / 5 + 1)
    needed = max(needed, 2)
    if len(whoWantsSkip) >= needed:
        if skip_song():
            await ctx.send("/me skipped song")
        else:
            await ctx.send(getTranslation("noSong"))
        whoWantsSkip.clear()
    else:
        await ctx.send("/me " + ctx.author.name + getTranslation("skip") + " (" + str(len(whoWantsSkip)) + "/" + str(needed) + ")")
        whenSkip = time.time()
        
# bot command to blacklist a song
@bot.command(name='blacklist', aliases=['blacklistsong'])
async def blacklist_command(ctx, song=None):
    if not token_info:
        await ctx.send("/me spotify not authenticated")
        return
    if not is_mod(ctx):
        return
    if not song:
        await ctx.send("/me Usage: !blacklist <song>")
        return
    try:
        info = get_song_info(song.strip())
    except:
        await ctx.send("/me Song not found")
        return
    if not info:
        await ctx.send("/me Song not found")
        return
    blacklist.append(info["uri"])
    await ctx.send("/me Added " + info["name"] + " - " + info["artists"][0]["name"] + " to the blacklist")
    # write to file
    with open("blacklisted.txt", "a") as file:
        file.write(info["uri"] + "\n")
        
# bot command to blacklist an artist
@bot.command(name='blacklistartist')
async def blacklistartist_command(ctx, artist=None):
    if not token_info:
        await ctx.send("/me spotify not authenticated")
        return
    if not is_mod(ctx):
        return
    if not artist:
        await ctx.send("/me Usage: !blacklistartist <artist>")
        return
    try:
        info = get_artist_info(artist.strip())
    except:
        await ctx.send("/me Artist not found")
        return
    if not info:
        await ctx.send("/me Artist not found")
        return
    blacklist.append(info["uri"])
    await ctx.send("/me Added " + info["name"] + " to the blacklist")
    # write to file
    with open("blacklisted.txt", "a") as file:
        file.write(info["uri"] + "\n")
        
# bot command to blacklist a user
@bot.command(name='blacklistuser')
async def blacklistuser_command(ctx, user=None):
    if not is_mod(ctx):
        return
    if not user:
        await ctx.send("/me Usage: !blacklistuser <user>")
        return
    user = user.strip().lower()
    blacklistedUsers.append(user)
    await ctx.send("/me Added " + user + " to the blacklist")
    # write to file
    with open("blacklistedusers.txt", "a") as file:
        file.write(user + "\n")

# parse raw data and return if the message is a redemption of the songrequest reward
def is_redemption(raw_data):
    attributes = raw_data.split(";")
    global reward_id
    for attribute in attributes:
        if "custom-reward-id=" + reward_id == attribute:
            return True
    return False

# bot command to force skip as mod
@bot.command(name='forceskip')
async def forceskip_command(ctx):
    if is_mod(ctx):
        if skip_song():
            await ctx.send("/me skipped song")
        else:
            await ctx.send(getTranslation("noSong"))

# process the redemption of the songrequest reward
async def process_redeem(song, channel):
    global token_info
    if not token_info:
        await channel.send("/me spotify not authenticated")
        return
    if not song:
        return
    song = song.strip()
    track = None
    artist = None
    # check if the song is a spotify link and query search results if not
    if "spotify:track:" not in song and "open.spotify.com" not in song:
        search_results = get_search_results(song)
        if not search_results or not search_results["tracks"]["items"]:
            await channel.send("/me Song not found")
            return
        song = search_results["tracks"]["items"][0]["uri"]
        track = search_results["tracks"]["items"][0]["name"] + " - " + search_results["tracks"]["items"][0]["artists"][0]["name"]
        artists = search_results["tracks"]["items"][0]["artists"]
    try:
        # get the song info if not already done
        if not track:
            info = get_song_info(song)
            track = info["name"] + " - " + info["artists"][0]["name"]
            song = info["uri"]
            artists = info["artists"]
        # check if the song is blacklisted
        if song in blacklist:
            await channel.send("/me Song is blacklisted " + get_alertus(channel.name))
            return
        # check if any artist of the song is blacklisted
        if any(artist["uri"] in blacklist for artist in artists):
            await channel.send("/me Artist is blacklisted " + get_alertus(channel.name))
            return
        # add the song to the queue
        add_track_to_queue(song)
    except Exception as e:
        # send error message if the song is not found or the user has no active device
        print("Error:", e)
        if "NO_ACTIVE_DEVICE" in str(e):
            await channel.send("/me No active device")
            return
        await channel.send("/me Song not found")
        return    
    await channel.send("/me added " + track + " to the queue")

# bot command to request a song
@bot.command(name='songrequest', aliases=['sr'])
async def songrequest_command(ctx, *, song):
    if not is_mod(ctx):
        return
    if not song:
        await ctx.send("/me Usage: !sr <name|link>")
        return
    await process_redeem(song, ctx.author.channel)
    
# get the blacklisted songs from cvs file
def fill_blacklist():
    global blacklist
    with open("blacklisted.txt", "r") as file:
        blacklist = file.read().splitlines()
    print(blacklist)
    with open("blacklistedusers.txt", "r") as file:
        global blacklistedUsers
        blacklistedUsers = file.read().splitlines()
    
# get the channel ids for the channels
def retrieve_channel_ids():
    global channel_ids
    response = requests.get("https://api.twitch.tv/helix/users?login=" + "&login=".join(channels), headers=get_twitch_headers())
    if response.status_code == 200:
        for user in response.json()["data"]:
            channel_ids[user["login"]] = user["id"]
    else:
        print("Error:", response.status_code)
    print(channel_ids)
    
# deserialize the lurk dictionary
def deserialize_lurks():
    global lurks
    if os.path.isfile("lurk.pickle"):
        with open('lurk.pickle', 'rb') as handle:
            lurks = pickle.load(handle)
    else:
        serialize_lurks()
        
        
# serialize the lurk dictionary
def serialize_lurks():
    global lurks 
    with open('lurk.pickle', 'wb') as handle:
        pickle.dump(lurks, handle, protocol=pickle.HIGHEST_PROTOCOL)

# run the bot
def run_bot():
    if __name__ == "__main__":
        threading.Thread(target=bot.run).start()

@app.route("/success")
def success():
    run_bot()
    retrieve_channel_ids()
    fill_blacklist()
    deserialize_lurks()
    return "Du kannst den tab jetzt schließen"

# run the flask app
webbrowser.open("https://localhost:3000", new=0, autoraise=True)
app.run(host="0.0.0.0", port=3000, debug=False, ssl_context="adhoc")
    
          