# This python program is a comprehensive implementation of a Twitch chatbot named Botpal, which integrates with various APIs, including OpenAI's GPT for AI responses and Spotify for music-related commands. The code is structured to handle environment variables, translations, Twitch commands, and Spotify OAuth authentication.

(title made by botpal himself)
*bot only works with spotify premium*

## to install:
 - install libraries using "pip install -r requirements.txt"
 - create .env file with all necessary environment variables in format:
 - replace zaroooos with your own channel in the channel and twitch tokens variables
 - run bot
 - run !createreward command in your twitch chat and copy the returned ID into the .env

```
SPOTIFY_CLIENT_ID=""
SPOTIFY_CLIENT_SECRET=""
TWITCH_CLIENT_ID=""
TWITCH_TOKEN="" # created using the link in the comment at the top of the file (while logged into the bot account)
TWITCH_CLIENT_SECRET=""

FLASK_SECRET_KEY="" # random string

WEATHER_API_KEY="" # from https://www.weatherapi.com/

GROQ_API_KEY="" # from https://console.groq.com/keys

TTS_KEY="" # from https://elevenlabs.io/

TWITCH_TOKEN_...="" # twitch token of your own channel created using the link in the comment at the top of the file while logged into your own account

REWARD_ID="" # keep empty if not affiliate

```

## All twitch commands:
### User commands
- !test: Sends a test message.
- !lurk: Notifies that the user is lurking.
- !elo: Retrieves the rapid elo rating of a player.
- !mods: Retrieves the list of moderators.
- !song: Retrieves the currently playing song.
- !queue or !q: Retrieves the next 3 Songs to be played.
- !skip or !voteskip: Initiates a vote to skip the current song.
- !songrequest or !sr: Requests a song to be added to the queue.
- !weather: Retrieve current weather in a city.

### Mod commands:
- !blacklist or !blacklistsong: Adds a song to the blacklist.
- !blacklistartist: Adds an artist to the blacklist.
- !blacklistuser: Bans a user from song requests.
- !forceskip: Forces the skipping of the current song.
- !volume or !vol: Changes the volume of the music.
- !createreward: Creates the custom reward for song requests return the ID to be put into the environment variable.