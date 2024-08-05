from dotenv import load_dotenv
import os
from twitchio.ext import commands
import time
import re
import random
import requests
import openai
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from flask import Flask, redirect, request, jsonify, session
import threading

# https://id.twitch.tv/oauth2/authorize?response_type=token&client_id=4rbssd4gv3vpwike8d0jjl29v41t19&redirect_uri=https://localhost:3000&scope=chat%3Aread+chat%3Aedit+channel%3Amoderate+moderator%3Aread%3Afollowers+moderator%3Amanage%3Aannouncements+channel%3Aread%3Aredemptions+user%3Aread%3Afollows+moderator%3Aread%3Afollowers

# get the environment variables
load_dotenv()
idSpotify = os.getenv("SPOTIFY_CLIENT_ID")
secretSpotify = os.getenv("SPOTIFY_CLIENT_SECRET")

twitch_token = os.getenv("TWITCH_TOKEN")
twitch_client_id = os.getenv("TWITCH_CLIENT_ID")
twitch_client_secret = os.getenv("TWITCH_CLIENT_SECRET")

ai_api_keys = [os.getenv("AI_KEY0"), os.getenv("AI_KEY1"), os.getenv("AI_KEY2"), os.getenv("AI_KEY3"), os.getenv("AI_KEY4")]
current_key = 0

# translations
language = "de"
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
        "noSong": "Es wird gerade kein Song abgespielt."
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
        "noSong": "Nothing is playing"
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
    initial_channels=["fritzpal", "lordzaros_", "haplolp", "klonoaofthewind", "2oleh2"]
)

# variables
klonoa = 0
deaths = 0
listOfIms = ["ich bin ein ", "i'm a ", "i am an ", "i am the ", "ich bin der ", "i'm the ", "im the ", "i am the ", "ich bin die ", "i bims der ", "i bims ", "ich heiße ", "i'm called ", "i'm named ", "i'm known as ", "mein name ist ", "i am ", "ich bin ", "i'm "]
regex_pattern = "|".join(map(re.escape, listOfIms))

# check if the message is a question
def is_question(text):
    if language == "de":
        return ("?" in text or "gibt es" in text or "kannst du" in text or "bist du" in text or "was" in text or "wer" in text or "warum" in text or "wie" in text or "wieso" in text or "weshalb" in text or "wozu" in text or "welcher" in text or "welche" in text or "welches" in text or "wann" in text or "wo " in text)
    return ("?" in text or "is there" in text or "can you" in text or "are you" in text or "do you" in text or "who" in text or "why" in text or "how" in text or "where" in text or "what" in text or "which" in text or "whom" in text or "whose" in text or "when" in text) 

# event listener for chat messages
@bot.event()
async def event_message(message):
    # ignore messages without author aka bot messages
    if not message.author:
        print("null: ", message.content)
        return
    print("chat:(" + message.author.channel.name + ") " + message.author.name,":", message.content)
    
    # 1% chance to tell someone they stink
    if random.random() < 0.005:
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
        await answer_question(message)
    
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
    if channel == "klonoaofthewind":
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
    if ctx.author.channel.name != "blome17":
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

# send request to AI API
def chat_with_gpt(prompt, channel, user):
    # create the client
    client = openai.OpenAI(
        api_key=ai_api_keys[current_key % len(ai_api_keys)],
        base_url="https://api.aimlapi.com",
    )
    
    # add the system prompt to the message
    system_content = getTranslation("systemPrompt") + channel + " " + getTranslation("systemPrompt2") + user + getTranslation("systemPrompt3")

    # retrieve the response from the AI
    chat_completion = client.chat.completions.create(
        model="mistralai/Mistral-7B-Instruct-v0.2",
        messages=[
            {"role": "system", "content": system_content},
            {"role": "user", "content": prompt},
        ],
        temperature=1.0,
        max_tokens=128,
    )

    return chat_completion

