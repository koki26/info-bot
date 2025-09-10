# ---------------------------------------
# 📅 Discord Info Bot
# Ukazuje den, datum a počet lidí na serveru
# Autor: Koki26
# ---------------------------------------

import discord
from discord.ext import commands, tasks
import datetime

intents = discord.Intents.default()
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

GUILD_ID = 123456789012345678  # tvůj server ID
CATEGORY_NAME = "📅 Info"
BOT_TOKEN = "TVŮJ_TOKEN"

# České názvy dní
CZECH_DAYS = [
    "pondělí", "úterý", "středa", "čtvrtek",
    "pátek", "sobota", "neděle"
]

@bot.event
async def on_ready():
    print(f"✅ Přihlášen jako {bot.user}")

    # Status bota
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name="kolik je nás na serveru 👀"
        ),
        status=discord.Status.online
    )

    update_channels.start()

@tasks.loop(minutes=1)
async def update_channels():
    guild = bot.get_guild(GUILD_ID)
    if guild is None:
        return

    # najít nebo vytvořit kategorii
    category = discord.utils.get(guild.categories, name=CATEGORY_NAME)
    if category is None:
        category = await guild.create_category(CATEGORY_NAME)

    # dnešní den a datum
    weekday = datetime.datetime.now().weekday()  # 0=pondělí, 6=neděle
    day_name = f"┣ 📅 {CZECH_DAYS[weekday]}"
    date_today = f"┣ 🗓️ {datetime.datetime.now().strftime('%d-%m-%Y')}"
    member_count = f"┗ 👥 {guild.member_count} lidí"

    wanted_names = [day_name, date_today, member_count]

    # zajistíme že máme přesně 3 kanály
    existing = category.voice_channels
    while len(existing) < 3:
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(connect=False, speak=False)
        }
        await category.create_voice_channel("dočasný", overwrites=overwrites)
        existing = category.voice_channels

    # přejmenujeme první tři kanály
    for channel, new_name in zip(existing[:3], wanted_names):
        if channel.name != new_name:
            await channel.edit(name=new_name)

    # smažeme všechny kanály navíc
    for channel in existing[3:]:
        await channel.delete()

bot.run(BOT_TOKEN)
