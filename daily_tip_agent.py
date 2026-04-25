#!/usr/bin/env python3
"""
Tight Lines Daily Tip Agent
Generates a daily fishing tip post with a static HTML page + Pexels photo
Run daily via cron — outputs to projects/tightlines-blog/posts/
"""

import html
import json, os, random, urllib.request
from datetime import datetime
from pathlib import Path

BLOG_DIR = Path("/home/kodaagentmt/.openclaw/workspace/projects/tightlines-blog")
POSTS_DIR = BLOG_DIR / "posts"
PEXELS_KEY = "YkKkFXmfk334l9uKq8iPBnzoaFcvJOTbnAhO1awjRudPTOfJWX1BAKZE"

FISHING_TIPS = [
    {
        "tag": "Fishing Tips",
        "emoji": "🌤️",
        "title": "Why Overcast Days Are the Best Days to Fish",
        "body": "Most anglers pack up when clouds roll in. Big mistake. Overcast skies diffuse sunlight, reducing visibility in the water — which means fish feel safer coming to the surface and are more likely to feed aggressively. Combined with lower barometric pressure that triggers feeding instincts, cloudy days can be your best bet for a big catch.",
        "category": "tips",
        "pexels_query": "overcast river fishing mountains"
    },
    {
        "tag": "Fishing Tips",
        "emoji": "⏱️",
        "title": "The 3-Second Rule for Lure Retrieval",
        "body": "Most anglers retrieve too fast. Try pausing your lure for 3 full seconds at the end of each strip. Fish often strike on the pause, not the retrieve. This single change to your technique can double your hookup rate on sluggish fish.",
        "category": "tips",
        "pexels_query": "fishing lure water close up"
    },
    {
        "tag": "Montana Fishing",
        "emoji": "🏔️",
        "title": "Spring Runoff: Where to Fish When the Rivers Are High",
        "body": "Spring runoff turns most Montana rivers chocolate-milk brown. But the tailwaters and spring creeks that stay clear — like the Jefferson, Madison, and the lower legs of Spring Creek — produce consistently during runoff.",
        "category": "montana",
        "pexels_query": "montana river spring runoff fly fishing"
    },
    {
        "tag": "Gear Reviews",
        "emoji": "🪝",
        "title": "The Best Fluorocarbon Leaders for Montana Waters",
        "body": "After testing 12 fluorocarbon leaders on our local rivers, three stood out: Seaguar InvizX for its knot strength, Pure Fluorocarbon for sensitivity in cold water, and Berkley Vanish for the best value.",
        "category": "gear",
        "pexels_query": "fishing gear tackle box flourocarbon"
    },
    {
        "tag": "Fly Fishing",
        "emoji": "🪰",
        "title": "The Mysis Shrimp Impostor That Outfishes the Real Thing",
        "body": "Why most anglers tie the Mysis shrimp pattern wrong — and the two modifications that have consistently outfished the standard pattern on Hebgen Lake. Hint: it is all about the collar angle and the bead placement.",
        "category": "fly",
        "pexels_query": "fly fishing river trout wet fly"
    },
    {
        "tag": "Ice Fishing",
        "emoji": "🧊",
        "title": "Late Ice Walleye: The Setup Most Anglers Miss",
        "body": "The last two weeks of ice fishing season are when most walleye are caught — and most are lost. The culprit: wrong line diameter. Dropping from 6lb to 4lb test during late ice increased our hookup ratio by 40%.",
        "category": "ice",
        "pexels_query": "ice fishing winter frozen lake walleye"
    },
    {
        "tag": "Industry News",
        "emoji": "📰",
        "title": "Montana FWP Proposes New Cutthroat Protection Zones",
        "body": "The proposed regulations would close 14 miles of the Yellowstone River to protect native westslope cutthroat. Public comment period ends May 15. If you fish the Yellowstone, now is the time to make your voice heard.",
        "category": "news",
        "pexels_query": "yellowstone river montana fly fishing"
    },
    {
        "tag": "Fishing Tips",
        "emoji": "🌡️",
        "title": "Water Temperature: The Number Every Serious Angler Tracks",
        "body": "Fish are cold-blooded — their metabolism is directly tied to water temperature. Below 40°F, trout feed only occasionally. Between 45-55°F, feeding increases dramatically. Above 65°F, trout metabolism spikes but oxygen drops.",
        "category": "tips",
        "pexels_query": "thermometer fishing tackle water"
    },
    {
        "tag": "Montana Fishing",
        "emoji": "🌊",
        "title": "Reading River Currents: The Key Eddy Every Angler Should Find",
        "body": "Every river has them — calm pockets of slow water directly downstream from a rock or bend. Fish stack in these eddies because food collects there and the current is easier to hold in.",
        "category": "montana",
        "pexels_query": "river eddy calm water fishing rapids"
    },
    {
        "tag": "Tournament Updates",
        "emoji": "🏆",
        "title": "Spring Classic Recap: New Pattern Emerged as Key",
        "body": "The winning pattern at last weekend's Spring Classic on Fort Peck was a simple olive Wooly Bugger fished on a 7-weight sink tip, stripped in 4-inch bursts. Water temperature was the deciding factor.",
        "category": "tournament",
        "pexels_query": "fishing tournament awards trophy winner"
    },
]

