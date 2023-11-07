import logging
import json
import hmac
import hashlib
import discord
import dotenv
import os
from fastapi import FastAPI, Request, HTTPException, status
from fastapi.responses import JSONResponse
import asyncio
from lines import RANDOM_LINES
import random
from fastapi.middleware.cors import (
    CORSMiddleware,
)

# Load environment variables
dotenv.load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Initialize FastAPI app
app = FastAPI()

origins = ['*']

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
) 


# Constants for configuration
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
DISCORD_GUILD_ID = os.getenv("DISCORD_GUILD_ID")
DISCORD_CHANNEL_NAME = os.getenv("DISCORD_CHANNEL_NAME")
DISCOURSE_WEBHOOK_SECRET = os.getenv("DISCOURSE_WEBHOOK_SECRET")

intents = discord.Intents.default()
intents.guilds = True
intents.guild_messages = True
intents.messages = True
intents.reactions = True

discord_client = discord.Client(intents=intents)


MESSAGE_TEMPLATE = "[{0}]({1}) {2} has been posted.\n{3}"

@discord_client.event
async def on_ready():
    logging.info(f"Logged in as {discord_client.user.name}")


async def validate_discourse_signature(request: Request, body: bytes):
    """Validate the incoming request using HMAC signature."""
    header_signature = request.headers.get("X-Discourse-Event-Signature")
    if not header_signature:
        return False

    sha_name, signature = header_signature.split("=")
    if sha_name != "sha256":
        return False

    mac = hmac.new(bytes(DISCOURSE_WEBHOOK_SECRET, "utf-8"), msg=body, digestmod=hashlib.sha256)
    return hmac.compare_digest(mac.hexdigest(), signature)


@app.post("/discourse_webhook")
async def discourse_webhook(request: Request):
    body = await request.body()
    # if not await validate_discostus_code=status.HTTP_400_BAD_REQUEST, detail="Invalid signature")

    data = await request.json()
    if data.get("topic") and data["topic"].get("category_id") == 8:  # 'Lyra Request For Comment' category ID
        topic = data["topic"]
        topic_id = data["topic"]["id"]
        await post_to_discord(topic)
        logging.info("Handled Discourse webhook for topic: %s", topic_id)
    return JSONResponse(content={"message": "OK"})


async def post_to_discord(topic):
    """Post the new topic to the Discord channel and react to it with a fire emoji."""
    guild = discord_client.get_guild(int(DISCORD_GUILD_ID))
    channel = discord.utils.get(guild.text_channels, name=DISCORD_CHANNEL_NAME)
    if channel:
        topic_id = topic["id"]
        topic_title = topic["title"]
        topic_slug = topic["slug"]
        topic_url = f"https://forums.lyra.finance/t/{topic_slug}/{topic_id}"
        
        # Get a random line from the lines.py file
        random_line = random.choice(RANDOM_LINES)
        message = MESSAGE_TEMPLATE.format(f"LRFC#{topic_id}", topic_url, topic_title, random_line)
        message_send = await channel.send(message)
        custom_emoji = discord.utils.get(guild.emojis, name='heart')  # Replace 'heath' with the exact name of your custom emoji
        if custom_emoji:
            await message.add_reaction(custom_emoji)
        else:
            logging.error("Custom emoji not found")
        await message_send.add_reaction("🔥")  # This line adds the fire reaction to the message
        custom_emoji = discord.utils.get(guild.emojis, name='Lyra')  # Replace 'heath' with the exact name of your custom emoji
        if custom_emoji:
            await message.add_reaction(custom_emoji)
        else:
            logging.error("Custom emoji not found")
        logging.info("Posted to Discord and reacted with fire: %s", topic_title)
    else:
        logging.error("Discord channel not found")


@app.on_event("startup")
async def startup_event():
    asyncio.create_task(discord_client.start(DISCORD_BOT_TOKEN))


@app.get("/")
async def read_root():
    return {"Hello": str(discord_client.user)}


if __name__ == "__main__":
    import uvicorn

    # Run the FastAPI app with Uvicorn on the main thread
    uvicorn.run(app, host="127.0.0.1", port=9988)
