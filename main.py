import os
import sys
import json
import time
import random
import string
import hashlib
import requests
from flask import Flask, jsonify, request
from datetime import datetime

# ===== YOUR CONFIG =====
GUILD_ID = os.environ.get("GUILD_ID", "3034682198")
BOT_COUNT = int(os.environ.get("BOT_COUNT", "10"))
SERVER = "IND"

# ===== YOUR SIAMBHAU API KEYS =====
FFINFO_KEY = os.environ.get("FFINFO_KEY", "FFINFO-Free")
BIND_KEY = os.environ.get("BIND_KEY", "BIND-FREE")

# SiamBhau API Base
API_BASE = "http://siambhau69.eu.cc"

# Use /tmp for Vercel
BASE_DIR = "/tmp"
ACCOUNTS_FILE = os.path.join(BASE_DIR, "account_status.txt")
DEBUG_FILE = os.path.join(BASE_DIR, "debug_log.txt")

app = Flask(__name__)

def log_debug(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    try:
        with open(DEBUG_FILE, "a") as f:
            f.write(line + "\n")
    except:
        pass

def log_section(title):
    log_debug("")
    log_debug("="*60)
    log_debug(f"  {title}")
    log_debug("="*60)

# ===== ROUTES =====
@app.route("/")
def home():
    return f"""
     
# 🔥 FF Guild Glory Bot — India 🇮🇳

 
⚙️ **Guild ID:** {GUILD_ID} | **Bots:** {BOT_COUNT} | **Server:** {SERVER}

 
✅ FFINFO Key: SET | ✅ BIND Key: SET

 
<a href='/accounts'>📁 Account Status</a>

 
<a href='/debug'>📄 Debug Log</a>

 
<a href='/stats'>📊 Stats</a>

 
<a href='/run'>🚀 RUN BOT NOW</a>

 
<a href='/test-keys'>🔑 Test API Keys</a>

 
---

### ⚡ How To Use

1. Set your guild to **Auto Approve ON** (no level/rank requirements)
2. Click **Run Bot Now**
3. Bot generates guest accounts → gets JWT → joins guild
4. Check **Account Status** to see results

### 📌 Note

`FFINFO-Free` key works for: Free Fire Info, JWT Generate, Ban Check
`BIND-FREE` key works for: Bind Tools

For **Guild Join** you may need a key with `guild` access (contact @SiamBhau on Telegram)
    """

@app.route("/test-keys")
def test_keys():
    """Test both API keys against various endpoints"""
    results = {}
    
    # Test FFINFO key on jwtgenerate
    try:
        test_uid = "1000000000"
        test_pass = "TESTPASSWORD123"
        r = requests.get(f"{API_BASE}/jwtgenerate/generate", params={
            "uid": test_uid, "password": test_pass, "key": FFINFO_KEY
        }, timeout=10)
        results["jwtgenerate (FFINFO key)"] = {
            "status": r.status_code,
            "response": r.json()
        }
    except Exception as e:
        results["jwtgenerate (FFINFO key)"] = {"error": str(e)}
    
    # Test FFINFO key on bancheck
    try:
        r = requests.get(f"{API_BASE}/bancheck", params={
            "uid": test_uid, "region": SERVER, "key": FFINFO_KEY
        }, timeout=10)
        results["bancheck (FFINFO key)"] = {
            "status": r.status_code,
            "response": r.json()
        }
    except Exception as e:
        results["bancheck (FFINFO key)"] = {"error": str(e)}
    
    # Test FFINFO key on guild/info
    try:
        r = requests.get(f"{API_BASE}/guild/info", params={
            "clan_id": GUILD_ID, "key": FFINFO_KEY
        }, timeout=10)
        results["guild/info (FFINFO key)"] = {
            "status": r.status_code,
            "response": r.json()
        }
    except Exception as e:
        results["guild/info (FFINFO key)"] = {"error": str(e)}
    
    # Test FFINFO key on guild/join
    try:
        r = requests.get(f"{API_BASE}/guild/join", params={
            "clan_id": GUILD_ID, "uid": test_uid, "pass": test_pass, "key": FFINFO_KEY
        }, timeout=10)
        results["guild/join (FFINFO key)"] = {
            "status": r.status_code,
            "response": r.json()
        }
    except Exception as e:
        results["guild/join (FFINFO key)"] = {"error": str(e)}
    
    # Test BIND key on guild/join
    try:
        r = requests.get(f"{API_BASE}/guild/join", params={
            "clan_id": GUILD_ID, "uid": test_uid, "pass": test_pass, "key": BIND_KEY
        }, timeout=10)
        results["guild/join (BIND key)"] = {
            "status": r.status_code,
            "response": r.json()
        }
    except Exception as e:
        results["guild/join (BIND key)"] = {"error": str(e)}
    
    return jsonify(results)

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
    acc_count = 0
    joined = 0
    if os.path.exists(ACCOUNTS_FILE):
        with open(ACCOUNTS_FILE) as f:
            content = f.read()
            acc_count = content.count("ACCOUNT #")
            joined = content.count("Joined Guild: True")
    
    return jsonify({
        "guild_id": GUILD_ID,
        "bots": BOT_COUNT,
        "server": SERVER,
        "accounts_processed": acc_count,
        "joined_guild": joined,
        "ffinfo_key": FFINFO_KEY,
        "bind_key": BIND_KEY,
        "status": "idle"
    })

@app.route("/run")
def run_bot():
    engine = BotEngine()
    try:
        engine.run_bot()
        return jsonify({
            "status": "completed",
            "accounts": len(engine.accounts),
            "joined": sum(1 for a in engine.accounts if a["joined_guild"]),
            "message": "Finished. Check /accounts and /debug."
        })
    except Exception as e:
        log_debug(f"FATAL ERROR: {str(e)}")
        return jsonify({"status": "error", "error": str(e)}), 500


# ===== BOT ENGINE =====
class BotEngine:
    def __init__(self):
        self.accounts = []
    
    def siambhau_request(self, endpoint, params, key=None):
        """Make request to SiamBhau API with appropriate key"""
        if key is None:
            # Try FFINFO key first, fallback to BIND key
            params["key"] = FFINFO_KEY
        else:
            params["key"] = key
        
        url = f"{API_BASE}{endpoint}"
        try:
            r = requests.get(url, params=params, timeout=20)
            data = r.json()
            return data, r.status_code
        except Exception as e:
            return {"error": str(e)}, 500
    
    def get_jwt(self, uid, password):
        """Get JWT token via SiamBhau API using FFINFO key"""
        log_debug(f"  [JWT] Getting token for UID {uid}...")
        data, status = self.siambhau_request("/jwtgenerate/generate", {
            "uid": uid, "password": password
        }, key=FFINFO_KEY)
        
        if status == 200 and data.get("status") in ("live", "valid"):
            token = data.get("token")
            if token:
                log_debug(f"  [JWT] ✅ Token obtained ({token[:30]}...)")
                return token
        
        log_debug(f"  [JWT] ❌ Failed: {data}")
        return None
    
    def check_ban(self, uid):
        """Check if account is banned"""
        log_debug(f"  [BANCHECK] Checking UID {uid}...")
        data, status = self.siambhau_request("/bancheck", {
            "uid": uid, "region": SERVER
        }, key=FFINFO_KEY)
        
        if status == 200:
            banned = data.get("banned", False)
            info = data.get("message", "Unknown")
            log_debug(f"  [BANCHECK] {'BANNED' if banned else 'OK'} - {info}")
            return banned, info
        return False, "Could not check"
    
    def get_guild_info(self):
        """Get guild information"""
        log_debug(f"  [GUILD INFO] Fetching info for {GUILD_ID}...")
        data, status = self.siambhau_request("/guild/info", {
            "clan_id": GUILD_ID
        }, key=FFINFO_KEY)
        
        if status == 200:
            log_debug(f"  [GUILD INFO] ✅ {data.get('name', 'N/A')}")
            return data
        log_debug(f"  [GUILD INFO] ❌ {data}")
        return None
    
    def join_guild(self, uid, password, jwt):
        """Join guild using available keys"""
        log_debug(f"  [JOIN] Attempting to join guild {GUILD_ID}...")
        
        # Try with FFINFO key first (if it has guild access)
        if jwt:
            data, status = self.siambhau_request("/guild/join", {
                "clan_id": GUILD_ID, "jwt": jwt
            }, key=FFINFO_KEY)
        else:
            data, status = self.siambhau_request("/guild/join", {
                "clan_id": GUILD_ID, "uid": uid, "pass": password
            }, key=FFINFO_KEY)
        
        if status == 200 and data.get("success"):
            log_debug(f"  [JOIN] ✅ Joined guild! {data.get('message', '')}")
            return True, data.get("message", "Joined")
        
        # If FFINFO key failed, try BIND key
        log_debug(f"  [JOIN] FFINFO key failed, trying BIND key...")
        if jwt:
            data2, status2 = self.siambhau_request("/guild/join", {
                "clan_id": GUILD_ID, "jwt": jwt
            }, key=BIND_KEY)
        else:
            data2, status2 = self.siambhau_request("/guild/join", {
                "clan_id": GUILD_ID, "uid": uid, "pass": password
            }, key=BIND_KEY)
        
        if status2 == 200 and data2.get("success"):
            log_debug(f"  [JOIN] ✅ Joined guild with BIND key!")
            return True, data2.get("message", "Joined")
        
        error_msg = data.get("message") or data.get("error") or "Access denied"
        log_debug(f"  [JOIN] ❌ Failed: {error_msg}")
        log_debug(f"  [JOIN] 💡 Tip: You may need a key with 'guild' access from @SiamBhau")
        return False, error_msg
    
    def generate_guest(self, index):
        """Generate guest credentials (real ones need the FF app)"""
        uid = str(random.randint(1000000000, 9999999999))
        pw = ''.join(random.choices(string.ascii_uppercase + string.digits, k=32))
        name = f"Guest_{index}"
        return uid, pw, name
    
    def run_bot(self):
        log_section("FF GUILD GLORY BOT - STARTING")
        log_debug(f"Guild ID: {GUILD_ID}")
        log_debug(f"Bot Count: {BOT_COUNT}")
        log_debug(f"Server: {SERVER}")
        log_debug(f"FFINFO Key: {FFINFO_KEY}")
        log_debug(f"BIND Key: {BIND_KEY}")
        
        # First, check guild info
        log_section("STEP 0: CHECK GUILD INFO")
        guild_info = self.get_guild_info()
        if guild_info:
            log_debug(f"Guild Name: {guild_info.get('name', 'N/A')}")
            log_debug(f"Members: {guild_info.get('memberCount', 'N/A')}")
            log_debug(f"Level: {guild_info.get('level', 'N/A')}")
        
        self.accounts = []
        
        for i in range(BOT_COUNT):
            log_section(f"ACCOUNT {i+1}/{BOT_COUNT}")
            uid, pw, name = self.generate_guest(i+1)
            log_debug(f"UID: {uid}")
            
            # Get JWT
            jwt = self.get_jwt(uid, pw)
            
            # Check ban
            banned, ban_info = self.check_ban(uid)
            
            # Join guild
            joined = False
            join_msg = "Not attempted"
            if not banned:
                joined, join_msg = self.join_guild(uid, pw, jwt)
            else:
                log_debug(f"  [SKIP] Account is banned")
            
            self.accounts.append({
                "uid": uid,
                "password": pw,
                "name": name,
                "jwt": jwt[:40] + "..." if jwt else "N/A",
                "banned": banned,
                "ban_info": ban_info,
                "joined_guild": joined,
                "join_message": join_msg,
                "status": "BANNED" if banned else ("IN GUILD" if joined else "ACTIVE"),
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            
            self.write_status()
            time.sleep(1.5)
        
        self.write_status()
        
        joined_count = sum(1 for a in self.accounts if a["joined_guild"])
        banned_count = sum(1 for a in self.accounts if a["banned"])
        
        log_section("BOT COMPLETE - SUMMARY")
        log_debug(f"Total: {len(self.accounts)}")
        log_debug(f"Joined Guild: {joined_count}")
        log_debug(f"Banned: {banned_count}")
        log_debug(f"Check /accounts for full details")
    
    def write_status(self):
        with open(ACCOUNTS_FILE, "w") as f:
            f.write("="*70 + "\n")
            f.write("FREE FIRE GUILD GLORY BOT - ACCOUNT STATUS\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Guild ID: {GUILD_ID}\n")
            f.write(f"Server: {SERVER}\n")
            f.write(f"Total: {len(self.accounts)}\n")
            f.write("="*70 + "\n\n")
            
            for i, acc in enumerate(self.accounts, 1):
                f.write(f"ACCOUNT #{i}\n")
                for k, v in acc.items():
                    f.write(f"  {k}: {v}\n")
                f.write("-"*40 + "\n")
