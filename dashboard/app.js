// ═══════════════════════════════════════════════
// EdTech Content Intelligence — Dynamic Dashboard
// ═══════════════════════════════════════════════

const API_BASE = window.location.port === "" ? "" : `http://localhost:8000`;

// ── Domain Config ──
const DOMAINS = {
  "AI & Machine Learning": { color: "#6366f1", keywords: ["machine learning","deep learning","ai:","ai ","artificial intelligence","nlp","natural language","reinforcement","llm","large language","generative ai","computer vision","speech","mlops","neural network","tensorflow","pytorch","transformer"] },
  "Data Science": { color: "#06b6d4", keywords: ["data science","statistics","big data","analytics","data visualization","statistical computing","tools in data","business data","data analysis","data mining"] },
  "Programming": { color: "#10b981", keywords: ["python","java","javascript","programming","algorithms","software engineering","software testing","system commands","application development","operating systems","dsa","data structures","web development","coding","react","node"] },
  "Mathematics": { color: "#f59e0b", keywords: ["math","calculus","mathematical thinking","diploma mathematics","linear algebra","probability","discrete math","optimization"] },
  "Business & Finance": { color: "#f43f5e", keywords: ["corporate finance","managerial economics","market research","financial forensics","game theory","industry 4.0","business analytics","entrepreneurship","management","marketing","economics"] },
  "Foundational": { color: "#8b5cf6", keywords: ["english","computational thinking","design thinking","professional growth","ct qualifier","privacy and security","communication"] },
  "Cloud & DevOps": { color: "#ec4899", keywords: ["cloud","aws","azure","docker","kubernetes","devops","ci/cd","terraform","serverless"] },
  "Cybersecurity": { color: "#14b8a6", keywords: ["cybersecurity","ethical hacking","penetration testing","network security","cryptography"] }
};

function classify(title) {
  const t = title.toLowerCase();
  for (const [domain, cfg] of Object.entries(DOMAINS)) {
    if (cfg.keywords.some(k => t.includes(k))) return domain;
  }
  return "Other";
}

function getDomainColor(d) { return DOMAINS[d]?.color || "#64748b"; }

// ── State ──
let courses = [];
let domainGroups = {};
let currentFilter = "all";
let currentSearch = "";
let sortKey = "lessons";
let sortDir = -1;
let activeChannelData = null;
let pieChart = null;
let barChart = null;

// ── Toast ──
function showToast(msg, type = "info") {
  const c = document.getElementById("toastContainer");
  const t = document.createElement("div");
  t.className = `toast ${type}`;
  t.textContent = msg;
  c.appendChild(t);
  setTimeout(() => { t.style.opacity = "0"; setTimeout(() => t.remove(), 300); }, 4000);
}

// ── Fill channel input from hint chips ──
function fillChannel(url) {
  document.getElementById("channelInput").value = url;
  document.getElementById("channelInput").focus();
}

// ── Load saved channels list ──
async function loadChannelList() {
  try {
    const res = await fetch(`${API_BASE}/api/channels`);
    if (!res.ok) throw new Error("API not reachable");
    const data = await res.json();
    const container = document.getElementById("channelChips");
    container.innerHTML = "";
    if (data.channels.length === 0) {
      container.innerHTML = '<span style="font-size:.75rem;color:var(--text-muted)">No channels scraped yet. Scrape one above!</span>';
      return;
    }
    data.channels.forEach(ch => {
      const btn = document.createElement("button");
      btn.className = "channel-chip";
      btn.dataset.slug = ch.slug;
      btn.textContent = ch.name || ch.handle;
      btn.onclick = () => loadChannel(ch.slug);
      container.appendChild(btn);
    });
  } catch (e) {
    document.getElementById("channelChips").innerHTML = '<span style="font-size:.75rem;color:var(--text-muted)">Start the API server to enable live scraping</span>';
  }
}

// ── Load a specific channel's data ──
async function loadChannel(slug) {
  try {
    const res = await fetch(`${API_BASE}/api/channels/${slug}`);
    if (!res.ok) throw new Error("Channel not found");
    const data = await res.json();
    activeChannelData = data;
    const items = data.courses || data.playlists || [];
    courses = items.map(c => ({
      title: c.title, lessons: c.lessons ?? c.videoCount ?? 0, url: c.url, domain: c.domain || classify(c.title), thumbnail: c.thumbnail
    }));
    // Highlight active chip
    document.querySelectorAll(".channel-chip").forEach(c => c.classList.toggle("active", c.dataset.slug === slug));
    renderAll();
    showToast(`Loaded ${data.channel.name} — ${courses.length} courses`, "success");
  } catch (e) {
    showToast("Failed to load channel: " + e.message, "error");
  }
}

