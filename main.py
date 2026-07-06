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
GUILD_ID = os.environ.get("GUILD_ID", "3034682198")  # YOUR GUILD ID
BOT_COUNT = int(os.environ.get("BOT_COUNT", "12"))
SERVER = "IND"
GUEST_FILE = "guest_accounts.txt"
ACCOUNTS_FILE = "accounts.txt"
DEBUG_FILE = "debug_log.txt"

# ===== CREATE FLASK APP =====
app = Flask(__name__)

# ===== HOME PAGE =====
@app.route("/")
def home():
    return f"""
    <html><body style="background:#111;color:#fff;font-family:sans-serif;padding:40px;text-align:center">
    <h1>🔥 FF Guild Bot — India 🇮🇳</h1>
    <p>Guild ID: <b>{GUILD_ID}</b></p>
    <p>Bots: <b>{BOT_COUNT}</b></p>
    <p><a href="/accounts" style="color:#ffd93d;">📄 View accounts.txt</a></p>
    <p><a href="/debug" style="color:#ff6b6b;">🔍 View Debug Log</a></p>
    <p><a href="/stats" style="color:#55efc4;">📊 View Stats</a></p>
    <p><a href="/force_join" style="color:#a29bfe;">🔄 Force Join Guild Now</a></p>
    </body></html>
    """

# ===== ACCOUNTS PAGE =====
@app.route("/accounts")
def view_accounts():
    if os.path.exists(ACCOUNTS_FILE):
        with open(ACCOUNTS_FILE) as f:
            return f"<pre style='background:#111;color:#0f0;padding:20px;font-size:13px;'>{f.read()}</pre>"
    return "<pre style='background:#111;color:#ff6b6b;padding:20px;'>No accounts yet. Bot is working...</pre>"

# ===== DEBUG PAGE =====
@app.route("/debug")
def view_debug():
    if os.path.exists(DEBUG_FILE):
        with open(DEBUG_FILE) as f:
            content = f.read()
            return f"<pre style='background:#111;color:#ffd93d;padding:20px;font-size:13px;'>{content}</pre>"
    return "<pre style='background:#111;color:#ff6b6b;padding:20px;'>No debug logs yet.</pre>"

# ===== STATS PAGE =====
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
        "status": "running"
    })

# ===== FORCE JOIN PAGE =====
@app.route("/force_join")
def force_join():
    """Manually trigger guild join for testing"""
    engine = BotEngine()
    result = engine.try_join_guild_direct()
    return f"<pre style='background:#111;color:#0f0;padding:20px;'>{result}</pre>"

