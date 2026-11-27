"""Shared production-only analytics markup for public HTML."""
GA4_MEASUREMENT_ID = "G-65LDZXWWQK"
LEGACY_GA4_TAG = (
    "<!-- Google tag (gtag.js) -->\n"
    f'<script async src="https://www.googletagmanager.com/gtag/js?id={GA4_MEASUREMENT_ID}"></script>\n'
    "<script>\n"
    "  window.dataLayer = window.dataLayer || [];\n"
    "  function gtag(){dataLayer.push(arguments);}\n"
    "  gtag('js', new Date());\n"
    f"  gtag('config', '{GA4_MEASUREMENT_ID}');\n"
    "</script>\n"
)
LEGACY_GA4_INSERTION = "\n" + LEGACY_GA4_TAG


def ga4_tag(*, research=False):
    config = f"    window.gtag('config', '{GA4_MEASUREMENT_ID}');\n"
    production_port = ""
    if research:
        production_port = " || window.location.port"
        # Retain referral domains without forwarding referrer path or query text.
        config = (
            "    var page = new URL(window.location.href);\n"
            "    var referrer = document.referrer ? new URL(document.referrer) : null;\n"
            f"    window.gtag('config', '{GA4_MEASUREMENT_ID}', {{\n"
            "      page_location: page.origin + page.pathname,\n"
            "      page_referrer: referrer && /^https?:$/.test(referrer.protocol) ? referrer.origin : ''\n"
            "    });\n"
        )
    return (
        "<!-- Google tag (gtag.js) -->\n"
        "<script>\n"
        "  (function () {\n"
        "    if (window.location.protocol !== 'https:' ||\n"
        "        !['drgezhang.com', 'www.drgezhang.com'].includes(window.location.hostname)"
        f"{production_port}) return;\n"
        "    window.dataLayer = window.dataLayer || [];\n"
        "    window.gtag = function(){window.dataLayer.push(arguments);};\n"
        "    window.gtag('js', new Date());\n"
        + config
        + "    var script = document.createElement('script');\n"
        "    script.async = true;\n"
        f"    script.src = 'https://www.googletagmanager.com/gtag/js?id={GA4_MEASUREMENT_ID}';\n"
        "    document.head.appendChild(script);\n"
        "  })();\n"
        "</script>\n"
    )


GA4_TAG = ga4_tag()
GA4_INSERTION = "\n" + GA4_TAG
RESEARCH_GA4_TAG = ga4_tag(research=True)
RESEARCH_HANDOFF_SCRIPT = '<script src="/assets/research-handoff.js" defer></script>'
RESEARCH_GA4_INSERTION = "\n" + RESEARCH_GA4_TAG + RESEARCH_HANDOFF_SCRIPT


def insert_ga4_tag(page):
    if page.count(GA4_INSERTION) + page.count(LEGACY_GA4_INSERTION) > 1:
        raise ValueError("Google tag must occur exactly once in the HTML head.")
    page = page.replace(LEGACY_GA4_INSERTION, GA4_INSERTION)
    if GA4_INSERTION in page:
        return page
    if page.count("<head>") != 1:
        raise ValueError("Google tag requires exactly one HTML head.")
    return page.replace("<head>", "<head>" + GA4_INSERTION, 1)


def with_research_measurement(page):
    if page.count("<head>") != 1 or page.count("</head>") != 1:
        raise ValueError("Research measurement requires exactly one HTML head.")
    if "googletagmanager.com/gtag/js" in page or RESEARCH_HANDOFF_SCRIPT in page:
        if (page.count(RESEARCH_GA4_INSERTION) == 1
                and page.count("googletagmanager.com/gtag/js") == 1
                and page.count(RESEARCH_HANDOFF_SCRIPT) == 1
                and RESEARCH_GA4_INSERTION in page.split("</head>", 1)[0].split("<head>", 1)[1]):
            return page
        raise ValueError("Unexpected existing research measurement markup.")
    return page.replace("</head>", RESEARCH_GA4_INSERTION + "</head>", 1)


def without_ga4_tag(page):
    """Ignore only exact shared analytics markup in content-date checks."""
    return (page.replace(GA4_INSERTION, "").replace(LEGACY_GA4_INSERTION, "")
            .replace(RESEARCH_GA4_INSERTION, ""))
