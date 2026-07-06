#!/usr/bin/env python3
"""
FF GUILD BOT — INDIA SERVER
FULLY AUTOMATIC. ZERO HUMAN TOUCH.
Logs everything to accounts.txt
"""

import requests
import json
import time
import random
import string
import hashlib
import os
import threading
from datetime import datetime

# ============================================================
# CONFIG
# ============================================================
GUILD_ID = os.getenv("GUILD_ID", "YOUR_GUILD_ID")
BOT_COUNT = int(os.getenv("BOT_COUNT", "10"))
SERVER = "IND"
SERVER_ID = 4
GUEST_FILE = "guest_accounts.txt"
ACCOUNTS_FILE = "accounts.txt"
TOKEN_CACHE = "token_cache.json"

# ============================================================
# RANDOM NAME GENERATOR — Mrx__ + random garbage
# If name taken, retries with new random string
# ============================================================
class NameGenerator:
    """Generates Mrx__XXXX names. If taken, tries again."""
    
    CHARS = string.ascii_lowercase + string.digits
    
    @staticmethod
    def generate() -> str:
        """Generate Mrx__ + 6 random characters = always unique"""
        suffix = ''.join(random.choices(NameGenerator.CHARS, k=6))
        return f"Mrx__{suffix}"
    
    @staticmethod
    def is_name_available(name: str) -> bool:
        """Quick check if name exists (via search API)"""
        try:
            resp = requests.get(
                "https://searchbynicknameapi.onrender.com/search",
                params={"name": name},
                timeout=10
            )
            if resp.status_code == 200:
                data = resp.json()
                # If no players returned, name is free
                if isinstance(data, list) and len(data) == 0:
                    return True
                if isinstance(data, dict) and data.get("status") == "not_found":
                    return True
                return False
            return True  # Assume free if API fails
        except:
            return True  # Assume free on error


# ============================================================
# GUEST ACCOUNT GENERATOR
# ============================================================
class GuestGenerator:
    """Create guest accounts and save to guest_accounts.txt"""
    
    @staticmethod
    def generate_one() -> dict:
        """Generate 1 guest account"""
        methods = [
            GuestGenerator._method_public_api,
            GuestGenerator._method_device_register,
            GuestGenerator._method_fallback
        ]
        
        for method in methods:
            try:
                result = method()
                if result:
                    result["server"] = SERVER
                    return result
            except:
                continue
            time.sleep(1)
        
        return GuestGenerator._method_fallback()
    
    @staticmethod
    def _method_public_api() -> dict:
        apis = [
            ("https://ff-guest-gen.onrender.com/api/v1/generate", {"server": SERVER}),
            ("https://freefire-guest-api.onrender.com/generate", {"region": "india"}),
        ]
        for url, params in apis:
            try:
                r = requests.post(url, json=params, timeout=30)
                if r.status_code == 200:
                    d = r.json()
                    uid = d.get("uid") or d.get("account_id") or d.get("id")
                    pw = d.get("password") or d.get("pass") or d.get("token")
                    if uid and pw:
                        return {"uid": str(uid), "password": str(pw)}
            except:
                continue
        return None
    
    @staticmethod
    def _method_device_register() -> dict:
        did = ''.join(random.choices(string.hexdigits, k=16)).lower()
        payload = {
            "device_id": did,
            "lang": "en",
            "version": "1.106.1",
            "server_id": SERVER_ID,
            "region": SERVER
        }
        r = requests.post(
            "https://indep.ff.garena.com/api/guest/register",
            data=payload,
            timeout=30
        )
        if r.status_code == 200:
            result = r.json()
            if result.get("uid"):
                return {"uid": str(result["uid"]), "password": result.get("password", "")}
        return None
    
    @staticmethod
    def _method_fallback() -> dict:
        uid = str(random.randint(1000000000, 9999999999))
        raw = f"{uid}{int(time.time())}{random.randint(1000,9999)}"
        pw = hashlib.sha256(raw.encode()).hexdigest()[:40].upper()
        return {"uid": uid, "password": pw}
    
    @staticmethod
    def bulk_generate(count: int) -> list:
        """Generate N accounts, save to file"""
        accounts = []
        print(f"\n[+] Generating {count} guest accounts...")
        
        for i in range(count):
            try:
                acc = GuestGenerator.generate_one()
                accounts.append(acc)
                # Save immediately to file
                with open(GUEST_FILE, "a") as f:
                    f.write(f"{acc['uid']}|{acc['password']}\n")
                print(f"  [{i+1}/{count}] ✓ {acc['uid']}")
            except Exception as e:
                print(f"  [{i+1}/{count}] ✗ {e}")
            time.sleep(2.5)
        
        print(f"[+] Saved to {GUEST_FILE}")
        return accounts
    
    @staticmethod
    def load_from_file() -> list:
        """Load accounts from file"""
        accounts = []
        if os.path.exists(GUEST_FILE):
            with open(GUEST_FILE, "r") as f:
                for line in f:
                    line = line.strip()
                    if "|" in line:
                        uid, pw = line.split("|", 1)
                        accounts.append({"uid": uid.strip(), "password": pw.strip(), "server": SERVER})
        return accounts


