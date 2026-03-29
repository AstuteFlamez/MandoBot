import discord
from discord.ext import commands
from discord import app_commands
from utils.database import get_db


class Economy(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    # =========================
    # FORMAT MONEY
    # =========================
    def format_money(self, amount):
        return f"${amount:,.2f}"

    # =========================
    # MEDALS
    # =========================
    def get_medal(self, position):
        if position == 1:
            return "🥇"
        elif position == 2:
            return "🥈"
        elif position == 3:
            return "🥉"
        return f"#{position}"

    # =========================
    # /BALTOP COMMAND
    # =========================
    @app_commands.command(name="baltop", description="View the richest players on MandoMC")
    async def baltop(self, interaction: discord.Interaction):

        try:
            conn = get_db()
            cursor = conn.cursor(dictionary=True)

            cursor.execute("""
                SELECT username, balance
                FROM balances
                ORDER BY balance DESC
                LIMIT 10
            """)

            results = cursor.fetchall()

            if not results:
                await interaction.response.send_message(
                    "❌ No balance data found.",
                    ephemeral=True
                )
                return

            # =========================
            # BUILD EMBED
            # =========================
            embed = discord.Embed(
                title="💰 MandoMC Baltop",
                description="Top 10 richest players",
                color=discord.Color.gold()
            )

            lines = []

            for i, row in enumerate(results, start=1):
                medal = self.get_medal(i)
                name = row["username"]
                money = self.format_money(row["balance"])

                lines.append(f"{medal} **{name}** — {money}")

            embed.description = "\n".join(lines)

            embed.set_footer(text="MandoMC Economy")

            await interaction.response.send_message(embed=embed)

        except Exception as e:
            print(e)
            await interaction.response.send_message(
                "❌ Failed to fetch baltop.",
                ephemeral=True
            )

        finally:
            try:
                cursor.close()
                conn.close()
            except:
                pass


async def setup(bot):
    await bot.add_cog(Economy(bot))