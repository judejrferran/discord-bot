import discord
from discord.ext import commands
import json
import random
import os

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.messages = True
intents.dm_messages = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)
@bot.command()
@commands.is_owner()
async def say(ctx, *, message):
    await ctx.send(message)

# === CONFIG ===
ADMIN_GUILD_ID = 1467325897890595102  # Your admin server ID
JOIN_LOGS_CHANNEL_ID = 1467326504420642961  # join_logs
CONVOS_CHANNEL_ID = 1477597698902458569  # convos
VERIFIED_USERS_FILE = "verified_users.json"

# Multiple sequential questions for verification
VERIFICATION_QUESTIONS = [
    {"question": "What color is the sky?", "answer": "blue"},
    {"question": "What is 2 + 2?", "answer": "4"},
    {"question": "Type 'I am human'", "answer": "i am human"}
]

# Load verified users
if os.path.exists(VERIFIED_USERS_FILE):
    with open(VERIFIED_USERS_FILE, "r") as f:
        verified_users = json.load(f)
else:
    verified_users = {}

def save_verified_users():
    with open(VERIFIED_USERS_FILE, "w") as f:
        json.dump(verified_users, f)

# === EVENTS ===

@bot.event
async def on_member_join(member):
    """Trigger when a new member joins any server."""
    try:
        # Start sequential verification
        verified_users[str(member.id)] = {
            "verified": False,
            "current_q": 0,  # Track which question
            "answers": []
        }
        save_verified_users()
        await send_next_question(member)
    except Exception as e:
        print(f"Could not DM {member.name}: {e}")

    # Log join in join_logs
    admin_guild = bot.get_guild(ADMIN_GUILD_ID)
    join_channel = admin_guild.get_channel(JOIN_LOGS_CHANNEL_ID)
    await join_channel.send(f"New member joined: {member.name}#{member.discriminator}")

async def send_next_question(member):
    """Send the next verification question."""
    user_data = verified_users.get(str(member.id))
    if not user_data:
        return

    current_q = user_data["current_q"]
    if current_q >= len(VERIFICATION_QUESTIONS):
        # All questions answered
        user_data["verified"] = True
        save_verified_users()
        await member.send("✅ Verification complete! You can now interact in servers.")
        return

    question = VERIFICATION_QUESTIONS[current_q]["question"]
    await member.send(f"Question {current_q + 1}: {question}")

@bot.event
async def on_message(message):
    """Handle DMs for sequential verification and block unverified users."""
    if message.author == bot.user:
        return  # Ignore bot messages

    # --- DM VERIFICATION ---
    if isinstance(message.channel, discord.DMChannel):
        await message.add_reaction("✅")  # Auto-react
        admin_guild = bot.get_guild(ADMIN_GUILD_ID)
        convos_channel = admin_guild.get_channel(CONVOS_CHANNEL_ID)
        await convos_channel.send(f"DM from {message.author.name}#{message.author.discriminator}: {message.content}")

        user_data = verified_users.get(str(message.author.id))
        if user_data and not user_data["verified"]:
            current_q = user_data["current_q"]
            correct_answer = VERIFICATION_QUESTIONS[current_q]["answer"].lower()
            if message.content.lower().strip() == correct_answer:
                user_data["answers"].append(message.content)
                user_data["current_q"] += 1
                save_verified_users()
                await send_next_question(message.author)
            else:
                await message.channel.send("❌ Incorrect answer. Try again.")

    # --- BLOCK UNVERIFIED USERS IN SERVERS ---
    elif message.guild:
        user_data = verified_users.get(str(message.author.id))
        if not user_data or not user_data.get("verified", False):
            try:
                await message.delete()
                await message.author.send("You must verify via DM before interacting in servers!")
            except:
                print(f"Couldn't delete message or DM {message.author.name}")

    await bot.process_commands(message)

bot.run(os.getenv("DISCORD_TOKEN"))