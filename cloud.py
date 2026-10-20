import hashlib, os, sys, time
import requests

def load_env(path=".env"):
    if os.path.exists(path):
        for line in open(path):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())

def sign(params, secret):
    s = "&".join(f"{k}={params[k]}" for k in sorted(params))
    return hashlib.sha1((s + secret).encode()).hexdigest()

def upload(path, public_id, retries=3):
    load_env()
    cloud = os.environ["CLOUDINARY_CLOUD_NAME"]
    key = os.environ["CLOUDINARY_API_KEY"]
    secret = os.environ["CLOUDINARY_API_SECRET"]
    url = f"https://api.cloudinary.com/v1_1/{cloud}/image/upload"
    last = None
    for attempt in range(1, retries + 1):
        params = {"public_id": public_id, "overwrite": "false",
                  "timestamp": str(int(time.time()))}
        data = dict(params, api_key=key, signature=sign(params, secret))
        try:
            with open(path, "rb") as f:
                r = requests.post(url, data=data,
                                  files={"file": f}, timeout=60)
            if r.status_code == 200:
                return r.json()["secure_url"]
            if 400 <= r.status_code < 500 and r.status_code != 429:
                raise RuntimeError(f"Rejected: {r.status_code} {r.text[:200]}")
            last = f"{r.status_code} {r.text[:200]}"
        except requests.RequestException as e:
            last = str(e)
        time.sleep(2 * attempt)
    raise RuntimeError(f"Upload failed after {retries} tries: {last}")

if __name__ == "__main__":
    p = sys.argv[1]
    pid = "archive/" + os.path.splitext(os.path.basename(p))[0]
    print(upload(p, pid))
