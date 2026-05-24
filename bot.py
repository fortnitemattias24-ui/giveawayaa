import discord
from discord.ext import commands
import os

TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()

bot = commands.Bot(
    command_prefix="!",
    intents=intents
)

# =====================================================

class ScriptView(discord.ui.View):

    def __init__(self, script):
        super().__init__(timeout=None)
        self.script = script

    @discord.ui.button(
        label="Get Script!",
        style=discord.ButtonStyle.success
    )
    async def get_script(self, interaction: discord.Interaction, button: discord.ui.Button):

        await interaction.response.send_message(
            f"```lua\n{self.script}\n```",
            ephemeral=True
        )

# =====================================================

class PanelModal(discord.ui.Modal, title="Create Panel"):

    script_name = discord.ui.TextInput(label="Script Name")

    image_url = discord.ui.TextInput(label="Image URL")

    script_content = discord.ui.TextInput(
        label="Script",
        style=discord.TextStyle.paragraph
    )

    async def on_submit(self, interaction: discord.Interaction):

        embed = discord.Embed(
            title=self.script_name.value,
            description="Click below to get script.",
            color=0x2b2d31
        )

        embed.set_image(url=self.image_url.value)

        await interaction.channel.send(
            embed=embed,
            view=ScriptView(self.script_content.value)
        )

        await interaction.response.send_message(
            "✅ Created panel.",
            ephemeral=True
        )

# =====================================================

class GiveawayView(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=None)
        self.users = []

    @discord.ui.button(
        label="Enter Giveaway",
        style=discord.ButtonStyle.primary,
        emoji="🎉"
    )
    async def enter(self, interaction: discord.Interaction, button: discord.ui.Button):

        if interaction.user.id in self.users:

            await interaction.response.send_message(
                "❌ Already entered.",
                ephemeral=True
            )
            return

        self.users.append(interaction.user.id)

        button.label = f"Entries: {len(self.users)}"

        await interaction.message.edit(view=self)

        await interaction.response.send_message(
            "✅ Joined giveaway.",
            ephemeral=True
        )

# =====================================================

class GiveawayModal(discord.ui.Modal, title="Create Giveaway"):

    giveaway_title = discord.ui.TextInput(label="Title")

    winners = discord.ui.TextInput(label="Winners")

    ends_in = discord.ui.TextInput(label="Ends In")

    async def on_submit(self, interaction: discord.Interaction):

        embed = discord.Embed(
            title=f"🎉 {self.giveaway_title.value}",
            description=(
                f"👑 Hosted By: {interaction.user.mention}\n"
                f"🏆 Winners: {self.winners.value}\n"
                f"⏰ Ends In: {self.ends_in.value}"
            ),
            color=0x2b2d31
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
# NEW COMMAND NAMES
# =====================================================

@bot.tree.command(name="newpanel", description="Create panel")
async def newpanel(interaction: discord.Interaction):

    await interaction.response.send_modal(
        PanelModal()
    )

@bot.tree.command(name="newgiveaway", description="Create giveaway")
async def newgiveaway(interaction: discord.Interaction):

    await interaction.response.send_modal(
        GiveawayModal()
    )

# =====================================================

@bot.event
async def on_ready():

    synced = await bot.tree.sync()

    print(f"Logged in as {bot.user}")
    print(f"Synced {len(synced)} commands")

# =====================================================

bot.run(TOKEN)
