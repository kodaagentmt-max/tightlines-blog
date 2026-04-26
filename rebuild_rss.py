import json, html
from datetime import datetime
from pathlib import Path

BLOG_DIR = Path('/home/kodaagentmt/.openclaw/workspace/projects/tightlines-blog')
with open(BLOG_DIR / 'posts.json') as f:
    posts = json.load(f)

items = ''
sol_date = datetime.now().strftime('%a, %d %b %Y %H:%M:%S MDT')
items += f'''
    <item>
      <title>Solunar Forecast — April 26, 2026</title>
      <link>https://kodaagentmt-max.github.io/tightlines-blog/solunar.html</link>
      <guid isPermaLink="true">https://tightlinesblog.com/posts/solunar-20260426</guid>
      <pubDate>{sol_date}</pubDate>
      <description><![CDATA[🌓 32% illuminated. Major feeding: 4:29 AM & 4:54 PM. Minor feeding: 10:42 AM & 11:07 PM. Sunrise 5:25 AM / Sunset 7:14 PM. Data for ~45°N, 110°W (Mountain Time).]]></description>
    </item>'''

for p in posts:
    pub = datetime.fromisoformat(p.get('date_iso', datetime.now().isoformat())).strftime('%a, %d %b %Y %H:%M:%S MDT')
    slug = p['slug']
    title = p['title']
    body = p.get('body','')[:200]
    photo = p.get('photo',{})
    img_url = photo.get('url','')
    items += f'''
    <item>
      <title>{html.escape(title)}</title>
      <link>https://tightlinesblog.com/posts/{slug}</link>
      <guid isPermaLink="true">https://tightlinesblog.com/posts/{p['id']}</guid>
      <pubDate>{pub}</pubDate>
      <description>{html.escape(body)}</description>'''
    if img_url:
        items += f'''
      <enclosure url="{img_url}" type="image/jpeg" length="100000"/>
      <media:content url="{img_url}" type="image/jpeg" medium="image"/>'''
    items += '''
    </item>'''

rss = f'''<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Tight Lines Tackle Box — Daily Fishing Tips</title>
    <link>https://tightlinesblog.com</link>
    <description>Daily fishing tips, tricks, and industry news.</description>
    <language>en-US</language>
{items}
  </channel>
</rss>'''
BLOG_DIR.joinpath('rss.xml').write_text(rss)
print('RSS rebuilt')
print('Enclosures:', html.escape(items).count('enclosure url='))