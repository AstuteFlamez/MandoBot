import discord
from discord.ext import commands
from discord.ui import Button, View

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


# =========================
# SELECT MENU
# =========================
class TicketTypeSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(
                label=cat,
                description=f"Open a {cat} ticket"
            )
            for cat in TICKET_CATEGORIES
        ]
        super().__init__(placeholder="Choose ticket type...", options=options)

    async def callback(self, interaction: discord.Interaction):
        global ticket_counter
        ticket_counter += 1

        guild = interaction.guild
        category = discord.utils.get(guild.categories, name="Support")

        if category is None:
            await interaction.response.send_message(
                "❌ Category 'Support' not found.",
                ephemeral=True
            )
            return

        # =========================
        # PERMISSIONS
        # =========================
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True
            )
        }

        for role in get_staff_roles(guild):
            overwrites[role] = discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True
            )

        # =========================
        # CREATE CHANNEL
        # =========================
        channel_name = f"🎫・ticket-{ticket_counter}"

        ticket_channel = await guild.create_text_channel(
            name=channel_name,
            category=category,
            overwrites=overwrites
        )

        # =========================
        # EMBED
        # =========================
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


# =========================
# MAIN VIEW
# =========================
class TicketView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketTypeSelect())


# =========================
# CLOSE BUTTON
# =========================
class CloseTicketView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Close Ticket", style=discord.ButtonStyle.danger)
    async def close_ticket(self, interaction: discord.Interaction, button: Button):

        channel = interaction.channel
        user = interaction.user

        is_staff = any(role.name in STAFF_ROLES for role in user.roles)

        # Allow staff OR ticket creator
        if not is_staff and not channel.permissions_for(user).view_channel:
            await interaction.response.send_message(
                "❌ You cannot close this ticket.",
                ephemeral=True
            )
            return

        await interaction.response.send_message(
            "🔒 Closing ticket...",
            ephemeral=True
        )

        await channel.delete()


# =========================
# COG
# =========================
class Tickets(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="ticketpanel")
    @commands.has_permissions(administrator=True)
    async def ticket_panel(self, ctx):

        embed = discord.Embed(
            title="🎫 Create a Ticket",
            description="Select a category below to open a ticket.",
            color=discord.Color.blurple()
        )

        await ctx.send(embed=embed, view=TicketView())


# =========================
# LOAD
# =========================
async def setup(bot):
    await bot.add_cog(Tickets(bot))