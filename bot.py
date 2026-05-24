import discord
from discord.ext import commands
import os

TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# =========================================================
# SCRIPT BUTTON
# =========================================================

class ScriptButton(discord.ui.View):

    def __init__(self, script):
        super().__init__(timeout=None)
        self.script = script

    @discord.ui.button(
        label="Get Script!",
        style=discord.ButtonStyle.success,
        emoji="📜"
    )
    async def script_btn(self, interaction: discord.Interaction, button: discord.ui.Button):

        await interaction.response.send_message(
            f"```lua\n{self.script}\n```",
            ephemeral=True
        )

# =========================================================
# PANEL MODAL
# =========================================================

class PanelModal(discord.ui.Modal, title="Create Panel"):

    script_name = discord.ui.TextInput(
        label="Script Name"
    )

    image_url = discord.ui.TextInput(
        label="Image URL"
    )

    script_content = discord.ui.TextInput(
        label="Script",
        style=discord.TextStyle.paragraph
    )

    async def on_submit(self, interaction: discord.Interaction):

        embed = discord.Embed(
            title=self.script_name.value,
            description="Click below to get the script.",
            color=0x2b2d31
        )

        embed.set_image(url=self.image_url.value)

        await interaction.channel.send(
            embed=embed,
            view=ScriptButton(self.script_content.value)
        )

        await interaction.response.send_message(
            "✅ Panel created.",
            ephemeral=True
        )

# =========================================================
# GIVEAWAY BUTTON
# =========================================================

class GiveawayButton(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=None)
        self.users = []

    @discord.ui.button(
        label="Enter Giveaway",
        emoji="🎉",
        style=discord.ButtonStyle.primary
    )
    async def enter(self, interaction: discord.Interaction, button: discord.ui.Button):

        if interaction.user.id in self.users:

            await interaction.response.send_message(
                "❌ You already joined.",
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

# =========================================================
# GIVEAWAY MODAL
# =========================================================

class GiveawayModal(discord.ui.Modal, title="Create Giveaway"):

    title_input = discord.ui.TextInput(
        label="Giveaway Title"
    )

    winners_input = discord.ui.TextInput(
        label="Total Winners"
    )

    ends_input = discord.ui.TextInput(
        label="Ends In"
    )

    async def on_submit(self, interaction: discord.Interaction):

        embed = discord.Embed(
            title=f"🎉 {self.title_input.value}",
            description=(
                f"👑 Hosted By: {interaction.user.mention}\n"
                f"🏆 Winners: {self.winners_input.value}\n"
                f"⏰ Ends In: {self.ends_input.value}"
            ),
            color=0x2b2d31
        )

        await interaction.channel.send(
            embed=embed,
            view=GiveawayButton()
        )

        await interaction.response.send_message(
            "✅ Giveaway created.",
            ephemeral=True
        )

# =========================================================
# PANEL COMMAND
# =========================================================

@bot.tree.command(name="panel", description="Create script panel")
async def panel(interaction: discord.Interaction):

    await interaction.response.send_modal(
        PanelModal()
    )

# =========================================================
# GIVEAWAY COMMAND
# =========================================================

@bot.tree.command(name="giveaway", description="Create giveaway")
async def giveaway(interaction: discord.Interaction):

    await interaction.response.send_modal(
        GiveawayModal()
    )

# =========================================================
# READY
# =========================================================

@bot.event
async def on_ready():

    await bot.tree.sync()

    print(f"Logged in as {bot.user}")

# =========================================================
# START
# =========================================================

bot.run(TOKEN)