function promptScrapeMode() {
  const url = document.getElementById("channelInput").value.trim();
  if (!url) { showToast("Please enter a YouTube channel URL", "error"); return; }
  if (!url.includes("youtube.com")) { showToast("Please enter a valid YouTube URL", "error"); return; }
  document.getElementById("scrapeModeModal").style.display = "flex";
}

function closeScrapeModal() {
  document.getElementById("scrapeModeModal").style.display = "none";
}

// ── Start a live scrape ──
async function startScrape(mode = 'courses') {
  closeScrapeModal();
  const url = document.getElementById("channelInput").value.trim();

  const btn = document.getElementById("scrapeBtn");
  btn.disabled = true;
  btn.querySelector(".btn-text").style.display = "none";
  btn.querySelector(".btn-loader").style.display = "inline";
  document.getElementById("statusDot").classList.add("scraping");
  document.getElementById("statusText").textContent = "Scraping...";

  const progress = document.getElementById("scrapeProgress");
  progress.style.display = "block";
  document.getElementById("progressFill").style.width = "30%";
  document.getElementById("progressText").textContent = "Launching browser & navigating to channel...";

  try {
    const res = await fetch(`${API_BASE}/api/scrape`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ channel_url: url, mode: mode })
    });
    const data = await res.json();
    if (data.status === "already_running") {
      showToast("Scrape already in progress for this channel", "info");
    }
    // Poll for completion
    const slug = data.slug;
    document.getElementById("progressFill").style.width = "60%";
    document.getElementById("progressText").textContent = "Scrolling & extracting course data...";
    await pollScrapeStatus(slug);
  } catch (e) {
    showToast("Scrape failed. Is the API server running? (python api/server.py)", "error");
  } finally {
    btn.disabled = false;
    btn.querySelector(".btn-text").style.display = "inline";
    btn.querySelector(".btn-loader").style.display = "none";
    document.getElementById("statusDot").classList.remove("scraping");
    document.getElementById("statusText").textContent = "Ready";
    progress.style.display = "none";
  }
}

async function pollScrapeStatus(slug) {
  for (let i = 0; i < 60; i++) {
    await new Promise(r => setTimeout(r, 3000));
    try {
      const res = await fetch(`${API_BASE}/api/scrape/status/${slug}`);
      const data = await res.json();
      if (data.status === "done") {
        document.getElementById("progressFill").style.width = "100%";
        document.getElementById("progressText").textContent = "Done! Loading dashboard...";
        const total = data.result_summary?.total_courses ?? data.result_summary?.total_playlists ?? 0;
        showToast(`Scrape complete! ${total} items found.`, "success");
        await loadChannelList();
        await loadChannel(slug);
        return;
      }
      if (data.status === "error") {
        showToast("Scrape error: " + (data.error || "Unknown error"), "error");
        return;
      }
      document.getElementById("progressFill").style.width = `${60 + i}%`;
    } catch (e) { /* keep polling */ }
  }
  showToast("Scrape timed out", "error");
}

// ── Render everything ──
function renderAll() {
  // Build domain groups
  domainGroups = {};
  courses.forEach(c => {
    (domainGroups[c.domain] = domainGroups[c.domain] || []).push(c);
  });

  const totalLessons = courses.reduce((s, c) => s + c.lessons, 0);
  const avgLessons = courses.length ? Math.round(totalLessons / courses.length) : 0;
  const domainCount = Object.keys(domainGroups).length;

  // Active channel banner
  const banner = document.getElementById("activeChannel");
  if (activeChannelData) {
    banner.style.display = "block";
    document.getElementById("activeChannelName").textContent = activeChannelData.channel.name;
    const scraped = activeChannelData.channel.scraped_at;
    document.getElementById("activeChannelMeta").textContent = scraped ? `· Scraped ${new Date(scraped).toLocaleDateString()}` : "";
  }

  // Hero stats
  document.getElementById("heroStats").innerHTML = [
    { num: courses.length, label: "Courses Tracked", color: "#6366f1" },
    { num: totalLessons.toLocaleString(), label: "Total Lessons", color: "#06b6d4" },
    { num: domainCount, label: "Domains", color: "#10b981" },
    { num: avgLessons, label: "Avg Lessons", color: "#f59e0b" }
  ].map((s, i) => `<div class="hero-stat animate-in animate-delay-${i+1}">
    <span class="num" style="color:${s.color}">${s.num}</span>
    <span class="label">${s.label}</span>
  </div>`).join("");

  renderStats();
  renderCharts();
  renderDomainCards();
  renderFilterChips();
  renderTable();
  renderInsights();
  reobserve();
}

