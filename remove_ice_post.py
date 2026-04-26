import json
from pathlib import Path

BLOG_DIR = Path("/home/kodaagentmt/.openclaw/workspace/projects/tightlines-blog")
POSTS_DIR = BLOG_DIR / "posts"

with open(BLOG_DIR / "posts.json") as f:
    posts = json.load(f)

print("Before:", [p['id'] for p in posts])
posts = [p for p in posts if p.get("id") != "20260426"]
print("After:", [p['id'] for p in posts])

with open(BLOG_DIR / "posts.json", "w") as f:
    json.dump(posts, f, indent=2)

print("Done")