language = "de"

# formats a time in seconds to a human readable format
def time_format(seconds: int) -> str:
    if seconds == 0:
        return None
    d = seconds // (3600 * 24)
    h = seconds // 3600 % 24
    m = seconds % 3600 // 60
    s = seconds % 3600 % 60
    if d > 0:
        return ' {:02d}d {:02d}h {:02d}m {:02d}s'.format(d, h, m, s).replace(" 0", " ").strip()
    elif h > 0:
        return ' {:02d}h {:02d}m {:02d}s'.format(h, m, s).replace(" 0", " ").strip()
    elif m > 0:
        return ' {:02d}m {:02d}s'.format(m, s).replace(" 0", " ").strip()
    elif s > 0:
        return ' {:02d}s'.format(s).replace(" 0", " ").strip()
    

# returns the alertus emoji for the given channel
def get_alertus(channel):
    if channel == "haplolp":
        return "haplolALERTUs"
    if channel == "klonoaofthewind" or channel == "b1gf1sch":
        return "ALERTUS"
    if channel == "fritzpal" or channel == "lordzaros_":
        return "ALERTUs"
    return "🚨"

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