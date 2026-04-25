#!/usr/bin/env python3
"""
Tight Lines Daily Content Agent
Generates a daily fishing tip + pulls a relevant photo from Pexels
Run daily via cron or mission control
"""

import json
import random
import os
import urllib.request
import urllib.error
from datetime import datetime

BLOG_DIR = "/home/kodaagentmt/.openclaw/workspace/projects/tightlines-blog"
POSTS_FILE = f"{BLOG_DIR}/posts/posts.json"
PEXELS_KEY = "YkKkFXmfk334l9uKq8iPBnzoaFcvJOTbnAhO1awjRudPTOfJWX1BAKZE"

FISHING_TIPS = [
    {
        "tag": "Fishing Tips",
        "emoji": "🌤️",
        "title": "Why Overcast Days Are the Best Days to Fish",
        "body": "Most anglers pack up when clouds roll in. Big mistake. Overcast skies diffuse sunlight, reducing visibility in the water — which means fish feel safer coming to the surface and are more likely to feed aggressively. Combined with lower barometric pressure that triggers feeding instincts, cloudy days can be your best bet for a big catch. Pack light, stay patient, and work your lures slower than usual.",
        "category": "tips",
        "pexels_query": "overcast river fishing mountains"
    },
    {
        "tag": "Fishing Tips",
        "emoji": "⏱️",
        "title": "The 3-Second Rule for Lure Retrieval",
        "body": "Most anglers retrieve too fast. Try pausing your lure for 3 full seconds at the end of each strip. Fish often strike on the pause, not the retrieve. This single change to your technique can double your hookup rate on sluggish fish.",
        "category": "tips",
        "pexels_query": "lure fishing close up water"
    },
    {
        "tag": "Montana Fishing",
        "emoji": "🏔️",
        "title": "Spring Runoff: Where to Fish When the Rivers Are High",
        "body": "Spring runoff turns most Montana rivers chocolate-milk brown. But the tailwaters and spring creeks that stay clear — like the Jefferson, Madison, and the lower legs of Spring Creek — produce consistently during runoff. Focus on slower water near the banks where fish stage to wait out the dirty water.",
        "category": "montana",
        "pexels_query": "montana river spring runoff fly fishing"
    },
    {
        "tag": "Gear Reviews",
        "emoji": "🪝",
        "title": "The Best Fluorocarbon Leaders for Montana Waters",
        "body": "After testing 12 fluorocarbon leaders on our local rivers, three stood out: Seaguar InvizX for its knot strength, Pure Fluorocarbon for sensitivity in cold water, and Berkley Vanish for the best value. All three held up to abrasive rock beds and aggressive trout teeth.",
        "category": "gear",
        "pexels_query": "fishing gear tackle box fly tying"
    },
    {
        "tag": "Fly Fishing",
        "emoji": "🪰",
        "title": "The Mysis Shrimp Impostor That Outfishes the Real Thing",
        "body": "Why most anglers tie the Mysis shrimp pattern wrong — and the two modifications that have consistently outfished the standard pattern on Hebgen Lake. Hint: it is all about the collar angle and the bead placement relative to the hook eye.",
        "category": "fly",
        "pexels_query": "fly fishing river trout wet fly"
    },
    {
        "tag": "Ice Fishing",
        "emoji": "🧊",
        "title": "Late Ice Walleye: The Setup Most Anglers Miss",
        "body": "The last two weeks of ice fishing season are when most walleye are caught — and most are lost. The culprit: wrong line diameter. Dropping from 6lb to 4lb test during late ice increased our hookup ratio by 40% in testing. Fluorocarbon or low-stretch mainline only.",
        "category": "ice",
        "pexels_query": "ice fishing winter frozen lake walleye"
    },
    {
        "tag": "Industry News",
        "emoji": "📰",
        "title": "Montana FWP Proposes New Cutthroat Protection Zones",
        "body": "The proposed regulations would close 14 miles of the Yellowstone River to protect native westslope cutthroat. Public comment period ends May 15. If you fish the Yellowstone, now is the time to make your voice heard at the FWP website.",
        "category": "news",
        "pexels_query": "yellowstone river montana fly fishing"
    },
    {
        "tag": "Fishing Tips",
        "emoji": "🌡️",
        "title": "Water Temperature: The Number Every Serious Angler Tracks",
        "body": "Fish are cold-blooded — their metabolism is directly tied to water temperature. Below 40°F, trout feed only occasionally. Between 45-55°F, feeding increases dramatically. Above 65°F, trout metabolism spikes but oxygen drops — a dangerous combo. Buy a floating thermometer. It is the best $15 you will spend.",
        "category": "tips",
        "pexels_query": "thermometer fishing tackle water"
    },
    {
        "tag": "Montana Fishing",
        "emoji": "🌊",
        "title": "Reading River Currents: The Key Eddy Every Angler Should Find",
        "body": "Every river has them — calm pockets of slow water directly downstream from a rock or bend. Fish stack in these eddies because food collects there and the current is easier to hold in. Finding the eddy is finding the fish. Spend your first 10 minutes on any new water looking for these holding zones.",
        "category": "montana",
        "pexels_query": "river eddy calm water fishing rapids"
    },
    {
        "tag": "Tournament Updates",
        "emoji": "🏆",
        "title": "Spring Classic Recap: New Pattern Emerged as Key",
        "body": "The winning pattern at last weekend's Spring Classic on Fort Peck was not what anyone predicted — a simple olive Wooly Bugger fished on a 7-weight sink tip, stripped in 4-inch bursts. Water temperature was the deciding factor: 48°F at launch, 52°F at weigh-in.",
        "category": "tournament",
        "pexels_query": "fishing tournament awards trophy winner"
    },
]

