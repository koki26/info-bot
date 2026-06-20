# ---------------------------------------
# 🤖 Discord Info + Whitelist Bot s /help a webovým rozhraním
# Slash příkazy: /help, /whitelist
# Webové rozhraní: /admin
# Autor: Koki26
# ---------------------------------------

import discord
from discord.ext import commands, tasks
from discord import app_commands
import datetime
import os
from dotenv import load_dotenv
import asyncio
from flask import Flask, render_template, request, redirect, session, flash, jsonify
import requests
import secrets
import json
from typing import List, Dict
import threading
import concurrent.futures

load_dotenv()

# =========================
# KONSTANTY A KONFIGURACE
# =========================
BOT_TOKEN = os.environ.get("BOT_TOKEN")
GUILD_ID = int(os.environ.get("GUILD_ID"))
PORT = int(os.environ.get("PORT", 10000))
SECRET_KEY = os.environ.get("SECRET_KEY", secrets.token_hex(32))
MAX_ERRORS_ALLOWED = int(os.environ.get("MAX_ERRORS_ALLOWED", 3))

# Info kanály
CATEGORY_NAME = "📅 Info"

# Whitelist
WL_ROLE_ID = 1517661951994364136     # ID role "Whitelisted"
ADDER_ROLE_ID = 1415779903219175475   # ID role "Whitelist Adder"
RESULTS_CHANNEL_ID = 1415779774286008451  # ID kanálu #wl-vysledky
REMOVE_ROLE_ID = int(os.environ.get("REMOVE_ROLE_ID", 1517662000954736691))  # ID role k odebrání při udělení whitelistu

# OAuth2
CLIENT_ID = os.environ.get("DISCORD_CLIENT_ID")
CLIENT_SECRET = os.environ.get("DISCORD_CLIENT_SECRET")
REDIRECT_URI = os.environ.get("REDIRECT_URI", "http://localhost:10000/callback")

# =========================
# FLASK WEB SERVER
# =========================
app = Flask(__name__)
app.secret_key = SECRET_KEY

# =========================
# DISCORD BOT
# =========================
CZECH_DAYS = [
    "pondělí", "úterý", "středa", "čtvrtek",
    "pátek", "sobota", "neděle"
]

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Globální proměnná pro sdílení bota s Flaskem
bot_instance = None

# ---------------------------------------
# POMOCNÉ FUNKCE PRO WEB
# ---------------------------------------
def get_bot():
    """Vrátí instanci Discord bota"""
    return bot_instance

async def get_non_whitelisted_members(guild):
    """Vrátí seznam členů bez whitelist role"""
    wl_role = guild.get_role(WL_ROLE_ID)
    if not wl_role:
        return []
    
    non_whitelisted = []
    for member in guild.members:
        if not member.bot and wl_role not in member.roles:
            non_whitelisted.append({
                'id': str(member.id),
                'name': member.name,
                'display_name': member.display_name,
                'avatar_url': member.avatar.url if member.avatar else member.default_avatar.url
            })
    
    return non_whitelisted