function renderStats() {
  if (!courses.length) {
    document.getElementById("statsGrid").innerHTML = '<div class="empty-state"><div class="empty-icon">📡</div><p>Scrape a channel to see stats</p></div>';
    return;
  }
  const totalLessons = courses.reduce((s, c) => s + c.lessons, 0);
  const avgLessons = Math.round(totalLessons / courses.length);
  const deepCount = courses.filter(c => c.lessons >= 90).length;
  const topCourse = courses.reduce((a, b) => a.lessons > b.lessons ? a : b);
  const topDomain = Object.entries(domainGroups).sort((a, b) => b[1].length - a[1].length)[0];

  document.getElementById("statsGrid").innerHTML = [
    { icon: "📚", value: courses.length, label: "Total Courses" },
    { icon: "🎓", value: totalLessons.toLocaleString(), label: "Total Lessons" },
    { icon: "📐", value: avgLessons, label: "Avg Lessons/Course" },
    { icon: "🏆", value: topCourse.lessons, label: `Top: ${topCourse.title.slice(0, 20)}…` },
    { icon: "🔬", value: deepCount, label: "Deep Courses (90+)" },
    { icon: "🏷️", value: topDomain[0], label: `Largest Domain (${topDomain[1].length})` }
  ].map(s => `<div class="stat-card">
    <div class="icon">${s.icon}</div>
    <div class="value">${s.value}</div>
    <div class="stat-label">${s.label}</div>
  </div>`).join("");
}

function renderCharts() {
  if (pieChart) pieChart.destroy();
  if (barChart) barChart.destroy();

  if (!courses.length) return;

  pieChart = new Chart(document.getElementById("domainPieChart"), {
    type: "doughnut",
    data: {
      labels: Object.keys(domainGroups),
      datasets: [{ data: Object.values(domainGroups).map(g => g.length), backgroundColor: Object.keys(domainGroups).map(getDomainColor), borderColor: "#111827", borderWidth: 2, hoverOffset: 8 }]
    },
    options: {
      responsive: true, maintainAspectRatio: false, cutout: "62%",
      plugins: { legend: { position: "bottom", labels: { color: "#94a3b8", padding: 16, font: { family: "Inter", size: 11 }, usePointStyle: true, pointStyleWidth: 8 } } }
    }
  });

  const domainNames = Object.keys(domainGroups);
  const domainAvgs = domainNames.map(d => {
    const g = domainGroups[d];
    return Math.round(g.reduce((s, c) => s + c.lessons, 0) / g.length);
  });

  barChart = new Chart(document.getElementById("depthBarChart"), {
    type: "bar",
    data: {
      labels: domainNames.map(n => n.length > 14 ? n.slice(0, 12) + "…" : n),
      datasets: [{ label: "Avg Lessons", data: domainAvgs, backgroundColor: domainNames.map(d => getDomainColor(d) + "cc"), borderColor: domainNames.map(getDomainColor), borderWidth: 1, borderRadius: 6, barPercentage: 0.65 }]
    },
    options: {
      responsive: true, maintainAspectRatio: false, indexAxis: "y",
      scales: {
        x: { grid: { color: "rgba(255,255,255,.05)" }, ticks: { color: "#64748b", font: { family: "Inter", size: 11 } } },
        y: { grid: { display: false }, ticks: { color: "#94a3b8", font: { family: "Inter", size: 11 } } }
      },
      plugins: { legend: { display: false } }
    }
  });
}

