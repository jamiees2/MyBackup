from pyquery import PyQuery as pq
import requests
import os

from session import session as s

from utils import save, stripQuery, jsondump

def getAssignment(url):
    data = s.get(url)
    doc = pq(data.content)
    tables = doc(".ruContentPage>center>form>table")
    host = stripQuery(url)
    ret = {}
    ret["description"] = getAssignmentDescription(tables.eq(0), host)
    if len(tables) >= 3:
        ret["grade"] = getAssignmentGrade(tables.eq(1), host)
        ret["handin"] = getAssignmentHandin(tables.eq(2), host)
        ret["statistics"] = getAssignmentStatistics(doc(".ruContentPage>table"), host)

    return ret
def getAssignmentHandin(table, host):

    rows = list(table.children("tr").items())
    ret = {}
    ret["comment"] = rows[-2].children("td").eq(2).html().replace("<br/>","\n").strip()
    ret["files"] = []
    files = rows[-1].children("td").eq(2)
    if len(files.children()) == 1 and len(files.find("table")) == 1:
        ret["files"] = readFileTable(files.find("table"), host)
    return ret

def getAssignmentGrade(table, host):
    items = ["grade", "ranking", "comments"]
    grade = {}
    for id, i in zip(items,[1,2,3]):
        grade[id] = table.children("tr").eq(i).children("td").eq(2).html().replace("<br/>","\n").strip()
    grade["files"] = []
    files = table.children("tr").eq(4).children("td").eq(2)
    if len(files.children()) == 1 and len(files.find("table")) == 1:
        grade["files"] = readFileTable(files.find("table"), host)
    return grade

def getAssignmentDescription(desctable, host):
    # The assignment description
    desc = {}
    items = ["due", "description", "percent", "filetype", "filenumber"]
    for id, i in zip(items,[1,2,4,5,6]):
        desc[id] = ":".join(desctable.children("tr").eq(i).text().split(":")[1:]).strip()
    desc["title"] = desctable.find("tr").eq(0).text()

    # Files
    desc["files"] = []
    files = desctable.children("tr").eq(3).children("td").eq(2)
    if len(files.children()) == 1 and len(files.find("table")) == 1:
        desc["files"] = readFileTable(files.find("table"), host)

    return desc

def readFileTable(table, host):
    files = []
    for item in list(table.find("tr").items())[1:]:
        files.append({
            "filename": item.find("td").eq(1).text(),
            "url": host + item.find("td").eq(1).find("a").attr("href"),
            "size": item.find("td").eq(2).text(),
            "date": item.find("td").eq(3).text()
        })
    return files

def getAssignmentStatistics(table, host):
    ret = {}
    ret["image"] = host + table.children("tr").eq(0).find("img").attr("src")

    stats = table.children("tr").eq(1).find("table tr").not_(".ruTableTitle").children("td").items()
    stats = list(stats)
    ret["average"] = stats[1].text()
    ret["middle"] = stats[4].text()
    ret["standarddev"] = stats[6].text()
    ret["mostcommon"] = stats[9].text()
    ret["handins"] = stats[11].text()
    return ret

def getAssignments(url):
    host = stripQuery(url)
    data = s.get(url)
    doc = pq(data.content)
    tableQ = ".ruContentPage > center > .ruTable"
    titles = [el.text() for el in doc(tableQ + " > .ruTableTitle").items() if el.text() != ""]
    tables = doc(tableQ + " .ruTable").items()
    assignments = []
    for table in tables:
        title = [el.text() for el in table.find("tr.ruTableTitle th").items()]
        assign = []
        for el in table.find("tr").not_(".ruTableTitle").items():
            if el.text().strip() == "": continue
            d = []
            for item in el.find("td").items():
                if len(item.children()) == 0:
                    d.append(item.text())
                else:
                    # Assert that this is a link if it has children
                    assert len(item.children()) == 1 and len(item.find("a")) == 1
                    d.append((item.find("a").text(), host + item.find("a").attr("href")))
            assign.append(dict(zip(title, d)))

        assignments.append(assign)
    return dict(zip(titles,assignments))

def downloadAssignments(url, handin=False):
    assignments = getAssignments(url)
    os.mkdir("assignments")
    for k, v in assignments.items():
        os.mkdir(os.path.join("assignments", k))
        for item in v:
            print("Processing %s/%s" % (k, item["Nafn"][0]))
            path = os.path.join("assignments", k, item["Nafn"][0])
            os.mkdir(path)
            assignment = getAssignment(item["Nafn"][1])

            # Description
            descr = os.path.join(path, "description")
            os.mkdir(descr)
            jsondump(os.path.join(descr,"description.json"), assignment["description"])
            for item in assignment["description"]["files"]:
                save(descr, item["url"])

            if handin:
                if "grade" in assignment:
                    grade = os.path.join(path, "grade")
                    os.mkdir(grade)
                    jsondump(os.path.join(grade, "grade.json"), assignment["grade"])
                    for item in assignment["grade"]["files"]:
                        save(grade, item["url"])

                if "handin" in assignment:
                    handin = os.path.join(path, "handin")
                    os.mkdir(handin)
                    jsondump(os.path.join(handin, "handin.json"), assignment["handin"])

                if "statistics" in assignment:
                    jsondump(os.path.join(path,"stats.json"), assignment["statistics"])
                    save(os.path.join(path, "stats.jpg"), assignment["statistics"]["image"])
