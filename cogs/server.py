from discord.ext import commands, tasks
from discord import app_commands
from mcstatus import JavaServer
import discord

SERVER_IP = "142.4.205.127:25565"

class Server(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.update_status.start()

    # =========================
    # FORMAT FUNCTION
    # =========================
    def format_players(self, count):
        return f"{count} player online" if count == 1 else f"{count} players online"

    # =========================
    # STATUS LOOP
    # =========================
    @tasks.loop(seconds=30)
    async def update_status(self):
        try:
            server = JavaServer.lookup(SERVER_IP)
            status = server.status()

            text = self.format_players(status.players.online)

            await self.bot.change_presence(
                activity=discord.Activity(
                    type=discord.ActivityType.watching,
                    name=text
                )
            )

        except Exception as e:
            print("Status error:", e)
            await self.bot.change_presence(
                activity=discord.Activity(
                    type=discord.ActivityType.watching,
                    name="Server offline"
                )
            )

    @update_status.before_loop
    async def before_update(self):
        await self.bot.wait_until_ready()

    # =========================
    # SLASH COMMAND
    # =========================
    @app_commands.command(name="players", description="View online player count")
    async def players(self, interaction: discord.Interaction):
        try:
            server = JavaServer.lookup(SERVER_IP)
            status = server.status()

            text = self.format_players(status.players.online)

            await interaction.response.send_message(f"👥 {text}")

        except Exception as e:
            print("Command error:", e)
            await interaction.response.send_message(
                "❌ Server offline.",
                ephemeral=True
            )


async def setup(bot):
    await bot.add_cog(Server(bot))