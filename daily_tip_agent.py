#!/usr/bin/env python3
"""
Tight Lines Daily Tip Agent
Generates a daily fishing tip post with a static HTML page + Pexels photo
Run daily via cron — outputs to projects/tightlines-blog/posts/
"""

import html
import json, os, random, urllib.request, math
from datetime import datetime, timedelta
from pathlib import Path

BLOG_DIR = Path("/home/kodaagentmt/.openclaw/workspace/projects/tightlines-blog")
POSTS_DIR = BLOG_DIR / "posts"
IMAGES_DIR = BLOG_DIR / "images"

# --- Solunar Calculator ---
MOON_CYCLE = 29.53058867
KNOWN_NEW_MOON = datetime(2000, 1, 6)

def get_moon_phase(date):
    days = (date - KNOWN_NEW_MOON).total_seconds() / 86400
    return (days % MOON_CYCLE) / MOON_CYCLE

def moon_name(phase):
    names = ['🌑', '🌒', '🌓', '🌔', '🌕', '🌖', '🌗', '🌘']
    return names[int(phase * 8) % 8]

def fmt(h):
    hh = int(h)
    mm = int((h - hh) * 60)
    suffix = 'AM' if hh < 12 else 'PM'
    hh = hh % 12 or 12
    return f"{hh}:{mm:02d} {suffix}"

def lunar_transit(date, lon):
    days = (date - KNOWN_NEW_MOON).total_seconds() / 86400
    return (20 + ((days % MOON_CYCLE) / MOON_CYCLE) * 24 - lon / 15) % 24

def sunrise_sunset(lat, lon, date):
    lat_r = lat * math.pi / 180
    doy = (date - datetime(date.year, 1, 1)).days
    decl = 23.45 * math.sin(2 * math.pi * (284 + doy) / 365) * math.pi / 180
    cos_h = -math.tan(lat_r) * math.tan(decl)
    if cos_h < -1:
        h_deg = 180
    elif cos_h > 1:
        h_deg = 0
    else:
        h_deg = math.acos(cos_h) * 180 / math.pi
    noon = 12 - lon / 15
    tz = -7  # MDT
    sr = (noon - h_deg / 15 + tz) % 24
    ss = (noon + h_deg / 15 + tz) % 24
    return sr, ss

def solunar_forecast():
    """Return today's solunar forecast dict."""
    today = datetime.now()
    lat, lon = 45.5, -110.0
    phase = get_moon_phase(today)
    sr, ss = sunrise_sunset(lat, lon, today)
    lt = lunar_transit(today, lon)
    tz = -7
    major = sorted([(lt + tz) % 24, (lt + 12.42 + tz) % 24])
    minor = sorted([(major[0] + 6.21) % 24, (major[1] + 6.21) % 24])
    illum = round(abs(phase - 0.5) * 200)
    return {
        'date': today.strftime('%B %d, %Y'),
        'moon': moon_name(phase),
        'illum': illum,
        'sr': fmt(sr),
        'ss': fmt(ss),
        'major1': fmt(major[0]),
        'major2': fmt(major[1]),
        'minor1': fmt(minor[0]),
        'minor2': fmt(minor[1]),
    }

def solunar_rss_item(sol):
    """Format today's solunar data as an RSS <item>."""
    date_str = datetime.now().strftime("%a, %d %b %Y %H:%M:%S MDT")
    desc = (
        f"{sol['moon']} {sol['illum']}% illuminated. "
        f"Major feeding: {sol['major1']} & {sol['major2']}. "
        f"Minor feeding: {sol['minor1']} & {sol['minor2']}. "
        f"Sunrise {sol['sr']} / Sunset {sol['ss']}. "
        f"Data for ~45°N, 110°W (Mountain Time)."
    )
    slug = datetime.now().strftime("solunar-%Y%m%d")
    return (
        f'\n    <item>'
        f'\n      <title>Solunar Forecast — {sol["date"]}</title>'
        f'\n      <link>https://kodaagentmt-max.github.io/tightlines-blog/solunar.html</link>'
        f'\n      <guid isPermaLink="true">https://tightlinesblog.com/posts/{slug}</guid>'
        f'\n      <pubDate>{date_str}</pubDate>'
        f'\n      <description><![CDATA[{desc}]]></description>'
        f'\n    </item>'
    )

