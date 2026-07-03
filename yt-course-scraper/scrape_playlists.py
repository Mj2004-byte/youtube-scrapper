from playwright.sync_api import sync_playwright
import json
import time

URL = "https://www.youtube.com/@IITMadrasBSDegreeProgramme/playlists"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto(URL, timeout=60000)

    # Scroll multiple times
    for _ in range(15):
        page.mouse.wheel(0, 5000)
        time.sleep(1.5)

    playlists = page.evaluate("""
    () => Array.from(document.querySelectorAll('ytd-grid-playlist-renderer')).map(p => {
        const a = p.querySelector('a#video-title');
        return {
            title: a?.innerText.trim(),
            url: a ? 'https://www.youtube.com' + a.getAttribute('href') : null,
            thumbnail: p.querySelector('img')?.src || null
        }
    })
    """)

    browser.close()

with open("all_playlists.json", "w", encoding="utf-8") as f:
    json.dump(playlists, f, indent=2, ensure_ascii=False)

print(f"✅ Found {len(playlists)} playlists")
