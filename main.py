#!/usr/bin/env python3
"""
FREE FIRE GUILD BOT — INDIA SERVER
100% AUTOMATIC. 
JUST SET GUILD_ID AND RUN.
"""

import os
import sys
import threading

# Set your guild ID here or via environment variable
os.environ["GUILD_ID"] = os.environ.get("GUILD_ID", "YOUR_GUILD_ID_HERE")
os.environ["BOT_COUNT"] = os.environ.get("BOT_COUNT", "10")

from auto_bot import AutoBot, create_app

if __name__ == "__main__":
    # Start bot in background
    bot = AutoBot()
    bot_thread = threading.Thread(target=bot.full_auto, daemon=True)
    bot_thread.start()
    
    # Start web dashboard
    app = create_app()
    port = int(os.environ.get("PORT", 5000))
    print(f"\n[+] Dashboard: http://0.0.0.0:{port}")
    print(f"[+] accounts.txt: http://0.0.0.0:{port}/accounts")
    app.run(host="0.0.0.0", port=port, debug=False)
