import discord
from discord.ext import commands
from discord.ui import Button, View
import logging
from dotenv import load_dotenv
import os

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

if not TOKEN:
    raise ValueError("DISCORD_TOKEN not found")

handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='/', intents=intents)

ROLE_NAME = "Mando Citizen"

async def send_rules(bot):
    for guild in bot.guilds:

        category = discord.utils.get(guild.categories, name="❗Server Info")
        if not category:
            print("❌ Category '❗Server Info' not found")
            continue

        channel = discord.utils.get(category.text_channels, name="❗┃rules")
        if not channel:
            print("❌ Channel '❗┃rules' not found")
            continue

        # Prevent duplicate messages
        async for msg in channel.history(limit=10):
            if msg.author == bot.user:
                print("⚠️ Rules already sent, skipping")
                return

        embed = discord.Embed(
            title="📜 MandoMC Discord Rules",
            color=discord.Color.dark_gray()
        )

        embed.add_field(
            name="Respect",
            value=(
                "• Be respectful to all members — no harassment, hate speech, or toxicity.\n"
                "• Respect all opinions and do not spread hate.\n"
                "• If treated wrongly, report instead of escalating."
            ),
            inline=False
        )

        embed.add_field(
            name="Chat Behavior",
            value=(
                "• No spamming, flooding, or excessive caps.\n"
                "• Use channels for their intended purpose."
            ),
            inline=False
        )

        embed.add_field(
            name="Content",
            value=(
                "• Keep content appropriate — no NSFW or offensive material.\n"
                "• No cheating, exploiting, or discussing hacks."
            ),
            inline=False
        )

        embed.add_field(
            name="Advertising",
            value="• Do not advertise or self-promote without permission.",
            inline=False
        )

        embed.add_field(
            name="Staff",
            value="• Follow staff instructions at all times.",
            inline=False
        )

        embed.add_field(
            name="Punishments",
            value="Failure to follow these rules may result in warnings, mutes, or bans.",
            inline=False
        )

        embed.set_footer(text="MandoMC Network")

        await channel.send(embed=embed)
        print("✅ Rules message sent")

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    await send_rules(bot)

@bot.event
async def on_member_join(member):
    role = discord.utils.get(member.guild.roles, name=ROLE_NAME)

    if role:
        try:
            await member.add_roles(role)
            print(f"✅ Gave role to {member.name}")
        except Exception as e:
            print(f"❌ Role error: {e}")

TICKET_CATEGORIES = [
    "Support",
    "Bug Report",
    "Player Report",
    "Staff Application"
]

STAFF_ROLES = ["Mando Studios", "Moderator", "Server Mod"]

ticket_counter = 0

def get_staff_roles(guild):
    roles = []
    for name in STAFF_ROLES:
        role = discord.utils.get(guild.roles, name=name)
        if role:
            roles.append(role)
    return roles

class TicketTypeSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label=cat, description=f"Open a {cat} ticket")
            for cat in TICKET_CATEGORIES
        ]
        super().__init__(placeholder="Choose ticket type...", options=options)

    async def callback(self, interaction: discord.Interaction):
        global ticket_counter
        ticket_counter += 1

        guild = interaction.guild
        category = discord.utils.get(guild.categories, name="Support")

        if category is None:
            await interaction.response.send_message("❌ Category 'Support' not found.", ephemeral=True)
            return

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True)
        }

        for role in get_staff_roles(guild):
            overwrites[role] = discord.PermissionOverwrite(view_channel=True, send_messages=True)

        channel_name = f"🎫・ticket-{ticket_counter}"

        ticket_channel = await guild.create_text_channel(
            name=channel_name,
            category=category,
            overwrites=overwrites
        )

        embed = discord.Embed(
            title=f"🎫 {self.values[0]} Ticket",
            description=f"{interaction.user.mention} created a ticket.",
            color=discord.Color.green()
        )

        view = CloseTicketView()

        await ticket_channel.send(
            content=f"{interaction.user.mention}",
            embed=embed,
            view=view
        )

        await interaction.response.send_message(
            f"✅ Ticket created: {ticket_channel.mention}",
            ephemeral=True
        )

class TicketView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketTypeSelect())

class CloseTicketView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Close Ticket", style=discord.ButtonStyle.danger)
    async def close_ticket(self, interaction: discord.Interaction, button: Button):
        channel = interaction.channel
        user = interaction.user

        is_staff = any(role.name in STAFF_ROLES for role in user.roles)

        if not is_staff and not channel.permissions_for(user).view_channel:
            await interaction.response.send_message("❌ You cannot close this ticket.", ephemeral=True)
            return

        await interaction.response.send_message("🔒 Closing ticket...", ephemeral=True)
        await channel.delete()

@bot.command(name="ticketpanel")
@commands.has_permissions(administrator=True)
async def ticket_panel(ctx):
    embed = discord.Embed(
        title="🎫 Create a Ticket",
        description="Select a category below to open a ticket.",
        color=discord.Color.blurple()
    )

    await ctx.send(embed=embed, view=TicketView())

bot.run(TOKEN, log_handler=handler, log_level=logging.INFO)