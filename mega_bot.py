import yfinance as yf,pandas as pd,requests,time
from datetime import datetime,timezone
TOPIC="gold-ai-ug-788408267";URL=f"https://ntfy.sh/{TOPIC}";BRAND="FXMEGA v13.2 LIVE 5SEC";GOLD_OFF=21.43;SILVER_OFF=0.12;DXY="DX-Y.NYB"
BINANCE_CRYPTO={"BITCOIN":"BTCUSDT","ETHEREUM":"ETHUSDT","SOLANA":"SOLUSDT","BNB":"BNBUSDT","XRP":"XRPUSDT","DOGECOIN":"DOGEUSDT"}
BINANCE_GOLD={"GOLD":"PAXGUSDT","SILVER":"XAGUSDT"}
def news():
 b=set()
 try:
  r=requests.get("https://nfs.faireconomy.media/ff_calendar_thisweek.json",timeout=15).json();now=datetime.now(timezone.utc)
  for e in r:
   if e.get("impact")!="High":continue
   try:et=datetime.fromisoformat(e.get("date").replace("Z","+00:00"))
   except:continue
   if -60<=(et-now).total_seconds()/60<=60:b.add(e.get("country","").strip())
 except:pass
 return b
def binance_df(sym):
 try:
  url=f"https://api.binance.com/api/v3/klines?symbol={sym}&interval=15m&limit=100"
  r=requests.get(url,timeout=10).json()
  if isinstance(r,dict) and "code" in r:return pd.DataFrame()
  df=pd.DataFrame(r,columns=["Ot","Op","H","L","C","V","Ct","QV","Tr","TB","TQ","I"])
  df['Open']=pd.to_numeric(df['Op']);df['High']=pd.to_numeric(df['H']);df['Low']=pd.to_numeric(df['L']);df['Close']=pd.to_numeric(df['C']);time.sleep(1)
  return df
 except:return pd.DataFrame()
def yahoo_df(L):
 for s in L:
  try:
   d=yf.download(s,period="10d",interval="15m",auto_adjust=True,progress=False)
   if d is not None and not d.empty and len(d)>50:
    if isinstance(d.columns,pd.MultiIndex):d.columns=d.columns.get_level_values(0)
    return d,s
  except:continue
 return pd.DataFrame(),None
def yahoo_h1(L):
 for s in L:
  try:
   d=yf.download(s,period="20d",interval="1h",auto_adjust=True,progress=False)
   if d is not None and not d.empty and len(d)>50:
    if isinstance(d.columns,pd.MultiIndex):d.columns=d.columns.get_level_values(0)
    return d
  except:continue
 return pd.DataFrame()
def gdxy():
 try:
  d=yf.download(DXY,period="5d",interval="15m",auto_adjust=True,progress=False)
  if d is None or d.empty:d=yf.download("DX=F",period="5d",interval="15m",auto_adjust=True,progress=False)
  if isinstance(d.columns,pd.MultiIndex):d.columns=d.columns.get_level_values(0)
  c=d['Close'];e=c.ewm(span=13).mean();return float(c.iloc[-1]),float(e.iloc[-1]),float(c.iloc[-1])<float(e.iloc[-1]),float(c.iloc[-1])>float(e.iloc[-1]),float(e.iloc[-1])<float(e.iloc[-2]),float(e.iloc[-1])>float(e.iloc[-2])
 except:return None,None,False,False,False,False
def send(m,buy=True):
 try:
  requests.post(URL,data=m.encode('utf-8'),headers={"Title":f"{'BUY' if buy else 'SELL'} - {BRAND}","Priority":"high"},timeout=10)
  time.sleep(5)
 except:pass
def ff(x):
 try:return float(x.iloc[0]) if hasattr(x,'iloc') else float(x)
 except:return float(x)
