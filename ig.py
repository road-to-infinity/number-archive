import os, sys, time, requests
from cloud import load_env, upload
from caption import caption

BASE = "https://graph.instagram.com/v26.0"

def call(method, path, **p):
    p["access_token"] = os.environ["INSTAGRAM_ACCESS_TOKEN"]
    kw = {"data": p} if method == "POST" else {"params": p}
    try:
        r = requests.request(method, BASE + path, timeout=60, **kw)
    except requests.RequestException as e:
        raise RuntimeError("Network error: " + type(e).__name__)
    try:
        j = r.json()
    except ValueError:
        j = {"error": {"message": r.text[:200]}}
    if r.status_code >= 400 or "error" in j:
        e = j.get("error", {})
        msg = e.get("message", e) if isinstance(e, dict) else e
        raise RuntimeError(f"API {r.status_code}: {msg}")
    return j

def account():
    return call("GET", "/me", fields="user_id,username,account_type")

def limit(uid):
    return call("GET", f"/{uid}/content_publishing_limit",
                fields="quota_usage,config")

def publish(uid, url, cap):
    c = call("POST", f"/{uid}/media", image_url=url, caption=cap)["id"]
    for _ in range(30):
        s = call("GET", f"/{c}", fields="status_code").get("status_code")
        if s == "FINISHED":
            break
        if s in ("ERROR", "EXPIRED"):
            raise RuntimeError("Container " + s)
        time.sleep(3)
    else:
        raise RuntimeError("Container not ready in time")
    return call("POST", f"/{uid}/media_publish", creation_id=c)["id"]

if __name__ == "__main__":
    load_env()
    a = account()
    uid = a.get("user_id") or a["id"]
    print("Account:", a.get("username"), a.get("account_type"))
    print("Limit:", limit(uid))
    if "--post" in sys.argv:
        n = int(sys.argv[sys.argv.index("--post") + 1])
        url = upload(f"images/{n:06d}.jpg", f"a3/{n:06d}")
        print("Posted media id:", publish(uid, url, caption(n)))