async def add_to_whitelist(member_id: int, errors: int, passed: bool, adder_name: str):
    """Přidá hráče na whitelist a odebere roli pokud je definována"""
    guild = get_bot().get_guild(GUILD_ID)
    if not guild:
        return False, "Guild not found"
    
    member = guild.get_member(member_id)
    if not member:
        return False, "Member not found"
    
    results_channel = guild.get_channel(RESULTS_CHANNEL_ID)
    wl_role = guild.get_role(WL_ROLE_ID)
    
    if not wl_role:
        return False, "Whitelist role not found"
    
    # Role k odebrání (pokud je definována)
    remove_role = None
    if REMOVE_ROLE_ID > 0:
        remove_role = guild.get_role(REMOVE_ROLE_ID)
    
    if passed:
        # Přidání role whitelist
        try:
            await member.add_roles(wl_role)
            role_assigned = True
        except Exception as e:
            role_assigned = False
            print(f"Chyba při přidávání whitelist role: {e}")
        
        # Odebrání role (pokud existuje)
        role_removed = False
        if remove_role and remove_role in member.roles:
            try:
                await member.remove_roles(remove_role)
                role_removed = True
            except Exception as e:
                print(f"Chyba při odebírání role: {e}")
        
        embed = discord.Embed(
            title="✅ Hráč prošel whitelistem!",
            description=f"**{member.display_name}** prošel s `{errors}` chybami.\nPřidal: {adder_name}\nGratulujeme! 🎉",
            color=discord.Color.green()
        )
        
        # Přidání informací o rolích do embedu
        if not role_assigned or (remove_role and not role_removed):
            embed.add_field(
                name="⚠️ Upozornění",
                value="",
                inline=False
            )
            
            if not role_assigned:
                embed.add_field(
                    name="Role whitelist",
                    value="Nepodařilo se automaticky přidat. Prosím, přidej ji manuálně.",
                    inline=True
                )
            
            if remove_role and not role_removed:
                embed.add_field(
                    name=f"Role {remove_role.name}",
                    value="Nepodařilo se automaticky odebrat. Prosím, odeber ji manuálně.",
                    inline=True
                )
        
        embed.set_image(url="https://i.ibb.co/0Vs96g1h/sss.png")
        
        if results_channel:
            await results_channel.send(embed=embed)
        
        return True, f"Hráč {member.display_name} byl přidán na whitelist"
    
    else:
        embed = discord.Embed(
            title="❌ Hráč neprošel whitelistem!",
            description=f"**{member.display_name}** neuspěl při whitelist testu.\nPřidal: {adder_name}",
            color=discord.Color.red()
        )
        embed.set_image(url="https://i.ibb.co/84m4cfBZ/ssss.png")
        
        if results_channel:
            await results_channel.send(embed=embed)
        
        return True, f"Hráč {member.display_name} neprošel whitelistem"

# ---------------------------------------
# FLASK ROUTES
# ---------------------------------------
@app.route("/")
def home():
    return render_template("home.html")

@app.route("/admin")
def admin():
    if 'user_id' not in session:
        # Přesměrování na Discord OAuth2
        discord_auth_url = f"https://discord.com/api/oauth2/authorize?client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&response_type=code&scope=identify+guilds"
        return redirect(discord_auth_url)
    
    return redirect("/dashboard")

@app.route("/callback")
def callback():
    code = request.args.get('code')
    if not code:
        return "Chyba: Chybí autorizační kód", 400
    
    # Získání access tokenu
    data = {
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': REDIRECT_URI,
        'scope': 'identify guilds'
    }
    
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    
    try:
        token_resp = requests.post('https://discord.com/api/oauth2/token', data=data, headers=headers, timeout=10)
        token_resp.raise_for_status()
        token_data = token_resp.json()
        
        if 'access_token' not in token_data:
            flash("Chyba při získávání tokenu", "error")
            return redirect("/")
        
        # Získání informací o uživateli
        auth_headers = {'Authorization': f'Bearer {token_data["access_token"]}'}
        
        user_resp = requests.get('https://discord.com/api/users/@me', headers=auth_headers, timeout=10)
        user_resp.raise_for_status()
        user_data = user_resp.json()
        
        guilds_resp = requests.get('https://discord.com/api/users/@me/guilds', headers=auth_headers, timeout=10)
        guilds_resp.raise_for_status()
        guilds_data = guilds_resp.json()
        
    except requests.exceptions.RequestException as e:
        print(f"Chyba HTTP requestu: {e}")
        flash("Chyba při komunikaci s Discord API", "error")
        return redirect("/")
    except ValueError as e:
        print(f"Chyba parsování JSON: {e}")
        flash("Chyba při zpracování odpovědi", "error")
        return redirect("/")
    
    # Kontrola, zda je uživatel v guild
    user_in_guild = any(str(guild['id']) == str(GUILD_ID) for guild in guilds_data)
    
    if not user_in_guild:
        flash("Nejsi členem tohoto Discord serveru!", "error")
        return redirect("/")
    
    # Uložení do session
    session['user_id'] = user_data['id']
    session['username'] = user_data['username']
    session['avatar'] = user_data.get('avatar', '')
    
    # Kontrola role přímo přes Discord bota
    bot = get_bot()
    guild = bot.get_guild(GUILD_ID)
    
    if guild:
        member = guild.get_member(int(user_data['id']))
        if member:
            has_permission = any(role.id == ADDER_ROLE_ID for role in member.roles)
            session['has_permission'] = has_permission
            if not has_permission:
                flash("Nemáš oprávnění pro přístup do admin panelu!", "error")
                return redirect("/")
    
    return redirect("/dashboard")

