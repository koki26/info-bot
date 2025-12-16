# Whitelist Discord Bot s Webovým Rozhraním 🤖🌐

Kompletní Discord bot pro správu whitelistu s webovým admin panelem. Obsahuje automatické info kanály, slash commands a moderní webové rozhraní pro správu whitelistu.

![Python](https://img.shields.io/badge/Python-3.8+-blue)
![Discord.py](https://img.shields.io/badge/Discord.py-2.0+-purple)
![Flask](https://img.shields.io/badge/Flask-2.0+-green)

## 📋 Obsah
- [Funkce](#-funkce)
- [Instalace - Lokální vývoj](#-instalace---lokální-vývoj)
- [Deploy na Render.com](#%EF%B8%8F-deploy-na-rendercom)
- [Konfigurace](#%EF%B8%8F-konfigurace)
- [Použití](#-použití)
- [Podpora](#-kontakt-a-podpora)

## ✨ Funkce

### 🤖 Discord Bot
- **Automatické info kanály** - zobrazují den, datum a počet členů
- **Slash commands** - `/whitelist`, `/help`
- **Automatické role** - přidává whitelist role po schválení
- **Oznámení** - posílá embed zprávy do výsledného kanálu
- **České názvy dní** - lokalizované pro české uživatele

### 🌐 Webové rozhraní
- **Discord OAuth2 přihlášení** - bezpečné přihlášení přes Discord
- **Kontrola oprávnění** - pouze uživatelé s admin rolí
- **Dashboard** - přehled všech členů bez whitelist role
- **Interaktivní UI** - počítadlo chyb s validací
- **Automatické schvalování** - nad nastavený počet chyb nelze schválit
- **Responsive design** - funguje na mobilech i počítačích

## 🚀 Instalace - Lokální vývoj

### 1. Předpoklady
- Python 3.8 nebo vyšší
- Discord účet s vlastním serverem

### 2. Klonování a nastavení
```bash
# Naklonuj repository
git clone https://github.com/vaše-username/info-bot.git
cd info-bot

# Vytvoř virtuální prostředí
python -m venv venv

# Aktivuj virtuální prostředí
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# Nainstaluj závislosti
pip install -r requirements.txt
```

### 3. Konfigurace `.env` souboru
Vytvoř nebo uprav soubor `.env` v kořenové složce:

```env
# ========================================
# DISCORD BOT CONFIG
# ========================================
BOT_TOKEN=tvůj_discord_bot_token_zde
GUILD_ID=1415779866559156274  # ID tvého Discord serveru
PORT=10000  # Port pro web server (Render automaticky nastaví)

# ========================================
# DISCORD OAUTH2 (pro webové přihlášení)
# ========================================
DISCORD_CLIENT_ID=123456789012345678  # Tvůj Discord Application ID
DISCORD_CLIENT_SECRET=tvůj_discord_client_secret_zde
REDIRECT_URI=http://localhost:10000/callback  # Pro lokální vývoj
# REDIRECT_URI=https://tvuj-bot.onrender.com/callback  # Pro produkci na Render

# ========================================
# WHITELIST CONFIG
# ========================================
MAX_ERRORS_ALLOWED=3  # Maximální počet chyb pro schválení

# ========================================
# DISCORD ROLE IDs (nahraď vlastními ID)
# ========================================
WL_ROLE_ID=vaše_whitelist_role_id_zde     # Role pro whitelistované hráče
ADDER_ROLE_ID=vaše_admin_role_id_zde      # Role pro adminy (mohou spravovat whitelist)
RESULTS_CHANNEL_ID=vaše_kanál_id_zde      # Kanál pro výsledky (#wl-vysledky nebo podobně)

# ========================================
# SECURITY
# ========================================
SECRET_KEY=tvůj_náhodný_bezpečný_klíč_zde
```

**Jak získat jednotlivé hodnoty:**
- **BOT_TOKEN:** [Discord Developer Portal → Aplikace → Bot → Reset Token](https://discord.com/developers/applications)
- **GUILD_ID:** Discord → Zapnout Developer Mode → Pravý klik na server → Copy ID
- **Role IDs:** Discord → Developer Mode → Pravý klik na roli/kanál → Copy ID
- **DISCORD_CLIENT_ID/CLIENT_SECRET:** Discord Developer Portal → OAuth2 → General
- **SECRET_KEY:** Spusť `python -c "import secrets; print(secrets.token_hex(32))"`

### 4. Nastavení Discord aplikace
1. Na [Discord Developer Portal](https://discord.com/developers/applications):
2. V **OAuth2 → Redirects** přidej: `http://localhost:10000/callback` (a později i Render URL)
3. V **Bot → Privileged Gateway Intents** zapni:
   - ✅ PRESENCE INTENT
   - ✅ SERVER MEMBERS INTENT  
   - ✅ MESSAGE CONTENT INTENT

### 5. Spuštění
```bash
python main.py
```

Bot bude dostupný na:
- Webové rozhraní: http://localhost:10000
- Discord bot: Online na vašem serveru

## ☁️ Deploy na Render.com

### 1. Příprava repozitáře
```bash
# Pokud ještě nemáš soubory na GitHubu:
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/vaše-username/info-bot.git
git push -u origin main
```

### 2. Vytvoření aplikace na Render
1. Jdi na [render.com](https://render.com)
2. Klikni **New +** → **Web Service**
3. Připoj své GitHub repository
4. Vyplň konfiguraci:
   - **Name:** `váš-název-botu` (např. `my-whitelist-bot`)
   - **Environment:** `Python 3`
   - **Region:** `Frankfurt` (nebo nejbližší)
   - **Branch:** `main`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python main.py`

### 3. Nastavení Environment Variables na Render
V sekci **Environment** přidej tyto proměnné (nahraď hodnoty vlastními):

| Klíč | Hodnota | Popis |
|------|---------|-------|
| `BOT_TOKEN` | `tvůj_discord_bot_token` | **[POVINNÉ]** Získat z Discord Developer Portal |
| `GUILD_ID` | `id_tvého_serveru` | Pravý klik na váš server → Copy ID |
| `DISCORD_CLIENT_ID` | `tvůj_client_id` | **[POVINNÉ]** Získat z Discord OAuth2 |
| `DISCORD_CLIENT_SECRET` | `tvůj_client_secret` | **[POVINNÉ]** Získat z Discord OAuth2 |
| `REDIRECT_URI` | `https://váš-bot.onrender.com/callback` | Uprav podle názvu aplikace |
| `MAX_ERRORS_ALLOWED` | `3` | Nastav podle potřeby |
| `WL_ROLE_ID` | `id_whitelist_role` | ID role pro whitelistované hráče |
| `ADDER_ROLE_ID` | `id_admin_role` | ID role pro správce whitelistu |
| `RESULTS_CHANNEL_ID` | `id_výsledkového_kanálu` | Kanál pro oznámení výsledků |
| `SECRET_KEY` | `náhodný_klíč_64_znaků` | **[POVINNÉ]** Vygeneruj pomocí příkazu |
| `PORT` | `10000` | Port pro web server |

**Generování SECRET_KEY:**
```bash
# Na Windows:
python -c "import secrets; print(secrets.token_hex(32))"

# Na Mac/Linux:
python3 -c "import secrets; print(secrets.token_hex(32))"
```

### 4. Aktualizace Discord OAuth2
1. Na Discord Developer Portal v **OAuth2 → Redirects** přidej:
   ```
   https://váš-bot.onrender.com/callback
   ```
   (nahraď `váš-bot` skutečným názvem tvé aplikace na Render)

2. V **OAuth2 → General**:
   - Zkopíruj Client ID → vlož jako `DISCORD_CLIENT_ID` na Render
   - Zkopíruj Client Secret → vlož jako `DISCORD_CLIENT_SECRET` na Render

### 5. Deploy a testování
1. Klikni **Create Web Service**
2. Počkej na dokončení deploye (2-5 minut)
3. Zkopíruj URL aplikace z Render dashboardu
4. Otevři URL v prohlížeči → měla by se zobrazit úvodní stránka

### 6. Přidání bota na server
1. Na Discord Developer Portal → OAuth2 → URL Generator:
   - Scopes: `bot`, `applications.commands`
   - Bot Permissions: `Manage Roles`, `Read Messages`, `Send Messages`, `View Channels`
2. Použij vygenerovaný URL pro přidání bota na váš server
3. **Důležité:** Přesuň roli bota nad whitelist role v nastavení serveru

## ⚙️ Konfigurace

### Nastavení rolí a kanálů
- **WL_ROLE_ID:** Role, která se přiřadí hráčům po schválení whitelistu
- **ADDER_ROLE_ID:** Role, která umožňuje přístup k webovému admin panelu
- **RESULTS_CHANNEL_ID:** Kanál, kam se posílají oznámení o výsledcích whitelistu

### Info kanály
- Kategorie: `📅 Info` (vytvoří se automaticky)
- Kanály: Den v týdnu, datum, počet členů
- Aktualizace: Každou minutu

## 🎮 Použití

### Discord commands
```
/help - Zobrazí nápovědu
/whitelist [hráč] [stav] [chyby] - Přidá hráče na whitelist
```

### Webové rozhraní
1. Přejdi na URL z Render (nebo http://localhost:10000 lokálně)
2. Klikni "Přihlásit se přes Discord"
3. Přihlaš se pomocí Discord účtu
4. **Musíš mít správnou admin roli na serveru**
5. Dashboard zobrazí všechny čekající hráče
6. Klikni na hráče → nastav počet chyb → schval/zamítni

### Pracovní postup
1. Hráč se přihlásí na Discord server
2. Admin otevře webové rozhraní
3. Vybere hráče ze seznamu čekajících
4. Nastaví počet chyb (0-MAX_ERRORS_ALLOWED)
5. Klikne "Prošel" nebo "Neprošel"
6. Bot automaticky:
   - Přidá whitelist roli (pokud prošel)
   - Pošle oznámení do výsledného kanálu
   - Aktualizuje seznam čekajících

## ❌ Řešení problémů

### Bot se nespustí
```bash
# Chyba: Missing BOT_TOKEN
# Řešení: Zkontroluj .env soubor nebo Environment Variables na Render
```

### Webové přihlášení nefunguje
```bash
# Chyba: Invalid redirect_uri
# Řešení: Přidej URL do Discord OAuth2 Redirects na obou místech
# Lokální: http://localhost:10000/callback
# Render: https://váš-bot.onrender.com/callback
```

### Role se nepřidává
```bash
# Chyba: Missing Permissions
# Řešení: Přesuň roli bota nad whitelist role v nastavení serveru
# Server Settings → Roles → Přesuň bot roli nahoru
```

### Info kanály se nevytvářejí
```bash
# Chyba: Bot nemá oprávnění spravovat kanály
# Řešení: Přidej botovi roli s oprávněním "Manage Channels"
```

## 📞 Kontakt a podpora

### Potřebuješ pomoc?
1. Zkontroluj, zda máš správně nastavené:
   - BOT_TOKEN na Render/Discord Developer Portal
   - OAuth2 Redirect URLs na obou místech
   - Role pozice bota na serveru
2. Prohlédni si logy na Render Dashboard
3. Otevři Issue na GitHubu

---