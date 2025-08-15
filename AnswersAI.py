from groq import Groq
import time
from BotpalUtils import get_system_prompt
from dotenv import load_dotenv
from BotpalTTS import read_out_text


load_dotenv()
prompt_queue = []

msg_queue = []
current_user = None

# add a prompt to the queue
def add_prompt(prompt):
    prompt_queue.append(prompt)
    if len(prompt_queue) > 3:
        prompt_queue.pop(0)

# send request to AI API
def chat_with_gpt(msg_queue, channel, user):
    global prompt_queue
    systemprompt = get_system_prompt(channel, user)
    if len(prompt_queue) > 0:
        systemprompt += " Aber das allerwichtigste ist: "
    for p in prompt_queue:
        if not p.endswith(".") and not p.endswith("!") and not p.endswith("?"):
            p += "."
        p = p[0].upper() + p[1:]
        systemprompt += p + " "
    systemprompt = systemprompt.strip()
    
    client = Groq()
    completion = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        # model="llama3-8b-8192",
        messages=[{"role": "system", "content": systemprompt}] + msg_queue,
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
    
    global current_user, msg_queue
    if current_user != message.author.name:
        msg_queue.clear()
    current_user = message.author.name
    msg_queue.append({"role": "user", "content": prompt})
    
    try:
        response = chat_with_gpt(msg_queue, message.author.channel.name, message.author.name)
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
    
    msg_queue.append({"role": "assistant", "content": send})

    # read out the response if TTS is enabled
    if tts_enabled:
        read_out_text(send)
        
    # add the alertus emoji to the response at the end if it was modified
    if changed:
        send = send + " " + get_alertus(message.author.channel.name)
        print("original: " + unchanged)
    await message.channel.send(send)
    