#!/usr/bin/env python3
"""Which robots pay, and how much — the crawl test's report (publish/crawlpay.js).

    python3 tools/crawlpay_report.py [days]        # default 7

Writes ~/Desktop/1 — NEXT UP/CRAWL TEST — which robots take, which give back (<date>).txt
and prints the same text. Reads traffic_eye over the Analytics Engine SQL API
with the nanobotco-fleet token (~/.config/nanobotco/keys.json → cloudflare).

Three tables:
  TAKE    requests and distinct pages per AI agent
  GIVE    people arriving from an AI answer page (referrer host), and fetches a
          person triggered by asking (ChatGPT-User, Claude-User, Perplexity-User…)
  PAY     requests that carried a price header or a signed identity, and — while
          CRAWLPAY_ASK is on — the share of each training crawler's requests
          that met a 402 (one page in ten; a share falling below ~10% means
          the crawler is steering around the ask)
"""
import datetime as dt
import json
import os
import sys
import urllib.request

DAYS = int(sys.argv[1]) if len(sys.argv) > 1 else 7
KEYS = json.load(open(os.path.expanduser("~/.config/nanobotco/keys.json")))["cloudflare"]
URL = f"https://api.cloudflare.com/client/v4/accounts/{KEYS['account_id']}/analytics_engine/sql"
SITE = "motdang.net"
WHEN = f"timestamp > NOW() - INTERVAL '{DAYS}' DAY"
AI_HOSTS = ["chatgpt.com", "chat.openai.com", "perplexity.ai", "www.perplexity.ai", "claude.ai",
            "gemini.google.com", "copilot.microsoft.com", "www.meta.ai", "meta.ai", "you.com",
            "chat.deepseek.com", "grok.com", "chat.mistral.ai", "duckduckgo.com"]
PERSON_FETCH = ["ChatGPT-User", "Claude-User", "Perplexity-User", "MistralAI-User", "DuckAssistBot"]
PROBE = "/__crawlpay-check"


def sql(q):
    req = urllib.request.Request(URL, data=(q + " FORMAT JSON").encode(),
                                 headers={"Authorization": f"Bearer {KEYS['api_token']}"})
    return json.load(urllib.request.urlopen(req, timeout=60))["data"]


def n(x):
    return f"{round(float(x)):,}"


take = sql(f"""SELECT blob3 AS agent, SUM(_sample_interval*double1) AS req,
  COUNT(DISTINCT blob4) AS pages,
  SUM(IF(blob6='402', _sample_interval*double1, 0.0)) AS asked
  FROM traffic_eye WHERE blob1='{SITE}' AND blob2='ai' AND {WHEN}
  GROUP BY agent ORDER BY req DESC""")
hosts = ",".join(f"'{h}'" for h in AI_HOSTS)
give = sql(f"""SELECT blob7 AS ref, SUM(_sample_interval*double1) AS n FROM traffic_eye
  WHERE blob1='{SITE}' AND blob2='human' AND blob7 IN ({hosts}) AND {WHEN}
  GROUP BY ref ORDER BY n DESC""")
pay = sql(f"""SELECT blob3 AS agent, blob10 AS arm, blob11 AS price, blob12 AS signer,
  SUM(_sample_interval*double5) AS n FROM traffic_eye
  WHERE blob1='{SITE}' AND blob9='crawlpay' AND blob4 NOT LIKE '{PROBE}%' AND {WHEN}
  GROUP BY agent, arm, price, signer ORDER BY n DESC LIMIT 40""")

today = dt.date.today().isoformat()
out = [f"CRAWL TEST — {SITE}, last {DAYS} days, to {today}", ""]
out += ["TAKE — AI agents reading the site", "",
        f"  {'agent':<22}{'requests':>12}{'pages':>10}{'met 402':>10}"]
for r in take:
    share = f"{100 * float(r['asked']) / float(r['req']):.1f}%" if float(r["asked"]) else "–"
    out.append(f"  {r['agent']:<22}{n(r['req']):>12}{n(r['pages']):>10}{share:>10}")
out += ["", "GIVE — people sent back", ""]
fetch = [r for r in take if r["agent"] in PERSON_FETCH]
for r in fetch:
    out.append(f"  {r['agent']:<22}{n(r['req']):>12}  fetches a person asked for")
for r in give:
    out.append(f"  {r['ref']:<22}{n(r['n']):>12}  people arriving from an AI answer")
if not fetch and not give:
    out.append("  none counted")
out += ["", "PAY — requests saying they can pay, or signed", ""]
for r in pay:
    out.append(f"  {r['agent']:<22}{n(r['n']):>8}  {r['arm']:<8} {r['price'] or '-':<32} {r['signer'] or '-'}")
if not pay:
    out.append("  none yet")
text = "\n".join(out) + "\n"
print(text)
dest = os.path.expanduser(f"~/Desktop/1 — NEXT UP/CRAWL TEST — which robots take, which give back ({today}).txt")
open(dest, "w").write(text)
print(dest)
