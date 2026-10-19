"""Tracked formatting fix: text runs that inherited the 'CommentReference' character style from the 4 Oct diff (the tail of the
'Stability of the final coalition' paragraph rendered at 8 pt in the default font) get the paragraph's body formatting
(Times New Roman, 9 pt), with a w:rPrChange recording the old properties.  Usage: python fix_rpr.py <unpacked_dir> [--author] [--date]"""
import sys, re, copy
from lxml import etree
W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
def qn(t): return "{%s}%s" % (W, t)
args = sys.argv[1:]; d = args[0]
author = args[args.index("--author") + 1] if "--author" in args else "Claude"
date = args[args.index("--date") + 1] if "--date" in args else "2026-10-07T23:00:00Z"
path = f"{d}/word/document.xml"; tree = etree.parse(path); root = tree.getroot(); body = root.find(qn("body"))
ids = [int(x) for x in re.findall(r'w:id="(\d+)"', open(path, encoding="utf8").read())]; next_id = max(ids + [1000])
n = 0
for r in list(body.iter(qn("r"))):
    rpr = r.find(qn("rPr"))
    if rpr is None: continue
    rs = rpr.find(qn("rStyle"))
    if rs is None or rs.get(qn("val")) != "CommentReference" or r.find(qn("commentReference")) is not None: continue
    if not "".join(x.text or "" for x in r.iter(qn("t"), qn("delText"))).strip(): continue
    old = copy.deepcopy(rpr)
    for c in list(rpr): rpr.remove(c)
    f = etree.SubElement(rpr, qn("rFonts")); f.set(qn("ascii"), "Times New Roman"); f.set(qn("hAnsi"), "Times New Roman"); f.set(qn("cs"), "Times New Roman")
    for tag in ("i", "iCs"):
        if old.find(qn(tag)) is not None: etree.SubElement(rpr, qn(tag))
    sz = etree.SubElement(rpr, qn("sz")); sz.set(qn("val"), "18"); szcs = etree.SubElement(rpr, qn("szCs")); szcs.set(qn("val"), "18")
    va = old.find(qn("vertAlign"))
    if va is not None: rpr.append(copy.deepcopy(va))
    next_id += 1
    ch = etree.SubElement(rpr, qn("rPrChange")); ch.set(qn("id"), str(next_id)); ch.set(qn("author"), author); ch.set(qn("date"), date)
    for c in old.findall(qn("rPrChange")): old.remove(c)
    ch.append(old)
    n += 1
tree.write(path, xml_declaration=True, encoding="UTF-8", standalone=True)
print(f"formatting fixed in {n} runs")
