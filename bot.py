import discord
from discord.ext import commands, tasks
from discord import app_commands
import aiosqlite
import random
import time
import os

TOKEN = os.getenv("DISCORD_TOKEN")
DB = "bot.db"

GUILD_ID = 1504178459902087188

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

```
    await db.execute("""
    CREATE TABLE IF NOT EXISTS giveaway_entries (
        giveaway_id INTEGER,
        user_id INTEGER
    )
    """)

    await db.commit()
```

# =========================================================

# SCRIPT PANEL SYSTEM

# =========================================================

class ScriptView(discord.ui.View):
def **init**(self, script):
super().**init**(timeout=None)
self.script = script

````
@discord.ui.button(
    label="Get Script!",
    emoji="📜",
    style=discord.ButtonStyle.success
)
async def get_script(self, interaction: discord.Interaction, button: discord.ui.Button):
    await interaction.response.send_message(
        f"```lua\n{self.script}\n```",
        ephemeral=True
    )
````

class ScriptModal(discord.ui.Modal, title="Create Script Panel"):

```
script_name = discord.ui.TextInput(
    label="Script Name",
    required=True,
    max_length=100
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
        description="Press the button below to get the script.",
        color=0x2b2d31
    )

    embed.set_image(url=self.image_url.value)
    embed.set_footer(text=f"Made by {interaction.user.display_name}")

    await interaction.channel.send(
        embed=embed,
        view=ScriptView(self.script_content.value)
    )

    await interaction.response.send_message(
        "✅ Script panel created.",
        ephemeral=True
    )
```

# =========================================================

# GIVEAWAY SYSTEM

# =========================================================

class GiveawayView(discord.ui.View):
def **init**(self):
super().**init**(timeout=None)
self.entrants = set()
self.giveaway_id = None

```
@discord.ui.button(
    label="Enter Giveaway",
    emoji="🎁",
    style=discord.ButtonStyle.primary
)
async def enter_giveaway(self, interaction: discord.Interaction, button: discord.ui.Button):

    async with aiosqlite.connect(DB) as db:

        existing = await db.execute_fetchone(
            "SELECT * FROM giveaway_entries WHERE giveaway_id = ? AND user_id = ?",
            (self.giveaway_id, interaction.user.id)
        )

        if existing:
            await interaction.response.send_message(
                "❌ You already entered.",
                ephemeral=True
            )
            return

        await db.execute(
            "INSERT INTO giveaway_entries (giveaway_id, user_id) VALUES (?, ?)",
            (self.giveaway_id, interaction.user.id)
        )

        await db.commit()

        total = await db.execute_fetchall(
            "SELECT * FROM giveaway_entries WHERE giveaway_id = ?",
            (self.giveaway_id,)
        )

    button.label = f"Entrants ({len(total)})"

    await interaction.message.edit(view=self)

    await interaction.response.send_message(
        "✅ You entered the giveaway.",
        ephemeral=True
    )
```

class GiveawayModal(discord.ui.Modal, title="Create Giveaway"):

```
giveaway_title = discord.ui.TextInput(
    label="Giveaway Title",
    required=True
)

winners = discord.ui.TextInput(
    label="Total Winners",
    required=True
)

duration = discord.ui.TextInput(
    label="Duration In Minutes",
    required=True
)

async def on_submit(self, interaction: discord.Interaction):

    winners = int(self.winners.value)
    duration = int(self.duration.value)

    ends_at = int(time.time()) + (duration * 60)

    embed = discord.Embed(
        title=self.giveaway_title.value,
        color=0x2b2d31
    )

    embed.description = (
        f"🎁 **Winners:** {winners}\n"
        f"⏰ **Ends In:** {duration} minutes\n"
        f"👑 **Hosted By:** {interaction.user.mention}"
    )

    view = GiveawayView()

    msg = await interaction.channel.send(
        embed=embed,
        view=view
    )

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
        "✅ Giveaway created.",
        ephemeral=True
    )
```

# =========================================================

# GIVEAWAY END TASK

# =========================================================

@tasks.loop(seconds=30)
async def check_giveaways():

```
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
```

# =========================================================

# COMMANDS

# =========================================================

@bot.tree.command(
name="panel",
description="Create a script panel",
guild=discord.Object(id=GUILD_ID)
)
@app_commands.default_permissions(administrator=True)
async def panel(interaction: discord.Interaction):
await interaction.response.send_modal(ScriptModal())

@bot.tree.command(
name="giveaway",
description="Create a giveaway",
guild=discord.Object(id=GUILD_ID)
)
@app_commands.default_permissions(administrator=True)
async def giveaway(interaction: discord.Interaction):
await interaction.response.send_modal(GiveawayModal())

# =========================================================

# READY

# =========================================================

@bot.event
async def on_ready():

```
await setup_db()

guild = discord.Object(id=GUILD_ID)

await bot.tree.sync(guild=guild)

check_giveaways.start()

print(f"✅ Logged in as {bot.user}")
```

# =========================================================

# START

# =========================================================

bot.run(TOKEN)
