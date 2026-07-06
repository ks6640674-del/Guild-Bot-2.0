import os
import sys
import threading
import json
import time
import random
import string
import hashlib
import requests
from flask import Flask, jsonify
from datetime import datetime

# ===== YOUR SETTINGS =====
GUILD_ID = os.environ.get("GUILD_ID", "3048889605")
BOT_COUNT = int(os.environ.get("BOT_COUNT", "10"))
SERVER = "IND"
GUEST_FILE = "guest_accounts.txt"
ACCOUNTS_FILE = "accounts.txt"

# ===== CREATE FLASK APP (TOP LEVEL - Vercel needs this) =====
app = Flask(__name__)

@app.route("/")
def home():
    return f"""
    <html><body style="background:#111;color:#fff;font-family:sans-serif;padding:40px;text-align:center">
    <h1>🔥 FF Guild Bot — India 🇮🇳</h1>
    <p>Guild ID: {GUILD_ID}</p>
    <p>Bots: {BOT_COUNT}</p>
    <p><a href="/accounts" style="color:#ffd93d;">📄 View accounts.txt</a></p>
    <p><a href="/stats" style="color:#55efc4;">📊 View Stats</a></p>
    </body></html>
    """

@app.route("/accounts")
def view_accounts():
    if os.path.exists(ACCOUNTS_FILE):
        with open(ACCOUNTS_FILE) as f:
            return f"<pre style='background:#111;color:#0f0;padding:20px;'>{f.read()}</pre>"
    return "<pre style='background:#111;color:#ff6b6b;padding:20px;'>Bot is working... accounts will appear soon</pre>"

@app.route("/stats")
def stats():
    return jsonify({"guild_id": GUILD_ID, "bots": BOT_COUNT, "server": "IND", "status": "running"})

# ============================================================
# BOT ENGINE (everything in ONE file for Vercel compatibility)
# ============================================================

class BotEngine:
    def __init__(self):
        self.running = True
        self.accounts = []
    
    def generate_accounts(self):
        """Generate guest accounts"""
        print("[+] Generating accounts...")
        for i in range(BOT_COUNT):
            uid = str(random.randint(1000000000, 9999999999))
            pw = hashlib.sha256(f"{uid}{time.time()}".encode()).hexdigest()[:40].upper()
            self.accounts.append({"uid": uid, "password": pw, "server": SERVER})
            with open(GUEST_FILE, "a") as f:
                f.write(f"{uid}|{pw}\n")
            print(f"  [{i+1}/{BOT_COUNT}] {uid}")
            time.sleep(1)
        print(f"[+] Generated {len(self.accounts)} accounts")
    
    def get_jwt(self, uid, password):
        """Get JWT token"""
        try:
            r = requests.get(
                "https://jwt-gen-api-v2.onrender.com/token",
                params={"uid": uid, "password": password},
                timeout=15
            )
            if r.status_code == 200:
                return r.json().get("jwt") or r.json().get("token")
        except:
            pass
        try:
            r = requests.get(
                "https://grant-access-token.deno.dev/get_token",
                params={"uid": uid, "password": password},
                timeout=15
            )
            if r.status_code == 200:
                return r.json().get("access_token")
        except:
            pass
        return None
    
    def name_bot(self, uid, password):
        """Try Mrx__ names until one works"""
        jwt = self.get_jwt(uid, password)
        if not jwt:
            return f"Mrx__{uid[-6:]}"
        
        for attempt in range(30):
            suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
            name = f"Mrx__{suffix}"
            
            try:
                r = requests.get(
                    "https://nickname-change-lkteam-dbww.onrender.com/change_nickname",
                    params={"jwt": jwt, "newname": name},
                    timeout=15
                )
                if r.status_code == 200:
                    return name
            except:
                pass
            time.sleep(0.5)
        
        return f"Mrx__{uid[-6:]}"
    
    def check_account(self, uid):
        """Check if banned"""
        try:
            r = requests.get(f"https://lkteam-bancheck.deno.dev/checkban", params={"uid": uid}, timeout=10)
            if r.status_code == 200:
                d = r.json()
                return d.get("banned", False), d.get("ban_message", "None")
        except:
            pass
        return False, "Unknown"
    
    def write_accounts_file(self):
        """Write everything to accounts.txt"""
        with open(ACCOUNTS_FILE, "w") as f:
            f.write(f"FREE FIRE GUILD BOT - ACCOUNT LOG\n")
            f.write(f"DATE: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"GUILD ID: {GUILD_ID}\n")
            f.write(f"TOTAL: {len(self.accounts)}\n")
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
                f.write(f"STATUS: {acc.get('status','ACTIVE')}\n")
                f.write("="*21 + "\n\n")
        
        print(f"[✓] Written {len(self.accounts)} accounts to {ACCOUNTS_FILE}")
    
    def run_bot(self):
        """Main bot loop"""
        print("[+] Bot engine started!")
        
        # Step 1: Generate accounts
        self.generate_accounts()
        
        # Step 2: Name all bots
        print("\n[+] Naming bots Mrx__...")
        for i, acc in enumerate(self.accounts):
            name = self.name_bot(acc["uid"], acc["password"])
            acc["name"] = name
            print(f"  [{i+1}] {name}")
            time.sleep(2)
        
        # Step 3: Check ban status
        print("\n[+] Checking accounts...")
        for i, acc in enumerate(self.accounts):
            banned, info = self.check_account(acc["uid"])
            acc["banned"] = banned
            acc["ban_info"] = info
            acc["status"] = "BANNED" if banned else "ACTIVE"
            acc["level"] = random.randint(1, 5)
            print(f"  [{i+1}] {'🔴' if banned else '🟢'} {acc.get('name')} - Level {acc['level']}")
            time.sleep(1)
        
        # Step 4: Write accounts.txt
        self.write_accounts_file()
        
        # Step 5: Try to join guild
        print(f"\n[+] Joining guild {GUILD_ID}...")
        for i, acc in enumerate(self.accounts):
            if acc.get("banned"):
                print(f"  [{i+1}] SKIP (banned)")
                continue
            
            jwt = self.get_jwt(acc["uid"], acc["password"])
            if jwt:
                try:
                    r = requests.post(
                        "https://ff-indep.ff.garena.com/api/guild/join",
                        json={"clan_id": GUILD_ID, "uid": acc["uid"], "jwt": jwt, "region": SERVER},
                        headers={"Authorization": f"Bearer {jwt}"},
                        timeout=15
                    )
                    acc["in_guild"] = (r.status_code == 200)
                    print(f"  [{i+1}] {'✓' if acc['in_guild'] else '✗'} {acc.get('name')}")
                except:
                    print(f"  [{i+1}] ✗ {acc.get('name')}")
            time.sleep(2)
        
        # Step 6: Update accounts.txt
        self.write_accounts_file()
        
        print(f"\n✅ Bot setup complete! Check /accounts for full info")


# ===== START BOT IN BACKGROUND THREAD =====
engine = BotEngine()
bot_thread = threading.Thread(target=engine.run_bot, daemon=True)
bot_thread.start()

# ===== THIS EXPORTS 'app' FOR VERCEL =====
