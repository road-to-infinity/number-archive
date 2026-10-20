import os, sys, time, requests
from cloud import load_env, upload
from generator import spell

BASES = ["https://graph.threads.net/v1.0", "https://graph.threads.com/v1.0"]

def text(n):
    return f"{n} - {spell(n)}\n\n#roadtoinfinity"

def call(method, path, **p):
    p["access_token"] = os.environ["THREADS_ACCESS_TOKEN"]
    kw = {"data": p} if method == "POST" else {"params": p}
    last = "unknown"
    for base in BASES:
        try:
            r = requests.request(method, base + path, timeout=60, **kw)
        except requests.RequestException as e:
            last = "Network error: " + type(e).__name__
            continue
        try:
            j = r.json()
        except ValueError:
            j = {"error": {"message": r.text[:200]}}
        if r.status_code >= 400 or "error" in j:
            e = j.get("error", {})
            msg = e.get("message", e) if isinstance(e, dict) else e
            raise RuntimeError(f"API {r.status_code}: {msg}")
        return j
    raise RuntimeError(last)

def publish(uid, url, txt):
    c = call("POST", f"/{uid}/threads", media_type="IMAGE",
             image_url=url, text=txt)["id"]
    for _ in range(25):
        s = call("GET", f"/{c}", fields="status").get("status")
        if s == "FINISHED":
            break
        if s in ("ERROR", "EXPIRED"):
            raise RuntimeError("Container " + s)
        time.sleep(3)
    else:
        raise RuntimeError("Container not ready in time")
    return call("POST", f"/{uid}/threads_publish", creation_id=c)["id"]

if __name__ == "__main__":
    load_env()
    uid = os.environ["THREADS_USER_ID"]
    print("Threads account:", call("GET", "/me", fields="username").get("username"))
    if "--post" in sys.argv:
        n = int(sys.argv[sys.argv.index("--post") + 1])
        url = upload(f"images/{n:06d}.jpg", f"a3/{n:06d}")
        print("Posted Threads id:", publish(uid, url, text(n)))
