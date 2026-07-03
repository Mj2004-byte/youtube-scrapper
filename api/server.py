"""
FastAPI Server for EdTech Content Intelligence.
Provides REST endpoints for scraping, data access, and channel management.
"""

import os
import json
from pathlib import Path
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse
from pydantic import BaseModel

from scraper import (
    scrape_channel_courses,
    scrape_channel_playlists,
    load_existing_channel,
    list_saved_channels,
    load_channel_snapshots,
    DATA_DIR,
)
from classifier import classify, get_all_domains, DOMAINS


# ── Seed existing IITM data on startup ──
def seed_iitm_data():
    """Import existing iitm_bs_courses.json into the new data structure."""
    iitm_slug = "iitmadrasbsdegreeprogramme"
    target_dir = DATA_DIR / iitm_slug
    latest_path = target_dir / "latest.json"

    if latest_path.exists():
        return  # Already seeded

    # Look for existing scraped data
    old_data_path = Path(__file__).parent.parent / "yt-course-scraper" / "iitm_bs_courses.json"
    if not old_data_path.exists():
        return

    target_dir.mkdir(parents=True, exist_ok=True)

    with open(old_data_path, "r", encoding="utf-8") as f:
        raw_courses = json.load(f)

    # Convert to new format
    import re
    courses = []
    for c in raw_courses:
        lesson_str = c.get("lessons", "0")
        match = re.search(r"(\d+)", str(lesson_str))
        lesson_count = int(match.group(1)) if match else 0
        courses.append({
            "title": c["title"],
            "lessons": lesson_count,
            "url": c.get("url", ""),
            "thumbnail": c.get("thumbnail"),
            "domain": classify(c["title"])
        })

    result = {
        "channel": {
            "name": "IIT Madras BS Degree Programme",
            "handle": "@IITMadrasBSDegreeProgramme",
            "slug": iitm_slug,
            "url": "https://www.youtube.com/@IITMadrasBSDegreeProgramme",
            "subscribers": None,
            "scraped_at": datetime.now().isoformat(),
        },
        "courses": courses,
        "stats": {
            "total_courses": len(courses),
            "total_lessons": sum(c["lessons"] for c in courses),
        }
    }

    # Save metadata
    with open(target_dir / "metadata.json", "w", encoding="utf-8") as f:
        json.dump(result["channel"], f, indent=2, ensure_ascii=False)

    # Save as latest and dated snapshot
    date_str = datetime.now().strftime("%Y-%m-%d")
    for path in [latest_path, target_dir / f"{date_str}.json"]:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"[OK] Seeded IITM BS data: {len(courses)} courses")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    seed_iitm_data()
    yield
    # Shutdown — nothing to clean up


# ── App ──
app = FastAPI(
    title="EdTech Content Intelligence API",
    description="Scrape, classify, and analyze YouTube educational channels",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve dashboard as static files
DASHBOARD_DIR = Path(__file__).parent.parent / "dashboard"
app.mount("/dashboard", StaticFiles(directory=str(DASHBOARD_DIR), html=True), name="dashboard")


# ── Request Models ──
class ScrapeRequest(BaseModel):
    channel_url: str
    mode: str = "courses"  # "courses" or "playlists"


# ── Track active scrape jobs ──
scrape_jobs: dict[str, dict] = {}


# ── Routes ──

@app.get("/")
async def root():
    """Redirect to dashboard."""
    return RedirectResponse(url="/dashboard/")


@app.get("/api/channels")
async def get_channels():
    """List all saved channels."""
    channels = list_saved_channels()
    return {"channels": channels, "count": len(channels)}


@app.get("/api/channels/{slug}")
async def get_channel(slug: str):
    """Get latest data for a specific channel."""
    data = load_existing_channel(slug)
    if not data:
        raise HTTPException(status_code=404, detail=f"Channel '{slug}' not found")
    return data


@app.get("/api/channels/{slug}/snapshots")
async def get_channel_snapshots(slug: str):
    """Get all historical snapshots for trend analysis."""
    snapshots = load_channel_snapshots(slug)
    if not snapshots:
        raise HTTPException(status_code=404, detail=f"No snapshots found for '{slug}'")
    return {"slug": slug, "snapshots": snapshots, "count": len(snapshots)}


@app.post("/api/scrape")
async def start_scrape(req: ScrapeRequest, background_tasks: BackgroundTasks):
    """
    Start a background scrape job for a YouTube channel.
    Returns immediately with a job_id to poll for status.
    """
    from scraper import _slugify, _extract_handle_from_url
    handle = _extract_handle_from_url(req.channel_url)
    slug = _slugify(handle)

    # Check if already running
    if slug in scrape_jobs and scrape_jobs[slug].get("status") == "running":
        return {"status": "already_running", "slug": slug, "message": "Scrape is already in progress"}

    scrape_jobs[slug] = {
        "status": "running",
        "channel_url": req.channel_url,
        "started_at": datetime.now().isoformat(),
        "mode": req.mode,
    }

    def do_scrape():
        import asyncio
        import sys
        if sys.platform == 'win32':
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
            
        try:
            if req.mode == "playlists":
                result = asyncio.run(scrape_channel_playlists(req.channel_url, headless=False))
            else:
                result = asyncio.run(scrape_channel_courses(req.channel_url, headless=False))
            scrape_jobs[slug] = {
                "status": "done",
                "channel_url": req.channel_url,
                "completed_at": datetime.now().isoformat(),
                "result_summary": result.get("stats", {}),
                "channel": result.get("channel", {}),
            }
        except Exception as e:
            scrape_jobs[slug] = {
                "status": "error",
                "channel_url": req.channel_url,
                "error": str(e),
            }

    background_tasks.add_task(do_scrape)

    return {
        "status": "started",
        "slug": slug,
        "message": f"Scraping {req.channel_url} in the background. Poll /api/scrape/status/{slug} for updates."
    }


@app.get("/api/scrape/status/{slug}")
async def get_scrape_status(slug: str):
    """Check the status of a scrape job."""
    if slug not in scrape_jobs:
        raise HTTPException(status_code=404, detail=f"No scrape job found for '{slug}'")
    return scrape_jobs[slug]


@app.get("/api/domains")
async def get_domains():
    """Get all domain classifications and their colors."""
    return {"domains": get_all_domains()}


@app.get("/api/compare")
async def compare_channels(slugs: str):
    """
    Compare multiple channels side by side.
    Usage: /api/compare?slugs=iitm_bs,mit_ocw
    """
    slug_list = [s.strip() for s in slugs.split(",") if s.strip()]
    if len(slug_list) < 2:
        raise HTTPException(status_code=400, detail="Provide at least 2 channel slugs, comma-separated")

    comparison = []
    for slug in slug_list:
        data = load_existing_channel(slug)
        if data:
            # Compute domain distribution
            domain_dist = {}
            for c in data.get("courses", []):
                d = c.get("domain", "Other")
                domain_dist[d] = domain_dist.get(d, 0) + 1
            comparison.append({
                "channel": data.get("channel", {}),
                "stats": data.get("stats", {}),
                "domain_distribution": domain_dist,
            })

    return {"comparison": comparison, "count": len(comparison)}


# ── Entry point ──
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=True)