PEXELS_KEY = "YkKkFXmfk334l9uKq8iPBnzoaFcvJOTbnAhO1awjRudPTOfJWX1BAKZE"

# Pre-approved image library — vetted by KC
APPROVED_IMAGES = [
    "13740880", "4376190", "4343735", "13740883", "4830329", "7454998", "14062103", "10112459",  # Bass fish
    "6478088", "4822241", "4822301", "6478099", "6478171", "14339533", "6478199", "4822245",       # Lures
    "294674", "14339521", "4828161", "1165125", "26690286", "10922533", "5537642", "31910643",     # Fishermen
]

def get_approved_photo():
    """Pick a random approved image and return a photo dict."""
    chosen_id = random.choice(APPROVED_IMAGES)
    return {
        "url": f"https://kodaagentmt-max.github.io/tightlines-blog/images/approved_{chosen_id}.jpg",
        "local_path": f"../images/approved_{chosen_id}.jpg",
        "photographer": "Pexels",
        "alt": "Fishing photography"
    }

FISHING_TIPS = [
    {
        "tag": "Fishing Tips",
        "emoji": "🌤️",
        "title": "Why Overcast Days Are the Best Days to Fish",
        "body": "Most anglers pack up their rods and head home when clouds roll in. This is one of the most costly mistakes in fishing. Overcast skies do several things that make fish feed more aggressively: First, they diffuse direct sunlight, reducing visibility underwater so fish feel safer prowling the shallows. Second, cloud cover typically coincides with dropping barometric pressure — a trigger that activates feeding instincts in nearly all freshwater fish. Third, choppy water from subtle winds breaks up the surface silhouette, making fish less line-shy. Next time dark clouds gather, stay on the water. Fish the mid-morning hours when clouds are thickest, focus on points and shallow flats, and try slower presentations — the fish will be hungry and bold.",
        "category": "tips",
        "pexels_query": "overcast river fishing mountains"
    },
    {
        "tag": "Fishing Tips",
        "emoji": "⏱️",
        "title": "The 3-Second Rule for Lure Retrieval",
        "body": "Retrieval speed is the most overlooked variable in fishing. Most anglers strip way too fast, yanking the fly or lure past the fish's strike zone. The fix is deceptively simple: pause for a full 3 seconds after every strip. This gives the fly time to sink, drift naturally, and trigger the predatory strike instinct — especially in cold water or when fish are sluggish. The pause also lets you feel the subtle, almost imperceptible bite that happens when the fish isn't committed. Once you start counting 'one-Mississippi' pauses, you'll notice hookups that you were previously missing entirely. Pro tip: count the pause out loud so you don't rush it. After 30 days of practice, this becomes muscle memory.",
        "category": "tips",
        "pexels_query": "fishing lure water close up"
    },
    {
        "tag": "Regional Fishing",
        "emoji": "🏔️",
        "title": "Spring Runoff: Where to Fish When the Rivers Are High",
        "body": "Spring runoff turns most rivers chocolate-milk brown. But the tailwaters and spring creeks that stay clear — like the Jefferson, Madison, and other clear spring creeks — produce consistently during runoff.",
        "category": "montana",
        "pexels_query": "montana river spring runoff fly fishing"
    },
    {
        "tag": "Gear Reviews",
        "emoji": "🪝",
        "title": "The Best Fluorocarbon Leaders for Your Waters",
        "body": "After testing 12 fluorocarbon leaders in local rivers, three stood out: Seaguar InvizX for its knot strength, Pure Fluorocarbon for sensitivity in cold water, and Berkley Vanish for the best value.",
        "category": "gear",
        "pexels_query": "fishing gear tackle box flourocarbon"
    },
    {
        "tag": "Fly Fishing",
        "emoji": "🪰",
        "title": "The Mysis Shrimp Impostor That Outfishes the Real Thing",
        "body": "The Mysis shrimp is one of the most important patterns for stillwater fishing, particularly for feeding rainbows and browns in lakes with significant invertebrate populations. But most anglers tie it wrong in two critical ways that cost them fish. First, the collar angle: the hackle fibers should be tied at a 45-degree backward angle, not swept back. This gives the pattern a swimming motion on the retrieve that mimics a swimming shrimp — not a dying one. Second, bead placement: the tungsten bead should be positioned at the front of the hook shank, not centered, to keep the pattern riding hook-point-up. This prevents foul-ups and ensures better bottom contact. tying the pattern with these two adjustments will immediately set you apart from most anglers on the water.",
        "category": "fly",
        "pexels_query": "fly fishing river trout wet fly"
    },
    {
        "tag": "Ice Fishing",
        "emoji": "🧊",
        "title": "Late Ice Walleye: The Setup Most Anglers Miss",
        "body": "Late ice is the most underutilized opportunity in fishing. Most anglers have already put their gear away, but the last two weeks of ice produce some of the best walleye action of the entire year. The key adjustment most anglers miss is line diameter. As ice thins and light penetrates deeper water, walleye become line-shy — they see the main line and become cautious. Dropping from 6lb to 4lb test fluorocarbon makes a dramatic difference in bite detection and hookup rates. You'll feel subtle strikes that would previously be masked, and the thinner diameter sinks faster, keeping your presentation in the strike zone longer. Additionally, downsizing your jig from 3/8oz to 1/4oz matches the more subtle feeding window of late-season walleye. Combine both and your ratio climbs dramatically.",
        "category": "ice",
        "pexels_query": "ice fishing winter frozen lake walleye"
    },
    {
        "tag": "Industry News",
        "emoji": "📰",
        "title": "FWP Proposes New Cutthroat Protection Zones",
        "body": "The proposed regulations would close 14 miles of the Yellowstone to protect native westslope cutthroat. Public comment period ends May 15. If you fish the Yellowstone, now is the time to make your voice heard.",
        "category": "news",
        "pexels_query": "yellowstone river montana fly fishing"
    },
    {
        "tag": "Fishing Tips",
        "emoji": "🌡️",
        "title": "Water Temperature: The Number Every Serious Angler Tracks",
        "body": "Understanding water temperature is the single most powerful tool in fishing. Fish are cold-blooded, meaning their metabolic rate is governed entirely by the temperature of the water around them. Below 40°F, trout become sluggish, feeding only sporadically as their bodies slow. Between 45-55°F, everything changes — digestion accelerates, aggressive feeding behavior kicks in, and fish actively patrol rather than holding static. Above 65°F, things get complicated: metabolism continues climbing but oxygen saturation in water drops precipitously, creating a situation where fish are hungry but physically limited in their ability to process food. Knowing the temperature of the water you're fishing tells you what retrieval speed to use, where fish will position in the water column, and what patterns will trigger response. Carry a simple thermometer and log your catches — the pattern data over time is invaluable.",
        "category": "tips",
        "pexels_query": "thermometer fishing tackle water"
    },
    {
        "tag": "Regional Fishing",
        "emoji": "🌊",
        "title": "Reading River Currents: The Key Eddy Every Angler Should Find",
        "body": "Eddy formation is one of the most fundamental concepts in river fishing, and mastering it separates consistently productive anglers from the casual crowd. An eddy forms when current hits an obstruction — a rock, a submerged log, a river bend — and creates a circular flow pattern on the downstream side. The water in this circulation is calmer, food particles collect there naturally, and fish can hold position with minimal energy expenditure. Reading a river for eddies means looking for any change in the banks or bottom topography that interrupts the current. The largest, most patient fish typically hold in the deepest part of the eddy, not the obvious tail-out area. Cast upstream of the eddy and let your fly or lure drift naturally into the current seam — this is where most productive takes occur, right at the boundary between the circulating water and the main current.",
        "category": "montana",
        "pexels_query": "river eddy calm water fishing rapids"
    },
    {
        "tag": "Tournament Updates",
        "emoji": "🏆",
        "title": "Spring Classic Recap: New Pattern Emerged as Key",
        "body": "The winning pattern at last weekend's Spring Classic on major reservoirs was a simple olive Wooly Bugger fished on a 7-weight sink tip, stripped in 4-inch bursts. Water temperature was the deciding factor.",
        "category": "tournament",
        "pexels_query": "fishing tournament awards trophy winner"
    },
]

