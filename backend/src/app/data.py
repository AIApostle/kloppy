"""Provider catalog metadata; connection state is read from Supabase."""

from copy import deepcopy

INTEGRATIONS = [
    {
        "id": "meta-ads",
        "name": "Meta Ads",
        "kind": "Application",
        "category": "Paid social",
        "description": "Read Meta Ads account and campaign context through an allowlisted MCP server.",
        "status": "Available",
        "connected": False,
    },
    {
        "id": "google-ads",
        "name": "Google Ads",
        "kind": "Application",
        "category": "Paid search",
        "description": "Read Google Ads account and campaign context through an allowlisted MCP server.",
        "status": "Available",
        "connected": False,
    },
    {
        "id": "hubspot",
        "name": "HubSpot",
        "kind": "Application",
        "category": "CRM",
        "description": "Read CRM records and lifecycle context through an allowlisted MCP server.",
        "status": "Available",
        "connected": False,
    },
    {
        "id": "mailchimp",
        "name": "Mailchimp",
        "kind": "Application",
        "category": "Email",
        "description": "Read email campaign and audience context through an allowlisted MCP server.",
        "status": "Available",
        "connected": False,
    },
    {
        "id": "canva",
        "name": "Canva",
        "kind": "Application",
        "category": "Design",
        "description": "Read connected design files and brand assets through an allowlisted MCP server.",
        "status": "Available",
        "connected": False,
    },
    {
        "id": "figma",
        "name": "Figma",
        "kind": "Resource",
        "category": "Design files",
        "description": "Read campaign boards and brand systems through an allowlisted MCP server.",
        "status": "Available",
        "connected": False,
    },
    {
        "id": "google-drive",
        "name": "Google Drive",
        "kind": "Resource",
        "category": "Knowledge",
        "description": "Read briefs, research, and campaign files through an allowlisted MCP server.",
        "status": "Available",
        "connected": False,
    },
    {
        "id": "notion",
        "name": "Notion",
        "kind": "Resource",
        "category": "Knowledge",
        "description": "Read launch notes and brand context through an allowlisted MCP server.",
        "status": "Available",
        "connected": False,
    },
    {
        "id": "ga4",
        "name": "Google Analytics",
        "kind": "Resource",
        "category": "Performance",
        "description": "Read analytics reports through an allowlisted MCP server.",
        "status": "Available",
        "connected": False,
    },
    {
        "id": "shopify",
        "name": "Shopify",
        "kind": "Application",
        "category": "Commerce",
        "description": "Read product and storefront context through an allowlisted MCP server.",
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
