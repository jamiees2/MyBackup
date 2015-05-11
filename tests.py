from utils import stripQuery, save, saveRedirect, saveLink
from session import session as s
from pyquery import PyQuery as pq
import os

def getTests(url):
    host = stripQuery(url)
    data = s.get(url)
    doc = pq(data.content)
    table = doc(".ruContentPage > center > .ruTable")
    title = [el.text() for el in table.find("tr.ruTableTitle th").items()]
    stuff = []
    for el in table.find("tr").not_(".ruTableTitle").items():
        if el.text().strip() == "": continue
        d = []
        for item in el.find("td").items():
            if len(item.children()) == 0:
                d.append(item.text())
            elif len(item.children()) == 1 and len(item.find("a[href]")) == 1:
                url = item.find("a").attr("href")
                if url.startswith("?"): url = host + url
                d.append((item.find("a").text(), url))
            else:
                d.append(item.text())
        stuff.append(dict(zip(title, d)))
    return stuff

def downloadTests(url):
    tests = getTests(url)
    print("Processing Tests")
    os.mkdir("tests")
    for v in tests:
        print("Saving %s" % v["Próf"][0])
        save("tests", v["Próf"][1])