NEWS_ITEMS = [
    "Montana Fish Wildlife and Parks announced extended fishing hours on three Madison River segments starting May 1.",
    "New catch-and-release regulations for 2026 will require barbless hooks on designated water — check your state regulations for specific waterways affected.",
    "Hebgen Lake is now ice-free. Anglers are reporting good catches of brown trout near the incoming channels.",
    "The Missouri River below Fort Peck is running high but clear — producing solid walleye numbers in the tailrace.",
    "Crowded boat ramps are the top complaint at Montana state parks. FWP is piloting a new reservation system for seven high-traffic ramps this summer.",
]

# ─── Pexels ────────────────────────────────────────────────────────────────────
def fetch_pexels_image(query, retries=3):
    url = f"https://api.pexels.com/v1/search?query={urllib.parse.quote(query)}&per_page=5&orientation=landscape"
    headers = {
        "Authorization": PEXELS_KEY,
        "User-Agent": "TightLinesBlog/1.0 (kodaagentmt; contact@kodaagentmt.com)"
    }
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read())
                photos = data.get("photos", [])
                if photos:
                    chosen = random.choice(photos)
                    return {
                        "url": chosen["src"]["large"],
                        "thumb": chosen["src"]["medium"],
                        "original": chosen["src"]["original"],
                        "photographer": chosen["photographer"],
                        "alt": chosen.get("alt", query)
                    }
        except Exception as e:
            print(f"  [Pexels attempt {attempt+1} failed: {e}]")
    return None

