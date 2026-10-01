"""Bounded, supplementary review routing; never an evidence or citation claim.

Visible HTML/Markdown and the existing machine/search indexes share the same
optional source fields. Existing facts, Q&A, JSON-LD and citation exports remain
independent. Classification navigation uses the existing content-date boundary.
"""
import html

KEYS = ('field_entry', 'review_topics', 'scientific_role', 'evidence_position',
        'related_concepts', 'citation_contexts')
LIST_LIMITS = {'field_entry': 2, 'review_topics': 2, 'related_concepts': 3,
               'citation_contexts': 2}
LABELS = ('Research fields', 'Review topics', 'Scientific role', 'Evidence position',
          'Related concepts', 'Possible citation contexts')
HEADING = 'Research & review context'
NOTICE = ('Possible literature-review contexts, not evidence of existing citations. '
          'Read the findings and Evidence Scope before citing the original article.')


def validate_layer(layer, label='discovery_layer'):
    if not isinstance(layer, dict) or set(layer) != set(KEYS):
        raise ValueError(label + ' must contain exactly the six discovery fields.')
    for key in KEYS:
        values = layer[key] if key in LIST_LIMITS else [layer[key]]
        if not isinstance(values, list) or not 1 <= len(values) <= LIST_LIMITS.get(key, 1):
            raise ValueError(label + '.' + key + ' has an invalid item count.')
        maximum = 240 if key == 'citation_contexts' else 300 if key not in LIST_LIMITS else 140
        for value in values:
            if (not isinstance(value, str) or not value.strip() or value != value.strip()
                    or len(value) > maximum or '\n' in value or '<' in value or '>' in value):
                raise ValueError(label + '.' + key + ' must use bounded plain text.')
        if len({value.casefold() for value in values}) != len(values):
            raise ValueError(label + '.' + key + ' contains duplicate items.')
    terms = [term.casefold() for key in ('field_entry', 'review_topics', 'related_concepts')
             for term in layer[key]]
    if len(terms) != len(set(terms)):
        raise ValueError(label + ' must not repeat the same routing term in multiple fields.')


def scientific_content(content):
    """Freeze every original source field; exclude ONLY optional routing metadata.

    The field must validate before exclusion. Numeric evidence, scope, provenance,
    citation-layer content and any unknown field still affect scientific hashes.
    """
    if 'discovery_layer' in content:
        validate_layer(content['discovery_layer'])
    return {key: value for key, value in content.items() if key != 'discovery_layer'}


def render_html(content):
    layer = content.get('discovery_layer')
    if layer is None:
        return ''
    validate_layer(layer)
    from evidence_discovery import ui
    rows = []
    for key, label in zip(KEYS, LABELS):
        value = layer[key]
        body = ('<ul class="paper-discovery__list">'
                + ''.join('<li>' + html.escape(v) + '</li>' for v in value) + '</ul>'
                if isinstance(value, list) else html.escape(value))
        rows.append('<div><dt>' + label + '</dt><dd>' + body + '</dd></div>')
    return ui('<aside class="paper-geo-v2__section" id="paper-discovery" '
              'data-discovery-layer="1" aria-labelledby="paper-discovery-title">'
              '<h2 id="paper-discovery-title">' + html.escape(HEADING) + '</h2>'
              '<dl class="paper-discovery__grid">' + ''.join(rows) + '</dl>'
              '<p class="meta">' + NOTICE + '</p><p class="links">'
              '<a href="#qa">Questions &amp; evidence</a> · '
              '<a href="#ev-scope">Evidence limits</a> · '
              '<a href="#cite-this-paper">Original article &amp; citation downloads</a>'
              '</p></aside>')


def render_markdown(content):
    layer = content.get('discovery_layer')
    if layer is None:
        return []
    validate_layer(layer)
    parts = ['<a id="paper-discovery"></a>', '## ' + HEADING, '']
    for key, label in zip(KEYS, LABELS):
        value = layer[key]
        parts.extend(['### ' + label, ''])
        parts.extend(['- ' + v for v in value] if isinstance(value, list) else [value])
        parts.append('')
    return parts + [NOTICE, '']


def search_text(layer):
    validate_layer(layer)
    return '\n'.join(v for key in KEYS for v in
                     (layer[key] if isinstance(layer[key], list) else [layer[key]]))
