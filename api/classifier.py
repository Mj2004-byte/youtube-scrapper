"""
Domain classification for educational courses.
Keyword-based classification into EdTech domains.
"""

DOMAINS = {
    "AI & Machine Learning": {
        "color": "#6366f1",
        "keywords": [
            "machine learning", "deep learning", "ai:", "ai ", "artificial intelligence",
            "nlp", "natural language", "reinforcement", "llm", "large language",
            "generative ai", "computer vision", "speech", "mlops", "neural network",
            "tensorflow", "pytorch", "transformer"
        ]
    },
    "Data Science": {
        "color": "#06b6d4",
        "keywords": [
            "data science", "statistics", "big data", "analytics", "data visualization",
            "statistical computing", "tools in data", "business data", "data analysis",
            "data mining", "data engineering", "pandas", "numpy"
        ]
    },
    "Programming": {
        "color": "#10b981",
        "keywords": [
            "python", "java", "javascript", "programming", "algorithms", "software engineering",
            "software testing", "system commands", "application development", "operating systems",
            "dsa", "data structures", "web development", "react", "node", "django", "flask",
            "c++", "rust", "golang", "typescript", "html", "css", "full stack", "frontend",
            "backend", "coding", "competitive programming"
        ]
    },
    "Mathematics": {
        "color": "#f59e0b",
        "keywords": [
            "math", "calculus", "mathematical thinking", "diploma mathematics",
            "linear algebra", "probability", "discrete math", "numerical methods",
            "optimization", "geometry"
        ]
    },
    "Business & Finance": {
        "color": "#f43f5e",
        "keywords": [
            "corporate finance", "managerial economics", "market research",
            "financial forensics", "game theory", "industry 4.0", "business analytics",
            "entrepreneurship", "management", "marketing", "accounting", "economics",
            "startup", "product management"
        ]
    },
    "Foundational": {
        "color": "#8b5cf6",
        "keywords": [
            "english", "computational thinking", "design thinking", "professional growth",
            "ct qualifier", "privacy and security", "communication", "soft skills",
            "interview", "career"
        ]
    },
    "Cloud & DevOps": {
        "color": "#ec4899",
        "keywords": [
            "cloud", "aws", "azure", "gcp", "docker", "kubernetes", "devops",
            "ci/cd", "terraform", "microservices", "serverless"
        ]
    },
    "Cybersecurity": {
        "color": "#14b8a6",
        "keywords": [
            "cybersecurity", "ethical hacking", "penetration testing", "network security",
            "cryptography", "information security", "cyber"
        ]
    }
}


def classify(title: str) -> str:
    """Classify a course title into a domain."""
    t = title.lower()
    for domain, cfg in DOMAINS.items():
        if any(k in t for k in cfg["keywords"]):
            return domain
    return "Other"


def get_domain_color(domain: str) -> str:
    """Get the color for a domain."""
    return DOMAINS.get(domain, {}).get("color", "#64748b")


def get_all_domains() -> dict:
    """Return all domain configurations."""
    return DOMAINS