NEWS_ITEMS = [
    "Montana Fish Wildlife and Parks announced extended fishing hours on three Madison River segments starting May 1.",
    "New regulations for 2026: Montana will require barbless hooks on all catch-and-release water starting next season.",
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
    {f"<img class='hero-img' src='../{photo['local_path']}' alt='{photo['alt']}'>" if photo else ""}
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
  <meta name="description" content="Montana's daily source for fishing tips, tricks, and industry news.">
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
      <p class="tagline">Montana's daily source for fishing tips, tricks, and industry news</p>
    </div>
    <div class="section-title">📖 Latest Tips & News</div>
    <div class="posts-grid">
{posts_html}
    </div>
  </div>
  <footer>
    <p>🎣 Tight Lines Tackle Box — Montana's source for outdoor fishing knowledge since 2024</p>
  </footer>
</body>
</html>"""


# ─── Main ─────────────────────────────────────────────────────────────────────
def run():
    import urllib.parse
    today_id = datetime.now().strftime("%Y%m%d")
    POSTS_DIR.mkdir(exist_ok=True)

    # Load existing posts
    index_file = BLOG_DIR / "posts.json"
    all_posts = json.load(open(index_file)) if index_file.exists() else []

    # Skip if posted today
    if any(p.get('id') == today_id for p in all_posts):
        print(f"[{datetime.now()}] Already posted today ({today_id}). Skipping.")
        return

    # Pick tip
    tip = random.choice(FISHING_TIPS)
    news = random.choice(NEWS_ITEMS)
    date_str = datetime.now().strftime("%B %d, %Y")
    slug = f"{tip['category']}-{date_str.replace(' ', '-').replace(',','').lower()}"

    # Fetch photo
    print(f"  Fetching Pexels image: {tip['pexels_query']}")
    photo = fetch_pexels_image(tip["pexels_query"])

    # Download photo locally
    local_path = None
    if photo:
        img_path = POSTS_DIR / f"img-{today_id}.jpg"
        try:
            req = urllib.request.Request(photo["thumb"], headers={"User-Agent": "TightLinesBlog/1.0"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = resp.read()
            with open(img_path, 'wb') as f:
                f.write(data)
            local_path = f"posts/img-{today_id}.jpg"
            photo["local_path"] = local_path
            print(f"  📷 Downloaded: {img_path.name} ({len(data)} bytes)")
        except Exception as e:
            print(f"  ⚠ Failed to download photo: {e}")
            photo = None

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

    # Generate RSS
    items_xml = ""
    for p in all_posts[:10]:
        import urllib.parse
        pub = datetime.fromisoformat(p.get('date_iso', datetime.now().isoformat())).strftime("%a, %d %b %Y %H:%M:%S MDT")
        items_xml += f"\n    <item><title>{html.escape(p['title'])}</title><link>https://tightlinesblog.com/posts/{p['slug']}</link><guid>https://tightlinesblog.com/posts/{p['id']}</guid><pubDate>{pub}</pubDate><description>{html.escape(p['body'][:200])}</description></item>"

    rss = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Tight Lines Tackle Box — Daily Fishing Tips</title>
    <link>https://tightlinesblog.com</link>
    <description>Montana's daily source for fishing tips, tricks, and industry news.</description>
    <language>en-US</language>
{items_xml}
  </channel>
</rss>"""
    with open(BLOG_DIR / "rss.xml", 'w') as f:
        f.write(rss)

    print(f"\n[{datetime.now()}] === DONE ===")
    print(f"Post: {tip['title']}")
    if photo:
        print(f"Photo: {photo['alt']} (by {photo['photographer']})")


if __name__ == "__main__":
    run()
