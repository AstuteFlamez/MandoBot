import discord
from discord.ext import commands
import asyncio
from utils.database import get_db

LINKED_ROLE = "Linked"

class Link(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="link")
    async def link(self, ctx, code: str):

        try:
            await ctx.message.delete()
        except:
            pass

        code = code.upper()

        try:
            conn = get_db()
            cursor = conn.cursor(dictionary=True)

            # Prevent duplicate linking
            cursor.execute(
                "SELECT * FROM links WHERE discord_id = %s AND linked = TRUE",
                (str(ctx.author.id),)
            )

            if cursor.fetchone():
                msg = await ctx.send("❌ Your Discord account is already linked.")
                await asyncio.sleep(5)
                await msg.delete()
                return

            # Check code
            cursor.execute("SELECT * FROM links WHERE link_code = %s", (code,))
            result = cursor.fetchone()

            if not result:
                msg = await ctx.send("❌ Invalid or expired code.")
                await asyncio.sleep(5)
                await msg.delete()
                return

            if result["linked"]:
                msg = await ctx.send("❌ This code has already been used.")
                await asyncio.sleep(5)
                await msg.delete()
                return

            # Update DB
            cursor.execute(
                "UPDATE links SET discord_id = %s, linked = TRUE WHERE link_code = %s",
                (str(ctx.author.id), code)
            )
            conn.commit()

            role = discord.utils.get(ctx.guild.roles, name=LINKED_ROLE)
            if role:
                await ctx.author.add_roles(role)

            msg = await ctx.send("✅ Successfully linked your account!")
            await asyncio.sleep(5)
            await msg.delete()

        except Exception as e:
            print(e)
            msg = await ctx.send("❌ Error linking your account.")
            await asyncio.sleep(5)
            await msg.delete()

        finally:
            try:
                cursor.close()
                conn.close()
            except:
                pass

async def setup(bot):
    await bot.add_cog(Link(bot))