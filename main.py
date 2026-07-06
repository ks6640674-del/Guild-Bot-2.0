#!/usr/bin/env python3
"""
FREE FIRE GUILD BOT — INDIA SERVER
100% AUTOMATIC
"""

import os
import sys
import threading
from flask import Flask, jsonify

# === SET YOUR GUILD ID HERE OR USE ENV VARIABLE ===
GUILD_ID = os.environ.get("GUILD_ID", "3048889605")  # CHANGE THIS NUMBER
BOT_COUNT = int(os.environ.get("BOT_COUNT", "10"))

os.environ["GUILD_ID"] = GUILD_ID
os.environ["BOT_COUNT"] = str(BOT_COUNT)

from auto_bot import AutoBot

# ===== CREATE FLASK APP AT TOP LEVEL (Vercel needs this) =====
app = Flask(__name__)

@app.route("/")
def home():
    return f"""
    <html><body style="background:#111;color:#fff;font-family:sans-serif;padding:40px;text-align:center">
    <h1>🔥 FF Guild Bot — India 🇮🇳</h1>
    <p>Guild ID: {GUILD_ID}</p>
    <p>Bots: {BOT_COUNT}</p>
    <p>Status: <span style="color:#55efc4;">RUNNING</span></p>
    <p><a href="/accounts" style="color:#ffd93d;">📄 View accounts.txt</a></p>
    <p><a href="/stats" style="color:#55efc4;">📊 View Stats</a></p>
    </body></html>
    """

@app.route("/accounts")
def view_accounts():
    if os.path.exists("accounts.txt"):
        with open("accounts.txt") as f:
            content = f.read()
            return f"<pre style='background:#111;color:#0f0;padding:20px;font-size:14px;'>{content}</pre>"
    return "<pre style='background:#111;color:#ff6b6b;padding:20px;'>No accounts generated yet. Bot is working...</pre>"

@app.route("/stats")
def stats():
    from auto_bot import GuestGenerator
    accounts = GuestGenerator.load_from_file()
    return jsonify({
        "total_accounts": len(accounts),
        "server": "IND",
        "guild_id": GUILD_ID,
        "status": "running",
        "bot_count": BOT_COUNT
    })

# ===== START BOT IN BACKGROUND =====
def start_bot():
    bot = AutoBot()
    bot.full_auto()

# Start bot in a background thread
bot_thread = threading.Thread(target=start_bot, daemon=True)
bot_thread.start()

# ===== THIS IS WHAT VERCEL NEEDS =====
# Vercel will use 'app' from this file automatically

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