# ─── HTML Generation ─────────────────────────────────────────────────────────────
def generate_post_html(tip, photo, news):
    date_str = datetime.now().strftime("%B %d, %Y")
    slug = f"{tip['category']}-{date_str.replace(' ', '-').replace(',','').lower()}"
    news_html = f"<p class='news-blurb'>📰 {news}</p>" if news else ""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{tip['title']} — Tight Lines Tackle Box</title>
  <meta name="description" content="{tip['body'][:155]}">
  <meta property="og:title" content="{tip['title']}">
  <meta property="og:description" content="{tip['body'][:200]}">
  <meta property="og:image" content="{photo['url'] if photo else ''}">
  <meta property="og:type" content="article">
  <link rel="stylesheet" href="../style.css">
  <style>
    body {{ background: #0a1628; color: #c8dff5; font-family: 'Georgia', serif; margin: 0; }}
    .container {{ max-width: 720px; margin: 0 auto; padding: 40px 20px; }}
    .hero-img {{ width: 100%; max-height: 420px; object-fit: cover; border-radius: 8px; margin-bottom: 32px; }}
    .tag {{ font-size: 12px; text-transform: uppercase; letter-spacing: 2px; color: #00d4aa; margin-bottom: 12px; }}
    h1 {{ font-family: 'Georgia', serif; font-size: 28px; color: #fff; margin-bottom: 16px; line-height: 1.3; }}
    .date {{ font-size: 13px; color: #7a9cc6; margin-bottom: 28px; border-bottom: 1px solid #1a4a7a; padding-bottom: 16px; }}
    .body {{ font-size: 17px; line-height: 1.8; color: #c8dff5; margin-bottom: 24px; }}
    .news-blurb {{ background: #0f2847; border-left: 3px solid #ffd700; padding: 14px 18px; font-size: 14px; color: #7a9cc6; margin: 28px 0; }}
    .photo-credit {{ font-size: 11px; color: #7a9cc6; text-align: right; margin-top: -24px; margin-bottom: 28px; }}
    .back {{ display: inline-block; margin-top: 32px; color: #00d4aa; text-decoration: none; font-size: 14px; }}
    .back:hover {{ color: #ffd700; }}
  </style>
</head>
<body>
  <div class="container">
    {f"<img class='hero-img' src='{photo['local_path']}' alt='{photo['alt']}'>" if photo else ""}
    <div class="tag">{tip['tag']}</div>
    <h1>{tip['title']}</h1>
    <div class="date">📅 {date_str} — Tight Lines Daily Tip</div>
    <p class="body">{tip['body']}</p>
    {news_html}
    {"<p class='photo-credit'>📷 Photo by {photo['photographer']} on Pexels</p>" if photo else ""}
    <a class="back" href="../index.html">← Back to Tight Lines</a>
  </div>
</body>
</html>"""


def generate_index_html(posts):
    posts_html = ""
    for p in posts:
        img_html = f"<img src='{p['local_path']}' alt='{p['photo']['alt']}' style='width:100%;height:160px;object-fit:cover;'>" if p.get('photo') else f"<div style='width:100%;height:160px;display:flex;align-items:center;justify-content:center;font-size:40px;background:#1a4a7a;'>{p['emoji']}</div>"
        posts_html += f"""
    <div class="post-card">
      <a href="posts/{p['slug']}.html">
        <div class="post-thumb">{img_html}</div>
      </a>
      <div class="post-body">
        <div class="post-tag">{p['tag']}</div>
        <a class="post-title" href="posts/{p['slug']}.html">{p['title']}</a>
        <p class="post-excerpt">{p['body'][:120]}...</p>
        <div class="post-meta">📅 {p['date']}</div>
      </div>
    </div>"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>🎣 Tight Lines Tackle Box — Daily Fishing Tips</title>
  <meta name="description" content="Daily fishing tips, tricks, and industry news.">
  <link rel="alternate" type="application/rss+xml" title="Tight Lines RSS" href="rss.xml">
  <link href="https://fonts.googleapis.com/css2?family=Special+Elite&family=Roboto+Slab:wght@400;700&display=swap" rel="stylesheet">
  <style>
    :root {{ --bg: #0a1628; --card: #0f2847; --water: #1a4a7a; --accent: #00d4aa; --gold: #ffd700; --white: #fff; --dim: #7a9cc6; --text: #c8dff5; }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ background: var(--bg); color: var(--text); font-family: 'Roboto Slab', serif; line-height: 1.7; min-height: 100vh; }}
    a {{ color: var(--accent); text-decoration: none; }}
    a:hover {{ color: var(--gold); }}
    .top-bar {{ background: var(--card); border-bottom: 2px solid var(--water); padding: 12px 20px; display: flex; justify-content: space-between; align-items: center; }}
    .top-bar .brand {{ font-family: 'Special Elite', cursive; font-size: 18px; color: var(--accent); }}
    .container {{ max-width: 900px; margin: 0 auto; padding: 30px 20px; }}
    .hero {{ text-align: center; padding: 30px 20px; margin-bottom: 30px; }}
    .hero h1 {{ font-family: 'Special Elite', cursive; font-size: 36px; color: var(--accent); margin-bottom: 8px; }}
    .hero .tagline {{ font-size: 15px; color: var(--dim); }}
    .section-title {{ font-family: 'Special Elite', cursive; font-size: 20px; color: var(--accent); margin-bottom: 20px; padding-bottom: 10px; border-bottom: 2px solid var(--water); }}
    .posts-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 20px; margin-bottom: 40px; }}
    .post-card {{ background: var(--card); border: 1px solid var(--water); overflow: hidden; transition: all 0.2s; }}
    .post-card:hover {{ border-color: var(--accent); transform: translateY(-2px); }}
    .post-thumb {{ height: 160px; overflow: hidden; }}
    .post-body {{ padding: 16px; }}
    .post-tag {{ font-size: 9px; text-transform: uppercase; letter-spacing: 1.5px; color: var(--accent); margin-bottom: 8px; }}
    .post-title {{ font-size: 15px; color: var(--white); margin-bottom: 8px; line-height: 1.4; display: block; }}
    .post-excerpt {{ font-size: 12px; color: var(--dim); margin-bottom: 10px; display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden; }}
    .post-meta {{ font-size: 10px; color: var(--dim); }}
    footer {{ text-align: center; padding: 30px; border-top: 1px solid var(--water); color: var(--dim); font-size: 13px; }}
    .rss-btn {{ background: rgba(255,215,0,0.1); border: 1px solid var(--gold); color: var(--gold); padding: 5px 12px; font-size: 11px; border-radius: 3px; }}
  </style>
</head>
<body>
  <div class="top-bar">
    <div class="brand">🎣 Tight Lines Tackle Box</div>
    <a href="rss.xml"><button class="rss-btn">📡 RSS</button></a>
  </div>
  <div class="container">
    <div class="hero">
      <h1>🎣 Tight Lines Tackle Box</h1>
      <p class="tagline">Daily fishing tips, tricks, and industry news</p>
    </div>
    <div class="section-title">📖 Latest Tips & News</div>
    <div class="posts-grid">
{posts_html}
    </div>
  </div>
  <footer>
    <p><img src="images/tagsoup-logo.png" alt="Tight Lines" style="height:28px;vertical-align:middle;"> Tight Lines Tackle Box — Your source for outdoor fishing knowledge since 2024</p>
  </footer>
</body>
</html>"""


# ─── Seasonal filter ───────────────────────────────────────────────────────────
import datetime as _dt

def _is_seasonal(tip):
    """Return True if the tip is appropriate for the current month.
    Ice fishing tips -> Nov through Mar only.
    All other tips -> always OK.
    """
    tag = tip.get('tag', '')
    if 'Ice' in tag or 'ice' in tip.get('category', ''):
        month = datetime.now().month
        return month in (11, 12, 1, 2, 3)
    return True

# ─── Main ─────────────────────────────────────────────────────────────────────
def run():
    import urllib.parse
    today_id = datetime.now().strftime("%Y%m%d")
    POSTS_DIR.mkdir(exist_ok=True)

    # Load existing posts
    index_file = BLOG_DIR / "posts.json"
    all_posts = json.load(open(index_file)) if index_file.exists() else []

    # Skip if posted today — but always update RSS with today's solunar data
    if any(p.get('id') == today_id for p in all_posts):
        print(f"[{datetime.now()}] Already posted today ({today_id}). Skipping new tip.")
        # Still update RSS with today's solunar forecast
        _update_solunar_in_rss(all_posts)
        print(f"  Updated RSS with today's solunar forecast")
        return

    # Pick tip — filter out seasonal items that don't fit current conditions
    valid_tips = [t for t in FISHING_TIPS if _is_seasonal(t)]
    tip = random.choice(valid_tips)
    news = random.choice(NEWS_ITEMS)
    date_str = datetime.now().strftime("%B %d, %Y")
    slug = f"{tip['category']}-{date_str.replace(' ', '-').replace(',','').lower()}"

    # Use pre-approved image — no Pexels API call needed
    print(f"  Using approved image from vetted library")
    photo = get_approved_photo()
    local_path = photo["local_path"]

    post_record = {
        "id": today_id,
        "date": date_str,
        "slug": slug,
        **tip,
        "news_blurb": news,
        "photo": {k: v for k, v in photo.items()} if photo else None,
        "local_path": local_path
    }

    # Save post record
    all_posts.insert(0, post_record)
    all_posts = all_posts[:30]
    json.dump(all_posts, open(index_file, 'w'), indent=2)

    # Generate static HTML post
    post_html = generate_post_html(tip, photo, news)
    with open(POSTS_DIR / f"{slug}.html", 'w') as f:
        f.write(post_html)
    print(f"  📄 Generated post HTML: posts/{slug}.html")

    # Generate updated index
    index_html = generate_index_html(all_posts)
    with open(BLOG_DIR / "index.html", 'w') as f:
        f.write(index_html)
    print(f"  📋 Updated index.html with {len(all_posts)} posts")

    # Update RSS with today's solunar + posts
    _update_solunar_in_rss(all_posts)
    print(f"  📡 Updated RSS with today's solunar forecast")

    print(f"\n[{datetime.now()}] === DONE ===")
    print(f"Post: {tip['title']}")
    if photo:
        print(f"Photo: {photo['alt']} (by {photo['photographer']})")


def _build_rss(all_posts, solunar):
    """Build full RSS XML string with solunar item at top and posts below."""
    solunar_item = solunar_rss_item(solunar)
    items_xml = solunar_item
    for p in all_posts[:10]:
        pub = datetime.fromisoformat(p.get('date_iso', datetime.now().isoformat())).strftime("%a, %d %b %Y %H:%M:%S MDT")
        items_xml += f"\n    <item><title>{html.escape(p['title'])}</title><link>https://tightlinesblog.com/posts/{p['slug']}</link><guid>https://tightlinesblog.com/posts/{p['id']}</guid><pubDate>{pub}</pubDate><description>{html.escape(p['body'][:200])}</description></item>"
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Tight Lines Tackle Box — Daily Fishing Tips</title>
    <link>https://tightlinesblog.com</link>
    <description>Daily fishing tips, tricks, and industry news.</description>
    <language>en-US</language>
{items_xml}
  </channel>
</rss>"""

def _update_solunar_in_rss(all_posts):
    """Re-write RSS with fresh solunar item, keeping existing post items."""
    solunar = solunar_forecast()
    rss = _build_rss(all_posts, solunar)
    with open(BLOG_DIR / "rss.xml", 'w') as f:
        f.write(rss)
    _add_media_to_rss(all_posts)

def _add_media_to_rss(all_posts):
    """Add media:content and enclosure tags to RSS items by reading og:image from each post HTML."""
    import re
    rss_path = BLOG_DIR / "rss.xml"
    with open(rss_path) as f:
        content = f.read()
    item_pat = re.compile(r'(<item>)(.*?)(</item>)', re.DOTALL)
    def fix_item(m):
        item = m.group(0)
        slug_m = re.search(r'<link>https://tightlinesblog\.com/posts/([^<]+)</link>', item)
        if not slug_m:
            return item
        post_path = POSTS_DIR / f"{slug_m.group(1)}.html"
        if not post_path.exists():
            return item
        html_content = post_path.read_text()
        img_m = re.search(r'<meta property="og:image" content="([^"]+)"', html_content)
        if not img_m:
            return item
        img_url = img_m.group(1)
        media = f'\n      <enclosure url="{img_url}" type="image/jpeg" length="100000"/>\n      <media:content url="{img_url}" type="image/jpeg" medium="image"/>'
        item = re.sub(r'(<guid[^>]+>.*?</guid>)', r'\1' + media, item, flags=re.DOTALL)
        return item
    content = item_pat.sub(fix_item, content)
    with open(rss_path, 'w') as f:
        f.write(content)

if __name__ == "__main__":
    run()


if __name__ == "__main__":
    run()