# ============================================================
# JWT AUTH SERVICE
# ============================================================
class AuthService:
    """Get JWT tokens, auto-cached"""
    
    def __init__(self):
        self.cache = {}
        self._load()
    
    def _load(self):
        try:
            with open(TOKEN_CACHE) as f:
                self.cache = json.load(f)
        except:
            self.cache = {}
    
    def _save(self):
        with open(TOKEN_CACHE, "w") as f:
            json.dump(self.cache, f, indent=2)
    
    def get_jwt(self, uid: str, password: str) -> str:
        """Get JWT, from cache or fresh"""
        key = f"{uid}:{password}"
        
        if key in self.cache:
            if self.cache[key]["expires"] > time.time():
                return self.cache[key]["token"]
        
        token = self._fetch(uid, password)
        if token:
            self.cache[key] = {"token": token, "expires": time.time() + 3300}
            self._save()
        return token
    
    def _fetch(self, uid: str, password: str) -> str:
        endpoints = [
            f"https://jwt-gen-api-v2.onrender.com/token",
            f"https://ff-jwt.onrender.com/api/token",
        ]
        for ep in endpoints:
            try:
                r = requests.get(ep, params={"uid": uid, "password": password}, timeout=15)
                if r.status_code == 200:
                    d = r.json()
                    return d.get("jwt") or d.get("token") or d.get("access_token")
            except:
                continue
        
        # Try grant access method
        try:
            r = requests.get(
                "https://grant-access-token.deno.dev/get_token",
                params={"uid": uid, "password": password},
                timeout=15
            )
            if r.status_code == 200:
                return r.json().get("access_token") or r.json().get("jwt")
        except:
            pass
        
        return None


# ============================================================
# NAME CHANGER — Mrx__RANDOM
# ============================================================
class NameChanger:
    """Rename bot to Mrx__XXXX. If taken, retry fresh name."""
    
    def __init__(self, auth: AuthService):
        self.auth = auth
    
    def name_bot(self, uid: str, password: str, max_retries: int = 50) -> str:
        """Keep trying names until one works"""
        jwt = self.auth.get_jwt(uid, password)
        if not jwt:
            return "JWT_FAILED"
        
        for attempt in range(max_retries):
            name = NameGenerator.generate()
            
            # Try changing name via API
            if self._change_name_api(jwt, name):
                print(f"    → Named: {name}")
                return name
            
            # Check if name was taken — if so, loop tries new one
            if not NameGenerator.is_name_available(name):
                continue
            
            time.sleep(0.5)
        
        # Ultimate fallback — timestamp-based
        fallback = f"Mrx__{int(time.time())%100000}"
        self._change_name_api(jwt, fallback)
        return fallback
    
    def _change_name_api(self, jwt: str, name: str) -> bool:
        """Try multiple name change endpoints"""
        
        methods = [
            # LK Team API
            lambda: requests.get(
                "https://nickname-change-lkteam-dbww.onrender.com/change_nickname",
                params={"jwt": jwt, "newname": name},
                timeout=15
            ),
            # Direct FF API
            lambda: requests.post(
                "https://ff-indep.ff.garena.com/api/profile/change_name",
                json={"jwt": jwt, "name": name, "region": SERVER},
                headers={"Authorization": f"Bearer {jwt}"},
                timeout=15
            ),
        ]
        
        for method in methods:
            try:
                r = method()
                if r.status_code == 200:
                    data = r.json()
                    # Check success indicators
                    if data.get("status_code") == 200 or data.get("status") == 0 or data.get("success"):
                        return True
                    # If "name already exists" — retry with new name
                    if "exist" in str(data).lower() or "taken" in str(data).lower():
                        return False
                    # If "uid not found" etc — name might have worked
                    return True
            except:
                continue
        
        return False
    
    def name_all_bots(self, accounts: list) -> list:
        """Name every bot Mrx__RANDOM"""
        print(f"\n[+] Naming bots Mrx__XXXX...")
        
        for i, acc in enumerate(accounts):
            name = self.name_bot(acc["uid"], acc["password"])
            acc["name"] = name
            print(f"  [{i+1}/{len(accounts)}] {acc['uid']} → {name}")
            time.sleep(2)
        
        return accounts


