import requests
import xml.etree.ElementTree as ET

rss = "https://rss.blog.naver.com/allsix6.xml"

xml_text = requests.get(rss, timeout=10).text
root = ET.fromstring(xml_text)

items = root.find("channel").findall("item")[:10]
for it in items:
    print(it.findtext("title"))
    print(it.findtext("link"))
    print()
