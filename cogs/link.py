import discord
from discord.ext import commands
from discord import app_commands
from utils.database import get_db

LINKED_ROLE = "Linked"

class Link(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    # =========================
    # SLASH COMMAND
    # =========================
    @app_commands.command(name="link", description="Link or check your Minecraft account")
    @app_commands.describe(code="Your Minecraft link code (optional)")
    async def link(self, interaction: discord.Interaction, code: str = None):

        try:
            conn = get_db()
            cursor = conn.cursor(dictionary=True)

            # =========================
            # CHECK IF ALREADY LINKED
            # =========================
            cursor.execute(
                "SELECT * FROM links WHERE discord_id = %s AND linked = TRUE",
                (str(interaction.user.id),)
            )
            existing = cursor.fetchone()

            # =========================
            # NO CODE → STATUS CHECK
            # =========================
            if code is None:
                if existing:
                    await interaction.response.send_message(
                        "✅ Your Discord account is already linked.",
                        ephemeral=True
                    )
                else:
                    await interaction.response.send_message(
                        "❌ You are not linked. Use `/link CODE`.",
                        ephemeral=True
                    )
                return

            code = code.upper()

            # =========================
            # BLOCK DOUBLE LINKING
            # =========================
            if existing:
                await interaction.response.send_message(
                    "❌ Your Discord account is already linked.",
                    ephemeral=True
                )
                return

            # =========================
            # CHECK CODE
            # =========================
            cursor.execute(
                "SELECT * FROM links WHERE link_code = %s",
                (code,)
            )
            result = cursor.fetchone()

            if not result:
                await interaction.response.send_message(
                    "❌ Invalid or expired code.",
                    ephemeral=True
                )
                return

            if result["linked"]:
                await interaction.response.send_message(
                    "❌ This code has already been used.",
                    ephemeral=True
                )
                return

            # =========================
            # UPDATE DB
            # =========================
            cursor.execute(
                "UPDATE links SET discord_id = %s, linked = TRUE WHERE link_code = %s",
                (str(interaction.user.id), code)
            )
            conn.commit()

            # =========================
            # GIVE ROLE
            # =========================
            role = discord.utils.get(interaction.guild.roles, name=LINKED_ROLE)
            if role:
                await interaction.user.add_roles(role)

            await interaction.response.send_message(
                "✅ Successfully linked your account!",
                ephemeral=True
            )

        except Exception as e:
            print(e)
            await interaction.response.send_message(
                "❌ Error linking your account.",
                ephemeral=True
            )

        finally:
            try:
                cursor.close()
                conn.close()
            except:
                pass


async def setup(bot):
    await bot.add_cog(Link(bot))