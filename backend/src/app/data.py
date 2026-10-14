"""Demo data adapters used until persistence is connected."""

from copy import deepcopy

INTEGRATIONS = [
    {
        "id": "meta-ads",
        "name": "Meta Ads",
        "kind": "Application",
        "category": "Paid social",
        "description": "Draft audiences, ads, and spend plans for Instagram and Facebook.",
        "status": "Available",
        "connected": False,
    },
    {
        "id": "google-ads",
        "name": "Google Ads",
        "kind": "Application",
        "category": "Paid search",
        "description": "Prepare search and YouTube campaigns for review before launch.",
        "status": "Available",
        "connected": False,
    },
    {
        "id": "hubspot",
        "name": "HubSpot",
        "kind": "Application",
        "category": "CRM",
        "description": "Use contact lists and lifecycle context to shape campaign audiences.",
        "status": "Available",
        "connected": False,
    },
    {
        "id": "mailchimp",
        "name": "Mailchimp",
        "kind": "Application",
        "category": "Email",
        "description": "Create campaign drafts and send approved email journeys.",
        "status": "Available",
        "connected": False,
    },
    {
        "id": "canva",
        "name": "Canva",
        "kind": "Application",
        "category": "Design",
        "description": "Hand off approved briefs and retrieve ready-to-publish brand assets.",
        "status": "Available",
        "connected": False,
    },
    {
        "id": "figma",
        "name": "Figma",
        "kind": "Resource",
        "category": "Design files",
        "description": "Read campaign boards, brand systems, and feedback in one place.",
        "status": "Connected",
        "connected": True,
    },
    {
        "id": "google-drive",
        "name": "Google Drive",
        "kind": "Resource",
        "category": "Knowledge",
        "description": "Ground answers in briefs, research, catalogs, and past campaign files.",
        "status": "Connected",
        "connected": True,
    },
    {
        "id": "notion",
        "name": "Notion",
        "kind": "Resource",
        "category": "Knowledge",
        "description": "Bring launch notes, brand voice, and operating knowledge into context.",
        "status": "Available",
        "connected": False,
    },
    {
        "id": "ga4",
        "name": "Google Analytics",
        "kind": "Resource",
        "category": "Performance",
        "description": "Return traffic, conversion, and content signals to the campaign loop.",
        "status": "Available",
        "connected": False,
    },
    {
        "id": "shopify",
        "name": "Shopify",
        "kind": "Application",
        "category": "Commerce",
        "description": "Connect product, catalog, and storefront context for fashion launches.",
        "status": "Available",
        "connected": False,
    },
]

PROFILE = {
    "name": "Amara K.",
    "workspace": "Lagos launch Ame Studio",
    "digest_enabled": True,
}

CAMPAIGN = {
    "name": "Oyin Fab Studio · Lagos capsule",
    "status": "In progress",
    "updated": "12 min ago",
    "headline": "Good marketing starts with a better read.",
    "description": "Turn a Lagos fashion collection into a campaign your audience can feel — and your team can ship.",
    "insight": {
        "title": "Style is a social language.",
        "description": "The signal shows a strong affinity between Lagos design culture, independent music, and tools that make work feel personal.",
        "confidence": "Directional confidence",
    },
    "strategy": {
        "title": "Make work feel like yours.",
        "positioning": "Marketing clarity for people building their own way.",
        "pillar": "Your next best move, not another dashboard.",
        "channel": "Instagram · Creator partnerships",
    },
}

SEGMENTS = [
    {
        "name": "Culture-led early adopters",
        "note": "High affinity",
        "detail": "Lagos creatives who use style, music, and community as a signal of identity.",
        "signal": "Cultural signal",
        "color": "coral",
    },
    {
        "name": "Practical momentum buyers",
        "note": "Good fit",
        "detail": "Independent operators looking for a clearer way to turn attention into action.",
        "signal": "Product evidence",
        "color": "mint",
    },
    {
        "name": "Curious category switchers",
        "note": "Needs testing",
        "detail": "People exploring new tools who need proof before they change their routine.",
        "signal": "Market hypothesis",
        "color": "gold",
    },
]


def dashboard_payload() -> dict:
    """Return a copy so request handlers cannot mutate the source data."""
    return {
        "campaign": deepcopy(CAMPAIGN),
        "segments": deepcopy(SEGMENTS),
        "integration_count": sum(item["connected"] for item in INTEGRATIONS),
    }
