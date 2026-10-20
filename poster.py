import os, sys, json, math, time, datetime as dt
from cloud import load_env, upload, sign
from generator import render, find_font, spell
from caption import caption
import ig, post_threads, post_fb
import requests

TZ = dt.timezone(dt.timedelta(hours=5, minutes=30))
STATE = "state.json"
MAX_PER_RUN = 12
GAP = 30
RAMP = [(10, 10), (15, 20), (20, 30), (25, 40), (30, 50),
        (32, 60), (34, 70), (36, 80), (38, 90)]

def per_day(day):
    for last, n in RAMP:
        if day <= last:
            return n
    return 100

def load():
    if os.path.exists(STATE):
        return json.load(open(STATE))
    return {"next": 1, "done": []}

def save(s):
    json.dump(s, open(STATE, "w"), indent=1)

def th_publish(uid, url, txt):
    c = post_threads.call("POST", f"/{uid}/threads", media_type="IMAGE",
                          image_url=url, text=txt,
                          topic_tag="number_archive")["id"]
    time.sleep(8)
    ready = False
    for _ in range(25):
        try:
            st = post_threads.call("GET", f"/{c}", fields="status").get("status")
        except RuntimeError:
            st = None
        if st == "FINISHED":
            ready = True
            break
        if st in ("ERROR", "EXPIRED"):
            raise RuntimeError("Threads container " + st)
        time.sleep(4)
    if not ready:
        raise RuntimeError("Threads container not ready")
    last = None
    for _ in range(3):
        try:
            return post_threads.call("POST", f"/{uid}/threads_publish",
                                     creation_id=c)["id"]
        except RuntimeError as e:
            last = e
            time.sleep(6)
    raise last

def destroy(pid):
    p = {"public_id": pid, "timestamp": str(int(time.time()))}
    d = dict(p, api_key=os.environ["CLOUDINARY_API_KEY"],
             signature=sign(p, os.environ["CLOUDINARY_API_SECRET"]))
    requests.post("https://api.cloudinary.com/v1_1/%s/image/destroy"
                  % os.environ["CLOUDINARY_CLOUD_NAME"], data=d, timeout=30)

def main():
    load_env()
    dry = "--dry" in sys.argv
    s = load()
    if s.get("paused"):
        print("Paused.")
        return
    now = dt.datetime.now(TZ)
    today = now.date()
    s.setdefault("start_date", today.isoformat())
    day = (today - dt.date.fromisoformat(s["start_date"])).days + 1
    if s.get("date") != today.isoformat():
        s["date"], s["count"] = today.isoformat(), 0
    target = per_day(day)
    due = min(target, math.ceil(target * (now.hour + 1) / 24))
    todo = min(due - s["count"], MAX_PER_RUN)
    print(f"Day {day}: target {target}, posted today {s['count']}, due {due}, next number {s['next']}")
    if dry:
        print(caption(s["next"]))
        return
    if todo <= 0:
        save(s)
        return
    a = ig.account()
    uid = a.get("user_id") or a["id"]
    th_uid, page = os.environ["THREADS_USER_ID"], os.environ["FB_PAGE_ID"]
    font = find_font()
    for _ in range(todo):
        q = ig.limit(uid)["data"][0]
        if q["quota_usage"] >= q["config"]["quota_total"]:
            print("Instagram quota reached, stopping this run.")
            break
        n = s["next"]
        done = set(s.get("done", []))
        path = f"/tmp/{n:06d}.jpg"
        render(n, font).save(path, "JPEG", quality=95, optimize=True, subsampling=0)
        pid = f"a3/{n:06d}"
        url = upload(path, pid)
        steps = [("ig", lambda: ig.publish(uid, url, caption(n))),
                 ("th", lambda: th_publish(th_uid, url, f"{n} - {spell(n)}")),
                 ("fb", lambda: post_fb.publish(page, url, caption(n)))]
        for name, fn in steps:
            if name in done:
                continue
            try:
                fn()
            except Exception as e:
                s["done"] = sorted(done)
                save(s)
                print(f"FAILED {name} on {n}: {e}")
                sys.exit(1)
            done.add(name)
            s["done"] = sorted(done)
            save(s)
        s["next"], s["count"], s["done"] = n + 1, s["count"] + 1, []
        save(s)
        try:
            destroy(pid)
        except Exception:
            pass
        os.remove(path)
        print("Posted", n)
        time.sleep(GAP)
    save(s)

if __name__ == "__main__":
    main()
