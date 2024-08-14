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
from AnswersAI import answer_question

# https://id.twitch.tv/oauth2/authorize?response_type=token&client_id=4rbssd4gv3vpwike8d0jjl29v41t19&redirect_uri=https://localhost:3000&scope=channel%3Abot+channel%3Amanage%3Amoderators+channel%3Amanage%3Aredemptions

# get the environment variables
load_dotenv()
idSpotify = os.getenv("SPOTIFY_CLIENT_ID")
secretSpotify = os.getenv("SPOTIFY_CLIENT_SECRET")

twitch_token = os.getenv("TWITCH_TOKEN")
twitch_client_id = os.getenv("TWITCH_CLIENT_ID")
twitch_client_secret = os.getenv("TWITCH_CLIENT_SECRET")
reward_id = os.getenv("REWARD_ID")

# variables
klonoa = 0
deaths = 0
whoWantsSkip = []
whenSkip = 0
listOfIms = ["ich bin ein ", "i'm a ", "i am an ", "i am the ", "ich bin der ", "i'm the ", "im the ", "i am the ", "ich bin die ", "i bims der ", "i bims ", "ich heiße ", "i'm called ", "i'm named ", "i'm known as ", "mein name ist ", "i am ", "ich bin ", "i'm "]
regex_pattern = "|".join(map(re.escape, listOfIms))
channels = ["fritzpal", "klonoaofthewind", "haplolp", "lordzaros_"]
twitch_client_tokens = {"fritzpal": os.getenv("TWITCH_TOKEN_FRITZPAL"), "lordzaros_": os.getenv("TWITCH_TOKEN_ZAROS")}
channel_ids = {}
language = "de"
blacklist = []

# translations
def getTranslation(key):
    translationsDE = {
        "stink": " stinkt!",
        "iam": ", ich bin Botpal",
        "hallo": "Hallo ",
        "defaultResponse": "Ich bin ein Twitchbot namens Botpal. Ich bin allwissend und du kannst mich alles fragen.",
        "overloaded": "Ich bin gerade überfordert. Frag mich gleich nochmal.",
        "test": "/me Test erfolgreich",
        "systemPrompt": "Du bist ein Twitch Chatbot namens Botpal und du bist allwissend. Antworte immer nur mit EINEM ganz kurzen Satz und auf DEUTSCH. Du bist im stream vom streamer ",
        "systemPrompt2": " und der Zuschauer ",
        "systemPrompt3": " stellt dir eine Frage.",
        "allGood": "Mir geht es gut, danke der Nachfrage. Wie geht es dir ",
        "noSong": "Es wird gerade kein Song abgespielt.",
        "queue": "Die nächsten Songs sind",
        "skip": " möchte den Song skippen. ",
        "volumeSet": "Setze Lautstärke auf "
    }
    translationsEN = {
        "stink": " smells!",
        "iam": ", I am Botpal",
        "hallo": "Hello ",
        "defaultResponse": "I am a twitchbot named Botpal. I am all-knowing and you can ask me anything.",
        "overloaded": "I am a bit overwhelmed. Ask me again in a moment.",
        "test": "/me Test successful",
        "systemPrompt": "You are a Twitch chatbot named Botpal and you are all-knowing. Always respond with ONE very short sentence and in English. You are in the stream of the streamer ",
        "systemPrompt2": " and the viewer ",
        "systemPrompt3": " asks you a question.",
        "allGood": "I am fine, thank you for asking. How are you ",
        "noSong": "Nothing is playing",
        "queue": "The next songs are",
        "skip": " wants to skip the song. ",
        "volumeSet": "Set volume to "
    }
    
    if language == "de":
        return translationsDE[key]
    if language == "en":
        return translationsEN[key]
    
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

# check if the message is a question
def is_question(text):
    if language == "de":
        return ("?" in text or "gibt es" in text or "kannst du" in text or "bist du" in text or "was" in text or "wer" in text or "warum" in text or "wie" in text or "wieso" in text or "weshalb" in text or "wozu" in text or "welcher" in text or "welche" in text or "welches" in text or "wann" in text or "wo " in text)
    return ("?" in text or "is there" in text or "can you" in text or "are you" in text or "do you" in text or "who" in text or "why" in text or "how" in text or "where" in text or "what" in text or "which" in text or "whom" in text or "whose" in text or "when" in text) 

