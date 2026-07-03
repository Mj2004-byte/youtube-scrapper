"""Debug script - opens Fireship playlists page visibly and dumps what selectors find."""
import asyncio
from playwright.async_api import async_playwright

async def debug_scrape():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        url = "https://www.youtube.com/@Fireship/playlists"
        print(f"Navigating to: {url}")
        await page.goto(url, timeout=60000)
        await page.wait_for_timeout(8000)
        
        # Scroll a few times
        for i in range(10):
            await page.mouse.wheel(0, 3000)
            await page.wait_for_timeout(1500)
            print(f"Scroll {i+1}/10")
        
        await page.wait_for_timeout(3000)
        
        # Debug: check what's actually on the page
        debug_info = await page.evaluate("""
        () => {
            const info = {};
            
            // Check page URL (did it redirect?)
            info.currentUrl = window.location.href;
            
            // Check for consent dialogs
            info.consentDialogs = document.querySelectorAll('ytd-consent-bump-v2-lightbox, tp-yt-paper-dialog').length;
            
            // Check all possible playlist-related elements
            info.gridPlaylistRenderer = document.querySelectorAll('ytd-grid-playlist-renderer').length;
            info.richItemRenderer = document.querySelectorAll('ytd-rich-item-renderer').length;
            info.lockupViewModel = document.querySelectorAll('ytd-lockup-view-model').length;
            info.compactStation = document.querySelectorAll('ytd-compact-station-renderer').length;
            info.shelfRenderer = document.querySelectorAll('ytd-shelf-renderer').length;
            info.itemSectionRenderer = document.querySelectorAll('ytd-item-section-renderer').length;
            
            // Check for any links with list= param
            const playlistLinks = document.querySelectorAll('a[href*="list="]');
            info.playlistLinkCount = playlistLinks.length;
            info.samplePlaylistLinks = Array.from(playlistLinks).slice(0, 5).map(a => ({
                text: a.innerText?.trim()?.slice(0, 80),
                href: a.href?.slice(0, 120),
                tag: a.tagName,
                parentTag: a.parentElement?.tagName,
                grandparentTag: a.parentElement?.parentElement?.tagName,
                closestRenderer: a.closest('[class*="renderer"], [class*="model"]')?.tagName || 'none'
            }));
            
            // Check for tab bar - maybe playlists tab doesn't exist
            const tabs = Array.from(document.querySelectorAll('yt-tab-shape, tp-yt-paper-tab, [role="tab"]'));
            info.tabNames = tabs.map(t => t.innerText?.trim()).filter(Boolean);
            
            // Check channel name
            const nameEl = document.querySelector('yt-formatted-string.ytd-channel-name') 
                        || document.querySelector('#channel-name');
            info.channelName = nameEl?.innerText?.trim() || 'NOT FOUND';
            
            // Dump all custom element tags on the page that contain "playlist" or "grid"
            const allElements = new Set();
            document.querySelectorAll('*').forEach(el => {
                const tag = el.tagName.toLowerCase();
                if (tag.includes('playlist') || tag.includes('lockup') || tag.includes('shelf') || tag.includes('grid-playlist')) {
                    allElements.add(tag);
                }
            });
            info.relevantTags = Array.from(allElements);
            
            return info;
        }
        """)
        
        print("\n========== DEBUG INFO ==========")
        for key, value in debug_info.items():
            print(f"  {key}: {value}")
        print("================================\n")
        
        # Keep browser open for manual inspection
        print("Browser is open - inspect the page manually. Press Enter to close...")
        input()
        await browser.close()

asyncio.run(debug_scrape())