@app.route("/dashboard")
async def dashboard():
    if 'user_id' not in session:
        return redirect("/admin")
    
    if not session.get('has_permission', False):
        return "Nemáš oprávnění!", 403
    
    bot = get_bot()
    guild = bot.get_guild(GUILD_ID)
    
    if not guild:
        return "Bot není připojen k serveru", 500
    
    # Získání členů bez whitelistu
    non_whitelisted = await get_non_whitelisted_members(guild)
    
    return render_template("dashboard.html", 
                         members=non_whitelisted,
                         username=session['username'],
                         max_errors=MAX_ERRORS_ALLOWED)

@app.route("/process/<member_id>", methods=['POST'])
def process_member(member_id):  # SYNCHRONNÍ
    if 'user_id' not in session or not session.get('has_permission', False):
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        errors = int(request.form.get('errors', 0))
        passed = request.form.get('passed') == 'true'
        
        # Validace chyb
        if passed and errors > MAX_ERRORS_ALLOWED:
            return jsonify({'error': f'Nad {MAX_ERRORS_ALLOWED} chyb nelze projít!'}), 400
        
        # SYNC volání Discord API
        success, message = add_to_whitelist_sync(
            int(member_id), 
            errors, 
            passed,
            session['username']
        )
        
        if success:
            return jsonify({'success': True, 'message': message})
        else:
            return jsonify({'error': message}), 400
            
    except Exception as e:
        print(f"Chyba při zpracování: {e}")
        return jsonify({'error': str(e)}), 500


@app.route("/logout")
def logout():
    session.clear()
    flash("Byl jsi odhlášen", "info")
    return redirect("/")

# ---------------------------------------
# SYNCHRONNÍ POMOCNÉ FUNKCE
# ---------------------------------------

def add_to_whitelist_sync(member_id: int, errors: int, passed: bool, adder_name: str):
    """Přidá hráče na whitelist a odebere roli pokud je definována"""
    bot = get_bot()
    guild = bot.get_guild(GUILD_ID)
    if not guild:
        return False, "Bot není připojen k serveru"
    
    member = guild.get_member(member_id)
    if not member:
        return False, "Hráč nebyl nalezen na serveru"
    
    results_channel = guild.get_channel(RESULTS_CHANNEL_ID)
    wl_role = guild.get_role(WL_ROLE_ID)
    
    if not wl_role:
        return False, "Whitelist role nebyla nalezena"
    
    # Role k odebrání (pokud je definována)
    remove_role = None
    if REMOVE_ROLE_ID > 0:
        remove_role = guild.get_role(REMOVE_ROLE_ID)
    
    # Získáme event loop z bota (který běží v hlavním threadu)
    bot_loop = bot.loop
    
    try:
        if passed:
            # 1. PŘIDÁNÍ ROLE whitelist pomocí run_coroutine_threadsafe
            try:
                future = asyncio.run_coroutine_threadsafe(
                    member.add_roles(wl_role),
                    bot_loop
                )
                future.result(timeout=10)  # 10 sekund timeout
                role_assigned = True
            except asyncio.TimeoutError:
                role_assigned = False
                print("Timeout při přidávání whitelist role!")
            except discord.Forbidden:
                role_assigned = False
                print("Bot nemá oprávnění přidávat role!")
            except Exception as e:
                role_assigned = False
                print(f"Chyba při přidávání whitelist role: {e}")
            
            # 2. ODEBRÁNÍ ROLE (pokud existuje)
            role_removed = False
            if remove_role and remove_role in member.roles:
                try:
                    future = asyncio.run_coroutine_threadsafe(
                        member.remove_roles(remove_role),
                        bot_loop
                    )
                    future.result(timeout=10)
                    role_removed = True
                except asyncio.TimeoutError:
                    role_removed = False
                    print("Timeout při odebírání role!")
                except discord.Forbidden:
                    role_removed = False
                    print("Bot nemá oprávnění odebírat role!")
                except Exception as e:
                    role_removed = False
                    print(f"Chyba při odebírání role: {e}")
            
            # 3. VYTVOŘENÍ EMBED (stejné jako v /whitelist commandu)
            embed = discord.Embed(
                title="✅ Hráč prošel whitelistem!",
                description=f"**{member.display_name}** prošel s `{errors}` chybami.\nPřidal: {adder_name}\nGratulujeme! 🎉",
                color=discord.Color.green()
            )
            
            # Přidání informací o rolích do embedu
            if not role_assigned or (remove_role and not role_removed):
                embed.add_field(
                    name="⚠️ Upozornění",
                    value="",
                    inline=False
                )
                
                if not role_assigned:
                    embed.add_field(
                        name="Role whitelist",
                        value="Nepodařilo se automaticky přidat. Prosím, přidej ji manuálně.",
                        inline=True
                    )
                
                if remove_role and not role_removed:
                    embed.add_field(
                        name=f"Role {remove_role.name}",
                        value="Nepodařilo se automaticky odebrat. Prosím, odeber ji manuálně.",
                        inline=True
                    )
            
            embed.set_image(url="https://i.ibb.co/0Vs96g1h/sss.png")
            
            # 4. ODESLÁNÍ ZPRÁVY DO KANÁLU
            if results_channel:
                try:
                    future = asyncio.run_coroutine_threadsafe(
                        results_channel.send(embed=embed),
                        bot_loop
                    )
                    future.result(timeout=10)
                except Exception as e:
                    print(f"Chyba při odesílání zprávy: {e}")
            
            # 5. VRÁCENÍ ZPRÁVY
            message = f"Hráč {member.display_name} byl přidán na whitelist"
            if not role_assigned:
                message += ", ale whitelist role se nepodařila přidat"
            if remove_role and not role_removed:
                message += f", a role {remove_role.name} se nepodařila odebrat"
            message += "."
            
            return True, message
        
        else:  # Neprošel
            # VYTVOŘENÍ A ODESLÁNÍ EMBED PRO NEPROŠLÉHO
            embed = discord.Embed(
                title="❌ Hráč neprošel whitelistem!",
                description=f"**{member.display_name}** neuspěl při whitelist testu.\nPřidal: {adder_name}",
                color=discord.Color.red()
            )
            embed.set_image(url="https://i.ibb.co/84m4cfBZ/ssss.png")
            
            if results_channel:
                try:
                    future = asyncio.run_coroutine_threadsafe(
                        results_channel.send(embed=embed),
                        bot_loop
                    )
                    future.result(timeout=10)
                except Exception as e:
                    print(f"Chyba při odesílání zprávy: {e}")
            
            return True, f"Hráč {member.display_name} neprošel whitelistem"
            
    except Exception as e:
        print(f"Obecná chyba v add_to_whitelist_sync: {e}")
        return False, f"Chyba při zpracování: {str(e)}"

