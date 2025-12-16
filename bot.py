# ---------------------------------------
# 🤖 Discord Info + Whitelist Bot s /help
# Slash příkazy: /help, /whitelist
# Autor: Koki26
# ---------------------------------------

import discord
from discord.ext import commands, tasks
from discord import app_commands
import datetime
from dotenv import load_dotenv
import os
import threading
from flask import Flask

# =========================
# ENV
# =========================
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID"))
PORT = int(os.environ.get("PORT", 10000))  # Render PORT

# ---------------------------------------
# KONFIGURACE
# ---------------------------------------

# Info kanály
CATEGORY_NAME = "📅 Info"

# Whitelist
WL_ROLE_ID = 1415780201681391616     # ID role "Whitelisted"
ADDER_ROLE_ID = 1415779903219175475   # ID role "Whitelist Adder"
RESULTS_CHANNEL_ID = 1415779774286008451  # ID kanálu #wl-vysledky

# =========================
# FLASK WEB SERVER (pro Render)
# =========================
app = Flask(__name__)

@app.route("/")
def home():
    return "✅ Discord bot is running."

def run_web():
    app.run(host="0.0.0.0", port=PORT)

# =========================
# DISCORD BOT
# =========================
intents = discord.Intents.default()
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"🤖 Bot přihlášen jako {bot.user}")

# České názvy dní
CZECH_DAYS = [
    "pondělí", "úterý", "středa", "čtvrtek",
    "pátek", "sobota", "neděle"
]

# ---------------------------------------
# BOT
# ---------------------------------------
intents = discord.Intents.default()
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

# ---------------------------------------
# EVENTS
# ---------------------------------------
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

    # Start info kanálů
    update_channels.start()

    # Sync slash příkazů
    try:
        synced = await bot.tree.sync(guild=discord.Object(id=GUILD_ID))
        print(f"📌 Slash příkazy synchronizovány: {len(synced)}")
    except Exception as e:
        print(f"Chyba při sync: {e}")

# ---------------------------------------
# TASK: Info kanály
# ---------------------------------------
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

# ---------------------------------------
# SLASH COMMAND: /whitelist
# ---------------------------------------
@bot.tree.command(
    name="whitelist",
    description="Přidá hráče na whitelist",
    guild=discord.Object(id=GUILD_ID)
)
@app_commands.describe(
    hrac="Discord jméno hráče (např. User#1234)",
    stav="Zda hráč prošel nebo ne",
    chyby="Počet chyb (pokud prošel)"
)
@app_commands.choices(
    stav=[
        app_commands.Choice(name="Prošel", value="prosel"),
        app_commands.Choice(name="Neprošel", value="neprosel")
    ]
)
async def whitelist(interaction: discord.Interaction, hrac: str, stav: app_commands.Choice[str], chyby: int = 0):
    # Kontrola role
    member = interaction.guild.get_member(interaction.user.id)
    if not member:
        return await interaction.response.send_message("❌ Nepodařilo se najít tvůj účet na serveru.", ephemeral=True)

    if not any(role.id == ADDER_ROLE_ID for role in member.roles):
        return await interaction.response.send_message("❌ Nemáš oprávnění použít tento příkaz.", ephemeral=True)

    guild = interaction.guild
    results_channel = guild.get_channel(RESULTS_CHANNEL_ID)

    if stav.value == "prosel":
        # Najdi hráče podle jména
        target_member = None
        for guild_member in guild.members:
            if str(guild_member) == hrac:
                target_member = guild_member
                break
        
        if not target_member:
            return await interaction.response.send_message(
                f"❌ Hráč **{hrac}** nebyl nalezen na serveru. Zkontroluj, zda jsi zadal správné Discord jméno.", 
                ephemeral=True
            )
        
        # Přidání role
        wl_role = guild.get_role(WL_ROLE_ID)
        if not wl_role:
            return await interaction.response.send_message("❌ Whitelist role nebyla nalezena.", ephemeral=True)
        
        try:
            await target_member.add_roles(wl_role)
            role_assigned = True
        except discord.Forbidden:
            role_assigned = False
            print("Bot nemá oprávnění přidávat role.")
        except Exception as e:
            role_assigned = False
            print(f"Chyba při přidávání role: {e}")

        embed = discord.Embed(
            title="✅ Hráč prošel whitelistem!",
            description=f"**{hrac}** prošel s `{chyby}` chybami.\nGratulujeme! 🎉",
            color=discord.Color.green()
        )
        
        if not role_assigned:
            embed.add_field(
                name="⚠️ Upozornění",
                value="Role se nepodařilo automaticky přidat. Prosím, přidej ji manuálně.",
                inline=False
            )
            
        embed.set_image(url="https://i.ibb.co/0Vs96g1h/sss.png")

        if results_channel:
            await results_channel.send(embed=embed)

        if role_assigned:
            await interaction.response.send_message(f"✔ Hráč **{hrac}** byl whitelisted a role byla přidána.", ephemeral=True)
        else:
            await interaction.response.send_message(f"✔ Hráč **{hrac}** byl whitelisted, ale role se nepodařila přidat. Přidej ji manuálně.", ephemeral=True)

    elif stav.value == "neprosel":
        embed = discord.Embed(
            title="❌ Hráč neprošel whitelistem!",
            description=f"**{hrac}** neuspěl při whitelist testu.",
            color=discord.Color.red()
        )
        embed.set_image(url="https://i.ibb.co/84m4cfBZ/ssss.png")

        if results_channel:
            await results_channel.send(embed=embed)

        await interaction.response.send_message(f"❌ Hráč **{hrac}** neprošel.", ephemeral=True)

# ---------------------------------------
# SLASH COMMAND: /help
# ---------------------------------------
@bot.tree.command(
    name="help",
    description="Ukáže nápovědu k příkazům",
    guild=discord.Object(id=GUILD_ID)
)
async def help_cmd(interaction: discord.Interaction):
    embed = discord.Embed(
        title="📖 Nápověda k příkazům",
        color=discord.Color.blue()
    )
    embed.add_field(
        name="/whitelist [hráč] [stav] [chyby]",
        value="Přidá hráče do whitelistu nebo ukáže, že neprošel.\n"
              "Použitelné jen s rolí `Whitelist Adder`.\n"
              "**Poznámka:** Hráč musí být zadán v plném formátu (např. User#1234).",
        inline=False
    )
    embed.add_field(
        name="/help",
        value="Ukáže tuto nápovědu.",
        inline=False
    )
    embed.set_footer(text="ℹ️ Info kanály (den, datum, počet lidí) běží automaticky.")
    await interaction.response.send_message(embed=embed, ephemeral=True)

# =========================
# START
# =========================
if __name__ == "__main__":
    # Spustí web server v jiném vlákně
    threading.Thread(target=run_web, daemon=True).start()

    # Spustí Discord bota
    bot.run(BOT_TOKEN)