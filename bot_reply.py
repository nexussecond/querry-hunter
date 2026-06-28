import os
import requests
import datetime
import json

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID   = os.environ["CHAT_ID"]
SUPA_URL  = os.environ.get("SUPABASE_URL", "")
SUPA_KEY  = os.environ.get("SUPABASE_KEY", "")
PAGES_URL = os.environ.get("PAGES_URL", "")

# ── Fetch latest message from the bot ────────────────────────────────────────

def get_latest_message():
    """Gets the most recent message sent to the bot."""
    try:
        resp = requests.get(
            f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates",
            params={"limit": 1, "offset": -1},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        updates = data.get("result", [])
        if not updates:
            return None, None
        latest = updates[-1]
        msg    = latest.get("message", {})
        text   = msg.get("text", "").strip().lower()
        chat   = str(msg.get("chat", {}).get("id", ""))
        return text, chat
    except Exception as e:
        print(f"getUpdates failed: {e}")
        return None, None

# ── Supabase state fetch ──────────────────────────────────────────────────────

def get_state():
    if not SUPA_URL or not SUPA_KEY:
        return None
    try:
        resp = requests.get(
            f"{SUPA_URL}/rest/v1/hunter_state?id=eq.main&select=state",
            headers={
                "apikey": SUPA_KEY,
                "Authorization": f"Bearer {SUPA_KEY}",
            },
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        return data[0]["state"] if data and data[0] else None
    except Exception as e:
        print(f"Supabase fetch failed: {e}")
        return None

# ── Build reply based on what user typed ─────────────────────────────────────

def build_reply(text, state):
    today = datetime.date.today().strftime("%a %b %d %Y")

    # ── /status or "status" ──
    if any(k in text for k in ["/status", "status"]):
        if not state:
            return "⚠️ Could not reach the database. Try again later."

        xp            = state.get("totalXp", 0)
        level         = state.get("level", 1)
        streak        = state.get("streak", 0)
        rank_idx      = state.get("rankIdx", 0)
        gate_keys     = state.get("gateKeys", 0)
        shadows       = len(state.get("shadows", []))
        daily_ids     = state.get("dailyQuestIds", [])
        completed     = state.get("completedToday", [])
        daily_date    = state.get("dailyDate", "")
        done_count    = sum(1 for q in daily_ids if q in completed)
        ranks         = ["E", "D", "C", "B", "A", "S"]
        rank          = ranks[min(rank_idx, 5)]
        quests_line   = f"{done_count}/3 cleared ✅" if daily_date == today else "0/3 — not started"

        return (
            f"📊 [HUNTER STATUS REPORT]\n\n"
            f"Rank      : {rank}\n"
            f"Level     : {level}\n"
            f"Total XP  : {xp}\n"
            f"Streak    : {streak}d\n"
            f"Gate Keys : {gate_keys}\n"
            f"Shadows   : {shadows}\n"
            f"Quests    : {quests_line}\n\n"
            f"🔗 {PAGES_URL}"
        )

    # ── /quests or "quests" ──
    elif any(k in text for k in ["/quests", "quests", "quest"]):
        if not state:
            return "⚠️ Could not reach the database."
        daily_ids  = state.get("dailyQuestIds", [])
        completed  = state.get("completedToday", [])
        daily_date = state.get("dailyDate", "")
        if daily_date != today or not daily_ids:
            return "📋 No quests found for today. Open the game first to generate today's quests.\n\n🔗 " + PAGES_URL
        lines = []
        for qid in daily_ids:
            done = "✅" if qid in completed else "⬜"
            lines.append(f"{done} {qid.upper()}")
        remaining = sum(1 for q in daily_ids if q not in completed)
        summary = "All done! Streak protected. 🔥" if remaining == 0 else f"{remaining} quest(s) remaining."
        return f"📋 [TODAY'S QUESTS]\n\n" + "\n".join(lines) + f"\n\n{summary}\n\n🔗 {PAGES_URL}"

    # ── /streak or "streak" ──
    elif any(k in text for k in ["/streak", "streak"]):
        if not state:
            return "⚠️ Could not reach the database."
        streak = state.get("streak", 0)
        if streak == 0:
            return "🔥 Streak: 0 days. Complete today's quests to start one!\n\n🔗 " + PAGES_URL
        elif streak < 3:
            return f"🔥 Streak: {streak} day(s). Keep going!\n\n🔗 " + PAGES_URL
        else:
            return f"🔥 Streak: {streak} days. The system is impressed.\n\n🔗 " + PAGES_URL

    # ── /ping or "ping" ──
    elif any(k in text for k in ["/ping", "ping", "test", "hello", "hi", "hey"]):
        return (
            f"✅ [SYSTEM ONLINE]\n\n"
            f"Bot is active and responding.\n"
            f"Daily alerts fire at 8:00 PM IST.\n\n"
            f"Commands:\n"
            f"  /status  — full hunter stats\n"
            f"  /quests  — today's quest progress\n"
            f"  /streak  — current streak\n"
            f"  /ping    — check bot is alive\n\n"
            f"🔗 {PAGES_URL}"
        )

    # ── unknown ──
    else:
        return (
            f"⚔️ [SYSTEM]\n\n"
            f"Unknown command. Try one of these:\n\n"
            f"  /ping    — check bot is alive\n"
            f"  /status  — full hunter stats\n"
            f"  /quests  — today's quest progress\n"
            f"  /streak  — current streak\n\n"
            f"🔗 {PAGES_URL}"
        )

# ── Send reply ────────────────────────────────────────────────────────────────

def send_message(chat_id, text):
    try:
        resp = requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            data={"chat_id": chat_id, "text": text},
            timeout=10,
        )
        resp.raise_for_status()
        print(f"Reply sent to {chat_id}: {text[:60]}...")
    except Exception as e:
        print(f"Send failed: {e}")

# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    text, chat = get_latest_message()
    print(f"Latest message: '{text}' from chat: {chat}")

    # Only reply if the message is from your own chat
    if not text or str(chat) != str(CHAT_ID):
        print("No new message from owner — nothing to reply to.")
    else:
        state = get_state()
        reply = build_reply(text, state)
        send_message(chat, reply)