# ---------------------------------------
# DISCORD BOT EVENTS
# ---------------------------------------
@bot.event
async def on_ready():
    global bot_instance
    bot_instance = bot
    
    print(f"✅ Přihlášen jako {bot.user}")
    
    # Status bota
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name="whitelist admin panel 👀"
        ),
        status=discord.Status.online
    )
    
    # Start info kanálů
    update_channels.start()
    
    # Sync slash příkazů
    try:
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
    
    category = discord.utils.get(guild.categories, name=CATEGORY_NAME)
    if category is None:
        try:
            category = await guild.create_category(CATEGORY_NAME)
        except Exception as e:
            print(f"Chyba při vytváření kategorie: {e}")
            return
    
    weekday = datetime.datetime.now().weekday()
    day_name = f"📅・{CZECH_DAYS[weekday]}"
    date_today = f"🗓️・{datetime.datetime.now().strftime('%d-%m-%Y')}"
    member_count = f"👥・{guild.member_count} lidí"
    
    wanted_names = [day_name, date_today, member_count]
    existing = [ch for ch in category.channels if isinstance(ch, discord.VoiceChannel)]
    existing.sort(key=lambda x: x.position)
    
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
    
    existing = [ch for ch in category.channels if isinstance(ch, discord.VoiceChannel)]
    existing.sort(key=lambda x: x.position)
    
    for channel, new_name in zip(existing[:3], wanted_names):
        if channel.name != new_name:
            try:
                await channel.edit(name=new_name)
            except Exception as e:
                print(f"Chyba při přejmenování kanálu {channel.name}: {e}")
    
    if len(existing) > 3:
        for channel in existing[3:]:
            try:
                await channel.delete()
            except Exception as e:
                print(f"Chyba při mazání kanálu {channel.name}: {e}")

