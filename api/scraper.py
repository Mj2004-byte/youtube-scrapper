"""
Generic YouTube Channel Scraper.
Scrapes courses/playlists from ANY YouTube channel using Playwright.
"""

import asyncio
import json
import re
import os
from datetime import datetime
from pathlib import Path
from playwright.async_api import async_playwright

from classifier import classify


# ── Resolve data directory ──
DATA_DIR = Path(__file__).parent.parent / "data" / "channels"
DATA_DIR.mkdir(parents=True, exist_ok=True)


def _slugify(name: str) -> str:
    """Convert a channel name/URL into a filesystem-safe slug."""
    # Remove URL parts, keep just the handle or name
    name = name.strip("/").split("/")[-1]
    name = re.sub(r"[^a-zA-Z0-9_-]", "_", name).strip("_").lower()
    return name or "unknown_channel"


def _extract_handle_from_url(url: str) -> str:
    """Extract the @handle from a YouTube channel URL."""
    match = re.search(r"@([\w.-]+)", url)
    return match.group(0) if match else url.strip("/").split("/")[-1]


def _parse_lessons(lessons_str: str) -> int:
    """Parse '77 lessons' → 77."""
    if not lessons_str:
        return 0
    match = re.search(r"(\d+)", str(lessons_str))
    return int(match.group(1)) if match else 0


