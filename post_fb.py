import os, sys, requests
from cloud import load_env, upload
from caption import caption

G = "https://graph.facebook.com/v25.0"

def publish(page, url, cap):
    try:
        r = requests.post(f"{G}/{page}/photos", timeout=90, data={
            "url": url, "caption": cap,
            "access_token": os.environ["FB_PAGE_TOKEN"]})
    except requests.RequestException as e:
        raise RuntimeError("Network error: " + type(e).__name__)
    j = r.json()
    if r.status_code >= 400 or "error" in j:
        raise RuntimeError(f"API {r.status_code}: {j.get('error', {}).get('message')}")
    return j.get("post_id") or j.get("id")

if __name__ == "__main__":
    load_env()
    page = os.environ["FB_PAGE_ID"]
    n = int(sys.argv[sys.argv.index("--post") + 1])
    url = upload(f"images/{n:06d}.jpg", f"a3/{n:06d}")
    print("Posted Facebook id:", publish(page, url, caption(n)))
