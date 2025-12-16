# ---------------------------------------
# 🤖 Discord Info + Whitelist Bot s /help
# Slash příkazy: /help, /whitelist
# Autor: Koki26
# ---------------------------------------

import discord
from discord.ext import commands, tasks
from discord import app_commands
import datetime
import os
import threading
from flask import Flask

# =========================
# KONSTANTY
# =========================
BOT_TOKEN = os.environ.get("BOT_TOKEN")
GUILD_ID = int(os.environ.get("GUILD_ID"))
PORT = int(os.environ.get("PORT", 10000))

# Info kanály
CATEGORY_NAME = "📅 Info"

# Whitelist
WL_ROLE_ID = 1415780201681391616     # ID role "Whitelisted"
ADDER_ROLE_ID = 1415779903219175475   # ID role "Whitelist Adder"
RESULTS_CHANNEL_ID = 1415779774286008451  # ID kanálu #wl-vysledky

# =========================
# FLASK WEB SERVER (pro Render keep-alive)
# =========================
app = Flask(__name__)

@app.route("/")
def home():
    return "✅ Discord bot is running."

def run_web():
    app.run(host="0.0.0.0", port=PORT, debug=False)

# =========================
# DISCORD BOT
# =========================

# České názvy dní
CZECH_DAYS = [
    "pondělí", "úterý", "středa", "čtvrtek",
    "pátek", "sobota", "neděle"
]

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
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
        # Sync pro konkrétní guild
        guild = discord.Object(id=GUILD_ID)
        bot.tree.copy_global_to(guild=guild)
        synced = await bot.tree.sync(guild=guild)
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
        try:
            category = await guild.create_category(CATEGORY_NAME)
        except Exception as e:
            print(f"Chyba při vytváření kategorie: {e}")
            return

    # dnešní den a datum
    weekday = datetime.datetime.now().weekday()  # 0=pondělí, 6=neděle
    day_name = f"┣ 📅 {CZECH_DAYS[weekday]}"
    date_today = f"┣ 🗓️ {datetime.datetime.now().strftime('%d-%m-%Y')}"
    member_count = f"┗ 👥 {guild.member_count} lidí"

    wanted_names = [day_name, date_today, member_count]

    # zajistíme že máme přesně 3 kanály
    existing = [ch for ch in category.channels if isinstance(ch, discord.VoiceChannel)]
    
    # Seřadíme podle pozice
    existing.sort(key=lambda x: x.position)
    
    # Vytvoříme chybějící kanály
    while len(existing) < 3:
        try:
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(connect=False, speak=False)
            }
            new_channel = await category.create_voice_channel("dočasný", overwrites=overwrites)
            existing.append(new_channel)
        except Exception as e:
            print(f"Chyba při vytváření kanálu: {e}")
            break
    
    # Seřadíme znovu po přidání
    existing = [ch for ch in category.channels if isinstance(ch, discord.VoiceChannel)]
    existing.sort(key=lambda x: x.position)
    
    # přejmenujeme první tři kanály
    for channel, new_name in zip(existing[:3], wanted_names):
        if channel.name != new_name:
            try:
                await channel.edit(name=new_name)
            except Exception as e:
                print(f"Chyba při přejmenování kanálu {channel.name}: {e}")

    # smažeme všechny kanály navíc (pokud existují více než 3)
    if len(existing) > 3:
        for channel in existing[3:]:
            try:
                await channel.delete()
                print(f"Smazán přebytečný kanál: {channel.name}")
            except Exception as e:
                print(f"Chyba při mazání kanálu {channel.name}: {e}")

# ---------------------------------------
# SLASH COMMAND: /whitelist
# ---------------------------------------
@bot.tree.command(
    name="whitelist",
    description="Přidá hráče na whitelist"
)
@app_commands.describe(
    hrac="Discord jméno hráče (např. username)",
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
    if not any(role.id == ADDER_ROLE_ID for role in interaction.user.roles):
        return await interaction.response.send_message("❌ Nemáš oprávnění použít tento příkaz.", ephemeral=True)

    guild = interaction.guild
    results_channel = guild.get_channel(RESULTS_CHANNEL_ID)

    if stav.value == "prosel":
        # Najdi hráče podle jména (bez discriminatoru, protože Discord už ho nepoužívá)
        target_member = None
        for guild_member in guild.members:
            if guild_member.name == hrac or str(guild_member) == hrac or guild_member.display_name == hrac:
                target_member = guild_member
                break
        
        if not target_member:
            return await interaction.response.send_message(
                f"❌ Hráč **{hrac}** nebyl nalezen na serveru. Zkontroluj, zda jsi zadal správné jméno.", 
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
            description=f"**{target_member.display_name}** prošel s `{chyby}` chybami.\nGratulujeme! 🎉",
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
            await interaction.response.send_message(f"✔ Hráč **{target_member.display_name}** byl whitelisted a role byla přidána.", ephemeral=True)
        else:
            await interaction.response.send_message(f"✔ Hráč **{target_member.display_name}** byl whitelisted, ale role se nepodařila přidat. Přidej ji manuálně.", ephemeral=True)

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
    description="Ukáže nápovědu k příkazům"
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
              "**Poznámka:** Zadej jméno hráče (bez #).",
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
    # Ověření tokenu
    if not BOT_TOKEN:
        print("❌ Chybějící BOT_TOKEN v environment variables!")
        exit(1)
    
    if not GUILD_ID:
        print("❌ Chybějící GUILD_ID v environment variables!")
        exit(1)
    
    # Spustí web server v jiném vlákně (jen na Renderu)
    threading.Thread(target=run_web, daemon=True).start()
    print(f"🌐 Web server běží na portu {PORT}")

    # Spustí Discord bota
    print("🤖 Spouštím Discord bota...")
    bot.run(BOT_TOKEN)