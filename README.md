# This python program is a comprehensive implementation of a Twitch chatbot named Botpal, which integrates with various APIs, including OpenAI's GPT for AI responses and Spotify for music-related commands. The code is structured to handle environment variables, translations, Twitch commands, and Spotify OAuth authentication.

(title made by botpal himself)

to install:
 - install libraries using "pip install -r requirements.txt"
 - create .env file with all necessary environment variables in format:

```
SPOTIFY_CLIENT_ID=""
SPOTIFY_CLIENT_SECRET=""
TWITCH_CLIENT_ID=""
TWITCH_TOKEN="" # created using the link in the comment at the top of the file
TWITCH_CLIENT_SECRET=""

FLASK_SECRET_KEY="" # random string

AI_KEY0="" # api keys for aimlapi.com (5 because one of them can only process 10 requests per hour)
AI_KEY1=""
AI_KEY2=""
AI_KEY3=""
AI_KEY4=""

```
