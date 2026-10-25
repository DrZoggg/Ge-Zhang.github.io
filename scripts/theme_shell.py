"""Exact, reversible presentation additions shared by generated HTML pages.

Only these literal fragments are ignored for content-date comparisons. Unknown
scripts, altered controls, metadata and scientific text remain significant.
"""

THEME_INIT = '<script src="/assets/theme-init.js"></script>'
THEME_RUNTIME = '<script src="/assets/theme.js" defer></script>'
THEME_TOGGLE = (
    '<button class="theme-toggle" type="button" data-theme-toggle '
    'title="Switch to light theme" aria-label="Switch to light theme" hidden>'
    '<span data-theme-label>Light</span></button>'
)
GUIDE_THEME_HEADER = (
    '<header class="theme-guide-header"><nav aria-label="Display settings">'
    + THEME_TOGGLE + '</nav></header>'
)
GUIDE_THEME_STYLESHEET = (
    '<link rel="stylesheet" href="/assets/style.css" data-theme-shell="guide-style">'
)


def without_theme_shell(page):
    """Remove only known additions; never remove an arbitrary header or script."""
    # Remove the optional guide wrapper before its nested shared button.
    for fragment in (GUIDE_THEME_HEADER, GUIDE_THEME_STYLESHEET,
                     THEME_INIT, THEME_RUNTIME, THEME_TOGGLE):
        if page.count(fragment) > 1:
            raise ValueError('Duplicate theme shell fragment')
        page = page.replace(fragment, '')
    return page


def with_theme_shell(page, *, guide=False):
    original = without_theme_shell(page)
    if 'data-theme-toggle' in original or 'data-theme-shell=' in original:
        raise ValueError('Unrecognized theme shell: preserve and review before replacement')
    if original.count('<head>') != 1 or original.count('</head>') != 1:
        raise ValueError('Theme initialization requires exactly one HTML head')
    if guide:
        if '<header' in original or original.count('<body>') != 1:
            raise ValueError('Guide theme header requires its existing header-free body')
        result = original.replace('<body>', '<body>' + GUIDE_THEME_HEADER, 1)
        result = result.replace('</head>', GUIDE_THEME_STYLESHEET + '</head>', 1)
    else:
        if original.count('</nav></header>') != 1:
            raise ValueError('Theme control requires exactly one primary header navigation')
        result = original.replace('</nav></header>', THEME_TOGGLE + '</nav></header>', 1)
    # The blocking, tiny same-origin initializer precedes CSS and every other
    # script; the interaction script is deferred and has no graphics dependency.
    result = result.replace('<head>', '<head>' + THEME_INIT, 1)
    return result.replace('</head>', THEME_RUNTIME + '</head>', 1)
