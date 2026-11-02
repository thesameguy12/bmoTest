"""Internet access. The app does the fetching and hands the text to the model as
context - small models are unreliable at driving tools themselves."""
import datetime
import ipaddress
import re
import socket
import xml.etree.ElementTree as ET
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

import config

HEADERS = {"User-Agent": "BMO-desktop-pet/1.0 (personal project)"}
URL_RE = re.compile(r"https?://\S+")
WEATHER_WORDS = ("weather", "temperature", "forecast", "how cold", "how hot")
NEWS_WORDS = ("news", "headlines", "happening in the world")

WMO = {0: "clear sky", 1: "mostly clear", 2: "partly cloudy", 3: "overcast", 45: "fog", 48: "fog",
       51: "light drizzle", 53: "drizzle", 55: "heavy drizzle", 61: "light rain", 63: "rain",
       65: "heavy rain", 71: "light snow", 73: "snow", 75: "heavy snow", 80: "rain showers",
       81: "rain showers", 82: "violent rain showers", 95: "thunderstorm"}
_geo = {}


# ---------- weather & news (dedicated, fast, accurate) ----------
def _geocode(city):
    if city not in _geo:
        r = requests.get("https://geocoding-api.open-meteo.com/v1/search",
                         params={"name": city, "count": 1}, timeout=8).json()["results"][0]
        _geo[city] = (r["latitude"], r["longitude"], r["name"])
    return _geo[city]


def weather(text):
    m = re.search(r"\b(?:in|for)\s+([A-ZČŠŽ][\w\-]+(?: [A-ZČŠŽ][\w\-]+)?)", text)
    city = m.group(1) if m else config.CITY
    try:
        lat, lon, name = _geocode(city)
        d = requests.get("https://api.open-meteo.com/v1/forecast", params={
            "latitude": lat, "longitude": lon, "timezone": "auto",
            "current": "temperature_2m,weather_code,wind_speed_10m",
            "daily": "temperature_2m_max,temperature_2m_min"}, timeout=8).json()
        c, dy = d["current"], d["daily"]
        return (f"Weather in {name} right now: {WMO.get(c['weather_code'], 'unknown')}, "
                f"{c['temperature_2m']}°C, wind {c['wind_speed_10m']} km/h. "
                f"Today's high {dy['temperature_2m_max'][0]}°C, low {dy['temperature_2m_min'][0]}°C.")
    except Exception as e:
        return f"(Could not get weather: {e})"


def news():
    try:
        root = ET.fromstring(requests.get(config.NEWS_FEED, headers=HEADERS, timeout=8).content)
        titles = [i.findtext("title") for i in root.iter("item")][:5]
        return "Top news headlines:\n- " + "\n- ".join(titles)
    except Exception as e:
        return f"(Could not get news: {e})"


# ---------- general web ----------
def _is_public(url):
    """Basic guard: only http(s) and never local/private network addresses."""
    try:
        p = urlparse(url)
        if p.scheme not in ("http", "https") or not p.hostname:
            return False
        for info in socket.getaddrinfo(p.hostname, None):
            ip = ipaddress.ip_address(info[4][0])
            if ip.is_private or ip.is_loopback or ip.is_link_local:
                return False
        return True
    except Exception:
        return False


def read_page(url):
    if not _is_public(url):
        return ""
    try:
        r = requests.get(url, headers=HEADERS, timeout=8)
        r.raise_for_status()
        if "html" not in r.headers.get("content-type", ""):
            return ""
        soup = BeautifulSoup(r.content[:500_000], "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header", "aside", "form"]):
            tag.decompose()
        text = " ".join(p.get_text(" ", strip=True) for p in soup.find_all("p"))
        return re.sub(r"\s+", " ", text)[:config.PAGE_CHARS]
    except Exception:
        return ""


def _wikipedia(q):
    try:
        d = requests.get("https://en.wikipedia.org/w/api.php", headers=HEADERS, timeout=8, params={
            "action": "query", "list": "search", "srsearch": q, "format": "json",
            "srlimit": config.WEB_RESULTS}).json()
        return [{"title": h["title"],
                 "href": "https://en.wikipedia.org/wiki/" + h["title"].replace(" ", "_"),
                 "body": re.sub(r"<[^>]+>", "", h["snippet"])} for h in d["query"]["search"]]
    except Exception:
        return []


def search(q):
    try:
        from ddgs import DDGS
        res = DDGS().text(q, max_results=config.WEB_RESULTS)
        if res:
            return [{"title": r.get("title", ""), "href": r.get("href", ""),
                     "body": r.get("body", "")} for r in res]
    except Exception as e:
        print("[search] web search failed, falling back to Wikipedia:", e)
    return _wikipedia(q)


def web_context(q):
    results = search(q)
    if not results:
        return "(The web search failed or found nothing.)"
    out = f"Web search results for '{q}':\n" + "\n".join(
        f"- {r['title']}: {r['body'][:200]}" for r in results[:config.WEB_RESULTS])
    if config.FETCH_PAGES:
        page = read_page(results[0]["href"])
        if page:
            out += f"\n\nText from the top result ({results[0]['href']}):\n{page}"
    return out


def gather_context(text, route):
    """route(text) -> search query or None (asked to the LLM, see brain.py)."""
    t = text.lower()
    parts = [f"Current date and time: {datetime.datetime.now():%A, %d %B %Y, %H:%M}"]
    urls = URL_RE.findall(text)
    if any(w in t for w in WEATHER_WORDS):
        parts.append(weather(text))
    elif any(w in t for w in NEWS_WORDS):
        parts.append(news())
    elif urls:
        page = read_page(urls[0].rstrip(".,)"))
        parts.append(f"Text of {urls[0]}:\n{page}" if page else f"(Could not read {urls[0]}.)")
    elif len(text.split()) > 2:
        q = route(text)
        if q:
            print("[web] searching:", q)
            parts.append(web_context(q))
    return "\n".join(parts)
