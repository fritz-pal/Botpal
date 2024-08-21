import requests
from playsound import playsound
import os
from dotenv import load_dotenv

# herbie: Kz0DA4tCctbPjLay2QT1
# bartholomew: L5Oo1OjjHdbIvJDQFgmN
# Andreas: DQ5BY6XAAchoJ8FZQsqK
# der beamte: ceicSWVDzgXoWidth8WQ
# herr gruber: J5U94vRbS9drxnawJcoc
# asmr: tIsjSw3zL3puN5800Bxh
# businessman: Yf6I1OzNemrgGRsc8z1I
# aegon: OukEAqLfTzpM37uFE5LT
# professor: nzeAacJi50IvxcyDnMXa
voices = ["DQ5BY6XAAchoJ8FZQsqK", "OukEAqLfTzpM37uFE5LT", "Kz0DA4tCctbPjLay2QT1"]

load_dotenv()
CHUNK_SIZE = 1024 
XI_API_KEY = os.getenv("TTS_KEY")
number = 0
voiceNumber = 0

# headers
headers = {
    "Accept": "application/json",
    "xi-api-key": XI_API_KEY
}

def change_voice(changeTo):
    global voiceNumber
    voiceNumber = changeTo

# function to read out text
def read_out_text(text_to_speak):
    # request URL
    tts_url = f"https://api.elevenlabs.io/v1/text-to-speech/{voices[voiceNumber % 3]}/stream"
    # options
    data = {
        "text": text_to_speak,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.8,
            "style": 0.0,
            "use_speaker_boost": True
        }
    }
    response = requests.post(tts_url, headers=headers, json=data, stream=True)
    global number
    OUTPUT_PATH = f"HistoryTTS/output{number}.mp3"
    if response.ok:
        with open(OUTPUT_PATH, "wb") as f:
            for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
                f.write(chunk)
        playsound(OUTPUT_PATH)
        number += 1
    else:
        print(response.text)