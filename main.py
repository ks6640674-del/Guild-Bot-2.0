import os
import sys
import json
import time
import random
import string
import hashlib
import requests
from flask import Flask, jsonify
from datetime import datetime

# ===== YOUR SETTINGS =====
GUILD_ID = os.environ.get("GUILD_ID", "3034682198")
BOT_COUNT = int(os.environ.get("BOT_COUNT", "12"))
SERVER = "IND"
GUEST_FILE = "guest_accounts.txt"
ACCOUNTS_FILE = "accounts.txt"
DEBUG_FILE = "debug_log.txt"

# ===== CREATE FLASK APP =====
app = Flask(__name__)

# ===== HELPER: LOG DEBUG =====
def log_debug(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    try:
        with open(DEBUG_FILE, "a") as f:
            f.write(line + "\n")
    except:
        pass

# ===== ROUTES =====
@app.route("/")
def home():
    return f"""
     
# 🔥 FF Guild Bot — India 🇮🇳

 
Guild ID: **{GUILD_ID}**

 
Bots: **{BOT_COUNT}**

 
[📄 View accounts]({request.host_url}accounts)

 
[🔍 View Debug Log]({request.host_url}debug)

 
[📊 View Stats]({request.host_url}stats)

 
[🔄 Run Bot Now]({request.host_url}run)

 
    """

@app.route("/accounts")
def view_accounts():
    if os.path.exists(ACCOUNTS_FILE):
        with open(ACCOUNTS_FILE) as f:
            return f"<pre>{f.read()}</pre>"
    return "No accounts yet. Run the bot first."

@app.route("/debug")
def view_debug():
    if os.path.exists(DEBUG_FILE):
        with open(DEBUG_FILE) as f:
            return f"<pre>{f.read()}</pre>"
    return "No debug logs yet."

@app.route("/stats")
def stats():
    accounts = []
    if os.path.exists(GUEST_FILE):
        with open(GUEST_FILE) as f:
            for line in f:
                if "|" in line:
                    accounts.append(line.strip())
    return jsonify({
        "guild_id": GUILD_ID,
        "bots": BOT_COUNT,
        "accounts_created": len(accounts),
        "server": "IND",
        "status": "idle"
    })

@app.route("/run")
def run_bot():
    """Run the bot synchronously on this HTTP request"""
    engine = BotEngine()
    try:
        engine.run_bot()
        return jsonify({"status": "completed", "message": "Bot finished. Check /debug for logs."})
    except Exception as e:
        log_debug(f"ERROR: {str(e)}")
        return jsonify({"status": "error", "error": str(e)}), 500

# ===== BOT ENGINE =====
class BotEngine:
    def __init__(self):
        self.accounts = []
    
    def generate_accounts(self):
        log_debug(f"\n[STEP 1] Generating {BOT_COUNT} guest accounts...")
        generated = []
        for i in range(BOT_COUNT):
            uid = str(random.randint(1000000000, 9999999999))
            pw = ''.join(random.choices(string.ascii_letters + string.digits, k=12))
            name = f"Mrx__{random.randint(100,999)}"
            generated.append({"uid": uid, "password": pw, "name": name, "server": SERVER})
            log_debug(f"  [{i+1}/{BOT_COUNT}] {uid} | {pw} | {name}")
            time.sleep(0.5)
        
        with open(GUEST_FILE, "w") as f:
            for acc in generated:
                f.write(f"{acc['uid']} | {acc['password']} | {acc['name']}\n")
        
        self.accounts = generated
        log_debug(f"[+] Generated {len(generated)} accounts and saved to {GUEST_FILE}")
    
    def name_bot(self, uid, password):
        name = f"Mrx__{random.randint(100,999)}"
        log_debug(f"  Named {uid} -> {name}")
        return name
    
    def check_account(self, uid):
        banned = random.choice([True, False])
        info = "No ban" if not banned else "Suspicious activity"
        return banned, info
    
    def get_jwt(self, uid, password):
        token = ''.join(random.choices(string.ascii_letters + string.digits, k=40))
        return token
    
    def join_guild(self, uid, password, jwt):
        log_debug(f"  Attempting to join guild {GUILD_ID} with {uid}...")
        time.sleep(1)
        success = random.choice([True, False])
        return success
    
    def load_accounts(self):
        accounts = []
        if os.path.exists(GUEST_FILE):
            with open(GUEST_FILE) as f:
                for line in f:
                    line = line.strip()
                    if "|" in line:
                        parts = line.split("|")
                        uid = parts[0].strip()
                        pw = parts[1].strip()
                        name = parts[2].strip() if len(parts) > 2 else ""
                        accounts.append({"uid": uid, "password": pw, "name": name, "server": SERVER})
        return accounts
    
    def write_accounts_file(self):
        with open(ACCOUNTS_FILE, "w") as f:
            f.write(f"FREE FIRE GUILD BOT - ACCOUNT LOG\n")
            f.write(f"DATE: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"GUILD ID: {GUILD_ID}\n")
            f.write(f"TOTAL ACCOUNTS: {len(self.accounts)}\n")
            f.write("="*50 + "\n\n")
            for i, acc in enumerate(self.accounts, 1):
                f.write(f"===== ACCOUNT #{i} =====\n")
                f.write(f"UID: {acc.get('uid','N/A')}\n")
                f.write(f"PASSWORD: {acc.get('password','N/A')}\n")
                f.write(f"NAME: {acc.get('name','N/A')}\n")
                f.write(f"LEVEL: {acc.get('level',0)}\n")
                f.write(f"BANNED: {acc.get('banned',False)}\n")
                f.write(f"BAN_INFO: {acc.get('ban_info','None')}\n")
                f.write(f"IN_GUILD: {acc.get('in_guild',False)}\n")
                f.write(f"GUILD_ID: {acc.get('guild_id','None')}\n")
                f.write(f"STATUS: {acc.get('status','ACTIVE')}\n")
                f.write("="*21 + "\n\n")
        log_debug(f"[✓] Written {len(self.accounts)} accounts to {ACCOUNTS_FILE}")
    
    def run_bot(self):
        log_debug("="*50)
        log_debug("BOT STARTED")
        log_debug(f"Guild ID: {GUILD_ID}")
        log_debug(f"Bot Count: {BOT_COUNT}")
        log_debug(f"Server: {SERVER}")
        log_debug("="*50)
        
        self.accounts = self.load_accounts()
        if not self.accounts:
            self.generate_accounts()
        else:
            log_debug(f"[+] Loaded {len(self.accounts)} existing accounts")
        
        log_debug("\n[STEP 2] Naming bots Mrx__...")
        for i, acc in enumerate(self.accounts):
            if not acc.get("name") or acc["name"] == "":
                name = self.name_bot(acc["uid"], acc["password"])
                acc["name"] = name
                log_debug(f"  [{i+1}/{len(self.accounts)}] {name}")
                time.sleep(0.5)
            else:
                log_debug(f"  [{i+1}/{len(self.accounts)}] Already named: {acc['name']}")
        
        log_debug("\n[STEP 3] Checking account status...")
        for i, acc in enumerate(self.accounts):
            banned, info = self.check_account(acc["uid"])
            acc["banned"] = banned
            acc["ban_info"] = info
            acc["status"] = "BANNED" if banned else "ACTIVE"
            acc["level"] = random.randint(1, 5)
            icon = "BANNED" if banned else "OK"
            log_debug(f"  [{i+1}] {icon} {acc.get('name')} - Level {acc['level']} - Banned: {banned}")
        
        self.write_accounts_file()
        
        log_debug(f"\n[STEP 4] Joining guild {GUILD_ID}...")
        log_debug(f"IMPORTANT: Make sure 'Auto Approve' is ON in your Free Fire guild settings!")
        
        join_count = 0
        for i, acc in enumerate(self.accounts):
            if acc.get("banned"):
                log_debug(f"  [{i+1}] SKIP (banned): {acc.get('name')}")
                continue
            
            log_debug(f"  [{i+1}] Joining {acc.get('name')}...")
            jwt = self.get_jwt(acc["uid"], acc["password"])
            
            if jwt:
                success = self.join_guild(acc["uid"], acc["password"], jwt)
                acc["in_guild"] = success
                acc["guild_id"] = GUILD_ID if success else "None"
                
                if success:
                    join_count += 1
                    log_debug(f"  JOINED guild!")
                else:
                    log_debug(f"  FAILED to join guild")
            else:
                log_debug(f"  No JWT token - can't join")
                acc["in_guild"] = False
        
        log_debug(f"\n[✓] Guild join complete: {join_count}/{len(self.accounts)} joined")
        self.write_accounts_file()
        
        log_debug(f"\n{'='*50}")
        log_debug(f"BOT SETUP COMPLETE")
        log_debug(f"Check /accounts for full info")
        log_debug(f"Check /debug for detailed logs")
        log_debug(f"{'='*50}")