# ---------------------------------------
# SLASH COMMANDS (původní funkce + odebrání role)
# ---------------------------------------
@bot.tree.command(
    name="whitelist",
    description="Přidá hráče na whitelist"
)
@app_commands.describe(
    hrac="Discord jméno hráče",
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
    if not any(role.id == ADDER_ROLE_ID for role in interaction.user.roles):
        return await interaction.response.send_message("❌ Nemáš oprávnění!", ephemeral=True)
    
    if stav.value == "prosel" and chyby > MAX_ERRORS_ALLOWED:
        return await interaction.response.send_message(
            f"❌ Nelze projít s {chyby} chybami! Maximum je {MAX_ERRORS_ALLOWED}.",
            ephemeral=True
        )
    
    guild = interaction.guild
    results_channel = guild.get_channel(RESULTS_CHANNEL_ID)
    
    if stav.value == "prosel":
        target_member = None
        for guild_member in guild.members:
            if guild_member.name == hrac or str(guild_member) == hrac or guild_member.display_name == hrac:
                target_member = guild_member
                break
        
        if not target_member:
            return await interaction.response.send_message(
                f"❌ Hráč **{hrac}** nebyl nalezen!", 
                ephemeral=True
            )
        
        wl_role = guild.get_role(WL_ROLE_ID)
        if not wl_role:
            return await interaction.response.send_message("❌ Whitelist role nebyla nalezena.", ephemeral=True)
        
        # Odebrání role (pokud je definována)
        remove_role = None
        if REMOVE_ROLE_ID > 0:
            remove_role = guild.get_role(REMOVE_ROLE_ID)
        
        try:
            await target_member.add_roles(wl_role)
            role_assigned = True
        except Exception as e:
            role_assigned = False
            print(f"Chyba při přidávání whitelist role: {e}")
        
        # Odebrání role
        role_removed = False
        if remove_role and remove_role in target_member.roles:
            try:
                await target_member.remove_roles(remove_role)
                role_removed = True
            except Exception as e:
                role_removed = False
                print(f"Chyba při odebírání role: {e}")
        
        embed = discord.Embed(
            title="✅ Hráč prošel whitelistem!",
            description=f"**{target_member.display_name}** prošel s `{chyby}` chybami.\nGratulujeme! 🎉",
            color=discord.Color.green()
        )
        
        # Přidání informací o rolích do embedu
        if not role_assigned or (remove_role and not role_removed):
            embed.add_field(
                name="⚠️ Upozornění",
                value="",
                inline=False
            )
            
            if not role_assigned:
                embed.add_field(
                    name="Role whitelist",
                    value="Nepodařilo se automaticky přidat. Prosím, přidej ji manuálně.",
                    inline=True
                )
            
            if remove_role and not role_removed:
                embed.add_field(
                    name=f"Role {remove_role.name}",
                    value="Nepodařilo se automaticky odebrat. Prosím, odeber ji manuálně.",
                    inline=True
                )
        
        embed.set_image(url="https://i.ibb.co/0Vs96g1h/sss.png")
        
        if results_channel:
            await results_channel.send(embed=embed)
        
        response_msg = f"✔ Hráč **{target_member.display_name}** byl whitelisted"
        if not role_assigned:
            response_msg += ", ale whitelist role se nepodařila přidat"
        if remove_role and not role_removed:
            response_msg += f", a role {remove_role.name} se nepodařila odebrat"
        response_msg += "."
        
        await interaction.response.send_message(response_msg, ephemeral=True)
    
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
        value=f"Přidá hráče do whitelistu nebo ukáže, že neprošel.\nMaximální počet chyb pro schválení: {MAX_ERRORS_ALLOWED}\nPoužitelné jen s rolí `Whitelist Adder`.",
        inline=False
    )
    embed.add_field(
        name="/help",
        value="Ukáže tuto nápovědu.",
        inline=False
    )
    embed.add_field(
        name="Webové rozhraní",
        value="Přístupné na `/admin` pro Whitlelist Adders",
        inline=False
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)

# ---------------------------------------
# HTML TEMPLATES
# ---------------------------------------
@app.context_processor
def utility_processor():
    return dict(max_errors=MAX_ERRORS_ALLOWED)