# event listener for chat messages
@bot.event()
async def event_message(message: Message):
    # ignore messages without author aka bot messages
    if not message.author:
        print("null: ", message.content)
        return
    
    if is_redemption(message.raw_data):
        await process_redeem(message.content, message.channel)
        return
    
    print("chat:(" + message.author.channel.name + ") " + message.author.name,":", message.content)
    
    # 1% chance to tell someone they stink
    if random.random() < 0.002:
        await message.channel.send("@" + message.author.name + getTranslation("stink"))
        
    # check if the message is a greeting and respond with troll
    match = re.search(regex_pattern, message.content.lower())
    if match:
        nameString = message.content[match.end():].strip()
        print(match, nameString.split(" "))
        if nameString:
            await message.channel.send(getTranslation("hallo") + nameString.split(" ")[0].replace(",", "").replace(".", "") + getTranslation("iam"))

    # check if the message is a question and respond with the AI
    if ("botpal" in message.content.lower() or "fritzbot" in message.content.lower()) and is_question(message.content.lower()):
        await answer_question(message, getTranslation, get_alertus)
    
    # check if klonoa is on the toilet and respond with the time
    global klonoa
    if message.author.name == "klonoaofthewind":
        if klonoa > 0:
            await message.channel.send("/me Klonoa war " + str(round(time.time() - klonoa)) + " Sekunden auf dem Klo")
            klonoa = 0

    # echo emotes
    if message.author.name == "streamelements" and message.content == "DieStimmen":
        await message.channel.send("frfr")
    if message.author.name != "fritzbotpal" and message.content == get_alertus(message.author.channel.name):
        await message.channel.send(get_alertus(message.author.channel.name))

# command test
@bot.command(name='test')
async def test_command(ctx):
    await ctx.send(getTranslation("test"))

# returns the alertus emoji for the given channel
def get_alertus(channel):
    if channel == "haplolp":
        return "haplolALERTUs"
    if channel == "klonoaofthewind" or channel == "b1gf1sch":
        return "ALERTUS"
    if channel == "fritzpal" or channel == "lordzaros_":
        return "ALERTUs"
    return "🚨"

# command klo
@bot.command(name='klo')
async def pipi_command(ctx):
    global klonoa
    if klonoa == 0:
        klonoa = time.time()
        await ctx.send("/me Klonoa muss aufs Klo " + get_alertus(ctx.author.channel.name))

# command play
@bot.command(name='play')
async def play_command(ctx):
    if ctx.author.name != "fritzpal":
        return
    await ctx.send("!play")

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
            await ctx.send(f"/me 404 {subject} not found")
            return
        print("Error:", response.status_code)
        await ctx.send("/me Something went wrong trying to reach the API")
        return
    if 'chess_rapid' not in data:
        await ctx.send(f"/me {subject} has no rapid elo")
        return
    await ctx.send(f"/me {subject}'s rapid elo: {data['chess_rapid']['last']['rating']}")

# command death 
@bot.command(name='death')
async def death_command(ctx, amount = None):
    if ctx.author.channel.name != "blome17" and ctx.author.name != "fritzpal":
        return
    global deaths
    if amount:
        try:
            deaths = int(amount)
        except:
            deaths += 1
    else:
        deaths += 1
    await ctx.send(f"/me Vicky ist bisher {deaths} mal gestorben.")
    
# command to manually change api key
@bot.command(name='api-key')
async def api_key_command(ctx, key = None):
    if ctx.author.name == "fritzpal":
        global current_key
        if key:
            try:
                current_key = int(key)
            except:
                await ctx.send(f"/me Invalid key")
                return
        await ctx.send(f"/me Changed api key to: {current_key}")

    
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
    playback = get_spotify().current_playback()
    if not playback:
        return getTranslation("noSong")
    return playback["item"]["name"] + " - " + playback["item"]["artists"][0]["name"]

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
    if not is_mod(ctx.message._raw_data):
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
    if not is_mod(ctx.message._raw_data):
        return
    if not song:
        await ctx.send("/me Usage: !blacklist <song>")
        return
    info = get_song_info(song)
    if not info:
        await ctx.send("/me Song not found")
        return
    blacklist.append(info["uri"])
    await ctx.send("/me Added " + info["name"] + " - " + info["artists"][0]["name"] + " to the blacklist")
    # write to file
    with open("blacklisted.txt", "a") as file:
        file.write(info["uri"] + "\n")

# parse raw data and return if the user is a mod
def is_mod(raw_data):
    attributes = raw_data.split(";")
    print(attributes)
    for attribute in attributes:
        if "mod=1" == attribute or "display-name=Fritzpal" in attribute:
            return True
        if "mod=0" == attribute:
            return False
    return False

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
    if is_mod(ctx.message._raw_data):
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
    if "spotify:track:" not in song and "open.spotify.com" not in song:
        search_results = get_search_results(song)
        if not search_results or not search_results["tracks"]["items"]:
            await channel.send("/me Song not found")
            return
        song = search_results["tracks"]["items"][0]["uri"]
        track = search_results["tracks"]["items"][0]["name"] + " - " + search_results["tracks"]["items"][0]["artists"][0]["name"]
    try:
        if not track:
            info = get_song_info(song)
            track = info["name"] + " - " + info["artists"][0]["name"]
            song = info["uri"]
        if song in blacklist:
            await channel.send("/me Song is blacklisted " + get_alertus(channel.name))
            return
        add_track_to_queue(song)
    except Exception as e:
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

# run the bot
def run_bot():
    if __name__ == "__main__":
        threading.Thread(target=bot.run).start()

@app.route("/success")
def success():
    run_bot()
    retrieve_channel_ids()
    fill_blacklist()
    return "Du kannst den tab jetzt schließen"


# run the flask app
webbrowser.open("https://localhost:3000", new=0, autoraise=True)
app.run(host="0.0.0.0", port=3000, debug=False, ssl_context="adhoc")
    
          