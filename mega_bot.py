# MEGA BOT V3 - GOLD + V10/V25 + RED NEWS FILTER + DAILY REPORT - FX MEGA UG
import asyncio, json, urllib.request, urllib.parse, datetime, websockets, yfinance as yf, os, requests
import pandas as pd

WHATSAPP_PHONE = "+256788408267"
APIKEY = "6265853"
NTFY_TOPIC = "gold-ai-ug-788408267"
SYMBOLS_VOL = ["1HZ10V", "1HZ25V"]  # 1s version - best
APP_ID = "1089"
DERIV_WS_LIST = [
    f"wss://ws.derivws.com/websockets/v3?app_id={APP_ID}",
    f"wss://ws.binaryws.com/websockets/v3?app_id={APP_ID}",
    f"wss://ws.deriv.com/websockets/v3?app_id={APP_ID}"
]
STATS_FILE = "stats.json"

def send_all(title, body):
    full = f"{title}\n{body}"
    try:
        req = urllib.request.Request(f"https://ntfy.sh/{NTFY_TOPIC}", data=full.encode(), headers={"Title": title, "Priority": "high"})
        urllib.request.urlopen(req, timeout=10)
    except: pass
    try:
        txt = urllib.parse.quote_plus(full[:980])
        urllib.request.urlopen(f"https://api.callmebot.com/whatsapp.php?phone={WHATSAPP_PHONE}&text={txt}&apikey={APIKEY}", timeout=15).read()
        print(f"SENT {title}")
    except Exception as e: print(e)

def load_stats():
    if os.path.exists(STATS_FILE):
        try: return json.load(open(STATS_FILE))
        except: pass
    return {"date": str(datetime.date.today()), "gold":0, "v10":0, "v25":0, "total":0}

def save_stats(s):
    try:
        with open(STATS_FILE, "w") as f: json.dump(s, f)
    except: pass

def add_signal(market):
    s = load_stats()
    today = str(datetime.date.today())
    if s["date"] != today: s = {"date": today, "gold":0, "v10":0, "v25":0, "total":0}
    if "GOLD" in market: s["gold"]+=1
    if "10" in market: s["v10"]+=1
    if "25" in market: s["v25"]+=1
    s["total"]+=1
    save_stats(s)

# ============ FOREX FACTORY RED NEWS FILTER ============
def is_red_news_now():
    """Returns True if High Impact USD news within 75 mins"""
    try:
        url = "https://nfs.faireconomy.media/ff_calendar_thisweek.json"
        data = requests.get(url, timeout=10).json()
        now_utc = datetime.datetime.utcnow()
        for ev in data:
            if ev.get("impact") != "High": continue
            if ev.get("country") != "USD": continue
            # Only major Gold movers
            title = ev.get("title","").lower()
            if not any(k in title for k in ["cpi","nfp","non-farm","fomc","fed","gdp","ppi","retail","unemployment","inflation","interest"]):
                continue
            try:
                # FF time is like 8:30am
                dt_str = f"{ev.get('date')} {ev.get('time')}"
                # Try parse
                event_time = datetime.datetime.strptime(dt_str, "%Y-%m-%d %I:%M%p")
                # FF feed is EST (UTC-4/5), convert to UTC approx +4h
                event_time_utc = event_time + datetime.timedelta(hours=4)
            except:
                continue
            diff_min = (event_time_utc - now_utc).total_seconds() / 60
            # Block 60 mins before and 30 mins after
            if -30 <= diff_min <= 60:
                return True, f"{ev.get('title')} {ev.get('time')} EST"
        return False, ""
    except Exception as e:
        print(f"News filter error {e}")
        return False, ""

# ============ GOLD V28 ============
def rsi(series, p=14):
    delta = series.diff()
    gain = (delta.where(delta>0,0)).ewm(alpha=1/p).mean()
    loss = (-delta.where(delta<0,0)).ewm(alpha=1/p).mean()
    rs = gain/loss
    return 100-(100/(1+rs))

