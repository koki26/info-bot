# 📅 Discord Info & Whitelist Bot

Moderní Discord bot, který **automaticky spravuje informační kanály**
a zároveň poskytuje **whitelist systém přes slash příkazy**.

Bot zobrazuje **aktuální den, datum a počet členů** a umožňuje
spravovat whitelist přehledně a bezpečně. 🚀

---

## ✨ Funkce

### 📅 Info kanály
- ✅ Automaticky vytvoří kategorii `📅 Info`
- 📌 Udržuje **přesně 3 hlasové kanály**:
  - 📅 Aktuální den v týdnu (česky)
  - 🗓️ Aktuální datum
  - 👥 Počet členů na serveru
- 🔄 Automatická aktualizace **každou minutu**
- 🚫 Do kanálů se **nelze připojit** (slouží pouze jako informace)
- 🗑️ Nadbytečné kanály jsou automaticky odstraněny

---

### 🤖 Slash příkazy
- `/help` – zobrazí nápovědu k příkazům
- `/whitelist` – správa whitelistu hráčů

---

### 📝 Whitelist systém
- ➕ Přidání hráče na whitelist
- ❌ Označení hráče jako „neprošel“
- 🎭 Automatické přidání **Whitelist role**
- 🔐 Pouze pro uživatele s rolí **Whitelist Adder**
- 📢 Výsledky jsou odesílány do určeného kanálu
- 🎨 Přehledné embed zprávy s obrázky (Možnost upravit v kódu)

---

### 🔐 Bezpečnost
- 🔑 Token a ID serveru jsou načítány z `.env` souboru
- 🚫 Žádné citlivé údaje nejsou přímo v kódu

---

## 🛠️ Instalace

### 1️⃣ Klonování projektu
```bash
git clone https://github.com/koki26/info-bot.git
cd info-bot
````

---

### 2️⃣ Instalace závislostí

```bash
pip install -r requirements.txt
```

---

### 3️⃣ upravení `.env` souboru

V kořenové složce uprav soubor `.env`:

```env
GUILD_ID=123456789012345678
BOT_TOKEN=TVUJ_DISCORD_BOT_TOKEN
```


---

### 4️⃣ Spuštění bota

```bash
python main.py
```

---

## ⚙️ Požadavky

* Python **3.8+**
* `discord.py`
* `python-dotenv`

---

## 🎨 Ukázka

Kategorie na serveru:

```
📅 Info
┣ 📅 středa
┣ 🗓️ 10-09-2025
┗ 👥 128 lidí
```

---

## 👤 Autor

Vytvořil s láskou **Koki26** ❤️
Pro Saryho.

---

