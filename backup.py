from pyquery import PyQuery as pq
import re
from session import session as s
from utils import stripQuery, jsondump, genHtml
from assignments import downloadAssignments
from materials import downloadMaterials
from lectures import downloadLectures
from tests import downloadTests
import os
import shutil
import json
import sys
import argparse


def trim(s):
    r = re.escape("!@#$%^&*()[]{};:,./<>?\|`~-=_+]")
    return re.sub(r"[" + r + "]", " ", s).strip()
def getSideMenu(url):
    data = s.get(url)
    doc = pq(data.text)
    host = stripQuery(url)
    return {trim(a.text()): host + a.attr("href") for el in list(doc(".ruRight table").items())[:-1] for a in el.find("a[href]").items()}

def getTitle(tr):
    title = tr.find("th").eq(1).text()
    title, subtitle = title.split("\xa0-\xa0")
    return title, subtitle
def getTeachers(c, host):
    b = c.find("b:contains(\"Kennarar\")")
    table = c.find("b:contains(\"Kennarar\") + table")

    c.remove("b:contains(\"Kennarar\") + p") # In case there were no teachers, remove the message
    c.remove("b:contains(\"Kennarar\") + table")
    c.remove("b:contains(\"Kennarar\")")

    if len(table) == 1:
        ret = []
        html = pq(table.outer_html())
        [a.attr("href", host + a.attr("href")) for a in html.find("a").items() if a.attr("href").startswith("?Page")]

        for row in table.find("tr").items():
            t = row.children("td").eq(0)
            teacher = {"name": t.find("a").eq(0).text(), "url": host + t.find("a").eq(0).attr("href"), "email": t.find("a").eq(1).text()}
            status = row.children("td").eq(1).text().strip()
            ret.append((teacher,status))
        return ret, html.outer_html()
    return None, None

def getAbout(url):
    data = s.get(url)
    doc = pq(data.content)

    table = doc(".ruContentPage>table")
    ret = {}
    ret2 = {}
    ret["title"], ret["subtitle"] = getTitle(table.find("tr").eq(0))
    main = table.find("tr").eq(1).find("td").eq(1)
    ret["teachers"], ret2["teachers"] = getTeachers(main, stripQuery(url))
    ret2["main"] = main.html().strip()
    return ret, ret2

def getContent(url):
    data = s.get(url)
    doc = pq(data.content)
    d = doc(".ruContentPage>center>table")
    if len(d) == 0:
        d = doc(".ruContentPage>table")
    return d.remove("style").outer_html()

def main(args):
    parser = argparse.ArgumentParser(description="A MySchool course downloader thing")
    parser.add_argument("url", help="The link to the course")
    parser.add_argument("-n", "--handin", action="store_true", default=False, help="Save handins")
    opts = parser.parse_args(args)

    print("Getting Menu")
    urls = getSideMenu(opts.url)

    print("Scraping descriptions of class")
    info, infohtml = getAbout(urls["Lýsing"])
    schedule, schedulehtml = getAbout(urls["Kennsluáætlun"])
    skills, skillhtml = getAbout(urls["Hæfniviðmið"])
    method, methodhtml = getAbout(urls["Kennsluaðferð"])
    grading, gradinghtml = getAbout(urls["Námsmat"])
    announcementhtml = getContent(urls["Tilkynningar"])
    bookhtml = getContent(urls["Bækur"])

    print("Creating directory structure")
    try:
        shutil.rmtree(info["title"])
    except:
        pass
    os.mkdir(info["title"])
    os.chdir(info["title"])

    print("Saving class description")
    jsondump("info.json", info)

    genHtml("info.html",
            infohtml["main"] + "<br />" +
            skillhtml["main"] + "<br />" +
            methodhtml["main"] + "<br />" +
            gradinghtml["main"],
            title=(info["subtitle"]))
    genHtml("schedule.html", schedulehtml["main"], title=(info["subtitle"]))
    genHtml("teachers.html", infohtml["teachers"], title=(info["subtitle"]))
    genHtml("announcements.html", announcementhtml, title=info["subtitle"])
    genHtml("books.html", bookhtml, title=info["subtitle"])

    print("Saving additional data")
    downloadAssignments(urls["Verkefni"], handin=opts.handin)
    downloadMaterials(urls["Annað efni"])
    downloadLectures(urls["Fyrirlestrar"])
    downloadTests(urls["Prófabanki"])

if __name__ == "__main__":
    main(sys.argv[1:])
