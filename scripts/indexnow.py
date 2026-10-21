"""Meldt alle pagina's uit de sitemap bij IndexNow (Bing, Yandex, Seznam, Naver), zodat nieuwe prijzen snel in de zoekresultaten staan."""
import json, re, sys, time, urllib.request
SITE = "https://boodschappenvergelijk.nl"
KEY = "a120d17eeccff77c778d735d4429aac0"
def haal(u):
    return urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "indexnow-bot"}), timeout=60).read().decode()
for poging in range(10):  # wacht tot de nieuwe versie live staat
    try:
        if haal(f"{SITE}/{KEY}.txt").strip() == KEY: break
    except Exception as e: print("wacht op site:", e)
    time.sleep(60)
urls = re.findall(r"<loc>([^<]+)</loc>", haal(f"{SITE}/sitemap.xml"))
print(len(urls), "urls")
for i in range(0, len(urls), 10000):
    body = json.dumps({"host": "boodschappenvergelijk.nl", "key": KEY, "keyLocation": f"{SITE}/{KEY}.txt", "urlList": urls[i:i + 10000]}).encode()
    req = urllib.request.Request("https://api.indexnow.org/indexnow", data=body, headers={"Content-Type": "application/json; charset=utf-8"})
    try: print("IndexNow:", urllib.request.urlopen(req, timeout=60).status)
    except Exception as e: print("IndexNow mislukt:", e)
