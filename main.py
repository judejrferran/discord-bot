import discord
from discord.ext import commands
import os
from datetime import datetime

intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ====== YOU MUST SET THESE ======
CONTROL_LOG_CHANNEL_ID = 1467326504420642961  # your join-logs channel ID
AUTO_ROLE_NAME = "Member"
UNVERIFIED_ROLE_NAME = "Unverified"
VERIFIED_ROLE_NAME = "Verified"

# suspicious account settings
SUSPICIOUS_ACCOUNT_DAYS = 7   # < 7 days old = suspicious

# ====== BOT START ======
@bot.event
async def on_ready():
    print(f"{bot.user} is online.")

# ====== JOIN EVENT ======
@bot.event
async def on_member_join(member):
    guild = member.guild

    # ---- account age ----
    account_age_days = (datetime.utcnow() - member.created_at).days
    suspicious = account_age_days < SUSPICIOUS_ACCOUNT_DAYS

    # ---- Auto-role ----
    role = discord.utils.get(guild.roles, name=AUTO_ROLE_NAME)
    if role:
        try:
            await member.add_roles(role)
        except:
            pass

    # ---- Private logging to YOUR control server ----
    control_log_channel = bot.get_channel(CONTROL_LOG_CHANNEL_ID)
    if control_log_channel:
        await control_log_channel.send(
            f"📥 **New Join**\n"
            f"Server: **{guild.name}**\n"
            f"User: {member} \n"
            f"User ID: {member.id}\n"
            f"Account age: **{account_age_days} days**\n"
            f"Suspicious: {'⚠️ YES' if suspicious else 'No'}"
        )

    # ---- Server mod warning (only if suspicious) ----
    if suspicious:
        mod_logs = discord.utils.get(guild.text_channels, name="mod-logs")
        if mod_logs:
            await mod_logs.send(
                f"⚠️ **Suspicious new account joined**\n"
                f"User: {member.mention}\n"
                f"Account age: **{account_age_days} days** (threshold: {SUSPICIOUS_ACCOUNT_DAYS})"
            )

# ====== ADMIN SETUP COMMAND ======
@bot.command()
@commands.has_permissions(administrator=True)
async def setup(ctx):
    guild = ctx.guild

    # Create roles if missing
    for role_name in [AUTO_ROLE_NAME, UNVERIFIED_ROLE_NAME, VERIFIED_ROLE_NAME]:
        if not discord.utils.get(guild.roles, name=role_name):
            await guild.create_role(name=role_name)

    # Create mod-logs channel if missing
    if not discord.utils.get(guild.text_channels, name="mod-logs"):
        await guild.create_text_channel("mod-logs")

    await ctx.send("✅ Setup complete: roles + #mod-logs created.")

# ====== VERIFY COMMAND ======
@bot.command()
async def verify(ctx):
    guild = ctx.guild
    unverified = discord.utils.get(guild.roles, name=UNVERIFIED_ROLE_NAME)
    verified = discord.utils.get(guild.roles, name=VERIFIED_ROLE_NAME)

    if verified:
        try:
            await ctx.author.add_roles(verified)
        except:
            await ctx.send("❌ I can't assign roles. Please move my bot role above Verified.")
            return

    if unverified:
        try:
            await ctx.author.remove_roles(unverified)
        except:
            pass

    await ctx.send("✅ You are now verified!")

# ====== PRIVACY COMMAND ======
@bot.command()
async def privacy(ctx):
    await ctx.send(
        "**🔒 Privacy & Data Policy**\n"
        "This bot is an onboarding + security utility bot.\n\n"
        "**What it DOES collect:**\n"
        "• Join events (username, user ID, server name)\n"
        "• Account age (days since account creation)\n\n"
        "**What it DOES NOT collect:**\n"
        "• Message contents\n"
        "• DMs\n"
        "• Voice activity\n"
        "• Friend list or private user data\n\n"
        "**Why it collects join data:**\n"
        "• To help server admins detect raids / spam accounts\n\n"
        "**Removal:**\n"
        "Admins can remove the bot anytime from Server Settings → Integrations."
    )

# ====== HELP COMMAND ======
@bot.command()
async def helpme(ctx):
    await ctx.send(
        "**Commands:**\n"
        "`!setup` (admin only) - creates roles + mod logs channel\n"
        "`!verify` - gives Verified role\n"
        "`!privacy` - shows privacy policy\n"
        "`!helpme` - shows commands"
    )

bot.run(os.getenv("DISCORD_TOKEN"))