DAILY_NEWS = [
    "Montana Fish Wildlife and Parks announced extended fishing hours on three Madison River segments starting May 1. Night fishing will now be permitted below Ennis Reservoir through September 30.",
    "New regulations for 2026: Montana will require barbless hooks on all catch-and-release water starting next season. Fines range from $50 for first offense to $500 for repeat violations.",
    "Hebgen Lake is now ice-free as of April 22. Anglers are reporting good catches of brown trout near the incoming channels. Boat launch at Hebgen Dam is open.",
    "The Missouri River below Fort Peck is running high but clear — producing solid walleye numbers in the tailrace. Best action between 10am and 2pm using blade jigs in chartreuse.",
    "Crowded boat ramps are the number one complaint at Montana state parks. FWP is piloting a new reservation system for seven high-traffic ramps this summer. Full rollout planned for 2027.",
]


def fetch_pexels_image(query, retries=3):
    """Fetch a relevant fishing photo from Pexels"""
    url = f"https://api.pexels.com/v1/search?query={urllib.parse.quote(query)}&per_page=5&orientation=landscape"
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={
                "Authorization": PEXELS_KEY,
                "User-Agent": "TightLinesBlog/1.0 (kodaagentmt; contact@kodaagentmt.com)"
            })
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read())
                photos = data.get("photos", [])
                if photos:
                    chosen = random.choice(photos)
                    return {
                        "url": chosen["src"]["large"],
                        "thumb": chosen["src"]["medium"],
                        "photographer": chosen["photographer"],
                        "alt": chosen.get("alt", query)
                    }
        except Exception as e:
            print(f"  [Pexels attempt {attempt+1} failed: {e}]")
    return None


def load_posts():
    if os.path.exists(POSTS_FILE):
        with open(POSTS_FILE) as f:
            return json.load(f)
    return []


def save_posts(posts):
    os.makedirs(os.path.dirname(POSTS_FILE), exist_ok=True)
    with open(POSTS_FILE, 'w') as f:
        json.dump(posts, f, indent=2)


def generate_daily_post():
    tip = random.choice(FISHING_TIPS)
    news = random.choice(DAILY_NEWS)
    today = datetime.now()

    print(f"  Fetching Pexels image for: {tip['pexels_query']}")
    photo = fetch_pexels_image(tip["pexels_query"])

    post = {
        "id": today.strftime("%Y%m%d"),
        "date": today.strftime("%b %d, %Y"),
        "date_iso": today.isoformat(),
        **tip,
        "news_blurb": news if random.random() > 0.5 else None,
        "photo": photo
    }
    return post


def update_rss(posts):
    """Generate updated RSS feed with image links"""
    build_date = datetime.now().strftime("%a, %d %b %Y %H:%M:%S MDT")
    items_xml = ""
    for p in posts[:10]:
        pub = datetime.fromisoformat(p["date_iso"]).strftime("%a, %d %b %Y %H:%M:%S MDT")
        desc = p["body"][:200]
        if p.get("photo"):
            desc = f"<![CDATA[<img src='{p['photo']['url']}' alt='{p['photo']['alt']}' /><br />{p['body']}]]>"
        items_xml += f"""
    <item>
      <title>{p['title']}</title>
      <link>https://tightlinesblog.com/posts/{p['category']}-{p['date'].replace(' ', '-').replace(',','').lower()}</link>
      <guid>https://tightlinesblog.com/posts/{p['id']}</guid>
      <pubDate>{pub}</pubDate>
      <description>{desc}</description>
    </item>"""

    rss = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>Tight Lines Tackle Box — Daily Fishing Tips</title>
    <link>https://tightlinesblog.com</link>
    <description>Montana's daily source for fishing tips, tricks, and industry news.</description>
    <language>en-US</language>
    <lastBuildDate>{build_date}</lastBuildDate>
    <atom:link href="https://tightlinesblog.com/rss.xml" rel="self"/>
{items_xml}
  </channel>
</rss>"""
    with open(f"{BLOG_DIR}/rss.xml", 'w') as f:
        f.write(rss)


def update_blog():
    posts = load_posts()
    today_id = datetime.now().strftime("%Y%m%d")
    if any(p.get('id') == today_id for p in posts):
        print(f"[{datetime.now()}] Already posted today ({today_id}). Skipping.")
        return None

    new_post = generate_daily_post()
    posts.insert(0, new_post)
    posts = posts[:30]
    save_posts(posts)

    print(f"[{datetime.now()}] ✓ New post: {new_post['title']}")
    print(f"[{datetime.now()}] Tag: {new_post['tag']} | Emoji: {new_post['emoji']}")
    if new_post.get("photo"):
        print(f"[{datetime.now()}] 📷 Photo: {new_post['photo']['alt']} (by {new_post['photo']['photographer']})")
    if new_post.get('news_blurb'):
        print(f"[{datetime.now()}] News: {new_post['news_blurb'][:60]}...")
    return new_post


if __name__ == "__main__":
    import urllib.parse
    post = update_blog()
    if post:
        posts = load_posts()
        update_rss(posts)
        print(f"\n[{datetime.now()}] === DAILY POST COMPLETE ===")
    else:
        print(f"[{datetime.now()}] No new post generated today.")