# answer the question of the given message using the AI
async def answer_question(message):
    # replace the bot name with Botpal
    prompt = message.content.lower().replace("fritzbotpal", "Botpal").replace("fritzbot", "Botpal").replace("botpal", "Botpal").strip()
    print("prompt: " + prompt)
    try:
        response = chat_with_gpt(prompt, message.author.channel.name, message.author.name)
    except Exception as e:
        # send error message if the AI is overloaded change the key
        print("Error:", e)
        if "429" in str(e):
            global current_key
            current_key += 1
            print("key changed to: ", ai_api_keys[current_key % len(ai_api_keys)])
        await message.channel.send(getTranslation("overloaded"))
        return
    
    send = response.choices[0].message.content.strip()
    unchanged = send
    changed = False
    
    # strip botpal: from the beginning
    if send.lower().startswith("botpal:"):
        send = send[7:].strip()
    
    # limit the length of the response
    if len(send) > 400:
        send = send[:400]
        changed = True
    
    # cut off the response at the first special character
    for char in [">", "<", "/", "\r", "\n", "[", "#", "]"]:
        if char in send:
            send = send[:send.index(char)].strip()
            changed = True
    
    # cut off the response at the brace if it includes the word "instruction"
    if "instruction" in send.lower():
        match = re.search("[()]", send)
        if match:
            send = send[match.start():].strip()
            changed = True
    
    # send default response if the response if the ai is introducing itself
    if ("ich bin" in send.lower() or "i am" in send.lower() or "i'm" in send.lower()) and "botpal" in send.lower():
        send = getTranslation("defaultResponse")
        changed = True
        
    # replace "alles in ordnung"
    if "alles in ordnung" in send.lower():
        send = getTranslation("allGood") + "@" + message.author.name + "?"
        changed = True
    
    # add the alertus emoji to the response at the end if it was modified
    if changed:
        send = send + " " + get_alertus(message.author.channel.name)
        print("original: " + unchanged)
    await message.channel.send(send)
    
    
# authenticate with spotify
load_dotenv()
idSpotify = os.getenv("SPOTIFY_CLIENT_ID")
secretSpotify = os.getenv("SPOTIFY_CLIENT_SECRET")

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY")

redirect_uri = "https://localhost:3000/callback"
auth_url = "https://accounts.spotify.com/authorize"
token_url = "https://accounts.spotify.com/api/token"
api_base_url = "https://api.spotify.com/v1"

token_info = None
expires_at = 0

playlist_id = "6hxaRq6WflNyrwDVcVwCFj"

def create_spotify_oauth():
    return SpotifyOAuth(
        client_id=idSpotify,
        client_secret=secretSpotify,
        redirect_uri=redirect_uri,
        scope="user-read-playback-state user-modify-playback-state user-read-currently-playing user-read-playback-position user-read-recently-played user-top-read user-read-playback-position user-read-private user-read-email user-library-read user-library-modify playlist-read-private playlist-modify-public playlist-modify-private playlist-read-collaborative user-follow-read user-follow-modify user-read-recently-played",
    )

@app.route("/")
def index():
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
    expires_at = int(time.time()) + token_info["expires_in"]
    return redirect("/success")

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

def get_device():
    return get_spotify().devices()["devices"][0]["id"]

def get_currently_playing():
    playback = get_spotify().current_playback()
    if not playback:
        return getTranslation("noSong")
    return playback["item"]["name"] + " - " + playback["item"]["artists"][0]["name"]

def add_track_to_queue(track_uri):
    get_spotify().add_to_queue(track_uri)
    return 

def get_search_results(query):
    return get_spotify().search(query, 2, 0, "track")

def get_song_info(track_uri):
    return get_spotify().track(track_uri)

def skip_song():
    device_id = get_device()
    return get_spotify().next_track(device_id)

@bot.command(name='song')
async def song_command(ctx):
    if not token_info:
        await ctx.send("/me spotify not authenticated")
        return
    song = get_currently_playing()
    print(song)
    await ctx.send(song)
    
@bot.command(name='songrequest', aliases=['sr'])
async def songrequest_command(ctx, *, song):
    global token_info
    if not token_info:
        await ctx.send("/me spotify not authenticated")
        return
    if not song:
        await ctx.send("/me Usage: !sr <name|link>")
        return
    if "spotify:track:" not in song and "open.spotify.com" not in song:
        search_results = get_search_results(song)
        if not search_results:
            await ctx.send("/me Song not found")
            return
        song = search_results["tracks"]["items"][0]["uri"]
    try:
        add_track_to_queue(song)
    except Exception as e:
        print("Error:", e)
        await ctx.send("/me Song not found")
        return    
    track = search_results["tracks"]["items"][0]["name"] + " - " + search_results["tracks"]["items"][0]["artists"][0]["name"]
    await ctx.send("/me added " + track + " to the queue")


# run the bot
@app.route("/success")
def success():
    if __name__ == "__main__":
        threading.Thread(target=bot.run).start()
    return "Du kannst den tab jetzt schließen"
  
# run the flask app
app.run(host="0.0.0.0", port=3000, debug=True, ssl_context="adhoc")
    
          