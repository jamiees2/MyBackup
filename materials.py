from utils import stripQuery, save, saveRedirect
from session import session as s
from pyquery import PyQuery as pq
import os

def getMaterials(url):
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
                    d.append((item.find("a").text(), host + item.find("a").attr("href")))
                else:
                    d.append(item.text())
            stuff.append(dict(zip(title, d)))
        items.append(stuff)
    return dict(zip(titles,items))

def downloadMaterials(url):
    materials = getMaterials(url)
    print("Processing Materials")
    os.mkdir("materials")
    for k, v in materials.items():
        os.mkdir(os.path.join("materials", k))
        for item in v:
            print("Processing %s/%s" % (k, item["Heiti"][0]))
            path = os.path.join("materials", k, item["Heiti"][0])
            os.mkdir(path)
            url = item["Heiti"][1]

            if "?Page=Download" in url:
                save(path, url)
            elif "Action=16" in url:
                saveRedirect(os.path.join(path, "index.html"), url)

