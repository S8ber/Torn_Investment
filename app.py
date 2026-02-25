"""
Torn Investment Tracker
- Set your API key on line 10 below
- Run: python app.py
- Open: http://localhost:5000
"""

import os, time, threading, requests
from datetime import datetime
from flask import Flask, jsonify, Response

# ============================================================
#  PUT YOUR API KEY HERE
# ============================================================
API_KEY = os.environ.get("TORN_API_KEY", "PASTE_YOUR_KEY_HERE")
# ============================================================

CACHE_TTL = 60
app = Flask(__name__)
_cache = {"data": None, "ts": 0}
_lock = threading.Lock()

def fetch():
    try:
        r = requests.get(
            "https://api.torn.com/user/",
            params={"selections": "investments", "key": API_KEY},
            timeout=10
        )
        r.raise_for_status()
        d = r.json()
        if "error" in d:
            return {"error": f"Torn API: {d['error']['error']} (code {d['error']['code']})"}
        return d
    except Exception as e:
        return {"error": str(e)}

def get_data():
    with _lock:
        if _cache["data"] and (time.time() - _cache["ts"]) < CACHE_TTL:
            return _cache["data"]
        raw = fetch()
        if "error" in raw:
            return raw
        inv_raw = raw.get("investments", {})
        items, total_in, total_val = [], 0, 0
        for iid, inv in (inv_raw.items() if isinstance(inv_raw, dict) else []):
            if not isinstance(inv, dict):
                continue
            invested   = inv.get("money_invested", 0) or 0
            cur_val    = inv.get("current_value",  inv.get("total_value", invested)) or invested
            mat_ts     = inv.get("maturity", inv.get("maturity_time", 0)) or 0
            duration   = inv.get("duration", 0) or 0
            name       = inv.get("type", inv.get("name", f"Investment #{iid}"))
            profit     = cur_val - invested
            roi        = round((profit / invested * 100) if invested else 0, 2)
            now        = int(time.time())
            remaining  = max(0, mat_ts - now) if mat_ts else None
            items.append({"id": iid, "name": name, "invested": invested,
                          "current_value": cur_val, "profit": profit, "roi_pct": roi,
                          "maturity_ts": mat_ts, "duration": duration,
                          "time_remaining_s": remaining, "mature": bool(mat_ts and now >= mat_ts)})
            total_in  += invested
            total_val += cur_val
        total_profit = total_val - total_in
        result = {
            "summary": {
                "total_invested": total_in, "total_current_value": total_val,
                "total_profit": total_profit,
                "total_roi_pct": round((total_profit / total_in * 100) if total_in else 0, 2),
                "investment_count": len(items)
            },
            "investments": items,
            "fetched_at_human": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "cache_ttl": CACHE_TTL,
            "next_refresh_in": CACHE_TTL
        }
        _cache["data"] = result
        _cache["ts"] = time.time()
        return result

HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Torn Investments</title>
<link href="https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Orbitron:wght@400;700;900&display=swap" rel="stylesheet">
<style>
:root{--bg:#080c10;--surface:#0d1318;--border:#1a2a1f;--green:#00ff88;--green-dim:#00cc6a;--green-glow:rgba(0,255,136,.15);--red:#ff3860;--amber:#ffb347;--text:#c8e6d0;--muted:#4a6b52;--panel:#0b1219}
*{box-sizing:border-box;margin:0;padding:0}
body{background:var(--bg);color:var(--text);font-family:'Share Tech Mono',monospace;min-height:100vh;overflow-x:hidden}
body::before{content:'';position:fixed;inset:0;background:repeating-linear-gradient(to bottom,transparent,transparent 2px,rgba(0,0,0,.08) 2px,rgba(0,0,0,.08) 4px);pointer-events:none;z-index:9999}
body::after{content:'';position:fixed;inset:0;background-image:linear-gradient(rgba(0,255,136,.03) 1px,transparent 1px),linear-gradient(90deg,rgba(0,255,136,.03) 1px,transparent 1px);background-size:40px 40px;pointer-events:none;z-index:0}
.wrap{max-width:1100px;margin:0 auto;padding:32px 20px;position:relative;z-index:1}
header{display:flex;align-items:flex-start;justify-content:space-between;margin-bottom:40px;flex-wrap:wrap;gap:16px}
h1{font-family:'Orbitron',monospace;font-size:clamp(20px,4vw,32px);font-weight:900;letter-spacing:.1em;color:var(--green);text-shadow:0 0 30px rgba(0,255,136,.5)}
.sub{font-size:11px;color:var(--muted);letter-spacing:.3em;text-transform:uppercase;margin-top:6px}
.meta{text-align:right;font-size:11px;color:var(--muted);line-height:1.9}
.dot{display:inline-block;width:7px;height:7px;border-radius:50%;background:var(--green);box-shadow:0 0 8px var(--green);margin-right:6px;animation:pulse 2s infinite}
.dot.err{background:var(--red);box-shadow:0 0 8px var(--red);animation:none}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.3}}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:16px;margin-bottom:32px}
.card{background:var(--panel);border:1px solid var(--border);border-radius:4px;padding:20px 24px;position:relative;overflow:hidden}
.card::before{content:'';position:absolute;top:0;left:0;right:0;height:2px;background:linear-gradient(90deg,transparent,var(--green),transparent);opacity:.6}
.clabel{font-size:10px;letter-spacing:.25em;text-transform:uppercase;color:var(--muted);margin-bottom:10px}
.cval{font-family:'Orbitron',monospace;font-size:clamp(16px,2.5vw,24px);font-weight:700;line-height:1}
.pos{color:var(--green);text-shadow:0 0 20px rgba(0,255,136,.3)}
.neg{color:var(--red);text-shadow:0 0 20px rgba(255,56,96,.3)}
.neu{color:var(--text)}
.amb{color:var(--amber)}
.csub{font-size:11px;color:var(--muted);margin-top:8px}
.sh{display:flex;align-items:center;gap:12px;margin-bottom:16px;padding-bottom:10px;border-bottom:1px solid var(--border)}
.sh h2{font-family:'Orbitron',monospace;font-size:13px;letter-spacing:.2em;color:var(--muted);text-transform:uppercase}
.badge{background:var(--green-glow);border:1px solid rgba(0,255,136,.2);color:var(--green);font-size:10px;padding:2px 8px;border-radius:2px}
.list{display:flex;flex-direction:column;gap:12px}
.row{background:var(--panel);border:1px solid var(--border);border-radius:4px;padding:18px 24px;display:grid;grid-template-columns:1.5fr repeat(3,1fr) auto;gap:12px;align-items:center;position:relative}
.row.mat{border-color:rgba(255,179,71,.35)}
.row.mat::after{content:'READY';position:absolute;right:14px;top:8px;font-size:9px;color:var(--amber);letter-spacing:.2em;animation:pulse 1s infinite}
.fl{display:flex;flex-direction:column;gap:3px}
.fl .lbl{font-size:9px;letter-spacing:.2em;color:var(--muted);text-transform:uppercase}
.fname{font-family:'Orbitron',monospace;font-size:12px;color:var(--text);font-weight:700}
.cd{font-family:'Orbitron',monospace;font-size:12px;color:var(--amber)}
.cd.done{color:var(--green);animation:pulse 1s infinite}
.pb-wrap{height:3px;background:rgba(255,255,255,.05);border-radius:2px;overflow:hidden;margin-top:6px}
.pb{height:100%;background:linear-gradient(90deg,var(--green-dim),var(--green));border-radius:2px;box-shadow:0 0 8px var(--green)}
.strip{display:flex;align-items:center;justify-content:space-between;margin-top:32px;padding:12px 16px;background:var(--panel);border:1px solid var(--border);border-radius:4px;font-size:11px;color:var(--muted);flex-wrap:wrap;gap:8px}
.btn{background:none;border:1px solid rgba(0,255,136,.3);color:var(--green);font-family:'Share Tech Mono',monospace;font-size:11px;padding:5px 14px;border-radius:3px;cursor:pointer;letter-spacing:.1em}
.btn:hover{background:var(--green-glow);border-color:var(--green)}
.empty{text-align:center;padding:60px 20px;color:var(--muted)}
.empty .icon{font-size:36px;margin-bottom:16px;display:block}
.spin{width:20px;height:20px;border:2px solid rgba(0,255,136,.2);border-top-color:var(--green);border-radius:50%;animation:spin .8s linear infinite;margin:0 auto 16px}
@keyframes spin{to{transform:rotate(360deg)}}
.tos{margin-top:24px;padding:12px 16px;background:rgba(255,179,71,.05);border:1px solid rgba(255,179,71,.15);border-radius:4px;font-size:10px;color:var(--muted);line-height:1.9}
.tos strong{color:var(--amber)}
@media(max-width:650px){.row{grid-template-columns:1fr 1fr}.row .fl:first-child{grid-column:1/-1}}
</style>
</head>
<body>
<div class="wrap">
  <header>
    <div><h1>TORN INVESTMENTS</h1><div class="sub">Real-time portfolio tracker</div></div>
    <div class="meta">
      <span class="dot" id="dot"></span><span id="stxt">Connecting...</span><br>
      Last update: <span id="lu">—</span><br>
      Next refresh: <span id="nr">—</span>
    </div>
  </header>
  <div class="cards">
    <div class="card"><div class="clabel">Total Invested</div><div class="cval neu" id="si">—</div></div>
    <div class="card"><div class="clabel">Current Value</div><div class="cval" id="sv">—</div></div>
    <div class="card"><div class="clabel">Profit / Loss</div><div class="cval" id="sp">—</div><div class="csub" id="sr">ROI: —</div></div>
    <div class="card"><div class="clabel">Positions</div><div class="cval neu" id="sc">—</div></div>
  </div>
  <div class="sh"><h2>Positions</h2><span class="badge" id="bc">0</span></div>
  <div id="list" class="list"><div class="empty"><div class="spin"></div><p>Loading...</p></div></div>
  <div class="strip">
    <span>Auto-refresh every <strong id="ttl">60</strong>s &nbsp;·&nbsp; API key secured server-side &nbsp;·&nbsp; Read-only</span>
    <button class="btn" onclick="load()">REFRESH NOW</button>
  </div>
  <div class="tos"><strong>API ToS:</strong> &nbsp; Data Storage: <em>Not stored</em> &nbsp;|&nbsp; Sharing: <em>Nobody</em> &nbsp;|&nbsp; Purpose: <em>Personal tracking</em> &nbsp;|&nbsp; Key: <em>Server env only / not shared</em> &nbsp;|&nbsp; Access: <em>Limited — investments only</em></div>
