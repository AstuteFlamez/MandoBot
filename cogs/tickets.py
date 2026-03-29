import discord
from discord.ext import commands
from discord.ui import Button, View
from datetime import datetime

TICKET_CATEGORIES = [
    "Support",
    "Bug Report",
    "Player Report",
    "Staff Application"
]

STAFF_ROLES = ["Mando Studios", "Moderator", "Server Mod"]

# 🎨 COLORS
COLOR_CREATE = 0xFFD700
COLOR_CLAIM = 0x2ECC71
COLOR_MESSAGE = 0x3498DB
COLOR_CLOSE = 0xE74C3C

# 🧠 MEMORY (ticket_id -> messages)
TICKET_LOGS = {}


# =========================
# UTIL
# =========================
def is_staff(member):
    return any(role.name in STAFF_ROLES for role in member.roles)


def get_staff_roles(guild):
    return [
        discord.utils.get(guild.roles, name=r)
        for r in STAFF_ROLES
        if discord.utils.get(guild.roles, name=r)
    ]


def get_display_name(member):
    return getattr(member, "display_name", member.name)


# =========================
# COMBINED VIEW
# =========================
class TicketControlView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Claim", style=discord.ButtonStyle.success, custom_id="claim_ticket")
    async def claim(self, interaction: discord.Interaction, button: Button):

        if not is_staff(interaction.user):
            await interaction.response.send_message("❌ Staff only.", ephemeral=True)
            return

        embed = discord.Embed(
            description=f"🎫 **Ticket claimed by {get_display_name(interaction.user)}**",
            color=COLOR_CLAIM
        )
        embed.set_author(
            name="MandoMC Support",
            icon_url=interaction.user.display_avatar.url
        )

        await interaction.response.send_message(embed=embed)

        user = interaction.client.get_user(int(interaction.channel.topic))
        if user:
            try:
                dm = discord.Embed(
                    description=f"🎫 **Your ticket is now being handled by {get_display_name(interaction.user)}**",
                    color=COLOR_CLAIM
                )
                dm.set_author(
                    name="MandoMC Support",
                    icon_url=interaction.user.display_avatar.url
                )
                await user.send(embed=dm)
            except:
                pass

    @discord.ui.button(label="Close", style=discord.ButtonStyle.danger, custom_id="close_ticket")
    async def close(self, interaction: discord.Interaction, button: Button):

        if not is_staff(interaction.user):
            await interaction.response.send_message("❌ Staff only.", ephemeral=True)
            return

        channel = interaction.channel
        guild = interaction.guild
        user_id = channel.topic
        user = interaction.client.get_user(int(user_id))

        await interaction.response.send_message("🔒 Closing ticket...", ephemeral=True)

        # DM user
        if user:
            try:
                embed = discord.Embed(
                    description="✅ **Your ticket has been closed. Thank you!**",
                    color=COLOR_CLOSE
                )
                await user.send(embed=embed)
            except:
                pass

        # =========================
        # BUILD TRANSCRIPT
        # =========================
        logs = TICKET_LOGS.get(channel.id, [])

        transcript = "\n".join(logs) if logs else "No messages recorded."

        # Split if too long
        chunks = [transcript[i:i+1900] for i in range(0, len(transcript), 1900)]

        log_channel = discord.utils.get(guild.text_channels, name="🪵・ticket-logs")

        if log_channel:
            header = discord.Embed(
                title="🪵 Ticket Transcript",
                description=f"User: <@{user_id}>\nClosed by: {interaction.user.mention}",
                color=COLOR_CLOSE
            )
            await log_channel.send(embed=header)

            for chunk in chunks:
                await log_channel.send(f"```{chunk}```")

        # cleanup memory
        if channel.id in TICKET_LOGS:
            del TICKET_LOGS[channel.id]

        await channel.delete()


# =========================
# SELECT MENU
# =========================
class TicketSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label=c, description=f"Open a {c} ticket")
            for c in TICKET_CATEGORIES
        ]

        super().__init__(
            placeholder="Choose ticket type...",
            options=options,
            custom_id="ticket_select"
        )

    async def callback(self, interaction: discord.Interaction):
        await create_ticket(interaction.user, interaction.guild, self.values[0])
        await interaction.response.send_message("📬 Check your DMs!", ephemeral=True)


class TicketView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketSelect())


# =========================
# CREATE TICKET
# =========================
async def create_ticket(user, guild, category_name="Support", first_message=None):

    category = discord.utils.get(guild.categories, name="Tickets")
    if not category:
        return

    channel = await guild.create_text_channel(
        name=f"ticket-{user.name}",
        category=category,
        overwrites={
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            **{role: discord.PermissionOverwrite(view_channel=True) for role in get_staff_roles(guild)}
        }
    )

    channel.topic = str(user.id)

    # init log storage
    TICKET_LOGS[channel.id] = []

    embed = discord.Embed(
        title=f"🎫 {category_name} Ticket",
        description=f"User: {user.mention}",
        color=COLOR_CREATE
    )

    await channel.send(embed=embed, view=TicketControlView())

    if first_message:
        name = get_display_name(user)

        log_entry = f"[{datetime.now().strftime('%H:%M')}] {name}: {first_message}"
        TICKET_LOGS[channel.id].append(log_entry)

        msg_embed = discord.Embed(description=first_message, color=COLOR_MESSAGE)
        msg_embed.set_author(name=name, icon_url=user.display_avatar.url)

        await channel.send(embed=msg_embed)

    try:
        dm = discord.Embed(
            description="📩 **Your ticket has been created.**\nReply here to talk to staff.",
            color=COLOR_CREATE
        )
        await user.send(embed=dm)
    except:
        pass


# =========================
# COG
# =========================
class Tickets(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):

        if message.author.bot:
            return

        # =========================
        # USER → STAFF
        # =========================
        if isinstance(message.channel, discord.DMChannel):

            guild = self.bot.guilds[0]

            for channel in guild.text_channels:
                if channel.topic == str(message.author.id):

                    name = get_display_name(message.author)

                    log_entry = f"[{datetime.now().strftime('%H:%M')}] {name}: {message.content}"
                    TICKET_LOGS[channel.id].append(log_entry)

                    embed = discord.Embed(color=COLOR_MESSAGE)
                    embed.set_author(
                        name=name,
                        icon_url=message.author.display_avatar.url
                    )
                    embed.description = message.content

                    await channel.send(embed=embed)
                    return

            await create_ticket(
                message.author,
                guild,
                "Support",
                first_message=message.content
            )

        # =========================
        # STAFF → USER
        # =========================
        else:
            if message.channel.topic:

                if not is_staff(message.author):
                    return

                user = self.bot.get_user(int(message.channel.topic))

                name = get_display_name(message.author)

                log_entry = f"[{datetime.now().strftime('%H:%M')}] {name}: {message.content}"
                TICKET_LOGS[message.channel.id].append(log_entry)

                if user:
                    embed = discord.Embed(color=COLOR_MESSAGE)
                    embed.set_author(
                        name=name,
                        icon_url=message.author.display_avatar.url
                    )
                    embed.description = message.content

                    try:
                        await user.send(embed=embed)
                    except:
                        pass


# =========================
# LOAD
# =========================
async def setup(bot):
    await bot.add_cog(Tickets(bot))