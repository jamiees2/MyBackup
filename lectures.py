from utils import stripQuery, save, saveRedirect, saveLink
from session import session as s
from pyquery import PyQuery as pq
import os

def getLectures(url):
    host = stripQuery(url)
    data = s.get(url)
    doc = pq(data.content)
    tableQ = ".ruContentPage > center > form > .ruTable"
    titles = [el.text() for el in doc(tableQ + " > .ruTableTitle").items() if el.text() != ""]
    tables = doc(tableQ + " .ruTable").items()
    items = []
    for table in tables:
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
        items.append(stuff)
    return dict(zip(titles,items))

def downloadLectures(url):
    lectures = getLectures(url)
    print("Processing Lectures")
    os.mkdir("lectures")
    for k, v in lectures.items():
        os.mkdir(os.path.join("lectures", k))
        for item in v:
            print("Processing %s/%s" % (k, item["Heiti"]))
            path = os.path.join("lectures", k, item["Heiti"])
            os.mkdir(path)
            for link, title in {"Glærur": "slides","3/síðu": "3_page","6/síðu": "6_page","Hljóðgl.": "video","Annað": "other"}.items():
                l = item[link]
                if not l or len(l) != 2: continue

                _, url = l
                if "?Page=Download" in url:
                    save(path, url)
                elif "Action=16" in url:
                    saveRedirect(os.path.join(path, title + ".html"), url)
                else:
                    saveLink(os.path.join(path, title + ".html"), url)

