# -*- coding: utf-8 -*-
"""MONG 블로그 RSS → jobs.json (🎯 오늘 놓치면 아까운 공고 목록)
- 블로그 RSS 에서 '채용' 카테고리 글만 골라 제목·주소·썸네일·마감을 뽑는다
- 마감 = 제목·첫 문단에서 '마감'·'까지' 근처의 "M월 D일" (+ 시각). 못 뽑으면 overrides.json 에서, 그래도 없으면 목록에서 뺌
- 이미 jobs.json 에 있던 글은 RSS 에서 밀려나도(최근 50개만 옴) 마감 전까지 남겨 둠
깃허브 Actions 가 한 시간마다 돌림 (.github/workflows/update.yml). 손으로: python scripts/update.py
"""
import json, re, html, os, urllib.request
from datetime import datetime, timedelta, timezone

BLOG = "eleode123"
RSS = f"https://rss.blog.naver.com/{BLOG}.xml"
KST = timezone(timedelta(hours=9))
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "jobs.json")
OVR = os.path.join(ROOT, "overrides.json")


def grab(item, key):
    m = re.search(r"<%s>(?:<!\[CDATA\[)?([\s\S]*?)(?:\]\]>)?</%s>" % (key, key), item)
    return m.group(1).strip() if m else ""


def plain(s):
    s = re.sub(r"<[^>]+>", " ", html.unescape(s))
    return re.sub(r"\s+", " ", s).strip()


def parse_time(s):
    """'오후 2시(14:00)' · '10:00' · '18시' · '오후 5시 30분' → (시, 분)"""
    m = re.search(r"(\d{1,2}):(\d{2})", s)
    if m:
        return int(m.group(1)), int(m.group(2))
    m = re.search(r"(오전|오후)?\s*(\d{1,2})\s*시(?:\s*(\d{1,2})\s*분)?", s)
    if m:
        h = int(m.group(2))
        if m.group(1) == "오후" and h < 12:
            h += 12
        return h, int(m.group(3) or 0)
    return 23, 59


def find_deadline(text, pub):
    """'마감'·'까지' 앞뒤 30자 안의 첫 'M월 D일' (+ 그 뒤 25자 안의 시각)"""
    best = None
    for m in re.finditer(r"(\d{1,2})\s*월\s*(\d{1,2})\s*일", text):
        around = text[max(0, m.start() - 30): m.end() + 30]
        if not re.search(r"마감|까지", around):
            continue
        after = text[m.end(): m.end() + 25]
        h, mi = parse_time(re.split(r"마감|까지", after)[0] + (after if re.search(r"마감|까지", after) else ""))
        if not re.search(r"\d{1,2}:\d{2}|\d{1,2}\s*시", re.split(r"마감|까지", after)[0]):
            h, mi = 23, 59
        y = pub.year
        mon, day = int(m.group(1)), int(m.group(2))
        if mon < pub.month - 6:  # 12월 글에 '1월 5일' → 다음 해
            y += 1
        try:
            d = datetime(y, mon, day, h, mi, tzinfo=KST)
        except ValueError:
            continue
        # 접수 기간 "10월 6일부터 10월 19일까지" → 뒤 날짜가 마감 (같은 근처에 여러 개면 늦은 쪽)
        if best is None or (d > best and (d - best).days < 60 and m.start() < 400):
            best = d
        if m.start() > 400:
            break
    return best


def main():
    with urllib.request.urlopen(urllib.request.Request(RSS, headers={"User-Agent": "Mozilla/5.0 (mong-pick)"}), timeout=30) as r:
        xml = r.read().decode("utf-8", "ignore")
    old = {}
    if os.path.exists(OUT):
        for j in json.load(open(OUT, encoding="utf-8")).get("jobs", []):
            old[j["url"]] = j
    ovr = json.load(open(OVR, encoding="utf-8")) if os.path.exists(OVR) else {}
    now = datetime.now(KST)
    jobs = dict(old)
    for item in re.findall(r"<item>([\s\S]*?)</item>", xml):
        if "채용" not in grab(item, "category"):
            continue
        url = re.sub(r"\?.*$", "", grab(item, "link"))
        title = plain(grab(item, "title"))
        desc_raw = html.unescape(grab(item, "description"))
        m = re.search(r'<img[^>]+src="([^"]+)"', desc_raw)
        thumb = m.group(1) if m else ""
        try:
            pub = datetime.strptime(grab(item, "pubDate")[:25], "%a, %d %b %Y %H:%M:%S").replace(tzinfo=KST)
        except ValueError:
            pub = now
        o = ovr.get(url, {})
        if o.get("hide"):
            jobs.pop(url, None)
            continue
        end = o.get("end")
        if not end:
            d = find_deadline(title + " " + plain(desc_raw)[:600], pub)
            end = d.strftime("%Y-%m-%dT%H:%M") if d else (old.get(url, {}).get("end") or "")
        if not end:
            print("마감 못 찾음 (overrides.json 에 넣어 주세요):", title, url)
            continue
        jobs[url] = {"url": url, "title": o.get("title") or title, "thumb": thumb, "end": end, "posted": pub.strftime("%Y-%m-%d")}
    # 마감 지난 지 7일 넘은 글은 뺌
    keep = [j for j in jobs.values() if datetime.fromisoformat(j["end"]).replace(tzinfo=KST) > now - timedelta(days=7)]
    keep.sort(key=lambda j: j["end"])
    data = {"updated": now.strftime("%Y-%m-%d %H:%M"), "category": f"https://blog.naver.com/PostList.naver?blogId={BLOG}&from=postList&categoryNo=29", "jobs": keep}
    new = json.dumps(data, ensure_ascii=False, indent=1)
    prev = open(OUT, encoding="utf-8").read() if os.path.exists(OUT) else ""
    if re.sub(r'"updated": "[^"]*"', "", new) != re.sub(r'"updated": "[^"]*"', "", prev):
        open(OUT, "w", encoding="utf-8").write(new + "\n")
        print(f"jobs.json 갱신: {len(keep)}개")
    else:
        print("바뀐 것 없음")


if __name__ == "__main__":
    main()