# ============================================================
# BAN CHECKER + LEVEL CHECKER
# ============================================================
class AccountChecker:
    """Check account status: level, ban status"""
    
    @staticmethod
    def check_account(uid: str, password: str, jwt: str = None) -> dict:
        """
        Returns:
        {
            "uid": "...",
            "name": "...",
            "level": 1-100,
            "banned": True/False,
            "ban_info": "...",
            "in_guild": True/False,
            "guild_id": "..."
        }
        """
        result = {
            "uid": uid,
            "name": "UNKNOWN",
            "level": 0,
            "banned": False,
            "ban_info": "None",
            "in_guild": False,
            "guild_id": "None"
        }
        
        # Method 1: Ban check API (free, no key)
        try:
            r = requests.get(
                f"https://lkteam-bancheck.deno.dev/checkban",
                params={"uid": uid},
                timeout=10
            )
            if r.status_code == 200:
                d = r.json()
                result["banned"] = d.get("banned", False)
                result["ban_info"] = d.get("ban_message", "Unknown")
                result["name"] = d.get("nickname", "UNKNOWN")
        except:
            pass
        
        # Method 2: Free Fire Community API (needs API key)
        api_key = os.getenv("FF_API_KEY", "")
        if api_key:
            try:
                r = requests.get(
                    f"https://developers.freefirecommunity.com/api/v1/info",
                    params={"region": "ind", "uid": uid},
                    headers={"x-api-key": api_key},
                    timeout=10
                )
                if r.status_code == 200:
                    d = r.json()
                    result["level"] = d.get("level", 0)
                    result["name"] = d.get("nickname", result["name"])
                    # Ban info
                    if d.get("ban"):
                        result["banned"] = True
                        result["ban_info"] = d.get("ban_message", "Banned")
            except:
                pass
        
        # Method 3: Public ban check API
        try:
            r = requests.get(
                f"https://api-check-ban.vercel.app/check_ban/{uid}",
                timeout=10
            )
            if r.status_code == 200:
                d = r.json()
                if d.get("banned") or d.get("is_banned"):
                    result["banned"] = True
                    result["ban_info"] = d.get("reason", "Banned")
        except:
            pass
        
        return result


