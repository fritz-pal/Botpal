from groq import Groq
from BotpalUtils import get_system_prompt
from dotenv import load_dotenv
from BotpalTTS import read_out_text

load_dotenv()

# send request to AI API
def chat_with_gpt(prompt, channel, user):
    client = Groq()
    completion = client.chat.completions.create(
        model="llama3-8b-8192",
        messages=[
            {"role": "system", "content": get_system_prompt(channel, user)},
            {"role": "user", "content": prompt},
        ],
        temperature=1,
        max_tokens=1024,
        top_p=1,
        stream=True,
        stop=None,
    )

    response = ""
    for chunk in completion:
        response += chunk.choices[0].delta.content or ""

    return response

# answer the question of the given message using the AI
async def answer_question(message, getTranslation, get_alertus, tts_enabled):
    # replace the bot name with Botpal
    prompt = message.content.lower().replace("@fritzbotpal", "Botpal").replace("fritzbotpal", "Botpal").replace("fritzbot", "Botpal").replace("botpal", "Botpal").strip()
    print("prompt: " + prompt)
    try:
        response = chat_with_gpt(prompt, message.author.channel.name, message.author.name)
    except Exception as e:
        # send error message if the AI is overloaded change the key
        print("Error:", e)            
        await message.channel.send(getTranslation("overloaded"))
        return
    send = response.strip().replace("\\_", "_")
    unchanged = send
    changed = False
    
    # strip botpal: from the beginning
    if send.lower().startswith("botpal:"):
        send = send[7:].strip()
    
    # limit the length of the response
    if len(send) > 400:
        send = send[:400]
        changed = True
    
    # remove quotes from the response
    if send.startswith("\"") or send.startswith("„"):
        send = send[1:]
    if send.endswith("\"") or send.endswith("“"):
        send = send[:-1]
    
    # cut off the response at the first special character
    for char in [">", "<", "\r", "\n", "[", "]"]:
        if char in send:
            send = send[:send.index(char)].strip()
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
    if tts_enabled:
        read_out_text(send)