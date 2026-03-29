import discord
from discord.ext import commands
import logging
from dotenv import load_dotenv
import os
import asyncio

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

# 🔴 CRITICAL CHECK
if not TOKEN:
    raise ValueError("DISCORD_TOKEN is missing!")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True  # REQUIRED for member join events

bot = commands.Bot(command_prefix='/', intents=intents)

handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')


# =========================
# LOAD COGS
# =========================
async def load_cogs():
    for file in os.listdir("./cogs"):
        if file.endswith(".py"):
            try:
                print(f"🔌 Loading cog: {file}")
                await bot.load_extension(f"cogs.{file[:-3]}")
            except Exception as e:
                print(f"❌ Failed to load {file}: {e}")


# =========================
# MEMBER JOIN EVENT
# =========================
@bot.event
async def on_member_join(member: discord.Member):
    role_name = "Mando Citizen"

    role = discord.utils.get(member.guild.roles, name=role_name)

    if role is None:
        print(f"❌ Role '{role_name}' not found in {member.guild.name}")
        return

    try:
        await member.add_roles(role, reason="Auto role on join")
        print(f"✅ Gave {member.name} the '{role_name}' role")
    except discord.Forbidden:
        print("❌ Missing permissions to assign role")
    except Exception as e:
        print(f"❌ Failed to assign role: {e}")


# =========================
# READY EVENT
# =========================
@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")

    try:
        synced = await bot.tree.sync()
        print(f"🔄 Synced {len(synced)} commands")

        for cmd in synced:
            print(f" - /{cmd.name}")

    except Exception as e:
        print("❌ Sync error:", e)

    # ✅ FIXED VIEWS (UPDATED)
    try:
        from cogs.tickets import TicketView, TicketControlView

        bot.add_view(TicketView())
        bot.add_view(TicketControlView())

        print("✅ Ticket views loaded")

    except Exception as e:
        print("❌ Ticket view load failed:", e)


# =========================
# MAIN
# =========================
async def main():
    print("🚀 Starting bot...")

    await load_cogs()

    await bot.start(TOKEN)


# 🔥 IMPORTANT
if __name__ == "__main__":
    asyncio.run(main())