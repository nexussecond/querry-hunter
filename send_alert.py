import os, requests, json, datetime

BOT_TOKEN   = os.environ['BOT_TOKEN']
CHAT_ID     = os.environ['CHAT_ID']
SUPA_URL    = os.environ.get('SUPABASE_URL', '')
SUPA_KEY    = os.environ.get('SUPABASE_KEY', '')
PAGES_URL   = os.environ.get('PAGES_URL', '')

completed_today = False

if SUPA_URL and SUPA_KEY:
    try:
        r = requests.get(
            f"{SUPA_URL}/rest/v1/hunter_state?id=eq.main&select=state",
            headers={"apikey": SUPA_KEY, "Authorization": f"Bearer {SUPA_KEY}"}
        )
        data = r.json()
        if data and data[0]:
            state = data[0]['state']
            today = datetime.date.today().strftime('%a %b %d %Y')
            completed = state.get('completedToday', [])
            daily_ids = state.get('dailyQuestIds', [])
            daily_date = state.get('dailyDate', '')
            if daily_date == today and len(completed) >= 3:
                completed_today = True
    except Exception as e:
        print(f"Supabase check failed: {e}")

if completed_today:
    msg = f"✅ SYSTEM REPORT — All daily quests cleared, Hunter. Streak protected.\n\n{PAGES_URL}"
else:
    msg = f"⚔️ SYSTEM ALERT — Daily quests await. Your streak is at risk.\n\n{PAGES_URL}"

requests.post(
    f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
    json={"chat_id": CHAT_ID, "text": msg}
)
print(f"Sent: {msg[:60]}...")
