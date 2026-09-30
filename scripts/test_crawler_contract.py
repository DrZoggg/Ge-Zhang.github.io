"""Static crawl contract; live UA probes and search indexing are separate audits."""
import json
import unittest
import xml.etree.ElementTree as ET
from urllib.robotparser import RobotFileParser
from sync_common import ROOT
from test_machine_interfaces import Document, local

def validate_crawlers():
    robots=RobotFileParser();robots.parse((ROOT/'robots.txt').read_text(encoding='utf-8').splitlines())
    sitemap=ET.parse(ROOT/'sitemap.xml').getroot()
    urls=[x.find('{*}loc').text for x in sitemap]
    for url in urls:
        path=ROOT/'index.html' if url=='https://drgezhang.com/' else local(url)
        text=path.read_text(encoding='utf-8');p=Document(text)
        assert [l['href'] for l in p.links if l.get('rel')=='canonical']==[url]
        assert not any('noindex' in m.lower() for m in p.meta.get('robots',[]))
        for ua in ['Googlebot','bingbot','OAI-SearchBot','GPTBot','ChatGPT-User','PerplexityBot','Claude-SearchBot']:
            assert robots.can_fetch(ua,url)
        assert any(l.get('rel')=='icon' and l.get('href')=='/assets/favicon.svg' for l in p.links)
    assert (ROOT/'assets/favicon.svg').is_file()
    return len(urls)
class CrawlerTests(unittest.TestCase):
    def test_static_eligibility(self):validate_crawlers()
if __name__=='__main__':unittest.main()
