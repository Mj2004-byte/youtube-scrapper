<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/Playwright-Chromium-2EAD33?style=for-the-badge&logo=playwright&logoColor=white" />
  <img src="https://img.shields.io/badge/Gemini_AI-Powered-4285F4?style=for-the-badge&logo=googlegemini&logoColor=white" />
  <img src="https://img.shields.io/badge/Status-Active-00C853?style=for-the-badge" />
</p>

<h1 align="center">📊 EdTech Content Intelligence</h1>
<p align="center">
  <strong>Automated YouTube course scraping, AI-powered analysis & market research dashboard</strong><br/>
  <em>Turn raw YouTube data into actionable EdTech insights</em>
</p>

---

## 🎯 What It Does

Scrapes educational YouTube channels (courses & playlists), categorizes content by domain, detects market trends, and generates AI-powered insights — turning video catalogs into competitive intelligence.

```
📡 Scrape ──→ 🏷️ Categorize ──→ 📈 Analyze ──→ 🤖 AI Insights ──→ 📊 Dashboard
```

## ✨ Key Features

| Feature | Description |
|---|---|
| 🕷️ **Smart Scraping** | Playwright-based scraping with auto-scroll and lazy-load handling |
| 🏷️ **Domain Classification** | Auto-categorizes into AI/ML, Data Science, Programming, Math, Business |
| 📊 **Market Dashboard** | Interactive dashboard with charts, filters, and domain analytics |
| 🔍 **Content Gap Detection** | Identifies missing topics vs competitor channels |
| 🤖 **AI Insights** | Gemini-powered strategic recommendations |

## 🏗️ Project Structure

```
yt-channel-data-scrapper/
├── yt-course-scraper/
│   ├── scrape_courses.py          # Course scraper (Playwright)
│   ├── scrape_courses_fixed.py    # Enhanced with deep-link URLs
│   ├── scrape_playlists.py        # Playlist scraper
│   └── iitm_bs_courses.json       # Scraped data (55+ courses)
├── dashboard/
│   └── index.html                 # Market intelligence dashboard
└── README.md
```

## 🚀 Quick Start

```bash
# Install dependencies
pip install playwright
playwright install chromium

# Scrape courses
cd yt-course-scraper
python scrape_courses_fixed.py

# Scrape playlists
python scrape_playlists.py

# View dashboard — open dashboard/index.html in browser
```

## 📈 Data Overview

Tracking **IIT Madras BS Degree** — **55+ courses**, **3,900+ lessons**:

| Domain | Courses | Examples |
|---|---|---|
| AI & Machine Learning | 14 | ML Foundations, Deep Learning, NLP, LLMs |
| Programming & Dev | 10 | Python, Java, MAD-I, Software Engineering |
| Data Science | 7 | Statistics, Business Analytics, Big Data |
| Mathematics | 6 | Calculus, Linear Statistical Models |
| Business & Finance | 5 | Corporate Finance, Game Theory |

## 🎯 Use Cases

- **EdTech Companies** — Data-driven content strategy & competitor analysis
- **Course Creators** — Find underserved high-demand topics
- **Market Researchers** — Track educational content trends
- **Operations Teams** — Automate weekly competitive intelligence

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Scraping | Python + Playwright (Chromium) |
| Data | JSON + domain classification |
| Dashboard | HTML/CSS/JS + Chart.js |
| AI Layer | Google Gemini API |

## 🗺️ Roadmap

- [x] Course & playlist scraping with Playwright
- [x] Deep-link URL resolution
- [x] Interactive analytics dashboard
- [ ] Multi-channel tracking (MIT OCW, NPTEL, Coursera)
- [ ] Historical trend analysis
- [ ] Automated weekly email reports
- [ ] Full Gemini AI pipeline

---

<p align="center"><strong>Built with ❤️ for data-driven decision making</strong></p>