function renderDomainCards() {
  if (!courses.length) {
    document.getElementById("domainCards").innerHTML = '<div class="empty-state"><div class="empty-icon">🏷️</div><p>No domain data yet</p></div>';
    return;
  }
  document.getElementById("domainCards").innerHTML = Object.entries(domainGroups)
    .sort((a, b) => b[1].length - a[1].length)
    .map(([domain, items]) => {
      const color = getDomainColor(domain);
      const pct = Math.round((items.length / courses.length) * 100);
      const sorted = [...items].sort((a, b) => b.lessons - a.lessons);
      const shown = sorted.slice(0, 5);
      const more = sorted.length > 5 ? `<div class="domain-course-item" style="color:var(--text-muted);font-style:italic">+ ${sorted.length - 5} more courses</div>` : "";
      return `<div class="domain-card">
        <div class="domain-card-header">
          <div class="domain-dot" style="background:${color}"></div>
          <h3>${domain}</h3>
          <span class="domain-count">${items.length} courses · ${pct}%</span>
        </div>
        <div class="domain-bar"><div class="domain-bar-fill" style="width:${pct}%;background:${color}"></div></div>
        <div class="domain-courses">
          ${shown.map(c => `<div class="domain-course-item">
            <span>${c.title}</span>
            <span class="lessons-badge">${c.lessons} lessons</span>
          </div>`).join("")}
          ${more}
        </div>
      </div>`;
    }).join("");
}

function renderFilterChips() {
  const container = document.getElementById("filterChips");
  // Keep "All" chip, remove dynamic ones
  container.querySelectorAll(".chip:not([data-filter='all'])").forEach(c => c.remove());
  Object.keys(domainGroups).forEach(d => {
    const btn = document.createElement("button");
    btn.className = "chip";
    btn.dataset.filter = d;
    btn.textContent = d;
    container.appendChild(btn);
  });
}

function getDepthLevel(l) {
  if (l >= 90) return { label: "Deep", color: "#10b981", pct: 100 };
  if (l >= 50) return { label: "Medium", color: "#f59e0b", pct: 65 };
  return { label: "Light", color: "#f43f5e", pct: 30 };
}

function renderTable() {
  let filtered = [...courses];
  if (currentFilter !== "all") filtered = filtered.filter(c => c.domain === currentFilter);
  if (currentSearch) {
    const q = currentSearch.toLowerCase();
    filtered = filtered.filter(c => c.title.toLowerCase().includes(q) || c.domain.toLowerCase().includes(q));
  }
  filtered.sort((a, b) => {
    if (sortKey === "title") return sortDir * a.title.localeCompare(b.title);
    return sortDir * (a.lessons - b.lessons);
  });

  const tbody = document.getElementById("coursesBody");
  if (!filtered.length) {
    tbody.innerHTML = `<tr><td colspan="6" style="text-align:center;padding:2rem;color:var(--text-muted)">No courses found</td></tr>`;
    document.getElementById("tableFooter").textContent = "";
    return;
  }
  tbody.innerHTML = filtered.map((c, i) => {
    const depth = getDepthLevel(c.lessons);
    const color = getDomainColor(c.domain);
    return `<tr>
      <td>${i + 1}</td>
      <td class="course-title">${c.title}</td>
      <td><span class="domain-badge" style="background:${color}22;color:${color}">${c.domain}</span></td>
      <td><strong>${c.lessons}</strong></td>
      <td class="depth-bar-cell">
        <div class="depth-bar-bg"><div class="depth-bar-fg" style="width:${depth.pct}%;background:${depth.color}"></div></div>
      </td>
      <td>${c.url ? `<a href="${c.url}" target="_blank" class="link-btn">▶ Watch</a>` : '—'}</td>
    </tr>`;
  }).join("");

  document.getElementById("tableFooter").textContent = `Showing ${filtered.length} of ${courses.length} courses`;
}

