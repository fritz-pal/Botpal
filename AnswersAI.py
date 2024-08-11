import openai
import os
from dotenv import load_dotenv

load_dotenv()
ai_api_keys = [os.getenv("AI_KEY0"), os.getenv("AI_KEY1"), os.getenv("AI_KEY2"), os.getenv("AI_KEY3"), os.getenv("AI_KEY4")]
current_key = 0

# send request to AI API
def chat_with_gpt(systemprompt, prompt):
    # create the client
    client = openai.OpenAI(
        api_key=ai_api_keys[current_key % len(ai_api_keys)],
        base_url="https://api.aimlapi.com",
    )
    
    # add the system prompt to the message
    system_content = systemprompt

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
async def answer_question(message, getTranslation, get_alertus):
    # replace the bot name with Botpal
    prompt = message.content.lower().replace("@fritzbotpal", "Botpal").replace("fritzbotpal", "Botpal").replace("fritzbot", "Botpal").replace("botpal", "Botpal").strip()
    print("prompt: " + prompt)
    systemprompt = getTranslation("systemPrompt") + message.author.channel.name + " " + getTranslation("systemPrompt2") + message.author.name + getTranslation("systemPrompt3")

    try:
        response = chat_with_gpt(systemprompt, prompt)
    except Exception as e:
        # send error message if the AI is overloaded change the key
        print("Error:", e)
        if "429" in str(e):
            global current_key
            current_key += 1
            print("key changed to: ", ai_api_keys[current_key % len(ai_api_keys)])
        await message.channel.send(getTranslation("overloaded"))
        return
    
    send = response.choices[0].message.content.strip().replace("\\_", "_")
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
    for char in [">", "<", "\r", "\n", "[", "#", "]"]:
        if char in send:
            send = send[:send.index(char)].strip()
            changed = True
    
    # cut off the response at the braces
    if send.endswith(")"):
        if "(" in send:
            send = send[:send.rfind("(")].strip()
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