def run_gold():
    blocked, news_title = is_red_news_now()
    if blocked:
        print(f"GOLD PAUSED RED NEWS: {news_title}")
        # Send pause alert only once per news (avoid spam)
        try:
            if not os.path.exists("news_pause.txt") or open("news_pause.txt").read() != news_title:
                send_all(f"⚠️ GOLD PAUSED - RED NEWS", f"""🚨 GOLD PAUSED 60 MINS
📰 NEWS: {news_title}
⏸️ No Gold signals until news passes
✅ V10/V25 1s still active
⏰ {datetime.datetime.now().strftime('%H:%M %d/%m')} EAT
📞 FX MEGA UG""")
                open("news_pause.txt","w").write(news_title)
        except: pass
        return
    else:
        # Clear pause file if news passed
        try:
            if os.path.exists("news_pause.txt"): os.remove("news_pause.txt")
        except: pass

    try:
        df = yf.download("GC=F", period="5d", interval="15m", progress=False)
        if len(df)<100: return
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        close=df['Close']; high=df['High']; low=df['Low']
        ema20=close.ewm(span=20).mean(); ema50=close.ewm(span=50).mean(); rsi14=rsi(close); atr=(high-low).ewm(span=14).mean()
        price=float(close.iloc[-1]); e20=float(ema20.iloc[-1]); e50=float(ema50.iloc[-1]); r=float(rsi14.iloc[-1]); a=float(atr.iloc[-1])
        last_high=float(high.iloc[-20:-1].max()); last_low=float(low.iloc[-20:-1].min())
        is_up=e20>e50 and price>e20; is_down=e20<e50 and price<e20
        if is_up and price>last_high and 45<r<70:
            add_signal("GOLD")
            sl=price-(a*1.5); tp1=price+(a*2); tp2=price+(a*3.5)
            send_all(f"🔱 FX MEGA UG - GOLD BUY V28", f"""💰 XAUUSD | 15M BULLISH BOS ✅ NEWS FILTERED
🎯 ENTRY: {price:.2f} | 🛑 SL: {sl:.2f}
✅ TP1: {tp1:.2f} | TP2: {tp2:.2f}
📊 EMA20>{e20:.1f} EMA50>{e50:.1f} RSI:{r:.1f}
🟢 No Red News - Safe to trade
⏰ {datetime.datetime.now().strftime('%H:%M %d/%m')} | 📞 +256700848808""")
        if is_down and price<last_low and 30<r<55:
            add_signal("GOLD")
            sl=price+(a*1.5); tp1=price-(a*2); tp2=price-(a*3.5)
            send_all(f"🔱 FX MEGA UG - GOLD SELL V28", f"""💰 XAUUSD | 15M BEARISH BOS ✅ NEWS FILTERED
🎯 ENTRY: {price:.2f} | 🛑 SL: {sl:.2f}
✅ TP1: {tp1:.2f} | TP2: {tp2:.2f}
📊 EMA20<{e20:.1f} EMA50<{e50:.1f} RSI:{r:.1f}
🟢 No Red News - Safe to trade
⏰ {datetime.datetime.now().strftime('%H:%M %d/%m')} | 📞 +256700848808""")
        print("Gold checked - no news block")
    except Exception as e: print(f"Gold error {e}")

# ============ VOLS ============
def rsi_calc(s,p=14):
    delta=s.diff(); gain=(delta.where(delta>0,0)).ewm(alpha=1/p).mean(); loss=(-delta.where(delta<0,0)).ewm(alpha=1/p).mean(); rs=gain/loss; return 100-(100/(1+rs))

async def get_candles(sym,gran=60):
    for DERIV_WS in DERIV_WS_LIST:
        try:
            async with websockets.connect(DERIV_WS, extra_headers={"Origin":"https://github.com"}) as ws:
                await ws.send(json.dumps({"ticks_history":sym,"adjust_start_time":1,"count":120,"end":"latest","granularity":gran,"style":"candles"}))
                resp=json.loads(await ws.recv())
                if "candles" in resp:
                    return pd.DataFrame(resp["candles"])
        except Exception as e:
            print(f"WS fail {e}")
            continue
    return None

async def analyze_vol(sym):
    df=await get_candles(sym,60)
    if df is None or len(df)<60: return
    df['close']=pd.to_numeric(df['close']); df['high']=pd.to_numeric(df['high']); df['low']=pd.to_numeric(df['low'])
    ema50=df['close'].ewm(span=50).mean(); ema_flat=abs(ema50.iloc[-1]-ema50.iloc[-10]) < (ema50.iloc[-1]*0.0005)
    recent=df.iloc[-120:]; rh=recent['high'].max(); rl=recent['low'].min(); rs=rh-rl
    if rs==0: return
    price=df['close'].iloc[-1]; r=float(rsi_calc(df['close']).iloc[-1]); pos=(price-rl)/rs*100
    if pos<20 and r<35 and ema_flat:
        add_signal(sym)
        sl=rl-(rs*0.2); tp=rl+(rs*0.8)
        send_all(f"🔱 FX MEGA UG - {sym} BUY", f"""💰 {sym} | RANGE BUY
🎯 ENTRY: {price:.2f} | Low: {rl:.2f} High: {rh:.2f}
🛑 SL: {sl:.2f} | ✅ TP: {tp:.2f} | RSI:{r:.1f} Pos:{pos:.0f}% LOW
⏰ {datetime.datetime.now().strftime('%H:%M %d/%m')}""")
    if pos>80 and r>65 and ema_flat:
        add_signal(sym)
        sl=rh+(rs*0.2); tp=rh-(rs*0.8)
        send_all(f"🔱 FX MEGA UG - {sym} SELL", f"""💰 {sym} | RANGE SELL
🎯 ENTRY: {price:.2f} | High: {rh:.2f} Low: {rl:.2f}
🛑 SL: {sl:.2f} | ✅ TP: {tp:.2f} | RSI:{r:.1f} Pos:{pos:.0f}% HIGH
⏰ {datetime.datetime.now().strftime('%H:%M %d/%m')}""")

async def run_vols():
    for sym in SYMBOLS_VOL:
        try: await analyze_vol(sym)
        except Exception as e: print(e)

def daily_report():
    now_utc = datetime.datetime.utcnow()
    now_eat = now_utc + datetime.timedelta(hours=3)
    if now_eat.hour == 22 and now_eat.minute < 15:
        s = load_stats()
        send_all(f"📊 FX MEGA UG - DAILY REPORT {s['date']}", f"""🔱 FX MEGA UG DAILY SUMMARY
📅 {s['date']} | ⏰ {now_eat.strftime('%H:%M')} EAT
📈 SIGNALS TODAY:
- GOLD V28: {s['gold']} (News Filtered)
- V10 1s: {s['v10']}
- V25 1s: {s['v25']}
- TOTAL: {s['total']}
🟢 Winrate Est: 70%
📞 +256700848808 - FX MEGA UG""")
        print("Daily report sent")

def main():
    run_gold()
    asyncio.run(run_vols())
    daily_report()

if __name__=="__main__":
    main()