def fmt(p):p=float(p);return f"{p:.6f}" if p<0.01 else f"{p:.5f}" if p<1 else f"{p:.4f}" if p<10 else f"{p:.3f}" if p<100 else f"{p:.2f}"
def rsi(c,p=14):d=c.diff();g=(d.where(d>0,0)).rolling(p).mean();l=(-d.where(d<0,0)).rolling(p).mean();return 100-(100/(1+g/l))
blk=news()
if blk:print(f"BLOCKED {blk}")
else:
 dxy_cur,dxy_e,dxy_below,dxy_above,dxy_down,dxy_up=gdxy();pairs=["GOLD","SILVER","USDCHF","EURUSD","GBPUSD","USDJPY","BITCOIN","ETHEREUM","SOLANA","BNB","XRP","DOGECOIN"]
 for name in pairs:
  df=pd.DataFrame();src="";off=0
  if name in BINANCE_GOLD:
   src="BINANCE LIVE";df=binance_df(BINANCE_GOLD[name])
   if df.empty and name=="SILVER":src="YAHOO SILVER LIVE";df,_=yahoo_df(["SI=F"]);off=SILVER_OFF
   elif df.empty:print(f"{name} NO DATA");continue
   else:off=GOLD_OFF if name=="GOLD" else SILVER_OFF
  elif name in BINANCE_CRYPTO:
   src="BINANCE LIVE";df=binance_df(BINANCE_CRYPTO[name])
   if df.empty:print(f"{name} NO DATA");continue
  else:
   src="YAHOO FOREX";df,_=yahoo_df([f"{name}=X"]); 
  if df.empty:continue
  close=df['Close'];high=df['High'];low=df['Low'];op=df['Open']
  cur=ff(close.iloc[-1]);hnow=ff(high.iloc[-1]);lnow=ff(low.iloc[-1]);o=ff(op.iloc[-1]);hp=ff(high.iloc[-2]);lp=ff(low.iloc[-2])
  if off>0:cur-=off;hnow-=off;lnow-=off;o-=off;hp-=off;lp-=off
  pdh=ff((high-off if off>0 else high).iloc[-97:-1].max()) if off>0 else ff(high.iloc[-97:-1].max());pdl=ff((low-off if off>0 else low).iloc[-97:-1].min()) if off>0 else ff(low.iloc[-97:-1].min());mid=(pdh+pdl)/2
  tr=pd.concat([df['High']-df['Low'],(df['High']-df['Close'].shift()).abs(),(df['Low']-df['Close'].shift()).abs()],axis=1).max(axis=1);atr=ff(tr.rolling(14).mean().iloc[-1])
  if atr<cur*0.005:atr=cur*0.005
  e13=close.ewm(span=13).mean();e50=close.ewm(span=50).mean();en=ff(e13.iloc[-1]);ep=ff(e13.iloc[-2]);e50n=ff(e50.iloc[-1])
  if off>0:en-=off;ep-=off;e50n-=off
  up=en>ep;down=en<ep;rs=rsi(close);rsi_now=ff(rs.iloc[-1])
  bull_now=hnow-en;bull_prev=hp-ep;bear_now=lnow-en;bear_prev=lp-ep;bull_ok=(bull_prev<0 and bull_now>0) or bull_now>0;bear_ok=(bear_prev>0 and bear_now<0) or bear_now<0
  buy=False;sell=False;strat=src
  if name in ["GOLD","SILVER"]:
   bull_crt=lnow<pdl and cur>pdl and cur>mid;bear_crt=hnow>pdh and cur<pdh and cur<mid;body=abs(cur-o);rng=hnow-lnow;bp=body/rng if rng>0 else 0;bull_csd=cur>o and bp>0.6 and cur>hp;bear_csd=cur<o and bp>0.6 and cur<lp;b1=(bull_crt or bull_csd) and cur>en and up and bull_ok;s1=(bear_crt or bear_csd) and cur<en and down and bear_ok
   if name=="GOLD":buy=b1 and dxy_below and dxy_down;sell=s1 and dxy_above and dxy_up
   else:buy=b1;sell=s1
   strat=f"{name} {src} CRT+DXY"
  elif name in ["USDCHF","EURUSD","GBPUSD","USDJPY"]:
   ns=abs(cur-pdl)<atr*1.5;nr=abs(cur-pdh)<atr*1.5;rsi_b=rsi_now<48 and rsi_now>30;rsi_s=rsi_now>52 and rsi_now<70;df1=yahoo_h1([f"{name}=X"]);h1_up=False;h1_down=False
   if not df1.empty:hh=df1['High'].iloc[-5:-1].max();hl=df1['Low'].iloc[-5:-1].min();hc=ff(df1['Close'].iloc[-1]);h1_up=hc>float(hh);h1_down=hc<float(hl)
   b1=ns and rsi_b and up and bull_ok and h1_up;s1=nr and rsi_s and down and bear_ok and h1_down
   if name=="USDCHF":
    if dxy_up:s1=False
    if dxy_down:b1=False
   buy=b1;sell=s1;strat=f"FOREX {src} OB+RSI+H1"
  else:
   bos_u=cur>pdh;bos_d=cur<pdl;ret_b=abs(cur-pdh)<atr*0.8 and bos_u;ret_s=abs(cur-pdl)<atr*0.8 and bos_d;buy=ret_b and en>e50n and up and rsi_now>50;sell=ret_s and en<e50n and down and rsi_now<50;strat=f"CRYPTO {src} BREAK+RETEST"
  print(f"{name} {strat} E {fmt(cur)} LIVE {fmt(cur)} RSI {rsi_now:.1f} B:{buy} S:{sell}")
  if buy or sell:
   side="BUY" if buy else "SELL";e=cur;sl=e-1.5*atr if side=="BUY" else e+1.5*atr;t1=e+1*atr if side=="BUY" else e-1*atr;t2=e+2*atr if side=="BUY" else e-2*atr;msg=f"{side} {name} v13.2 {strat} ENTRY {fmt(e)} LIVE {fmt(e)} SL {fmt(sl)} TP1 {fmt(t1)} TP2 {fmt(t2)} ATR {fmt(atr)} RSI {rsi_now:.1f}"
   send(msg,buy)
print("DONE v13.2 - 5SEC delay + 1SEC between Binance calls - ALL LIVE")