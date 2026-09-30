"""Small Pages gate: guide identity, payloads, same-site links and KF anchors."""
import argparse
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urljoin, urlsplit
import xml.etree.ElementTree as ET
from research_guides import ROOT, SLUG, URL, require, validate_page


class Links(HTMLParser):
    def __init__(self):
        super().__init__(); self.links = []; self.ids = set()
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if 'id' in a: self.ids.add(a['id'])
        if tag in ('a','link') and a.get('href'): self.links.append(a['href'])


def validate_staged(stage, source=ROOT):
    stage = Path(stage).resolve()
    for ext in ('html','md'):
        name = 'research/'+SLUG+'.'+ext
        require((stage/name).is_file(), 'Missing staged guide: '+name)
        require((stage/name).read_bytes()==(source/name).read_bytes(), 'Staged guide payload differs: '+name)
    page=(stage/'research'/(SLUG+'.html')).read_text(encoding='utf-8')
    validate_page(page)
    parser=Links(); parser.feed(page)
    for href in parser.links:
        u=urlsplit(urljoin(URL,href))
        if u.netloc!='drgezhang.com': continue
        target=(stage/unquote(u.path).lstrip('/')).resolve()
        require(target.is_relative_to(stage), 'Unsafe staged link')
        require(target.is_file(), 'Missing staged guide link: '+href)
        if u.fragment:
            linked=Links(); linked.feed(target.read_text(encoding='utf-8'))
            require(u.fragment in linked.ids, 'Missing staged guide anchor: '+href)
    entries=ET.parse(stage/'sitemap.xml').getroot()
    urls=[n.text for n in entries.findall('{*}url/{*}loc')]
    require(urls.count(URL)==1, 'Guide must occur once in staged sitemap')
    for url in urls:
        u=urlsplit(url)
        target=stage/(u.path.lstrip('/') or 'index.html')
        require(target.is_file(), 'Sitemap URL has no staged file: '+url)
    require({p.name for p in (stage/'research').iterdir()}=={SLUG+'.html',SLUG+'.md','questions.html','questions.json'}, 'Unexpected staged research inventory')
    for name in ('questions.html','questions.json'):
        require((stage/'research'/name).read_bytes()==(source/'research'/name).read_bytes(), 'Staged question index differs: '+name)
    questions=Links();questions.feed((stage/'research/questions.html').read_text(encoding='utf-8'))
    for href in questions.links:
        u=urlsplit(urljoin('https://drgezhang.com/research/questions.html',href))
        if u.netloc!='drgezhang.com':continue
        target=(stage/unquote(u.path).lstrip('/')).resolve()
        require(target.is_relative_to(stage) and target.is_file(),'Missing/unsafe staged question target: '+href)
        if u.fragment:
            linked=Links();linked.feed(target.read_text(encoding='utf-8'))
            require(u.fragment in linked.ids,'Missing staged question anchor: '+href)
    require(urls.count('https://drgezhang.com/research/questions.html')==1,'Question index must occur once in sitemap')
    return {'guides':1,'same_site_links_checked':sum(urlsplit(urljoin(URL,h)).netloc=='drgezhang.com' for h in parser.links),'sitemap_urls':len(urls)}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('stage',type=Path)
    print('STAGED GUIDE PASS:',validate_staged(p.parse_args().stage))
