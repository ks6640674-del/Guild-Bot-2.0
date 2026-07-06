import os

class Config:
    # === YOUR GUILD ID (CHANGE THIS) ===
    GUILD_ID = os.getenv("GUILD_ID", "YOUR_GUILD_ID_HERE")
    BOT_COUNT = int(os.getenv("BOT_COUNT", "10"))
    
    # === INDIA SERVER ===
    SERVER = "IND"
    SERVER_ID = 4
    
    # === MATCH SETTINGS ===
    MATCHES_PER_BOT = 20  # Daily cap per bot
    CYCLE_DELAY = 60
    
    # === WEB DASHBOARD ===
    PORT = int(os.getenv("PORT", 5000))
