# A/B — robot arm vs human arm, 2026-10-01

Nan's call, 2026-09-28: $20 per arm, both start 2026-10-01 12:00 ICT. The robot arm is
mine; Nan runs the human arm, a boosted Facebook post.

## What "robot audience" can be bought for $20

Three things count as robot readers here. Only one of them sells placement:

| Door | What money buys | Status (searched 2026-09-28) |
|---|---|---|
| Pretraining crawl (GPTBot, CCBot, ClaudeBot…) | nothing, since no one sells crawl priority | robots.txt, llms.txt, llms-full.txt are already live, at $0 |
| Retrieval at answer time | nothing directly | answer pages are the lever, at $0 |
| **Ads inside an assistant's answer** | **CPC placement** | **ChatGPT Ads Manager: self-serve, no minimum, $2–8 CPC.** Perplexity withdrew its ads. Copilot ads only come through Microsoft Ads Performance Max. |

So the robot arm is a **ChatGPT Ads Manager** campaign: a person reading an assistant's
answer. The human arm is a person reading a feed. Both land on the same page.

Not verified: whether ChatGPT ads serve in Thailand (launch geo was US-first). If
Ads Manager won't allow TH targeting, fall back to Microsoft Ads (Copilot placement)
with the same $20, the same copy, and a TH geo target. Write down which one ran.

## The post (robot arm creative)

Landing, same for both arms except the tag:

- Robot: `https://motdang.net/?utm_source=chatgpt&utm_medium=paid&utm_campaign=ab-2610`
- Human: `https://motdang.net/?utm_source=facebook&utm_medium=paid&utm_campaign=ab-2610`

The Worker keeps `url.search` through its redirects (publish/worker.js:368, :382), so the tag survives.

Brand: **มดแดง Mot Dang**

Headlines. Run all three and let the platform rotate them. The character limits are my guess, so check them in the Ads Manager form:

1. `Chiang Mai, in Thai and English`
2. `What's near you in Chiang Mai`
3. `Chiang Mai & Chiang Rai directory`

Descriptions:

1. `Temples, clinics, food, toilets and pharmacies across both provinces, with each place named in Thai and English.`
2. `Look up a place, its phone number and its hours. Works on a phone, and keeps working when the signal drops.`

Image: `docs/card.png`, which is the site's brand card at 1200×630. The ad form may want a square, and none is built yet.

Context targeting (ChatGPT matches on conversation topics, not keywords):
Chiang Mai travel · living in Chiang Mai · Chiang Rai · Thailand expat · Thai
food · temples Thailand · medical care Thailand.

The copy only describes what the site does. It makes no promise and no comparison.

## Controls

| Setting | Robot arm | Human arm |
|---|---|---|
| Platform | ChatGPT Ads Manager (fallback: Microsoft Ads) | Facebook boost |
| Budget | $20 lifetime | $20 lifetime |
| Window | 2026-10-01 12:00 → 2026-10-08 12:00 ICT | same |
| Bid | CPC, auto | Boost objective: link clicks (not engagement, or the arms stop measuring the same thing) |
| Geo | Thailand; CM + CR if the form allows | same |
| Landing | tagged URL above | tagged URL above |

Only the platform and the creative should differ between the arms. Keep the audience and the timing the same.

**Baseline:** the untagged arrivals for 2026-09-24 12:00 → 2026-10-01 12:00. If the
arrival count described on /privacy.html is running on the live Worker, this is its
`utm_source`-free share. (This clone's publish/worker.js has no logging code, so
check that it exists on the machine that deploys.)

## What gets read on 2026-10-08

Primary metric, read from each ad manager: **cost per link click** = spend ÷ link clicks.
Also record impressions, CTR and spend actually delivered.

Secondary metric, read from the site: arrivals where `utm_campaign=ab-2610`, split by `utm_source`,
against the baseline.
The log has no identifiers, so one visitor's pages can't be linked into a visit.
Landings are the only site-side number.

## The expected result

At $2–8 CPC, $20 buys **3–10 clicks** in the robot arm. A Thai-geo Facebook boost
usually clears $0.05–0.30 CPC (from training, possibly stale), which is roughly 70–400 clicks.
The human arm will win cost per click by one to two orders of magnitude almost
certainly. The only open question is how large the gap is. Ten clicks can't
separate conversion quality, so treat the robot arm's second-order numbers as anecdotes.

What the robot arm can show that the human arm can't:
- whether ChatGPT serves the ad at all against Chiang Mai topics (impressions > 0)
- which headline it picks (the rotation report)
- whether organic `utm_source=chatgpt.com` arrivals move during and after the
  window. That tag is ChatGPT's own tag on organic citations and is separate
  from this campaign's `chatgpt`.

## Log

| Date | Arm | Spend | Impr. | Clicks | CPC | Site landings | Note |
|---|---|---|---|---|---|---|---|
| 2026-10-01 | R | | | | | | platform used: |
| 2026-10-01 | H | | | | | | |
| 2026-10-08 | R | | | | | | |
| 2026-10-08 | H | | | | | | |

Sources:
[Lapis, AI-assistant ads 2026](https://www.trylapis.com/resources/advertising-in-ai-assistants-chatgpt-gemini-perplexity) ·
[AuthorityTech, ChatGPT CPC](https://authoritytech.io/blog/chatgpt-advertising-brands-2026) ·
[Astiva, AI search ads status](https://astiva.ai/blog/ai-search-ads-2026-zero-click-market) ·
[Remway, self-serve no minimum](https://www.remway.app/chatgpt-ads-self-serve/)
