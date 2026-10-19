"""Accept the earlier revisions (20 Sept and 2 Oct 2026) inside the paragraphs that the 4 Oct edits rewrite or delete, so that the new
changes are plain <w:del>/<w:ins> and not nested inside earlier insertions. Usage: python accept_prior.py <unpacked_dir> <anchors.json> [from_anchor to_anchor ...]"""
import sys, json, re
from lxml import etree
W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
def qn(t): return "{%s}%s" % (W, t)
DATES = {"2026-09-20T22:00:00Z", "2026-10-02T19:30:00Z"}
d = sys.argv[1]; anchors = json.load(open(sys.argv[2])); ranges = list(zip(sys.argv[3::2], sys.argv[4::2]))
path = f"{d}/word/document.xml"
tree = etree.parse(path); root = tree.getroot()
def norm(s): return re.sub(r"\s+", " ", s.replace(" ", " ").replace("‑", "-").replace("‑", "-")).strip()
def ptext(p):
    out = []
    for el in p.iter():
        if el.tag == qn("t") and not any(a.tag == qn("del") for a in el.iterancestors()): out.append(el.text or "")
    return norm("".join(out))
body = root.find(qn("body"))
paras = [p for p in body.iter(qn("p"))]
def find(a):
    hits = [p for p in paras if norm(a) in ptext(p)]
    exact = [p for p in hits if ptext(p) == norm(a)]
    if len(hits) != 1 and len(exact) != 1: raise SystemExit(f"anchor matches {len(hits)} paragraphs: {a[:60]}")
    return exact[0] if len(exact) == 1 else hits[0]
targets = [find(a) for a in anchors]
for a, b in ranges:
    pa, pb = find(a), find(b); i, j = paras.index(pa), paras.index(pb); targets += paras[i:j + 1]
n_i = n_d = 0
for p in targets:
    for el in list(p.iter(qn("del"))):
        if el.get(qn("date")) in DATES and el.getparent() is not None: el.getparent().remove(el); n_d += 1
    for el in list(p.iter(qn("ins"))):
        if el.get(qn("date")) in DATES and el.getparent() is not None:
            par = el.getparent()
            if par.tag == qn("rPr"): par.remove(el)
            else:
                idx = par.index(el)
                for c in list(el): par.insert(idx, c); idx += 1
                par.remove(el)
            n_i += 1
tree.write(path, xml_declaration=True, encoding="UTF-8", standalone=True)
print(f"accepted earlier revisions in {len(targets)} paragraphs: {n_i} ins, {n_d} del")