</div>
<script>
const $=id=>document.getElementById(id);
const money=n=>'$'+Math.abs(n).toLocaleString('en-US',{maximumFractionDigits:0});
const pct=n=>(n>=0?'+':'')+n.toFixed(2)+'%';
function ftime(s){if(s==null)return'—';if(s<=0)return'MATURED';const h=Math.floor(s/3600),m=Math.floor((s%3600)/60),sec=s%60;return h>0?h+'h '+m+'m':m>0?m+'m '+sec+'s':sec+'s'}
let invs=[],nrAt=0,cdInt=null,rfInt=null;
function ticks(){
  const now=Math.floor(Date.now()/1000);
  invs.forEach(v=>{
    const el=$('cd'+v.id);if(!el||v.maturity_ts==null)return;
    const r=Math.max(0,v.maturity_ts-now);
    el.textContent=r<=0?'MATURED':ftime(r);el.className='cd'+(r<=0?' done':'');
    const pb=$('pb'+v.id);
    if(pb&&v.duration){pb.style.width=Math.min(100,(v.duration-r)/v.duration*100)+'%'}
  });
  $('nr').textContent=Math.max(0,nrAt-now)+'s';
}
function row(v){
  const pc=v.profit>0?'pos':v.profit<0?'neg':'neu';
  const time_html=v.maturity_ts?`<div class="fl"><span class="lbl">Time Left</span><span class="cd" id="cd${v.id}">—</span><div class="pb-wrap"><div class="pb" id="pb${v.id}" style="width:0%"></div></div></div>`:'<div class="fl"></div>';
  return`<div class="row${v.mature?' mat':''}">
    <div class="fl"><span class="fname">${v.name}</span><span class="lbl">ID #${v.id}</span></div>
    <div class="fl"><span class="lbl">Invested</span><span>${money(v.invested)}</span></div>
    <div class="fl"><span class="lbl">Value</span><span class="${v.current_value>=v.invested?'pos':'neg'}">${money(v.current_value)}</span></div>
    <div class="fl"><span class="lbl">Profit</span><span class="${pc}">${v.profit>=0?'+':''}${money(v.profit)}</span><span class="lbl ${v.roi_pct>=0?'pos':'neg'}">${pct(v.roi_pct)}</span></div>
    ${time_html}</div>`;
}
async function load(){
  try{
    const res=await fetch('/api/investments'),d=await res.json();
    if(d.error){
      $('dot').className='dot err';$('stxt').textContent='Error';
      $('list').innerHTML=`<div class="empty"><span class="icon">!</span><p>${d.error}</p></div>`;return;
    }
    $('dot').className='dot';$('stxt').textContent='Live';
    const s=d.summary;
    $('si').textContent=money(s.total_invested);
    $('sv').textContent=money(s.total_current_value);$('sv').className='cval '+(s.total_current_value>=s.total_invested?'pos':'neg');
    $('sp').textContent=(s.total_profit>=0?'+':'')+money(s.total_profit);$('sp').className='cval '+(s.total_profit>=0?'pos':'neg');
    $('sr').textContent='ROI: '+pct(s.total_roi_pct);
    $('sc').textContent=s.investment_count;$('bc').textContent=s.investment_count;
    $('lu').textContent=d.fetched_at_human;$('ttl').textContent=d.cache_ttl||60;
    invs=d.investments||[];
    $('list').innerHTML=invs.length?invs.map(row).join(''):`<div class="empty"><span class="icon">o</span><p>No active investments found.</p></div>`;
    nrAt=Math.floor(Date.now()/1000)+(d.next_refresh_in||d.cache_ttl||60);
    if(rfInt)clearTimeout(rfInt);rfInt=setTimeout(load,((d.next_refresh_in||d.cache_ttl||60)+1)*1000);
    if(cdInt)clearInterval(cdInt);cdInt=setInterval(ticks,1000);ticks();
  }catch(e){
    $('dot').className='dot err';$('stxt').textContent='Offline';
    $('list').innerHTML=`<div class="empty"><span class="icon">!</span><p>Cannot reach server.<br>${e.message}</p></div>`;
  }
}
load();
</script>
</body>
</html>"""

@app.route("/")
def index():
    return Response(HTML, mimetype="text/html")

@app.route("/api/investments")
def api_investments():
    if API_KEY == "PASTE_YOUR_KEY_HERE" or not API_KEY:
        return jsonify({"error": "No API key set. Open app.py and paste your Torn API key on line 13."}), 400
    d = get_data()
    if "error" in d:
        return jsonify(d), 502
    d["next_refresh_in"] = max(0, CACHE_TTL - int(time.time() - _cache["ts"]))
    return jsonify(d)

@app.route("/api/status")
def api_status():
    return jsonify({"status": "ok", "key_set": API_KEY != "PASTE_YOUR_KEY_HERE" and bool(API_KEY)})

if __name__ == "__main__":
    print("=" * 50)
    print("  Torn Investment Tracker")
    print("=" * 50)
    if API_KEY == "PASTE_YOUR_KEY_HERE" or not API_KEY:
        print("  [!] No API key set!")
        print("      Open app.py and edit line 13:")
        print('      API_KEY = "your_key_here"')
    else:
        masked = API_KEY[:4] + "*" * (len(API_KEY) - 8) + API_KEY[-4:]
        print(f"  [OK] Key: {masked}")
    print("  [OK] Open: http://localhost:5000")
    print("=" * 50)
    app.run(debug=False, host="0.0.0.0", port=5000)
