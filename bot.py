import discord
from discord.ext import commands
from discord import app_commands
import os

TOKEN = os.getenv("DISCORD_TOKEN")

GUILD_ID = 1504178459902087188

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(
    command_prefix="!",
    intents=intents
)

# =====================================================
# SCRIPT BUTTON VIEW
# =====================================================

class ScriptView(discord.ui.View):

    def __init__(self, script):
        super().__init__(timeout=None)
        self.script = script

    @discord.ui.button(
        label="Get Script!",
        emoji="📜",
        style=discord.ButtonStyle.success
    )
    async def get_script(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        await interaction.response.send_message(
            self.script,
            ephemeral=True
        )

# =====================================================
# PANEL MODAL
# =====================================================

class PanelModal(discord.ui.Modal, title="Create Script Panel"):

    script_name = discord.ui.TextInput(
        label="Script Name",
        required=True
    )

    image_url = discord.ui.TextInput(
        label="Image URL",
        required=True
    )

    script_content = discord.ui.TextInput(
        label="Script",
        style=discord.TextStyle.paragraph,
        required=True
    )

    async def on_submit(self, interaction: discord.Interaction):

        embed = discord.Embed(
            title=self.script_name.value,
            description="Click the button below to get the script.",
            color=0x2b2d31
        )

        embed.set_image(
            url=self.image_url.value
        )

        embed.set_footer(
            text=f"Made by {interaction.user}"
        )

        await interaction.channel.send(
            embed=embed,
            view=ScriptView(self.script_content.value)
        )

        await interaction.response.send_message(
            "✅ Script panel created.",
            ephemeral=True
        )

# =====================================================
# GIVEAWAY VIEW
# =====================================================

class GiveawayView(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=None)
        self.entries = set()

    @discord.ui.button(
        label="Enter Giveaway",
        emoji="🎁",
        style=discord.ButtonStyle.primary
    )
    async def enter_giveaway(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        if interaction.user.id in self.entries:

            await interaction.response.send_message(
                "❌ You already entered.",
                ephemeral=True
            )
            return

        self.entries.add(interaction.user.id)

        button.label = f"Entrants ({len(self.entries)})"

        await interaction.message.edit(view=self)

        await interaction.response.send_message(
            "✅ You entered the giveaway.",
            ephemeral=True
        )

# =====================================================
# GIVEAWAY MODAL
# =====================================================

class GiveawayModal(discord.ui.Modal, title="Create Giveaway"):

    giveaway_title = discord.ui.TextInput(
        label="Giveaway Title",
        required=True
    )

    total_winners = discord.ui.TextInput(
        label="Total Winners",
        required=True
    )

    ends_in = discord.ui.TextInput(
        label="Ends In",
        placeholder="1 hour",
        required=True
    )

    async def on_submit(self, interaction: discord.Interaction):

        embed = discord.Embed(
            title=self.giveaway_title.value,
            description=(
                f"🎁 Winners: {self.total_winners.value}\n"
                f"⏰ Ends In: {self.ends_in.value}\n"
                f"👑 Hosted By: {interaction.user.mention}"
            ),
            color=0x2b2d31
        )

        embed.set_footer(
            text="Click below to enter!"
        )

        await interaction.channel.send(
            embed=embed,
            view=GiveawayView()
        )

        await interaction.response.send_message(
            "✅ Giveaway created.",
            ephemeral=True
        )

# =====================================================
# /PANEL COMMAND
# =====================================================

@bot.tree.command(
    name="panel",
    description="Create a script panel",
    guild=discord.Object(id=GUILD_ID)
)
async def panel(interaction: discord.Interaction):

    await interaction.response.send_modal(
        PanelModal()
    )

# =====================================================
# /GIVEAWAY COMMAND
# =====================================================

@bot.tree.command(
    name="giveaway",
    description="Create a giveaway",
    guild=discord.Object(id=GUILD_ID)
)
async def giveaway(interaction: discord.Interaction):

    await interaction.response.send_modal(
        GiveawayModal()
    )

# =====================================================
# READY EVENT
# =====================================================

@bot.event
async def on_ready():

    guild = discord.Object(id=GUILD_ID)

    await bot.tree.sync(guild=guild)

    print(f"✅ Logged in as {bot.user}")

# =====================================================
# START BOT
# =====================================================

bot.run(TOKEN)
