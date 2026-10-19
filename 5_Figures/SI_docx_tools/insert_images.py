"""Insert pictures as TRACKED insertions (a new centred paragraph holding an inline drawing, wrapped in w:ins) before the caption paragraph
named by each entry of images.json: [{"before_anchor": "...", "png": "...", "width_in": 6.3}, ...].
Usage: python insert_images.py <unpacked_dir> <images.json> [--author Claude] [--date 2026-10-04T12:00:00Z]"""
import sys, json, os, re, shutil
from lxml import etree
from PIL import Image
W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
WP = "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"
A = "http://schemas.openxmlformats.org/drawingml/2006/main"
PIC = "http://schemas.openxmlformats.org/drawingml/2006/picture"
PR = "http://schemas.openxmlformats.org/package/2006/relationships"
def qn(t): return "{%s}%s" % (W, t)
d = sys.argv[1]; images = json.load(open(sys.argv[2]))
author = sys.argv[sys.argv.index("--author") + 1] if "--author" in sys.argv else "Claude"
date = sys.argv[sys.argv.index("--date") + 1] if "--date" in sys.argv else "2026-10-04T12:00:00Z"
doc = f"{d}/word/document.xml"; rels_path = f"{d}/word/_rels/document.xml.rels"
tree = etree.parse(doc); root = tree.getroot(); body = root.find(qn("body"))
rels = etree.parse(rels_path); rroot = rels.getroot()
def norm(s): return re.sub(r"\s+", " ", s.replace(" ", " ")).strip()
def ptext(p):
    return norm("".join(el.text or "" for el in p.iter() if el.tag == qn("t") and not any(a.tag == qn("del") for a in el.iterancestors())))
ids = [int(x) for x in re.findall(r'w:id="(\d+)"', open(doc, encoding="utf8").read())]; next_id = max(ids + [1000]) + 1
rid_nums = [int(m) for m in re.findall(r'Id="rId(\d+)"', open(rels_path).read())]; next_rid = max(rid_nums) + 1
media = f"{d}/word/media"; existing = [int(m) for m in re.findall(r"image(\d+)\.", " ".join(os.listdir(media)))]; next_img = max(existing) + 1
docpr_ids = [int(x) for x in re.findall(r'<wp:docPr id="(\d+)"', open(doc, encoding="utf8").read())]; next_docpr = max(docpr_ids + [1]) + 1
for im in images:
    paras = [p for p in body.iter(qn("p"))]
    hits = [p for p in paras if norm(im["before_anchor"]) in ptext(p)]
    if len(hits) != 1: raise SystemExit(f"anchor matches {len(hits)} paragraphs: {im['before_anchor'][:60]}")
    cap = hits[0]
    # the image part
    name = f"image{next_img}.png"; next_img += 1; shutil.copy(im["png"], os.path.join(media, name))
    rid = f"rId{next_rid}"; next_rid += 1
    rel = etree.SubElement(rroot, "{%s}Relationship" % PR); rel.set("Id", rid); rel.set("Type", f"{R}/image"); rel.set("Target", f"media/{name}")
    w_px, h_px = Image.open(im["png"]).size; cx = int(im["width_in"] * 914400); cy = int(cx * h_px / w_px)
    dp = next_docpr; next_docpr += 1
    xml = f'''<w:p xmlns:w="{W}" xmlns:r="{R}" xmlns:wp="{WP}" xmlns:a="{A}" xmlns:pic="{PIC}">
<w:pPr><w:jc w:val="center"/><w:rPr><w:ins w:id="{next_id}" w:author="{author}" w:date="{date}"/></w:rPr></w:pPr>
<w:ins w:id="{next_id + 1}" w:author="{author}" w:date="{date}"><w:r><w:rPr><w:noProof/></w:rPr><w:drawing>
<wp:inline distT="0" distB="0" distL="0" distR="0"><wp:extent cx="{cx}" cy="{cy}"/><wp:effectExtent l="0" t="0" r="0" b="0"/>
<wp:docPr id="{dp}" name="Picture {dp}" descr="{os.path.basename(im['png'])}"/><wp:cNvGraphicFramePr><a:graphicFrameLocks noChangeAspect="1"/></wp:cNvGraphicFramePr>
<a:graphic><a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture"><pic:pic>
<pic:nvPicPr><pic:cNvPr id="{dp}" name="Picture {dp}"/><pic:cNvPicPr><a:picLocks noChangeAspect="1" noChangeArrowheads="1"/></pic:cNvPicPr></pic:nvPicPr>
<pic:blipFill><a:blip r:embed="{rid}"/><a:srcRect/><a:stretch><a:fillRect/></a:stretch></pic:blipFill>
<pic:spPr bwMode="auto"><a:xfrm><a:off x="0" y="0"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:noFill/></pic:spPr>
</pic:pic></a:graphicData></a:graphic></wp:inline></w:drawing></w:r></w:ins></w:p>'''
    next_id += 2
    newp = etree.fromstring(xml)
    cap.addprevious(newp)
    print("inserted", name, "before", im["before_anchor"][:50])
tree.write(doc, xml_declaration=True, encoding="UTF-8", standalone=True)
rels.write(rels_path, xml_declaration=True, encoding="UTF-8", standalone=True)
ct = f"{d}/[Content_Types].xml"; c = open(ct).read()
if 'Extension="png"' not in c: c = c.replace("</Types>", '<Default Extension="png" ContentType="image/png"/></Types>'); open(ct, "w").write(c)
print("done")
