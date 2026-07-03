from playwright.sync_api import sync_playwright
import time
import json

URL = "https://www.youtube.com/@IITMadrasBSDegreeProgramme/courses"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)  # keep visible for now
    page = browser.new_page()

    print("Opening page...")
    page.goto(URL, timeout=60000)
    page.wait_for_timeout(8000)  # let YouTube JS load

    print("Scrolling page...")
    for _ in range(8):
        page.mouse.wheel(0, 3000)
        time.sleep(2)

    print("Extracting courses...")
    courses = page.evaluate("""
    () => {
        const items = Array.from(document.querySelectorAll('ytd-rich-grid-media'));
        return items.map(item => {
            const titleEl = item.querySelector('#video-title');
            const title = titleEl ? titleEl.innerText.trim() : null;

            const text = item.innerText;
            const lessonsMatch = text.match(/\\d+\\s+lessons/);
            const lessons = lessonsMatch ? lessonsMatch[0] : null;

            const link = titleEl ? titleEl.getAttribute('href') : null;

            const img =
              item.querySelector('img[src]') ||
              item.querySelector('img[data-src]');

            const thumbnail =
              img?.getAttribute('src') ||
              img?.getAttribute('data-src') ||
              null;

            if (!lessons) return null; // only keep real courses

            return {
                title,
                lessons,
                url: link ? 'https://www.youtube.com' + link : null,
                thumbnail
            };
        }).filter(Boolean);
    }
    """)

    browser.close()

with open("iitm_bs_courses.json", "w", encoding="utf-8") as f:
    json.dump(courses, f, indent=2, ensure_ascii=False)

print(f"✅ Fetched {len(courses)} courses")
