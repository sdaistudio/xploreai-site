import json,urllib.request,time,datetime,csv,sys
syms={"NIFTY50":"^NSEI","SENSEX":"^BSESN","RELIANCE":"RELIANCE.NS","TCS":"TCS.NS","INFY":"INFY.NS","HDFCBANK":"HDFCBANK.NS","ICICIBANK":"ICICIBANK.NS","SP500":"^GSPC","USDINR":"INR=X","GOLD":"GC=F","CRUDE":"CL=F","INDIAVIX":"^INDIAVIX"}
p1=int(datetime.datetime(2015,1,1).timestamp()); p2=int(datetime.datetime(2026,1,1).timestamp())
for name,s in syms.items():
    url=f"https://query1.finance.yahoo.com/v8/finance/chart/{urllib.parse.quote(s)}?period1={p1}&period2={p2}&interval=1d&events=div"
    req=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0"})
    d=json.load(urllib.request.urlopen(req))["chart"]["result"][0]
    q=d["indicators"]["quote"][0]; adj=d["indicators"].get("adjclose",[{}])[0].get("adjclose")
    with open(f"../data/{name}.csv","w",newline="") as f:
        w=csv.writer(f); w.writerow(["Date","Open","High","Low","Close","Adjusted","Volume"]); n=0
        for i,t in enumerate(d["timestamp"]):
            c=q["close"][i]
            if c is None: continue
            dt=datetime.datetime.utcfromtimestamp(t+d["meta"].get("gmtoffset",0)).date()
            r=lambda x: "" if x is None else round(x,4)
            w.writerow([dt,r(q["open"][i]),r(q["high"][i]),r(q["low"][i]),r(c),r(adj[i] if adj else c),q["volume"][i] or 0]); n+=1
    print(name,n); time.sleep(1)