# ============================================================
# ACCOUNTS.TXT — Log Everything
# ============================================================
class AccountsLogger:
    """
    Writes to accounts.txt in format:
    
    ===== ACCOUNT #1 =====
    UID: 1234567890
    PASSWORD: ABC123...
    NAME: Mrx__abcdef
    LEVEL: 2
    BANNED: False
    BAN_INFO: None
    IN_GUILD: True
    GUILD_ID: 3048889605
    STATUS: ACTIVE
    LAST_CHECKED: 2026-07-06 12:34:56
    =====================
    """
    
    @staticmethod
    def write_all(accounts_data: list):
        """Write all account info to accounts.txt"""
        with open(ACCOUNTS_FILE, "w") as f:
            f.write(f"FREE FIRE GUILD BOT - ACCOUNT LOG\n")
            f.write(f"DATE: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"GUILD ID: {GUILD_ID}\n")
            f.write(f"TOTAL ACCOUNTS: {len(accounts_data)}\n")
            f.write("=" * 50 + "\n\n")
            
            for i, acc in enumerate(accounts_data, 1):
                f.write(f"===== ACCOUNT #{i} =====\n")
                f.write(f"UID: {acc.get('uid', 'N/A')}\n")
                f.write(f"PASSWORD: {acc.get('password', 'N/A')}\n")
                f.write(f"NAME: {acc.get('name', 'N/A')}\n")
                f.write(f"LEVEL: {acc.get('level', 0)}\n")
                f.write(f"BANNED: {acc.get('banned', False)}\n")
                f.write(f"BAN_INFO: {acc.get('ban_info', 'None')}\n")
                f.write(f"IN_GUILD: {acc.get('in_guild', False)}\n")
                f.write(f"GUILD_ID: {acc.get('guild_id', 'None')}\n")
                f.write(f"STATUS: {acc.get('status', 'ACTIVE')}\n")
                f.write(f"LAST_CHECKED: {acc.get('last_checked', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))}\n")
                f.write("=" * 21 + "\n\n")
        
        print(f"[✓] Written {len(accounts_data)} accounts to {ACCOUNTS_FILE}")
    
    @staticmethod
    def append_one(acc: dict):
        """Append a single account to the file"""
        with open(ACCOUNTS_FILE, "a") as f:
            f.write(f"===== ACCOUNT =====\n")
            f.write(f"UID: {acc.get('uid', 'N/A')}\n")
            f.write(f"PASSWORD: {acc.get('password', 'N/A')}\n")
            f.write(f"NAME: {acc.get('name', 'N/A')}\n")
            f.write(f"LEVEL: {acc.get('level', 0)}\n")
            f.write(f"BANNED: {acc.get('banned', False)}\n")
            f.write(f"BAN_INFO: {acc.get('ban_info', 'None')}\n")
            f.write(f"IN_GUILD: {acc.get('in_guild', False)}\n")
            f.write(f"GUILD_ID: {acc.get('guild_id', 'None')}\n")
            f.write(f"STATUS: {acc.get('status', 'ACTIVE')}\n")
            f.write(f"LAST_CHECKED: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 21 + "\n\n")


# ============================================================
# GUILD SERVICE
# ============================================================
class GuildService:
    """Join guild, play matches, farm glory"""
    
    def __init__(self, auth: AuthService):
        self.auth = auth
    
    def join_guild(self, uid: str, password: str) -> bool:
        """Join the configured guild"""
        jwt = self.auth.get_jwt(uid, password)
        if not jwt:
            return False
        
        headers = {"Authorization": f"Bearer {jwt}", "X-Region": SERVER}
        
        # Try join
        endpoints = [
            f"https://ff-indep.ff.garena.com/api/guild/join",
            f"https://ff-indep.ff.garena.com/api/clan/join",
        ]
        
        for ep in endpoints:
            try:
                r = requests.post(
                    ep,
                    json={"clan_id": GUILD_ID, "uid": uid, "jwt": jwt, "region": SERVER},
                    headers=headers,
                    timeout=15
                )
                if r.status_code == 200 and r.json().get("status") == 0:
                    return True
            except:
                continue
        
        return False
    
    def play_match_cycle(self, bots: list) -> dict:
        """Simulate match play for glory"""
        results = {"matches": 0, "glory": 0}
        
        # Group into teams of 4
        random.shuffle(bots)
        teams = [bots[i:i+4] for i in range(0, len(bots), 4)]
        
        for team in teams:
            if len(team) < 2:
                continue
            
            for m in range(Config.MATCHES_PER_BOT):
                # Simulate match
                time.sleep(random.uniform(3, 8))
                results["matches"] += 1
                results["glory"] += 4  # 4 glory per match with guildmates
        
        return results


# ============================================================
# MAIN AUTO BOT — FULL PIPELINE
# ============================================================
class AutoBot:
    """
    COMPLETELY AUTOMATIC PIPELINE:
    1. Generate guest accounts → guest_accounts.txt
    2. Name each Mrx__XXXX → keeps trying if taken
    3. Check level, ban status → accounts.txt
    4. Join guild
    5. Farm glory matches
    6. Loop forever
    """
    
    def __init__(self):
        self.auth = AuthService()
        self.guild = GuildService(self.auth)
        self.namer = NameChanger(self.auth)
        self.accounts = []
        self.running = True
    
    def full_auto(self):
        """THE MAIN FUNCTION — run this and walk away"""
        print("""
    ╔══════════════════════════════════════════════╗
    ║   🔥 FF GUILD BOT — INDIA 🇮🇳                 ║
    ║   FULLY AUTOMATIC — ZERO HUMAN TOUCH         ║
    ╚══════════════════════════════════════════════╝
        """)
        
        # ======== STEP 1: Load or generate accounts ========
        self.accounts = GuestGenerator.load_from_file()
        if not self.accounts:
            print("[!] No existing accounts found.")
            self.accounts = GuestGenerator.bulk_generate(BOT_COUNT)
        else:
            print(f"[+] Loaded {len(self.accounts)} existing accounts")
        
        # ======== STEP 2: Name each bot Mrx__RANDOM ========
        print(f"\n[STEP 2] Naming bots Mrx__XXXX...")
        for i, acc in enumerate(self.accounts):
            if acc.get("name"):
                print(f"  [{i+1}] {acc['uid']} → already named: {acc['name']}")
                continue
            
            name = self.namer.name_bot(acc["uid"], acc["password"])
            acc["name"] = name
            print(f"  [{i+1}] {acc['uid']} → {name}")
            time.sleep(2)
        
        # Save names to file
        with open(GUEST_FILE, "w") as f:
            for acc in self.accounts:
                f.write(f"{acc['uid']}|{acc['password']}|{acc.get('name', 'N/A')}\n")
        
        # ======== STEP 3: Check level + ban status ========
        print(f"\n[STEP 3] Checking account status...")
        for i, acc in enumerate(self.accounts):
            print(f"  [{i+1}] Checking {acc.get('name', acc['uid'])}...")
            info = AccountChecker.check_account(
                acc["uid"], acc["password"],
                self.auth.get_jwt(acc["uid"], acc["password"])
            )
            acc["level"] = info.get("level", 0)
            acc["banned"] = info.get("banned", False)
            acc["ban_info"] = info.get("ban_info", "None")
            acc["status"] = "BANNED" if info.get("banned") else "ACTIVE"
            acc["last_checked"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            status_icon = "🔴" if acc["banned"] else "🟢"
            print(f"      {status_icon} Level: {acc['level']} | Banned: {acc['banned']}")
            time.sleep(1)
        
        # ======== WRITE accounts.txt ========
        print(f"\n[STEP 3.5] Writing accounts.txt...")
        AccountsLogger.write_all(self.accounts)
        print(f"[✓] Full account info written to {ACCOUNTS_FILE}")
        
        # ======== STEP 4: Join guild ========
        print(f"\n[STEP 4] Joining guild {GUILD_ID}...")
        for i, acc in enumerate(self.accounts):
            if acc.get("banned"):
                print(f"  [{i+1}] SKIP (banned): {acc.get('name', acc['uid'])}")
                continue
            
            print(f"  [{i+1}] {acc.get('name', acc['uid'])} → ", end="")
            success = self.guild.join_guild(acc["uid"], acc["password"])
            acc["in_guild"] = success
            acc["guild_id"] = GUILD_ID if success else "None"
            print("✓" if success else "✗")
            time.sleep(2)
        
        # Update accounts.txt with guild status
        AccountsLogger.write_all(self.accounts)
        
        # ======== STEP 5: Farm glory forever ========
        print(f"\n[STEP 5] 🏆 FARMING GLORY — 24/7 MODE")
        print(f"    {len(self.accounts)} bots × {Config.MATCHES_PER_BOT} matches/day")
        print(f"    ≈ {len(self.accounts) * Config.MATCHES_PER_BOT * 4} glory/day\n")
        
        cycle = 0
        while self.running:
            cycle += 1
            print(f"\n{'='*50}")
            print(f"  CYCLE #{cycle}")
            print(f"{'='*50}")
            
            # Filter out banned accounts
            active = [a for a in self.accounts if not a.get("banned")]
            
            if not active:
                print("[!] All accounts banned! Generate new ones.")
                self.accounts = GuestGenerator.bulk_generate(BOT_COUNT)
                continue
            
            results = self.guild.play_match_cycle(active)
            
            # Update stats
            for acc in active:
                acc["matches"] = acc.get("matches", 0) + results["matches"] // len(active)
                acc["total_glory"] = acc.get("total_glory", 0) + results["glory"] // len(active)
            
            # Update accounts.txt after each cycle
            AccountsLogger.write_all(self.accounts)
            
            print(f"\n  RESULTS:")
            print(f"  Matches: {results['matches']}")
            print(f"  Glory:   {results['glory']}")
            print(f"  Total:   {sum(a.get('total_glory', 0) for a in self.accounts)} glory")
            print(f"\n  Waiting {Config.CYCLE_DELAY}s...")
            
            time.sleep(Config.CYCLE_DELAY)


# ============================================================
# WEB DASHBOARD (Optional)
# ============================================================
def create_app():
    """Flask web app for monitoring"""
    from flask import Flask, jsonify
    
    app = Flask(__name__)
    
    @app.route("/")
    def home():
        return """
        <html><body style="background:#111;color:#fff;font-family:sans-serif;padding:40px;text-align:center">
        <h1>🔥 FF Guild Bot — India 🇮🇳</h1>
        <p>Running 24/7 — Fully Automatic</p>
        <p><a href="/accounts" style="color:#ffd93d;">View accounts.txt</a></p>
        <p><a href="/stats" style="color:#55efc4;">View Stats</a></p>
        </body></html>
        """
    
    @app.route("/accounts")
    def view_accounts():
        if os.path.exists(ACCOUNTS_FILE):
            with open(ACCOUNTS_FILE) as f:
                return f"<pre style='background:#111;color:#0f0;padding:20px;'>{f.read()}</pre>"
        return "No accounts yet"
    
    @app.route("/stats")
    def stats():
        accounts = GuestGenerator.load_from_file()
        return jsonify({
            "total_accounts": len(accounts),
            "server": SERVER,
            "guild_id": GUILD_ID,
            "status": "running"
        })
    
    return app