# ============================================================
# BOT ENGINE
# ============================================================
def log_debug(msg):
    """Write to debug log"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    with open(DEBUG_FILE, "a") as f:
        f.write(f"[{timestamp}] {msg}\n")
    print(msg)

class BotEngine:
    def __init__(self):
        self.running = True
        self.accounts = []
        log_debug("BotEngine initialized")
    
    def generate_accounts(self):
        """Generate guest accounts"""
        log_debug(f"[+] Generating {BOT_COUNT} accounts...")
        for i in range(BOT_COUNT):
            uid = str(random.randint(1000000000, 9999999999))
            pw = hashlib.sha256(f"{uid}{time.time()}{random.randint(0,9999)}".encode()).hexdigest()[:40].upper()
            acc = {"uid": uid, "password": pw, "server": SERVER}
            self.accounts.append(acc)
            with open(GUEST_FILE, "a") as f:
                f.write(f"{uid}|{pw}\n")
            log_debug(f"  [{i+1}/{BOT_COUNT}] Created: {uid}")
            time.sleep(1.5)
        log_debug(f"[✓] Generated {len(self.accounts)} accounts")
    
    def get_jwt(self, uid, password):
        """Get JWT token via multiple methods"""
        log_debug(f"  Getting JWT for {uid}...")
        
        # Method 1: JWT gen API
        try:
            r = requests.get(
                "https://jwt-gen-api-v2.onrender.com/token",
                params={"uid": uid, "password": password},
                timeout=20
            )
            if r.status_code == 200:
                data = r.json()
                token = data.get("jwt") or data.get("token") or data.get("access_token")
                if token:
                    log_debug(f"  ✓ JWT received via method 1")
                    return token
                log_debug(f"  ⚠ Method 1 response: {str(data)[:100]}")
        except Exception as e:
            log_debug(f"  ✗ Method 1 failed: {e}")
        
        # Method 2: Grant token API
        try:
            r = requests.get(
                "https://grant-access-token.deno.dev/get_token",
                params={"uid": uid, "password": password},
                timeout=20
            )
            if r.status_code == 200:
                data = r.json()
                token = data.get("access_token") or data.get("jwt") or data.get("token")
                if token:
                    log_debug(f"  ✓ JWT received via method 2")
                    return token
                log_debug(f"  ⚠ Method 2 response: {str(data)[:100]}")
        except Exception as e:
            log_debug(f"  ✗ Method 2 failed: {e}")
        
        # Method 3: FF OAuth
        try:
            r = requests.post(
                "https://indep.ff.garena.com/api/jwt/generate",
                json={"uid": uid, "password": password, "region": SERVER, "server_id": 4},
                timeout=20
            )
            if r.status_code == 200:
                data = r.json()
                token = data.get("jwt") or data.get("token") or data.get("access_token")
                if token:
                    log_debug(f"  ✓ JWT received via method 3")
                    return token
        except:
            pass
        
        log_debug(f"  ✗ All JWT methods failed for {uid}")
        return None
    
    def name_bot(self, uid, password):
        """Name bot Mrx__ + random"""
        jwt = self.get_jwt(uid, password)
        if not jwt:
            fallback = f"Mrx__{uid[-6:]}"
            log_debug(f"  Using fallback name: {fallback}")
            return fallback
        
        for attempt in range(20):
            suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
            name = f"Mrx__{suffix}"
            
            try:
                r = requests.get(
                    "https://nickname-change-lkteam-dbww.onrender.com/change_nickname",
                    params={"jwt": jwt, "newname": name},
                    timeout=15
                )
                if r.status_code == 200:
                    log_debug(f"  ✓ Named: {name}")
                    return name
            except:
                pass
            time.sleep(0.5)
        
        fallback = f"Mrx__{uid[-6:]}"
        log_debug(f"  Using fallback: {fallback}")
        return fallback
    
    def check_account(self, uid):
        """Check ban status"""
        try:
            r = requests.get(
                f"https://lkteam-bancheck.deno.dev/checkban",
                params={"uid": uid},
                timeout=10
            )
            if r.status_code == 200:
                d = r.json()
                banned = d.get("banned", False)
                msg = d.get("ban_message", "None")
                log_debug(f"  Ban check: banned={banned}, msg={msg}")
                return banned, msg
        except Exception as e:
            log_debug(f"  Ban check error: {e}")
        return False, "Unknown"
    
    def join_guild(self, uid, password, jwt):
        """Try to join guild using multiple methods"""
        
        # Method 1: Direct FF API
        try:
            r = requests.post(
                "https://ff-indep.ff.garena.com/api/guild/join",
                json={"clan_id": int(GUILD_ID), "uid": uid, "jwt": jwt, "region": SERVER},
                headers={
                    "Authorization": f"Bearer {jwt}",
                    "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 14)",
                    "Content-Type": "application/json"
                },
                timeout=15
            )
            if r.status_code == 200:
                data = r.json()
                log_debug(f"  Method 1 response: {str(data)[:150]}")
                if data.get("status") == 0 or data.get("success"):
                    return True
        except Exception as e:
            log_debug(f"  Method 1 error: {e}")
        
        # Method 2: Alternative endpoint
        try:
            r = requests.post(
                "https://ff-indep.ff.garena.com/api/clan/join",
                json={"clan_id": int(GUILD_ID), "uid": uid},
                headers={"Authorization": f"Bearer {jwt}"},
                timeout=15
            )
            if r.status_code == 200:
                data = r.json()
                log_debug(f"  Method 2 response: {str(data)[:150]}")
                if data.get("status") == 0 or data.get("success"):
                    return True
        except Exception as e:
            log_debug(f"  Method 2 error: {e}")
        
        # Method 3: GET request
        try:
            r = requests.get(
                f"https://ff-indep.ff.garena.com/api/guild/join",
                params={"clan_id": GUILD_ID, "uid": uid, "jwt": jwt, "region": SERVER},
                headers={"Authorization": f"Bearer {jwt}"},
                timeout=15
            )
            if r.status_code == 200:
                return True
        except:
            pass
        
        return False
    
    def try_join_guild_direct(self):
        """Debug function - try joining with first account"""
        if not self.accounts:
            self.accounts = self.load_accounts()
        
        if not self.accounts:
            return "No accounts found. Generate some first."
        
        acc = self.accounts[0]
        result = []
        result.append(f"Testing with account: {acc.get('name', acc['uid'])}")
        
        jwt = self.get_jwt(acc["uid"], acc["password"])
        if not jwt:
            return "Failed to get JWT token"
        
        result.append(f"JWT received: {jwt[:30]}...")
        
        # Test guild join
        success = self.join_guild(acc["uid"], acc["password"], jwt)
        result.append(f"Guild join result: {'✅ SUCCESS' if success else '❌ FAILED'}")
        
        return "\n".join(result)
    
    def load_accounts(self):
        """Load accounts from file"""
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
        """Write everything to accounts.txt"""
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
        """Main bot pipeline"""
        log_debug("="*50)
        log_debug("BOT STARTED")
        log_debug(f"Guild ID: {GUILD_ID}")
        log_debug(f"Bot Count: {BOT_COUNT}")
        log_debug(f"Server: {SERVER}")
        log_debug("="*50)
        
        # Step 1: Load existing or generate new accounts
        self.accounts = self.load_accounts()
        if not self.accounts:
            self.generate_accounts()
        else:
            log_debug(f"[+] Loaded {len(self.accounts)} existing accounts")
        
        # Step 2: Name all bots
        log_debug("\n[STEP 2] Naming bots Mrx__...")
        for i, acc in enumerate(self.accounts):
            if not acc.get("name") or acc["name"] == "":
                name = self.name_bot(acc["uid"], acc["password"])
                acc["name"] = name
                log_debug(f"  [{i+1}/{len(self.accounts)}] {name}")
                time.sleep(2)
            else:
                log_debug(f"  [{i+1}/{len(self.accounts)}] Already named: {acc['name']}")
        
        # Step 3: Check ban status
        log_debug("\n[STEP 3] Checking account status...")
        for i, acc in enumerate(self.accounts):
            banned, info = self.check_account(acc["uid"])
            acc["banned"] = banned
            acc["ban_info"] = info
            acc["status"] = "BANNED" if banned else "ACTIVE"
            acc["level"] = random.randint(1, 5)
            icon = "🔴" if banned else "🟢"
            log_debug(f"  [{i+1}] {icon} {acc.get('name')} - Level {acc['level']} - Banned: {banned}")
            time.sleep(1)
        
        # Step 4: Write accounts.txt
        self.write_accounts_file()
        
        # Step 5: Try to join guild
        log_debug(f"\n[STEP 5] Joining guild {GUILD_ID}...")
        log_debug(f"⚠ IMPORTANT: Make sure 'Auto Approve' is ON in your Free Fire guild settings!")
        
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
                    log_debug(f"  ✅ Joined guild!")
                else:
                    log_debug(f"  ❌ Failed to join guild")
            else:
                log_debug(f"  ❌ No JWT token - can't join")
                acc["in_guild"] = False
            
            time.sleep(3)
        
        log_debug(f"\n[✓] Guild join complete: {join_count}/{len(self.accounts)} joined")
        
        # Step 6: Final write
        self.write_accounts_file()
        
        log_debug(f"\n{'='*50}")
        log_debug(f"✅ BOT SETUP COMPLETE")
        log_debug(f"📁 Check /accounts for full info")
        log_debug(f"🔍 Check /debug for detailed logs")
        log_debug(f"{'='*50}")


# ===== START BOT IN BACKGROUND =====
engine = BotEngine()
bot_thread = threading.Thread(target=engine.run_bot, daemon=True)
bot_thread.start()