async def scrape_channel_courses(channel_url: str, headless: bool = True) -> dict:
    """
    Scrape the /courses tab of a YouTube channel.
    Returns a dict with channel metadata + courses list.
    """
    # Normalise URL
    channel_url = channel_url.rstrip("/")
    if not channel_url.endswith("/courses"):
        channel_url += "/courses"

    handle = _extract_handle_from_url(channel_url)
    slug = _slugify(handle)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=headless)
        page = await browser.new_page()

        print(f"[SCRAPE] Scraping: {channel_url}")
        await page.goto(channel_url, timeout=60000)
        await page.wait_for_timeout(5000)

        # Get channel name from page
        channel_name = await page.evaluate("""
        () => {
            const el = document.querySelector('yt-formatted-string.ytd-channel-name');
            return el ? el.innerText.trim() : null;
        }
        """)

        # Scroll to load all content
        print("[SCROLL] Scrolling to load all courses...")
        for i in range(10):
            await page.mouse.wheel(0, 3000)
            await page.wait_for_timeout(1500)

        # Extract courses
        print("[EXTRACT] Extracting courses...")
        raw_courses = await page.evaluate("""
        () => {
            const items = Array.from(document.querySelectorAll('ytd-rich-grid-media'));
            return items.map(item => {
                const titleEl = item.querySelector('#video-title');
                const title = titleEl?.innerText?.trim() || null;

                const lessonsMatch = item.innerText.match(/\\d+\\s+lessons/);
                const lessons = lessonsMatch ? lessonsMatch[0] : null;

                let url = null;
                try {
                    url = titleEl?.closest('a')?.href || null;
                } catch (e) {}

                const img = item.querySelector('img[src]') || item.querySelector('img[data-src]');
                const thumbnail = img?.getAttribute('src') || img?.getAttribute('data-src') || null;

                if (!title) return null;

                return { title, lessons, url, thumbnail };
            }).filter(Boolean);
        }
        """)

        # Also get subscriber count
        subscribers = await page.evaluate("""
        () => {
            const el = document.querySelector('#subscriber-count');
            return el ? el.innerText.trim() : null;
        }
        """)

        await browser.close()

    # Process courses
    courses = []
    for c in raw_courses:
        lesson_count = _parse_lessons(c.get("lessons", "0"))
        courses.append({
            "title": c["title"],
            "lessons": lesson_count,
            "url": c.get("url", ""),
            "thumbnail": c.get("thumbnail"),
            "domain": classify(c["title"])
        })

    # Build result
    result = {
        "channel": {
            "name": channel_name or handle,
            "handle": handle,
            "slug": slug,
            "url": channel_url.replace("/courses", ""),
            "subscribers": subscribers,
            "scraped_at": datetime.now().isoformat(),
        },
        "courses": courses,
        "stats": {
            "total_courses": len(courses),
            "total_lessons": sum(c["lessons"] for c in courses),
        }
    }

    # Save to data directory
    channel_dir = DATA_DIR / slug
    channel_dir.mkdir(parents=True, exist_ok=True)

    # Save metadata
    meta_path = channel_dir / "metadata.json"
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(result["channel"], f, indent=2, ensure_ascii=False)

    # Save timestamped snapshot
    date_str = datetime.now().strftime("%Y-%m-%d")
    snapshot_path = channel_dir / f"{date_str}.json"
    with open(snapshot_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    # Also save as 'latest.json' for quick access
    latest_path = channel_dir / "latest.json"
    with open(latest_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"[OK] Scraped {len(courses)} courses from {channel_name or handle}")
    return result


async def scrape_channel_playlists(channel_url: str, headless: bool = True) -> dict:
    """
    Scrape the /playlists tab of a YouTube channel.
    Returns a dict with channel metadata + playlists list.
    """
    channel_url = channel_url.rstrip("/")
    if not channel_url.endswith("/playlists"):
        channel_url = re.sub(r"/courses$", "", channel_url)
        if not channel_url.endswith("/playlists"):
            channel_url += "/playlists"

    handle = _extract_handle_from_url(channel_url)
    slug = _slugify(handle)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=headless)
        page = await browser.new_page()

        print(f"[SCRAPE] Scraping playlists: {channel_url}")
        await page.goto(channel_url, timeout=60000)
        await page.wait_for_timeout(6000)

        # Dismiss cookie/consent dialogs if present
        try:
            consent_btn = page.locator('button[aria-label*="Accept"], button[aria-label*="Reject"], tp-yt-paper-button.ytd-consent-bump-v2-lightbox')
            if await consent_btn.count() > 0:
                await consent_btn.first.click()
                await page.wait_for_timeout(2000)
        except Exception:
            pass

        # Get channel name
        channel_name = await page.evaluate("""
        () => {
            const el = document.querySelector('yt-formatted-string.ytd-channel-name')
                     || document.querySelector('#channel-name yt-formatted-string')
                     || document.querySelector('#text.ytd-channel-name')
                     || document.querySelector('#channel-header-container yt-formatted-string');
            if (el) return el.innerText.trim();
            // Fallback: get from page title
            const title = document.title || '';
            const match = title.match(/^(.+?)\\s*[-–]\\s*YouTube/);
            return match ? match[1].trim() : null;
        }
        """)

        # Scroll extensively to load all playlists
        print("[SCROLL] Scrolling to load all playlists...")
        for _ in range(20):
            await page.mouse.wheel(0, 4000)
            await page.wait_for_timeout(1500)

        # Wait for playlist items to appear
        await page.wait_for_timeout(3000)

        # Extract playlists using the simplest reliable approach
        raw_playlists = await page.evaluate("""
        () => {
            const results = [];
            const seen = new Set();
            const videoRegex = /(\d+)\s+video/;

            // Current YouTube layout: yt-lockup-view-model elements
            // Title is in h3 > a, video count in sibling links
            document.querySelectorAll('yt-lockup-view-model').forEach(el => {
                const titleLink = el.querySelector('h3 a');
                const title = titleLink ? titleLink.innerText.trim() : null;
                
                if (!title || seen.has(title)) return;
                seen.add(title);

                const playlistLink = el.querySelector('a[href*="playlist?list="]');
                const url = playlistLink ? playlistLink.href : (titleLink ? titleLink.href : null);

                let videoCount = null;
                const allText = el.innerText || '';
                const countMatch = allText.match(videoRegex);
                if (countMatch) videoCount = countMatch[0];

                results.push({
                    title,
                    url,
                    thumbnail: el.querySelector('img') ? el.querySelector('img').src : null,
                    videoCount
                });
            });

            // Fallback for older YouTube layout
            if (results.length === 0) {
                document.querySelectorAll('ytd-grid-playlist-renderer').forEach(el => {
                    const a = el.querySelector('a#video-title');
                    if (!a) return;
                    const title = a.innerText.trim();
                    if (!title || seen.has(title)) return;
                    seen.add(title);
                    const countEl = el.querySelector('#overlays span');
                    results.push({
                        title,
                        url: a.href,
                        thumbnail: el.querySelector('img') ? el.querySelector('img').src : null,
                        videoCount: countEl ? countEl.innerText.trim() : null
                    });
                });
            }

            return results;
        }
        """)

        # Get subscriber count too
        subscribers = await page.evaluate("""
        () => {
            const el = document.querySelector('#subscriber-count');
            return el ? el.innerText.trim() : null;
        }
        """)

        print(f"[EXTRACT] Found {len(raw_playlists)} raw playlists")
        await browser.close()

    playlists = []
    for pl in raw_playlists:
        video_count = _parse_lessons(pl.get("videoCount", "0"))
        playlists.append({
            "title": pl["title"],
            "lessons": video_count,
            "videoCount": video_count,
            "url": pl.get("url", ""),
            "thumbnail": pl.get("thumbnail"),
            "domain": classify(pl["title"])
        })

    result = {
        "channel": {
            "name": channel_name or handle,
            "handle": handle,
            "slug": slug,
            "url": channel_url.replace("/playlists", ""),
            "subscribers": subscribers,
            "scraped_at": datetime.now().isoformat(),
        },
        "playlists": playlists,
        "stats": {
            "total_playlists": len(playlists),
            "total_videos": sum(p["videoCount"] for p in playlists),
        }
    }

    # Save
    channel_dir = DATA_DIR / slug
    channel_dir.mkdir(parents=True, exist_ok=True)

    # Save metadata
    meta_path = channel_dir / "metadata.json"
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(result["channel"], f, indent=2, ensure_ascii=False)

    # Save timestamped snapshot
    date_str = datetime.now().strftime("%Y-%m-%d")
    playlist_path = channel_dir / f"playlists_{date_str}.json"
    with open(playlist_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    # Save as latest.json so dashboard can load it
    latest_path = channel_dir / "latest.json"
    with open(latest_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"[OK] Scraped {len(playlists)} playlists from {channel_name or handle}")
    return result


def load_existing_channel(slug: str) -> dict | None:
    """Load the latest.json for a saved channel."""
    latest_path = DATA_DIR / slug / "latest.json"
    if latest_path.exists():
        with open(latest_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def list_saved_channels() -> list[dict]:
    """List all channels that have been scraped and saved."""
    channels = []
    if not DATA_DIR.exists():
        return channels
    for channel_dir in DATA_DIR.iterdir():
        if channel_dir.is_dir():
            meta_path = channel_dir / "metadata.json"
            latest_path = channel_dir / "latest.json"
            if meta_path.exists():
                with open(meta_path, "r", encoding="utf-8") as f:
                    meta = json.load(f)
                # Count snapshots
                snapshots = [f for f in channel_dir.glob("20*.json")]
                meta["snapshot_count"] = len(snapshots)
                meta["has_data"] = latest_path.exists()
                channels.append(meta)
    return channels


def load_channel_snapshots(slug: str) -> list[dict]:
    """Load all timestamped snapshots for trend analysis."""
    channel_dir = DATA_DIR / slug
    if not channel_dir.exists():
        return []
    
    snapshots = []
    for f in sorted(channel_dir.glob("20*.json")):
        with open(f, "r", encoding="utf-8") as fp:
            data = json.load(fp)
            data["_snapshot_date"] = f.stem  # e.g. "2025-05-04"
            snapshots.append(data)
    return snapshots


# ── CLI entry point ──
if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python scraper.py <channel_url> [--playlists]")
        print("Example: python scraper.py https://www.youtube.com/@freecodecamp")
        sys.exit(1)

    url = sys.argv[1]
    mode = "--playlists" if "--playlists" in sys.argv else "--courses"

    if mode == "--playlists":
        asyncio.run(scrape_channel_playlists(url, headless=False))
    else:
        asyncio.run(scrape_channel_courses(url, headless=False))
