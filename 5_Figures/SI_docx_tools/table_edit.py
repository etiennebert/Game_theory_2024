"""Tracked edits inside an existing table of an unpacked .docx: insert rows (w:trPr/w:ins + inserted runs) and replace the text of
cells (w:del of the old runs, w:ins of the new text). The table is the first w:tbl after the paragraph that contains the anchor.
Usage: python table_edit.py <unpacked_dir> <edits.json> [--author Claude] [--date 2026-10-07T23:00:00Z]
edits.json: [{"table_after": "<caption anchor>",
              "insert_rows": [{"before_row_text": ["EU", "–", "0.1", "3,500 USD/ha"], "cells": ["EU", "–", ...]}, ...],   # matched on the first cells
              "set_cells": [{"row_text": ["EU alone · penalty 1.5%"], "col": 3, "text": "Japan"}, ...]}, ...]
A row is matched when its first len(row_text) cell texts equal row_text. Rows are inserted before the matched row (or appended when
before_row_text is null), copying the formatting of the row that follows (or of the last row)."""
import sys, json, re, copy
from lxml import etree
W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
def qn(t): return "{%s}%s" % (W, t)
args = sys.argv[1:]; d = args[0]; edits = json.load(open(args[1], encoding="utf8"))
author = args[args.index("--author") + 1] if "--author" in args else "Claude"
date = args[args.index("--date") + 1] if "--date" in args else "2026-10-07T23:00:00Z"
path = f"{d}/word/document.xml"
tree = etree.parse(path); root = tree.getroot(); body = root.find(qn("body"))
def norm(s): return re.sub(r"\s+", " ", s.replace(" ", " ")).strip()
def ptext(p): return norm("".join(t.text or "" for t in p.iter(qn("t")) if not any(a.tag == qn("del") for a in t.iterancestors())))
def celltext(tc): return norm("".join(t.text or "" for t in tc.iter(qn("t")) if not any(a.tag == qn("del") for a in t.iterancestors())))
ids = [int(x) for x in re.findall(r'w:id="(\d+)"', open(path, encoding="utf8").read())]; next_id = max(ids + [1000]) + 1
def nid():
    global next_id; next_id += 1; return str(next_id)
def find_table(anchor):
    hits = [p for p in body.iter(qn("p")) if norm(anchor) in ptext(p)]
    if len(hits) != 1: raise SystemExit(f"anchor matches {len(hits)} paragraphs: {anchor[:60]}")
    nxt = hits[0].getnext()
    while nxt is not None and nxt.tag != qn("tbl"): nxt = nxt.getnext()
    if nxt is None: raise SystemExit(f"no table after: {anchor[:60]}")
    return nxt
def rows_of(tbl): return [tr for tr in tbl if tr.tag == qn("tr")]
def match_row(tbl, key):
    hits = [tr for tr in rows_of(tbl) if [celltext(tc) for tc in tr.findall(qn("tc"))][:len(key)] == key]
    if len(hits) != 1: raise SystemExit(f"row key matches {len(hits)} rows: {key}")
    return hits[0]
def mark(el):  # a w:ins marker element
    m = etree.Element(qn("ins")); m.set(qn("id"), nid()); m.set(qn("author"), author); m.set(qn("date"), date); return m
def set_paragraph_text_inserted(p, text):
    """replace the content of a cell paragraph by one inserted run with the formatting of its first run"""
    rpr = None
    for r in p.iter(qn("r")):
        if r.find(qn("rPr")) is not None: rpr = copy.deepcopy(r.find(qn("rPr"))); break
    for child in list(p):
        if child.tag != qn("pPr"): p.remove(child)
    ppr = p.find(qn("pPr"))
    if ppr is None: ppr = etree.SubElement(p, qn("pPr")); p.insert(0, ppr)
    prpr = ppr.find(qn("rPr"))
    if prpr is None: prpr = etree.SubElement(ppr, qn("rPr"))
    for old in prpr.findall(qn("ins")) + prpr.findall(qn("del")): prpr.remove(old)
    prpr.insert(0, mark(None))
    ins = etree.SubElement(p, qn("ins")); ins.set(qn("id"), nid()); ins.set(qn("author"), author); ins.set(qn("date"), date)
    r = etree.SubElement(ins, qn("r"))
    if rpr is not None: r.append(rpr)
    t = etree.SubElement(r, qn("t")); t.text = text; t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
def insert_row(tbl, before_key, cells):
    rows = rows_of(tbl)
    ref = match_row(tbl, before_key) if before_key else rows[-1]
    template = ref if ref is not rows[0] else rows[1]
    tr = copy.deepcopy(template)
    trpr = tr.find(qn("trPr"))
    if trpr is None: trpr = etree.Element(qn("trPr")); tr.insert(0, trpr)
    for old in trpr.findall(qn("ins")) + trpr.findall(qn("del")): trpr.remove(old)
    trpr.append(mark(None))
    tcs = tr.findall(qn("tc"))
    if len(tcs) != len(cells): raise SystemExit(f"row has {len(tcs)} cells, {len(cells)} texts given")
    for tc, text in zip(tcs, cells):
        ps = tc.findall(qn("p"))
        for extra in ps[1:]: tc.remove(extra)
        set_paragraph_text_inserted(ps[0], text)
    if before_key: ref.addprevious(tr)
    else: tbl.append(tr)
def set_cell(tbl, row_key, col, text):
    tr = match_row(tbl, row_key); tc = tr.findall(qn("tc"))[col]; p = tc.findall(qn("p"))[0]
    rpr = None
    runs = [r for r in p if r.tag == qn("r")]
    if runs and runs[0].find(qn("rPr")) is not None: rpr = copy.deepcopy(runs[0].find(qn("rPr")))
    if runs:
        dele = etree.Element(qn("del")); dele.set(qn("id"), nid()); dele.set(qn("author"), author); dele.set(qn("date"), date)
        runs[0].addprevious(dele)
        for r in runs:
            for t in r.findall(qn("t")): t.tag = qn("delText")
            dele.append(r)
    ins = etree.SubElement(p, qn("ins")); ins.set(qn("id"), nid()); ins.set(qn("author"), author); ins.set(qn("date"), date)
    r = etree.SubElement(ins, qn("r"))
    if rpr is not None: r.append(rpr)
    t = etree.SubElement(r, qn("t")); t.text = text; t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
n_rows = n_cells = 0
for e in edits:
    tbl = find_table(e["table_after"])
    for ins in e.get("insert_rows", []): insert_row(tbl, ins.get("before_row_text"), ins["cells"]); n_rows += 1
    for sc in e.get("set_cells", []): set_cell(tbl, sc["row_text"], sc["col"], sc["text"]); n_cells += 1
tree.write(path, xml_declaration=True, encoding="UTF-8", standalone=True)
print(f"tables: {n_rows} rows inserted, {n_cells} cells replaced (ids up to {next_id})")