# =========================
# HTML TEMPLATES (inline)
# =========================
def setup_templates():
    """Vytvoří HTML šablony inline"""
    
    # Home page template
    home_template = '''
<!DOCTYPE html>
<html lang="cs">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Whitelist Admin Panel</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.8.1/font/bootstrap-icons.css">
    <style>
        body {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
        }
        .card {
            border: none;
            border-radius: 15px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
        }
        .btn-discord {
            background-color: #5865F2;
            color: white;
            padding: 12px 30px;
            font-size: 1.1rem;
        }
        .btn-discord:hover {
            background-color: #4752C4;
            color: white;
        }
        .login-container {
            max-width: 500px;
            margin: auto;
        }
        /* Footer styling */
        .footer {
            margin-top: 2rem;
            padding: 1rem 0;
            color: rgba(255, 255, 255, 0.7);
            font-size: 0.9rem;
        }
        .footer a {
            color: rgba(255, 255, 255, 0.9);
            text-decoration: none;
        }
        .footer a:hover {
            color: white;
            text-decoration: underline;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="login-container">
            <!-- Login Card -->
            <div class="card">
                <div class="card-body p-5">
                    <div class="text-center mb-4">
                        <i class="bi bi-shield-check display-1 text-primary"></i>
                        <h2 class="mt-3">Whitelist Admin Panel</h2>
                        <p class="text-muted">Přihlaste se pomocí Discord účtu</p>
                    </div>
                    
                    {% with messages = get_flashed_messages(with_categories=true) %}
                        {% if messages %}
                            {% for category, message in messages %}
                                <div class="alert alert-{{ 'danger' if category == 'error' else 'info' }} alert-dismissible fade show" role="alert">
                                    {{ message }}
                                    <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                                </div>
                            {% endfor %}
                        {% endif %}
                    {% endwith %}
                    
                    <div class="d-grid gap-2">
                        <a href="/admin" class="btn btn-discord">
                            <i class="bi bi-discord me-2"></i> Přihlásit se přes Discord
                        </a>
                    </div>
                    
                    <div class="mt-4 text-center">
                        <small class="text-muted">
                            Pro přístup potřebujete roli "Whitelist Adder" na Discord serveru
                        </small>
                    </div>
                </div>
            </div>
            
            <!-- Footer-->
            <div class="footer text-center mt-4">
                <hr class="my-3" style="border-color: rgba(255,255,255,0.2);">
                <p class="mb-0">
                    Made with ❤️ by 
                    <a href="https://github.com/koki26" target="_blank">koki26</a>
                    | 
                    <a href="https://github.com/koki26/info-bot" target="_blank">
                        <i class="bi bi-github me-1"></i>GitHub
                    </a>
                </p>
                <small class="text-muted">© 2025 Discord Whitelist Bot</small>
            </div>
        </div>
    </div>
    
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
    '''
    
    # Dashboard template
    dashboard_template = '''
    <!DOCTYPE html>
    <html lang="cs">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Whitelist Dashboard</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.8.1/font/bootstrap-icons.css">
        <style>
            :root {
                --discord-blurple: #5865F2;
                --discord-green: #57F287;
                --discord-red: #ED4245;
            }
            body {
                background-color: #f5f5f5;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            }
            .navbar {
                background-color: var(--discord-blurple);
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            .member-card {
                transition: transform 0.2s, box-shadow 0.2s;
                border: none;
                border-radius: 10px;
                overflow: hidden;
            }
            .member-card:hover {
                transform: translateY(-5px);
                box-shadow: 0 10px 20px rgba(0,0,0,0.1);
            }
            .member-avatar {
                width: 80px;
                height: 80px;
                border-radius: 50%;
                border: 3px solid var(--discord-blurple);
                object-fit: cover;
            }
            .btn-success {
                background-color: var(--discord-green);
                border-color: var(--discord-green);
            }
            .btn-danger {
                background-color: var(--discord-red);
                border-color: var(--discord-red);
            }
            .modal-header {
                background-color: var(--discord-blurple);
                color: white;
            }
            .error-counter {
                font-size: 2rem;
                font-weight: bold;
                color: var(--discord-blurple);
            }
            .error-input {
                width: 100px;
                text-align: center;
                font-size: 1.5rem;
                font-weight: bold;
            }
            .btn-control {
                width: 50px;
                height: 50px;
                font-size: 1.5rem;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            .empty-state {
                padding: 60px 20px;
                text-align: center;
                color: #6c757d;
            }
            .empty-state i {
                font-size: 4rem;
                margin-bottom: 20px;
                opacity: 0.5;
            }
        </style>
    </head>
    <body>
        <!-- Navbar -->
        <nav class="navbar navbar-expand-lg navbar-dark">
            <div class="container">
                <a class="navbar-brand" href="#">
                    <i class="bi bi-shield-check me-2"></i>
                    Whitelist Admin
                </a>
                <div class="d-flex align-items-center">
                    <span class="navbar-text me-3">
                        <i class="bi bi-person-circle me-1"></i> {{ username }}
                    </span>
                    <a href="/logout" class="btn btn-outline-light btn-sm">
                        <i class="bi bi-box-arrow-right"></i> Odhlásit
                    </a>
                </div>
            </div>
        </nav>
        
        <!-- Main Content -->
        <div class="container mt-4">
            <!-- Header -->
            <div class="row mb-4">
                <div class="col">
                    <div class="card">
                        <div class="card-body">
                            <h4 class="card-title mb-3">
                                <i class="bi bi-people me-2"></i> Čekající na whitelist
                            </h4>
                            <div class="row">
                                <div class="col-md-6">
                                    <div class="alert alert-info">
                                        <i class="bi bi-info-circle me-2"></i>
                                        <strong>Pravidla:</strong> Hráč může projít maximálně s {{ max_errors }} chybami
                                    </div>
                                </div>
                                <div class="col-md-6 text-end">
                                    <div class="h4 mb-0">{{ members|length }}</div>
                                    <small class="text-muted">celkem čekajících</small>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Members Grid -->
            <div class="row">
                {% if members %}
                    {% for member in members %}
                    <div class="col-lg-4 col-md-6 mb-4">
                        <div class="card member-card">
                            <div class="card-body text-center p-4">
                                <img src="{{ member.avatar_url }}" alt="Avatar" class="member-avatar mb-3">
                                <h5 class="card-title mb-1">{{ member.display_name }}</h5>
                                <p class="text-muted mb-3">@{{ member.name }}</p>
                                
                                <div class="d-grid gap-2">
                                    <button class="btn btn-success" onclick="openReviewModal('{{ member.id }}', '{{ member.display_name|e }}', '{{ member.avatar_url }}')">
                                        <i class="bi bi-check-circle me-2"></i> Přidat do whitelistu
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                    {% endfor %}
                {% else %}
                    <div class="col-12">
                        <div class="card empty-state">
                            <div class="card-body">
                                <i class="bi bi-emoji-smile"></i>
                                <h3 class="mt-3">Žádní čekající hráči</h3>
                                <p class="text-muted">Všichni členové mají whitelist roli!</p>
                            </div>
                        </div>
                    </div>
                {% endif %}
            </div>
        </div>
        
        <!-- Review Modal -->
        <div class="modal fade" id="reviewModal" tabindex="-1">
            <div class="modal-dialog modal-dialog-centered">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">Whitelist kontrola</h5>
                        <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body text-center">
                        <img id="modalAvatar" src="" alt="Avatar" class="member-avatar mb-3">
                        <h4 id="modalName" class="mb-4"></h4>
                        
                        <!-- Error Counter -->
                        <div class="mb-4">
                            <label class="form-label">Počet chyb:</label>
                            <div class="d-flex justify-content-center align-items-center mb-3">
                                <button class="btn btn-outline-secondary btn-control me-3" onclick="changeErrors(-1)">
                                    <i class="bi bi-dash-lg"></i>
                                </button>
                                
                                <input type="number" id="errorCount" class="form-control error-input" 
                                       value="0" min="0" max="{{ max_errors }}" 
                                       onchange="validateErrors()">
                                
                                <button class="btn btn-outline-secondary btn-control ms-3" onclick="changeErrors(1)">
                                    <i class="bi bi-plus-lg"></i>
                                </button>
                            </div>
                            <div class="text-muted small">
                                Maximum pro schválení: {{ max_errors }} chyb
                            </div>
                            <div id="errorAlert" class="alert alert-danger mt-2 d-none">
                                <i class="bi bi-exclamation-triangle me-2"></i>
                                Nad {{ max_errors }} chyb nelze hráče schválit!
                            </div>
                        </div>
                        
                        <!-- Result -->
                        <div class="mb-3">
                            <div class="h5" id="resultText">
                                <span id="passedText" class="text-success d-none">
                                    <i class="bi bi-check-circle me-2"></i>Projde
                                </span>
                                <span id="failedText" class="text-danger d-none">
                                    <i class="bi bi-x-circle me-2"></i>Neprojde
                                </span>
                            </div>
                        </div>
                    </div>
                    <div class="modal-footer justify-content-center">
                        <button type="button" class="btn btn-danger" onclick="submitResult(false)">
                            <i class="bi bi-x-circle me-2"></i> Neprošel
                        </button>
                        <button type="button" class="btn btn-success" onclick="submitResult(true)" id="submitPass">
                            <i class="bi bi-check-circle me-2"></i> Prošel
                        </button>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Success Toast -->
        <div class="toast-container position-fixed bottom-0 end-0 p-3">
            <div id="successToast" class="toast align-items-center text-white bg-success border-0" role="alert">
                <div class="d-flex">
                    <div class="toast-body">
                        <i class="bi bi-check-circle me-2"></i>
                        <span id="toastMessage"></span>
                    </div>
                    <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
                </div>
            </div>
        </div>
        
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
        <script>
            let currentMemberId = null;
            let currentMemberName = null;
            const maxErrors = {{ max_errors }};
            
            function openReviewModal(memberId, memberName, avatarUrl) {
                currentMemberId = memberId;
                currentMemberName = memberName;
                
                document.getElementById('modalName').textContent = memberName;
                document.getElementById('modalAvatar').src = avatarUrl;
                document.getElementById('errorCount').value = 0;
                
                validateErrors();
                
                const modal = new bootstrap.Modal(document.getElementById('reviewModal'));
                modal.show();
            }
            
            function changeErrors(delta) {
                const input = document.getElementById('errorCount');
                let value = parseInt(input.value) + delta;
                if (value < 0) value = 0;
                input.value = value;
                validateErrors();
            }
            
            function validateErrors() {
                const errors = parseInt(document.getElementById('errorCount').value);
                const canPass = errors <= maxErrors;
                
                document.getElementById('errorAlert').classList.toggle('d-none', canPass);
                document.getElementById('submitPass').disabled = !canPass;
                
                document.getElementById('passedText').classList.toggle('d-none', !canPass);
                document.getElementById('failedText').classList.toggle('d-none', canPass);
            }
            
            async function submitResult(passed) {
                const errors = parseInt(document.getElementById('errorCount').value);
                
                const formData = new FormData();
                formData.append('errors', errors);
                formData.append('passed', passed);
                
                try {
                    const response = await fetch(`/process/${currentMemberId}`, {
                        method: 'POST',
                        body: formData
                    });
                    
                    const result = await response.json();
                    
                    if (result.success) {
                        // Show success message
                        document.getElementById('toastMessage').textContent = result.message;
                        const toast = new bootstrap.Toast(document.getElementById('successToast'));
                        toast.show();
                        
                        // Close modal and reload page after delay
                        bootstrap.Modal.getInstance(document.getElementById('reviewModal')).hide();
                        setTimeout(() => location.reload(), 1500);
                    } else {
                        alert('Chyba: ' + result.error);
                    }
                } catch (error) {
                    alert('Chyba při odesílání: ' + error);
                }
            }
            
            // Initialize
            document.addEventListener('DOMContentLoaded', function() {
                document.getElementById('errorCount').addEventListener('input', validateErrors);
            });
        </script>
        <footer class="mt-4 py-3 text-center">
        <div class="container">
            <hr class="mb-3">
            <p class="mb-0 text-muted">
                <small>
                    Whitelist Bot | Made by 
                    <a href="https://github.com/koki26" target="_blank" class="text-decoration-none">koki26</a>
                    © 2025 - 2026
                </small>
            </p>
        </div>
    </footer>
    </body>
    </html>
    '''
    
    # Uložení šablon do složky templates
    os.makedirs('templates', exist_ok=True)
    
    with open('templates/home.html', 'w', encoding='utf-8') as f:
        f.write(home_template)
    
    with open('templates/dashboard.html', 'w', encoding='utf-8') as f:
        f.write(dashboard_template)

# =========================
# START
# =========================
if __name__ == "__main__":
    # Ověření konfigurace
    if not BOT_TOKEN:
        print("❌ Chybějící BOT_TOKEN!")
        exit(1)
    
    if not GUILD_ID:
        print("❌ Chybějící GUILD_ID!")
        exit(1)
    
    if not CLIENT_ID or not CLIENT_SECRET:
        print("⚠️  Pozor: Chybějící Discord OAuth2 credentials (CLIENT_ID, CLIENT_SECRET)")
        print("Webové rozhraní nebude fungovat správně!")
    
    # Vytvoření šablon
    setup_templates()
    
    # Spuštění Flask serveru v novém vlákně
    import threading
    
    def run_flask():
        app.run(host="0.0.0.0", port=PORT, debug=False, use_reloader=False)
    
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    print(f"🌐 Web server běží na portu {PORT}")
    
    # Spuštění Discord bota
    print("🤖 Spouštím Discord bota...")
    bot.run(BOT_TOKEN)