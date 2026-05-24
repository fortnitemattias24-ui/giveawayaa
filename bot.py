
import discord
from discord.ext import commands, tasks
from discord import app_commands
import aiosqlite
import asyncio
import random
import time
import os

TOKEN = os.getenv("DISCORD_TOKEN")
DB = "bot.db"

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# =========================================================
# DATABASE
# =========================================================

async def setup_db():
    async with aiosqlite.connect(DB) as db:
        await db.execute("""
        CREATE TABLE IF NOT EXISTS panels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message_id INTEGER,
            title TEXT,
            image TEXT,
            script TEXT
        )
        """)

        await db.execute("""
        CREATE TABLE IF NOT EXISTS giveaways (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message_id INTEGER,
            channel_id INTEGER,
            title TEXT,
            host_id INTEGER,
            winners INTEGER,
            ends_at INTEGER
        )
        """)

        await db.execute("""
        CREATE TABLE IF NOT EXISTS giveaway_entries (
            giveaway_id INTEGER,
            user_id INTEGER
        )
        """)

        await db.commit()

# =========================================================
# SCRIPT PANEL SYSTEM
# =========================================================

class ScriptModal(discord.ui.Modal, title="Create Script Panel"):
    script_name = discord.ui.TextInput(
        label="Script Name",
        placeholder="T1 Free Duels",
        required=True,
        max_length=100
    )

    image_url = discord.ui.TextInput(
        label="Image URL",
        placeholder="https://example.com/image.png",
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
            description="Press the button below to get the script.",
            color=0x2b2d31
        )

        embed.set_image(url=self.image_url.value)
        embed.set_footer(text=f"Made by {interaction.user.display_name}")

        view = ScriptView(self.script_content.value)

        msg = await interaction.channel.send(embed=embed, view=view)

        async with aiosqlite.connect(DB) as db:
            await db.execute(
                "INSERT INTO panels (message_id, title, image, script) VALUES (?, ?, ?, ?)",
                (
                    msg.id,
                    self.script_name.value,
                    self.image_url.value,
                    self.script_content.value
                )
            )
            await db.commit()

        await interaction.response.send_message(
            "✅ Script panel created.",
            ephemeral=True
        )

class ScriptView(discord.ui.View):
    def __init__(self, script):
        super().__init__(timeout=None)
        self.script = script

    @discord.ui.button(
        label="Get Script!",
        emoji="📜",
        style=discord.ButtonStyle.success,
        custom_id="get_script_button"
    )
    async def get_script(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            f"```lua\n{self.script}\n```",
            ephemeral=True
        )

# =========================================================
# GIVEAWAY SYSTEM
# =========================================================

class GiveawayModal(discord.ui.Modal, title="Create Giveaway"):
    giveaway_title = discord.ui.TextInput(
        label="Giveaway Title",
        placeholder="🎁 Key To Duel Script 🎁",
        required=True
    )

    total_winners = discord.ui.TextInput(
        label="Total Winners",
        placeholder="1",
        required=True
    )

    ends_in = discord.ui.TextInput(
        label="Ends In (minutes)",
        placeholder="60",
        required=True
    )

    async def on_submit(self, interaction: discord.Interaction):
        winners = int(self.total_winners.value)
        minutes = int(self.ends_in.value)

        ends_at = int(time.time()) + (minutes * 60)

        embed = discord.Embed(
            title=self.giveaway_title.value,
            color=0x2b2d31
        )

        embed.description = (
            f"• **Total Winners:** {winners}\n"
            f"• **Ends in:** {minutes} minutes\n"
            f"• **Hosted By:** {interaction.user.mention}"
        )

        embed.set_footer(text="Click the button below to enter!")

        view = GiveawayView()

        msg = await interaction.channel.send(embed=embed, view=view)

        async with aiosqlite.connect(DB) as db:
            cursor = await db.execute(
                "INSERT INTO giveaways (message_id, channel_id, title, host_id, winners, ends_at) VALUES (?, ?, ?, ?, ?, ?)",
                (
                    msg.id,
                    interaction.channel.id,
                    self.giveaway_title.value,
                    interaction.user.id,
                    winners,
                    ends_at
                )
            )

            giveaway_id = cursor.lastrowid
            await db.commit()

        view.giveaway_id = giveaway_id

        await interaction.response.send_message(
            "✅ Giveaway started.",
            ephemeral=True
        )