function renderInsights() {
  const grid = document.getElementById("insightsGrid");
  if (!courses.length) {
    grid.innerHTML = '<div class="empty-state"><div class="empty-icon">🤖</div><p>Scrape a channel to generate insights</p></div>';
    return;
  }

  const totalLessons = courses.reduce((s, c) => s + c.lessons, 0);
  const avgLessons = Math.round(totalLessons / courses.length);
  const sortedDomains = Object.entries(domainGroups).sort((a, b) => b[1].length - a[1].length);
  const topDomain = sortedDomains[0];
  const deepCourses = courses.filter(c => c.lessons >= 90);
  const lightCourses = courses.filter(c => c.lessons < 30);
  const channelName = activeChannelData?.channel?.name || "This channel";

  // Detect which domains are missing
  const allDomains = Object.keys(DOMAINS);
  const presentDomains = new Set(Object.keys(domainGroups));
  const missingDomains = allDomains.filter(d => !presentDomains.has(d));

  grid.innerHTML = `
    <div class="insight-card insight-strengths">
      <div class="insight-icon">💪</div>
      <h3>Strengths</h3>
      <ul>
        <li><strong>${topDomain[0]} dominance</strong> — ${topDomain[1].length} courses (${Math.round(topDomain[1].length/courses.length*100)}% of catalog)</li>
        <li><strong>Content depth</strong> — Average ${avgLessons} lessons/course${avgLessons > 60 ? " shows thorough coverage" : ""}</li>
        ${deepCourses.length ? `<li><strong>${deepCourses.length} deep courses</strong> (90+ lessons) — strong for serious learners</li>` : ""}
        <li><strong>${sortedDomains.length} domains</strong> covered across ${courses.length} courses</li>
      </ul>
    </div>
    <div class="insight-card insight-gaps">
      <div class="insight-icon">⚠️</div>
      <h3>Content Gaps</h3>
      <ul>
        ${missingDomains.slice(0, 3).map(d => `<li><strong>${d}</strong> — No courses detected in this domain</li>`).join("")}
        ${lightCourses.length > 3 ? `<li><strong>${lightCourses.length} light courses</strong> (< 30 lessons) may feel incomplete</li>` : ""}
        ${missingDomains.length === 0 ? "<li>Good coverage across all tracked domains!</li>" : ""}
      </ul>
    </div>
    <div class="insight-card insight-recommendations">
      <div class="insight-icon">🎯</div>
      <h3>Recommendations</h3>
      <ul>
        ${missingDomains.length ? `<li><strong>Add ${missingDomains[0]} content</strong> — gap vs competitors</li>` : ""}
        ${lightCourses.length ? `<li><strong>Expand shallow courses</strong> — ${lightCourses.slice(0,2).map(c=>c.title).join(", ")} could benefit from more lessons</li>` : ""}
        <li><strong>Double down on ${topDomain[0]}</strong> — already strongest domain</li>
        <li><strong>Track competitors</strong> — scrape more channels for comparison</li>
      </ul>
    </div>
    <div class="insight-card insight-trends">
      <div class="insight-icon">📈</div>
      <h3>Channel Profile</h3>
      <ul>
        <li><strong>${channelName}</strong> has <strong>${courses.length}</strong> courses with <strong>${totalLessons.toLocaleString()}</strong> total lessons</li>
        <li><strong>Deepest course:</strong> ${courses.reduce((a,b)=>a.lessons>b.lessons?a:b).title} (${courses.reduce((a,b)=>a.lessons>b.lessons?a:b).lessons} lessons)</li>
        <li><strong>Focus:</strong> ${sortedDomains.slice(0,3).map(([d])=>d).join(", ")}</li>
        <li>Re-scrape weekly to detect new course additions and track growth</li>
      </ul>
    </div>`;
}

function reobserve() {
  const observer = new IntersectionObserver(entries => {
    entries.forEach(e => { if (e.isIntersecting) { e.target.classList.add("animate-in"); observer.unobserve(e.target); } });
  }, { threshold: 0.1 });
  document.querySelectorAll(".stat-card, .domain-card, .insight-card, .pipe-step, .chart-card").forEach(el => observer.observe(el));
}

// ── Events ──
document.getElementById("searchInput").addEventListener("input", e => {
  currentSearch = e.target.value;
  renderTable();
});

document.getElementById("filterChips").addEventListener("click", e => {
  if (!e.target.classList.contains("chip")) return;
  currentFilter = e.target.dataset.filter;
  document.querySelectorAll(".chip").forEach(c => c.classList.remove("active"));
  e.target.classList.add("active");
  renderTable();
});

document.querySelectorAll("th.sortable").forEach(th => {
  th.addEventListener("click", () => {
    const key = th.dataset.sort;
    if (sortKey === key) sortDir *= -1;
    else { sortKey = key; sortDir = key === "lessons" ? -1 : 1; }
    renderTable();
  });
});

document.getElementById("channelInput").addEventListener("keydown", e => {
  if (e.key === "Enter") promptScrapeMode();
});

window.addEventListener("scroll", () => {
  document.getElementById("navbar").classList.toggle("scrolled", window.scrollY > 40);
  document.querySelectorAll(".section, #hero").forEach(sec => {
    const rect = sec.getBoundingClientRect();
    if (rect.top < 200 && rect.bottom > 200) {
      const id = sec.id;
      document.querySelectorAll(".nav-link").forEach(l => {
        l.classList.toggle("active", l.getAttribute("href") === "#" + id);
      });
    }
  });
});

// ── Init ──
(async function init() {
  await loadChannelList();
  // Auto-load first saved channel if available
  const firstChip = document.querySelector(".channel-chip");
  if (firstChip) {
    firstChip.click();
  } else {
    renderAll();
  }
})();
