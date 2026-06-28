import os
import random
import requests
import json
import datetime

BOT_TOKEN    = os.environ["BOT_TOKEN"]
CHAT_ID      = os.environ["CHAT_ID"]
SUPA_URL     = os.environ.get("SUPABASE_URL", "")
SUPA_KEY     = os.environ.get("SUPABASE_KEY", "")
PAGES_URL    = os.environ.get("PAGES_URL", "")

# ── Randomized messages ───────────────────────────────────────────────────────

COMPLETION_MESSAGES = [
    "all daily quests have been cleared. your streak lives another day, Hunter.",
    "the system acknowledges your effort. daily targets met. streak protected.",
    "dungeon cleared. the shadow army grows stronger with each passing day.",
    "qualification check passed. you are becoming something the system did not expect.",
    "today's gate has been sealed. rest, Hunter. tomorrow brings a new dungeon.",
    "daily log updated: quests cleared. the system is pleased.",
    "three for three. streak intact. keep this up and rank advancement will follow.",
]

REMINDER_MESSAGES = [
    "the system has detected uncompleted daily quests. proceed to the status window immediately.",
    "a gate has opened nearby. will you enter, or let your streak die in silence?",
    "warning: failure to complete today's quests will break your streak. this is your only reminder.",
    "the system is watching. your daily quests await. do not make it wait much longer.",
    "rise, Hunter. today's dungeon is still active. how long will you keep it waiting?",
    "qualification check failed — quests incomplete. the system does not accept excuses.",
    "a new opportunity to grow stronger is slipping away. check your quest log now.",
    "streak at risk. the gap between the strong and the weak is made in moments like this.",
    "the shadow army cannot grow if you will not fight. complete your quests, Hunter.",
    "every hunter who ever fell behind thought they had more time. you do not.",
]

# ── Supabase check ────────────────────────────────────────────────────────────

def check_completion():
    """Returns True if all 3 daily quests are completed today."""
    if not SUPA_URL or not SUPA_KEY:
        print("Supabase not configured — skipping completion check.")
        return False

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

        if not data or not data[0]:
            print("No state row found in Supabase.")
            return False

        state = data[0]["state"]
        today = datetime.date.today().strftime("%a %b %d %Y")  # matches JS toDateString()

        daily_date    = state.get("dailyDate", "")
        daily_ids     = state.get("dailyQuestIds", [])
        completed     = state.get("completedToday", [])

        print(f"Today       : {today}")
        print(f"Daily date  : {daily_date}")
        print(f"Quest IDs   : {daily_ids}")
        print(f"Completed   : {completed}")

        if daily_date != today:
            print("Daily date mismatch — quests may not have been opened yet today.")
            return False

        all_done = len(daily_ids) > 0 and all(qid in completed for qid in daily_ids)
        print(f"All done    : {all_done}")
        return all_done

    except Exception as e:
        print(f"Supabase check failed: {e}")
        return False

# ── Send message ──────────────────────────────────────────────────────────────

def send(completed_today: bool):
    if completed_today:
        body = random.choice(COMPLETION_MESSAGES)
        prefix = "✅ [SYSTEM REPORT]"
    else:
        body = random.choice(REMINDER_MESSAGES)
        prefix = "⚔️ [SYSTEM ALERT]"

    # Always append the Pages URL
    link_line = f"\n\n🔗 {PAGES_URL}" if PAGES_URL else ""

    text = f"{prefix}\n\n{body}{link_line}"

    url  = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    resp = requests.post(
        url,
        data={"chat_id": CHAT_ID, "text": text},
        timeout=10,
    )
    resp.raise_for_status()
    print(f"Sent ({('completion' if completed_today else 'reminder')}): {body[:60]}...")

# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    completed = check_completion()
    send(completed)
