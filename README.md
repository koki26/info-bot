# 📅 Discord Info Bot

Jednoduchý Discord bot, který automaticky spravuje informační kanály na tvém serveru.
Ukáže **aktuální den**, **datum** a **počet členů** na serveru. 🔥

---

## ✨ Funkce
- ✅ Automaticky vytvoří kategorii `📅 Info`
- 📌 Uvnitř kategorie udržuje **přesně 3 kanály**:
  - Den v týdnu (např. `📅 pondělí`)
  - Aktuální datum (např. `🗓️ 10-09-2025`)
  - Počet členů na serveru (např. `👥 128 lidí`)
- 🔄 Kanály se automaticky **aktualizují každou minutu**
- 🚫 Do kanálů se **nedá připojit** (slouží jen jako info)
- 🗑️ Bot smaže nadbytečné kanály → vždy zůstanou jen 3


---

## 🛠️ Instalace

1. Naklonuj si projekt nebo zkopíruj kód
   ```bash
   git clone https://github.com/koki26/info-bot.git
   cd info-bot
   ```
2. Nainstaluj potřebné knihovny

    ```bash
    pip install discord.py
    ```
3. Otevři main.py a nastav:


    - GUILD_ID = 123456789012345678  # ID tvého serveru
    - bot.run("TVŮJ_TOKEN")

4. Spusť bota

    ```bash
    python main.py
    ```

---

## ⚙️ Požadavky

    Python 3.8+
    discord.py


---

## 🎨 Ukázka
Kategorie bude vypadat takto:

📅 Info

┣ 📅 středa

┣ 🗓️ 10-09-2025

┗ 👥 128 lidí


---

## 👤 Autor
Vytvořil s láskou **Koki26** pro Saryho ❤️

---
