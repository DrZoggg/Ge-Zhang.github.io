"""Small Pages gate: guide and topic identity, payloads, same-site links and KF anchors."""
import argparse
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urljoin, urlsplit
import xml.etree.ElementTree as ET
from research_guides import ROOT, COMPARISONS, load_comparisons, urls as guide_urls, require, validate_page
from scientific_intents import TOPIC_METADATA, topic_path


class Links(HTMLParser):
    def __init__(self):
        super().__init__(); self.links = []; self.ids = set()
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if 'id' in a: self.ids.add(a['id'])
        if tag in ('a','link') and a.get('href'): self.links.append(a['href'])


def check_staged_links(page, base, stage):
    parser = Links()
    parser.feed(page)
    count = 0
    for href in parser.links:
        url = urlsplit(urljoin(base, href))
        if url.netloc != 'drgezhang.com':
            continue
        count += 1
        target = (stage / (unquote(url.path).lstrip('/') or 'index.html')).resolve()
        require(target.is_relative_to(stage) and target.is_file(), 'Missing/unsafe staged research target: ' + href)
        if url.fragment:
            linked = Links()
            linked.feed(target.read_text(encoding='utf-8'))
            require(url.fragment in linked.ids, 'Missing staged research anchor: ' + href)
    return count


def validate_staged(stage, source=ROOT):
    stage = Path(stage).resolve()
    expected_inventory = {'questions.html','questions.json'}
    workspace_slugs = {data['slug'] for data in load_comparisons(source)
                       if isinstance(data.get('research_use'), dict)
                       and 'task_workspace' in data['research_use']}
    same_site_links = 0
    for guide_url in guide_urls(source):
        slug = Path(urlsplit(guide_url).path).stem
        extensions = ('html','md','json') if slug in COMPARISONS else ('html','md')
        if slug in workspace_slugs:
            extensions += ('worksheet.csv','blank.csv')
        for ext in extensions:
            name = 'research/'+slug+'.'+ext
            expected_inventory.add(slug+'.'+ext)
            require((stage/name).is_file(), 'Missing staged guide: '+name)
            require((source/name).is_file(), 'Missing generated guide source: '+name)
            require((stage/name).read_bytes()==(source/name).read_bytes(), 'Staged guide payload differs: '+name)
        page=(stage/'research'/(slug+'.html')).read_text(encoding='utf-8')
        validate_page(page, guide_url)
        same_site_links += check_staged_links(page, guide_url, stage)
    topic_files = [Path(topic_path(topic_id)) for topic_id in TOPIC_METADATA]
    topic_urls = ['https://drgezhang.com/' + path.as_posix() for path in topic_files]
    expected_inventory.add('topics')
    staged_topics = stage / 'research' / 'topics'
    require(staged_topics.is_dir(), 'Missing staged research topics directory')
    require({path.name for path in staged_topics.iterdir()} == {path.name for path in topic_files},
            'Unexpected staged research topic inventory')
    for path, url in zip(topic_files, topic_urls):
        require((stage/path).is_file() and (source/path).is_file(), 'Missing staged research topic: ' + path.as_posix())
        require((stage/path).read_bytes() == (source/path).read_bytes(), 'Staged research topic payload differs: ' + path.as_posix())
        same_site_links += check_staged_links((stage/path).read_text(encoding='utf-8'), url, stage)
    entries=ET.parse(stage/'sitemap.xml').getroot()
    urls=[n.text for n in entries.findall('{*}url/{*}loc')]
    require(all(urls.count(u)==1 for u in [*guide_urls(source), *topic_urls]),
            'Guide or topic must occur once in staged sitemap')
    for url in urls:
        u=urlsplit(url)
        target=stage/(u.path.lstrip('/') or 'index.html')
        require(target.is_file(), 'Sitemap URL has no staged file: '+url)
    require({p.name for p in (stage/'research').iterdir()}==expected_inventory, 'Unexpected staged research inventory')
    for name in ('questions.html','questions.json'):
        require((stage/'research'/name).read_bytes()==(source/'research'/name).read_bytes(), 'Staged question index differs: '+name)
    question_url = 'https://drgezhang.com/research/questions.html'
    same_site_links += check_staged_links((stage/'research/questions.html').read_text(encoding='utf-8'), question_url, stage)
    require(urls.count(question_url)==1, 'Question index must occur once in sitemap')
    return {'guides':len(guide_urls(source)), 'topics':len(topic_urls),
            'same_site_links_checked':same_site_links, 'sitemap_urls':len(urls)}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('stage',type=Path)
    print('STAGED GUIDE PASS:',validate_staged(p.parse_args().stage))