class GiveawayView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.giveaway_id = None
        self.entrants = set()

    @discord.ui.button(
        label="Enter Giveaway",
        emoji="🎁",
        style=discord.ButtonStyle.primary,
        custom_id="enter_giveaway_button"
    )
    async def enter_giveaway(self, interaction: discord.Interaction, button: discord.ui.Button):
        async with aiosqlite.connect(DB) as db:
            existing = await db.execute_fetchone(
                "SELECT * FROM giveaway_entries WHERE giveaway_id = ? AND user_id = ?",
                (self.giveaway_id, interaction.user.id)
            )

            if existing:
                await interaction.response.send_message(
                    "❌ You already entered this giveaway.",
                    ephemeral=True
                )
                return

            await db.execute(
                "INSERT INTO giveaway_entries (giveaway_id, user_id) VALUES (?, ?)",
                (self.giveaway_id, interaction.user.id)
            )
            await db.commit()

            count = await db.execute_fetchall(
                "SELECT user_id FROM giveaway_entries WHERE giveaway_id = ?",
                (self.giveaway_id,)
            )

            total = len(count)

        button.label = f"Entrants ({total})"
        await interaction.message.edit(view=self)

        await interaction.response.send_message(
            "✅ You entered the giveaway.",
            ephemeral=True
        )

# =========================================================
# GIVEAWAY END TASK
# =========================================================

@tasks.loop(seconds=30)
async def check_giveaways():
    now = int(time.time())

    async with aiosqlite.connect(DB) as db:
        giveaways = await db.execute_fetchall(
            "SELECT * FROM giveaways WHERE ends_at <= ?",
            (now,)
        )

        for giveaway in giveaways:
            channel = bot.get_channel(giveaway[2])

            if not channel:
                continue

            users = await db.execute_fetchall(
                "SELECT user_id FROM giveaway_entries WHERE giveaway_id = ?",
                (giveaway[0],)
            )

            entrants = [u[0] for u in users]

            if not entrants:
                winners_text = "No entrants."
            else:
                selected = random.sample(
                    entrants,
                    min(len(entrants), giveaway[5])
                )

                winners_text = " ".join([f"<@{w}>" for w in selected])

            embed = discord.Embed(
                title="🎉 Giveaway Ended",
                description=(
                    f"**Prize:** {giveaway[3]}\n"
                    f"**Winners:** {winners_text}"
                ),
                color=0x57F287
            )

            await channel.send(embed=embed)

            await db.execute(
                "DELETE FROM giveaways WHERE id = ?",
                (giveaway[0],)
            )

            await db.execute(
                "DELETE FROM giveaway_entries WHERE giveaway_id = ?",
                (giveaway[0],)
            )

        await db.commit()

# =========================================================
# COMMANDS
# =========================================================

@bot.tree.command(name="panel", description="Create a script panel")
@app_commands.default_permissions(administrator=True)
async def panel(interaction: discord.Interaction):
    await interaction.response.send_modal(ScriptModal())

@bot.tree.command(name="giveaway", description="Create a giveaway")
@app_commands.default_permissions(administrator=True)
async def giveaway(interaction: discord.Interaction):
    await interaction.response.send_modal(GiveawayModal())

# =========================================================
# READY
# =========================================================

@bot.event
async def on_ready():
    await setup_db()

    bot.add_view(ScriptView("persistent"))
    bot.add_view(GiveawayView())

    await bot.tree.sync()

    check_giveaways.start()

    print(f"✅ Logged in as {bot.user}")

# =========================================================
# START
# =========================================================

bot.run(TOKEN)
