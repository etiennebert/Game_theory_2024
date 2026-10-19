"""Reject every tracked change carrying one date (default 2026-10-07T23:00:00Z) in an unpacked docx, writing a copy of the unpacked
folder: inserted runs, rows, paragraphs and pictures disappear, deleted runs come back, deleted paragraph marks are restored.
Used to check that the new pass changes nothing outside its own tracked changes:  reject the date, accept the rest  ==  accept all of
the previous version.   Usage: python reject_date.py <unpacked_in> <unpacked_out> [--date ...]"""
import sys, shutil, os
from lxml import etree
W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
def qn(t): return "{%s}%s" % (W, t)
src, dst = sys.argv[1], sys.argv[2]
date = sys.argv[sys.argv.index("--date") + 1] if "--date" in sys.argv else "2026-10-07T23:00:00Z"
if os.path.exists(dst): shutil.rmtree(dst)
shutil.copytree(src, dst)
path = f"{dst}/word/document.xml"; tree = etree.parse(path); root = tree.getroot()
n = {"ins": 0, "del": 0, "rows": 0, "paras": 0}
# rows inserted on the date
for tr in list(root.iter(qn("tr"))):
    trpr = tr.find(qn("trPr"))
    if trpr is not None and any(i.get(qn("date")) == date for i in trpr.findall(qn("ins"))): tr.getparent().remove(tr); n["rows"] += 1
# paragraphs whose mark was inserted on the date (new paragraphs): drop them whole
for p in list(root.iter(qn("p"))):
    ppr = p.find(qn("pPr")); rpr = ppr.find(qn("rPr")) if ppr is not None else None
    if rpr is not None and any(i.get(qn("date")) == date for i in rpr.findall(qn("ins"))): p.getparent().remove(p); n["paras"] += 1
# run-level insertions: remove; run-level deletions: unwrap and restore the text; markers in rPr: remove
for el in list(root.iter(qn("ins"))):
    if el.get(qn("date")) != date or el.getparent() is None: continue
    el.getparent().remove(el); n["ins"] += 1
for el in list(root.iter(qn("del"))):
    if el.get(qn("date")) != date or el.getparent() is None: continue
    par = el.getparent()
    if par.tag in (qn("rPr"), qn("trPr")): par.remove(el)
    else:
        for t in el.iter(qn("delText")): t.tag = qn("t")
        idx = par.index(el)
        for c in list(el): par.insert(idx, c); idx += 1
        par.remove(el)
    n["del"] += 1
tree.write(path, xml_declaration=True, encoding="UTF-8", standalone=True)
print("rejected", n)
