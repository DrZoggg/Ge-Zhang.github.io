"""Presentation-only pilot. No scientific text, metadata or extraction dependencies."""
import html
import json
from html.parser import HTMLParser
from sync_common import ROOT

PILOT_DOIS = frozenset(('10.1021/acs.jproteome.4c00522', '10.1111/jcmm.17789',
                        '10.1186/s12915-025-02400-x'))
STYLESHEET = '<link rel="stylesheet" href="../assets/evidence-presentation.css">'


def enabled(doi):
    config = json.loads((ROOT/'data/evidence_presentation.json').read_text(encoding='utf-8'))
    if not set(config) <= PILOT_DOIS or any(v != 'scholarly-first-v1' for v in config.values()):
        raise ValueError('Unsupported presentation pilot scope/version')
    return doi.lower() in config


def question_summary(content, *, anchor=False):
    return ('<section class="paper-geo-v2__section" data-v2-section="research-question"><h2>Research Question</h2><p>'
            + html.escape(content['research_question']) + '</p></section>\n'
            + '<section class="paper-geo-v2__section" data-v2-section="author-summary"'
            + (' id="ev-summary"' if anchor else '') + '><h2>Author Evidence Summary</h2><p>'
            + html.escape(content['author_summary']) + '</p></section>\n')


def finding_sections(markup):
    """Change only finding wrapper tag tokens, after unchanged copy controls attach.

    Parse source offsets in the generated V2 fragment; never serialize or rewrite
    its content, attributes, scripts, Q&A articles, or the whole HTML document.
    """
    offsets=[0]
    for line in markup.splitlines(keepends=True): offsets.append(offsets[-1]+len(line))
    class Findings(HTMLParser):
        def __init__(self): super().__init__(convert_charrefs=False); self.stack=[]; self.edits=[]
        def position(self):
            line,col=self.getpos(); return offsets[line-1]+col
        def handle_starttag(self,tag,attrs):
            if tag=='article':
                finding='paper-geo-v2__finding' in dict(attrs).get('class','').split()
                self.stack.append(finding)
                if finding:self.edits.append((self.position()+1,7,'section'))
        def handle_endtag(self,tag):
            if tag=='article':
                if not self.stack:raise ValueError('Unbalanced generated article')
                if self.stack.pop():self.edits.append((self.position()+2,7,'section'))
    parser=Findings();parser.feed(markup)
    if parser.stack:raise ValueError('Unclosed generated article')
    for start,length,value in reversed(parser.edits):markup=markup[:start]+value+markup[start+length:]
    return markup
