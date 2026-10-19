#!/usr/bin/env python3
"""redline.py - apply TRACKED CHANGES (Word redlining: w:ins / w:del) to an
unpacked .docx directory, editing word/document.xml in place.

CLI
---
    python redline.py <unpacked_dir> <edits.json> [--author "Claude"] [--date 2026-09-20T00:00:00Z]
                      [--split-field-runs]
    python redline.py --list <unpacked_dir>          # paragraph index / style / first 90 chars

--split-field-runs additionally gives every field character (w:fldChar / w:instrText) its own run.
merge_runs.py merges them into text runs, which Word accepts but which makes LibreOffice leak list
numbering to all following paragraphs when such a run sits in a list paragraph. Content is unchanged.

Module
------
    from redline import Redliner
    rl = Redliner(unpacked_dir, author="Claude", date="2026-09-20T00:00:00Z")
    rl.apply(ops)      # ops = list of dicts (see below); atomic: nothing is written on error
    rl.save()          # writes word/document.xml (never pretty-printed)

edits.json is either a JSON list of operations, or {"ops": [...]}.
Every operation names its target paragraph with an *anchor*: a distinctive
substring of the paragraph's plain text (whitespace, NBSP, curly quotes,
non-breaking hyphens and zero-width characters are normalised on both sides).
The anchor must match exactly ONE paragraph, otherwise the run fails loudly.
Operations are applied in order; anchors are resolved against the document as
modified by the previous operations (deleted text no longer matches, inserted
text does).

Operations (JSON)
-----------------
  {"op":"replace", "anchor":"...", "new":"<markup>", "mode":"diff"|"replace"}
      mode "diff" (default): word-level diff; unchanged words keep their
      original runs/formatting (citation fields, italics, superscripts...),
      deleted words go into <w:del>, inserted words into <w:ins> with the
      paragraph's base formatting plus the markup.
      mode "replace": every existing run is deleted and the new text inserted.
  {"op":"insert_after"|"insert_before", "anchor":"...",
   "paragraphs":[{"text":"<markup>", "style":"body"|"subheading"|"heading"|"caption"|"copy"}, ...]}
  {"op":"delete", "anchor":"...", "preceding_figures":N}   # N = also delete the N figure-only paragraphs before it
  {"op":"delete_figures_before", "anchor":"...", "count":N}   # only the N figure-only paragraphs before the anchor (caption kept)
  {"op":"delete_range", "from_anchor":"...", "to_anchor":"..."}     (inclusive; tables in between are deleted too)
  {"op":"insert_equation_after", "anchor":"...", "latex":"...", "number":"(5)"}
  {"op":"delete_table", "anchor":"..."}                (the table immediately following the anchor paragraph)
  {"op":"delete_table_containing", "anchor":"..."}     (the table whose cell text contains the anchor)
  {"op":"insert_table_after", "anchor":"...", "markdown":"| a | b |\\n|---|---|\\n| 1 | 2 |", "style":"TableGrid"}
  {"op":"comment", "anchor":"...", "text":"..."}

Markup for new text:  *italic*  **bold**  ^superscript^  ~subscript~  $$latex$$ (inline OMML)
Backslash escapes a marker character: \\* \\^ \\~ \\$ .  ^ and ~ spans may not contain
whitespace; * and ** spans may not start or end with whitespace.

Anchors: if several paragraphs contain the anchor but exactly one paragraph IS the anchor
(e.g. the heading "Methods"), that paragraph is taken. Paragraphs inside text boxes are
not searched (and cannot be edited).

Limitations
-----------
* Citation fields (Zotero, SEQ...) survive a diff when the word that carries them keeps
  its citation digits; removing a citation deletes the whole field (tracked); a citation
  added with ^n^ is plain superscript text, not a live field.
* Equations are tracked by wrapping m:oMathPara / m:oMath in w:ins / w:del (the schema-
  valid form). Word's own native form is a revision mark inside each math run; verify once
  in Word. pandoc ignores math inside w:ins/w:del, and a LibreOffice without its Math
  component renders no equations at all.
* Table insertion/deletion is tracked per row (w:trPr/w:ins|w:del); pandoc does not apply
  row-level tracking (LibreOffice and Word do).
* A fully deleted paragraph also gets its paragraph mark deleted, except the last paragraph
  of a table cell / of the body. LibreOffice keeps an empty paragraph when the deleted
  paragraph precedes a table; Word removes it.
* Comments are not tracked changes; comment.py dates them "now".
"""
from __future__ import annotations

import argparse
import copy
import datetime as _dt
import difflib
import json
import os
import re
import subprocess
import sys
import tempfile
import unicodedata
import zipfile
from pathlib import Path

from lxml import etree

__all__ = ["Redliner", "RedlineError", "parse_markup"]

# --------------------------------------------------------------------------- namespaces
W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
M = "http://schemas.openxmlformats.org/officeDocument/2006/math"
R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
W14 = "http://schemas.microsoft.com/office/word/2010/wordml"
XML_NS = "http://www.w3.org/XML/1998/namespace"
NSMAP = {"w": W, "m": M, "r": R, "w14": W14}


def qn(tag: str) -> str:
    prefix, local = tag.split(":")
    return "{%s}%s" % (NSMAP[prefix], local)


XML_SPACE = "{%s}space" % XML_NS
W_P, W_R, W_T, W_PPR, W_RPR = qn("w:p"), qn("w:r"), qn("w:t"), qn("w:pPr"), qn("w:rPr")
W_INS, W_DEL, W_DELTEXT = qn("w:ins"), qn("w:del"), qn("w:delText")
W_INSTRTEXT, W_DELINSTRTEXT, W_FLDCHAR = qn("w:instrText"), qn("w:delInstrText"), qn("w:fldChar")
W_TBL, W_TR, W_TC, W_TRPR, W_TCPR, W_TBLPR = (qn("w:tbl"), qn("w:tr"), qn("w:tc"), qn("w:trPr"),
                                              qn("w:tcPr"), qn("w:tblPr"))
W_BODY, W_SECTPR, W_PSTYLE = qn("w:body"), qn("w:sectPr"), qn("w:pStyle")
W_ID, W_AUTHOR, W_DATE, W_VAL = qn("w:id"), qn("w:author"), qn("w:date"), qn("w:val")
M_OMATH, M_OMATHPARA, M_R, M_T, M_RPR = qn("m:oMath"), qn("m:oMathPara"), qn("m:r"), qn("m:t"), qn("m:rPr")

# paragraph children that are transparent wrappers around runs
CONTAINER_TAGS = {qn("w:hyperlink"), qn("w:ins"), qn("w:moveTo"), qn("w:smartTag"), qn("w:customXml"),
                  qn("w:dir"), qn("w:bdo")}
# paragraph children kept verbatim, never placed inside a <w:del>
PROTECTED_TAGS = {qn("w:bookmarkStart"), qn("w:bookmarkEnd"), qn("w:commentRangeStart"), qn("w:commentRangeEnd"),
                  qn("w:permStart"), qn("w:permEnd"), qn("w:del"), qn("w:moveFrom"),
                  qn("w:moveFromRangeStart"), qn("w:moveFromRangeEnd"), qn("w:moveToRangeStart"),
                  qn("w:moveToRangeEnd"), qn("w:customXmlInsRangeStart"), qn("w:customXmlInsRangeEnd"),
                  qn("w:customXmlDelRangeStart"), qn("w:customXmlDelRangeEnd")}
# paragraph children treated as one atomic token whose text is their visible text
ATOMIC_TAGS = {M_OMATH, M_OMATHPARA, qn("w:sdt"), qn("w:fldSimple")}
DROP_TAGS = {qn("w:proofErr")}
SKIP_SIBLINGS = PROTECTED_TAGS | DROP_TAGS
# run children that render as one character
_RUN_CHAR_TAGS = {qn("w:tab"): "\t", qn("w:ptab"): "\t", qn("w:br"): "\n", qn("w:cr"): "\n",
                  qn("w:noBreakHyphen"): "‑", qn("w:softHyphen"): "­", qn("w:sym"): "￼"}

RPR_ORDER = ["rStyle", "rFonts", "b", "bCs", "i", "iCs", "caps", "smallCaps", "strike", "dstrike", "outline",
             "shadow", "emboss", "imprint", "noProof", "snapToGrid", "vanish", "webHidden", "color", "spacing",
             "w", "kern", "position", "sz", "szCs", "highlight", "u", "effect", "bdr", "shd", "fitText",
             "vertAlign", "rtl", "cs", "em", "lang", "eastAsianLayout", "specVanish", "oMath"]
PPR_ORDER = ["pStyle", "keepNext", "keepLines", "pageBreakBefore", "framePr", "widowControl", "numPr",
             "suppressLineNumbers", "pBdr", "shd", "tabs", "suppressAutoHyphens", "kinsoku", "wordWrap",
             "overflowPunct", "topLinePunct", "autoSpaceDE", "autoSpaceDN", "bidi", "adjustRightInd",
             "snapToGrid", "spacing", "ind", "contextualSpacing", "mirrorIndents", "suppressOverlap", "jc",
             "textDirection", "textAlignment", "textboxTightWrap", "outlineLvl", "divId", "cnfStyle", "rPr",
             "sectPr", "pPrChange"]

DEFAULT_SCRIPTS_DIR = Path(os.environ.get("REDLINE_DOCX_SCRIPTS", "/mnt/skills/public/docx/scripts"))

# schema order of the children of OMML property elements (pandoc emits some of them out of order)
OMML_PR_ORDER = {
    "accPr": ["chr", "ctrlPr"], "barPr": ["pos", "ctrlPr"],
    "boxPr": ["opEmu", "noBreak", "diff", "brk", "aln", "ctrlPr"],
    "borderBoxPr": ["hideTop", "hideBot", "hideLeft", "hideRight", "strikeH", "strikeV", "strikeBLTR",
                    "strikeTLBR", "ctrlPr"],
    "dPr": ["begChr", "sepChr", "endChr", "grow", "shp", "ctrlPr"],
    "eqArrPr": ["baseJc", "maxDist", "objDist", "rSpRule", "rSp", "ctrlPr"],
    "fPr": ["type", "ctrlPr"], "funcPr": ["ctrlPr"], "groupChrPr": ["chr", "pos", "vertJc", "ctrlPr"],
    "limLowPr": ["ctrlPr"], "limUppPr": ["ctrlPr"], "mcPr": ["count", "mcJc"],
    "mPr": ["baseJc", "plcHide", "rSpRule", "cGpRule", "rSp", "cSp", "cGp", "mcs", "ctrlPr"],
    "naryPr": ["chr", "limLoc", "grow", "subHide", "supHide", "ctrlPr"],
    "phantPr": ["show", "zeroWid", "zeroAsc", "zeroDesc", "transp", "ctrlPr"],
    "radPr": ["degHide", "ctrlPr"], "sPrePr": ["ctrlPr"], "sSubPr": ["ctrlPr"],
    "sSubSupPr": ["alnScr", "ctrlPr"], "sSupPr": ["ctrlPr"], "argPr": ["argSz"], "oMathParaPr": ["jc"],
    "rPr": ["lit", "nor", "scr", "sty", "brk", "aln"],
}


def fix_omml_order(el: etree._Element) -> None:
    """Re-order children of OMML property elements to the schema sequence."""
    for node in el.iter():
        if not isinstance(node.tag, str) or not node.tag.startswith("{" + M + "}"):
            continue
        order = OMML_PR_ORDER.get(_local(node.tag))
        if order is None or len(node) < 2:
            continue
        children = list(node)
        children.sort(key=lambda c: _order_index(order, _local(c.tag)))
        for c in children:
            node.remove(c)
        node.extend(children)

ZERO_WIDTH = "​‌‍﻿­⁠"
_TRANS = str.maketrans({
    "’": "'", "‘": "'", "“": '"', "”": '"', "‐": "-", "‑": "-",
    " ": " ", " ": " ", " ": " ", " ": " ", " ": " ", " ": " ",
    " ": " ", " ": " ", " ": " ", " ": " ", " ": " ", "　": " ",
})


class RedlineError(Exception):
    """Raised when an operation cannot be applied; nothing is written."""


# --------------------------------------------------------------------------- small helpers
def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def norm_key(s: str) -> str:
    """Normalisation used to compare words / anchors (never used for output)."""
    s = unicodedata.normalize("NFC", s).translate(_TRANS)
    return "".join(ch for ch in s if ch not in ZERO_WIDTH)


def norm_text(s: str) -> str:
    return re.sub(r"\s+", " ", norm_key(s)).strip()


def rendered(t: etree._Element) -> str:
    """Text of a w:t as Word draws it (edge whitespace trimmed unless preserved)."""
    text = t.text or ""
    if t.get(XML_SPACE) == "preserve":
        return text
    return text.strip(" \t\r\n")


def E(tag: str, attrib: dict | None = None, text: str | None = None) -> etree._Element:
    el = etree.Element(qn(tag) if not tag.startswith("{") else tag)
    if attrib:
        for k, v in attrib.items():
            el.set(qn(k) if ":" in k and not k.startswith("{") else k, str(v))
    if text is not None:
        el.text = text
    return el


def set_text(t: etree._Element, text: str) -> None:
    t.text = text
    if text and (text[0] in " \t\r\n" or text[-1] in " \t\r\n"):
        t.set(XML_SPACE, "preserve")
    elif XML_SPACE in t.attrib:
        del t.attrib[XML_SPACE]


def _order_index(order: list, local: str) -> int:
    try:
        return order.index(local)
    except ValueError:
        return len(order)


def set_ordered_child(parent: etree._Element, order: list, child: etree._Element, replace: bool = True):
    """Insert child into parent at the schema-ordered position (replacing same-named children)."""
    local = _local(child.tag)
    if replace:
        for old in parent.findall(child.tag):
            parent.remove(old)
    idx = _order_index(order, local)
    for i, existing in enumerate(parent):
        if _order_index(order, _local(existing.tag)) > idx:
            parent.insert(i, child)
            return child
    parent.append(child)
    return child


def clean_rpr(rpr: etree._Element | None) -> etree._Element | None:
    """Drop tracked-change bookkeeping from a copied rPr."""
    if rpr is None:
        return None
    for child in list(rpr):
        if _local(child.tag) in ("ins", "del", "moveFrom", "moveTo", "rPrChange"):
            rpr.remove(child)
    return rpr


def strip_ids(elem: etree._Element) -> etree._Element:
    """Remove w14:paraId/textId and rsid* attributes from a copied subtree."""
    for el in elem.iter():
        for attr in list(el.attrib):
            local = _local(attr)
            if local in ("paraId", "textId") or "rsid" in local.lower():
                del el.attrib[attr]
    return elem


def has_vert_align(rpr: etree._Element | None) -> bool:
    if rpr is None:
        return False
    va = rpr.find(qn("w:vertAlign"))
    return va is not None and va.get(W_VAL) in ("superscript", "subscript")


# --------------------------------------------------------------------------- markup
_MARKERS = (("**", "b"), ("*", "i"), ("^", "sup"), ("~", "sub"))


def parse_markup(text: str) -> list:
    """Parse the minimal markup into [(text, frozenset(styles))] and ("math", latex) items."""
    segs: list = []
    state: set = set()
    buf: list = []
    n = len(text)
    i = 0

    def flush():
        if buf:
            segs.append(("".join(buf), frozenset(state)))
            buf.clear()

    def valid_span(marker: str, start: int) -> bool:
        j = text.find(marker, start)
        while j != -1 and j > 0 and text[j - 1] == "\\":
            j = text.find(marker, j + len(marker))
        if j == -1:
            return False
        inner = text[start:j]
        if not inner or inner[0].isspace() or inner[-1].isspace():
            return False
        if marker in ("^", "~") and any(ch.isspace() for ch in inner):
            return False
        return True

    while i < n:
        ch = text[i]
        if ch == "\\" and i + 1 < n and text[i + 1] in "*^~$\\":
            buf.append(text[i + 1])
            i += 2
            continue
        if text.startswith("$$", i):
            j = text.find("$$", i + 2)
            if j > i + 2 and text[i + 2:j].strip():
                flush()
                segs.append(("math", text[i + 2:j].strip()))
                i = j + 2
                continue
        matched = False
        for marker, style in _MARKERS:
            if not text.startswith(marker, i):
                continue
            if marker == "*" and "b" in state and text.startswith("**", i):
                continue  # handled by the ** branch (state has b)
            if style in state:
                flush()
                state.discard(style)
                i += len(marker)
                matched = True
                break
            if valid_span(marker, i + len(marker)):
                flush()
                state.add(style)
                i += len(marker)
                matched = True
                break
            # not a valid span: literal
            if marker == "**":
                continue  # let the single-* branch decide
            break
        if matched:
            continue
        buf.append(ch)
        i += 1
    flush()
    return segs


# --------------------------------------------------------------------------- atoms
class Atom:
    """One unit of paragraph content: a visible character, an opaque element or a compound (field)."""
    __slots__ = ("kind", "text", "src", "run", "chain", "protected", "atoms", "drop_on_delete", "fmt")

    def __init__(self, kind, text, src=None, run=None, chain=(), protected=False, atoms=None,
                 drop_on_delete=False, fmt=None):
        self.kind = kind          # "char" | "obj" | "compound"
        self.text = text          # visible text ("" for zero-text objects)
        self.src = src            # source element (w:t / w:tab / w:fldChar / m:oMath ...), None for new text
        self.run = run            # containing w:r (None for paragraph-level objects and new text)
        self.chain = chain        # tuple of wrapper elements between the paragraph and the run
        self.protected = protected
        self.atoms = atoms or []  # inner atoms of a compound
        self.drop_on_delete = drop_on_delete
        self.fmt = fmt            # new text only: frozenset of styles, or ("math", latex)

    @property
    def is_gap(self) -> bool:
        return bool(self.text) and self.text.isspace()

    def flat(self):
        if self.kind == "compound":
            for a in self.atoms:
                yield from a.flat()
        else:
            yield self


def atomic_text(el: etree._Element) -> str:
    if el.tag in (M_OMATH, M_OMATHPARA):
        return "".join(t.text or "" for t in el.iter(M_T))
    return "".join(rendered(t) for t in el.iter(W_T))


def _flatten_run(run, chain, out):
    for child in run:
        tag = child.tag
        if tag == W_RPR:
            continue
        if tag == W_T:
            for ch in rendered(child):
                out.append(Atom("char", ch, child, run, chain))
        elif tag in _RUN_CHAR_TAGS:
            out.append(Atom("char", _RUN_CHAR_TAGS[tag], child, run, chain))
        elif tag == qn("w:lastRenderedPageBreak"):
            out.append(Atom("obj", "", child, run, chain, drop_on_delete=True))
        elif tag in (qn("w:commentReference"), qn("w:annotationRef"), W_DELTEXT, W_DELINSTRTEXT):
            out.append(Atom("obj", "", child, run, chain, protected=True))
        else:  # fldChar, instrText, drawing, pict, object, footnoteReference, separator, ...
            out.append(Atom("obj", "", child, run, chain))


def _flatten_children(parent, chain, out):
    for child in parent:
        tag = child.tag
        if tag == W_PPR:
            continue
        if tag == W_R:
            _flatten_run(child, chain, out)
        elif tag in CONTAINER_TAGS:
            _flatten_children(child, chain + (child,), out)
        elif tag in DROP_TAGS:
            continue
        elif tag in PROTECTED_TAGS:
            out.append(Atom("obj", "", child, None, chain, protected=True))
        elif tag in ATOMIC_TAGS:
            out.append(Atom("obj", atomic_text(child), child, None, chain))
        else:
            out.append(Atom("obj", "", child, None, chain, protected=True))


def _group_fields(atoms: list) -> list:
    """Turn every complete field (begin..end) into one compound atom; protect markers of fields that
    cross the paragraph boundary."""
    result: list = []
    stack: list = []
    for a in atoms:
        if a.kind == "obj" and a.src is not None and a.src.tag == W_FLDCHAR:
            kind = a.src.get(qn("w:fldCharType"))
            if kind == "begin":
                stack.append(len(result))
                result.append(a)
            elif kind == "end":
                if stack:
                    start = stack.pop()
                    inner = result[start:] + [a]
                    del result[start:]
                    result.append(Atom("compound", "".join(x.text for x in inner), None, None, a.chain,
                                       atoms=inner))
                else:
                    a.protected = True
                    result.append(a)
            else:
                result.append(a)
        elif a.kind == "obj" and a.src is not None and a.src.tag == W_INSTRTEXT and not stack:
            a.protected = True
            result.append(a)
        else:
            result.append(a)
    for start in stack:  # unterminated fields: keep their markers out of deletions
        for x in result[start:]:
            if x.kind == "obj" and x.src is not None and x.src.tag in (W_FLDCHAR, W_INSTRTEXT):
                x.protected = True
    return result


def paragraph_atoms(p: etree._Element) -> list:
    out: list = []
    _flatten_children(p, (), out)
    return _group_fields(out)


def tokenize(atoms: list):
    """Split atoms into a leading gap and units [token_atoms, trailing_gap_atoms]."""
    lead: list = []
    units: list = []
    for a in atoms:
        if a.is_gap:
            (units[-1][1] if units else lead).append(a)
        elif a.text == "":
            if units and not units[-1][1]:
                units[-1][0].append(a)
            else:
                (units[-1][1] if units else lead).append(a)
        else:
            if units and not units[-1][1]:
                units[-1][0].append(a)
            else:
                units.append([[a], []])
    return lead, units


def token_key(atoms: list) -> str:
    return norm_text("".join(a.text for a in atoms))


def new_atoms(markup: str) -> list:
    """Atoms for new text (per character, carrying their formatting)."""
    out: list = []
    for seg in parse_markup(markup):
        if seg[0] == "math":
            out.append(Atom("obj", seg[1], fmt=("math", seg[1])))
            continue
        text, fmt = seg
        for ch in text:
            if ch in ("\t", "\n") or (ch >= " " and ch not in "\x7f"):
                out.append(Atom("char", ch, fmt=fmt))
    return out


# --------------------------------------------------------------------------- the redliner
class Redliner:
    # A fully deleted paragraph that precedes a table also gets its paragraph mark deleted (Word removes
    # the paragraph on accept; LibreOffice leaves an empty paragraph either way).
    DELETE_MARK_BEFORE_TABLE = True

    def __init__(self, unpacked_dir, author: str = "Claude", date: str | None = None,
                 scripts_dir=None, split_field_runs: bool = False):
        self.dir = Path(unpacked_dir)
        self.split_fields = split_field_runs
        self.doc_path = self.dir / "word" / "document.xml"
        if not self.doc_path.is_file():
            raise RedlineError(f"{self.doc_path} not found (not an unpacked .docx?)")
        self.author = author
        self.initials = "".join(w[0] for w in re.findall(r"\w+", author)).upper() or "C"
        self.date = date or _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        self.scripts_dir = Path(scripts_dir) if scripts_dir else DEFAULT_SCRIPTS_DIR
        raw = self.doc_path.read_bytes()
        m = re.match(rb"\s*(<\?xml[^>]*\?>)", raw)
        self.xml_decl = m.group(1).decode("utf-8") if m else '<?xml version="1.0" encoding="UTF-8"?>'
        parser = etree.XMLParser(remove_blank_text=False, huge_tree=True, resolve_entities=False)
        self.root = etree.fromstring(raw, parser)
        self.body = self.root.find(W_BODY)
        if self.body is None:
            raise RedlineError("document.xml has no w:body")
        self._id = self._max_annotation_id()
        self.styles, self.default_pstyle = self._load_styles()
        self._omml_cache: dict = {}

    # ----------------------------------------------------------------- ids / tracking
    def _max_annotation_id(self) -> int:
        mx = 0
        for xml in (self.dir / "word").glob("*.xml"):
            try:
                for el in etree.parse(str(xml)).iter():
                    v = el.get(W_ID)
                    if v is not None and v.lstrip("-").isdigit():
                        mx = max(mx, int(v))
            except etree.XMLSyntaxError:
                continue
        return mx

    def next_id(self) -> str:
        self._id += 1
        return str(self._id)

    def new_track(self, tag: str) -> etree._Element:
        el = etree.Element(tag)
        el.set(W_ID, self.next_id())
        el.set(W_AUTHOR, self.author)
        el.set(W_DATE, self.date)
        return el

    def _load_styles(self):
        path = self.dir / "word" / "styles.xml"
        ids, default = set(), "Normal"
        if path.is_file():
            root = etree.parse(str(path)).getroot()
            for st in root.iter(qn("w:style")):
                sid = st.get(qn("w:styleId"))
                if sid:
                    ids.add(sid)
                    if st.get(qn("w:type")) == "paragraph" and st.get(qn("w:default")) in ("1", "true"):
                        default = sid
        return ids, default

    # ----------------------------------------------------------------- text access
    @staticmethod
    def para_text(p: etree._Element) -> str:
        """Plain text of a paragraph, identical to the text spelled by paragraph_atoms(p)."""
        parts: list = []

        def walk(parent):
            for child in parent:
                tag = child.tag
                if tag == W_PPR:
                    continue
                if tag == W_R:
                    for c in child:
                        ct = c.tag
                        if ct == W_T:
                            parts.append(rendered(c))
                        elif ct in _RUN_CHAR_TAGS:
                            parts.append(_RUN_CHAR_TAGS[ct])
                elif tag in CONTAINER_TAGS:
                    walk(child)
                elif tag in ATOMIC_TAGS:
                    parts.append(atomic_text(child))

        walk(p)
        return "".join(parts)

    def paragraphs(self):
        """All w:p in document order, skipping text boxes (they are duplicated in mc:Fallback)."""
        for p in self.root.iter(W_P):
            if any(anc.tag == qn("w:txbxContent") for anc in p.iterancestors()):
                continue
            yield p

    def find_paragraph(self, anchor: str) -> etree._Element:
        key = norm_text(anchor or "")
        if not key:
            raise RedlineError("empty anchor")
        matches, exact = [], []
        for p in self.paragraphs():
            text = norm_text(self.para_text(p))
            if key in text:
                matches.append(p)
                if text == key:
                    exact.append(p)
        if len(matches) > 1 and len(exact) == 1:
            return exact[0]  # several paragraphs contain the anchor, exactly one IS the anchor (e.g. a heading)
        if len(matches) != 1:
            raise RedlineError(f"anchor {anchor!r} matches {len(matches)} paragraphs (must match exactly 1)")
        return matches[0]

    def find_table_containing(self, anchor: str) -> etree._Element:
        key = norm_text(anchor or "")
        if not key:
            raise RedlineError("empty anchor")
        matches = []
        for tbl in self.root.iter(W_TBL):
            text = " ".join(self.para_text(p) for p in tbl.iter(W_P))
            if key in norm_text(text):
                matches.append(tbl)
        # a nested table and its parent both match: keep the innermost
        matches = [t for t in matches if not any(o is not t and t in o.iterancestors() for o in matches)]
        if len(matches) != 1:
            raise RedlineError(f"anchor {anchor!r} matches {len(matches)} tables (must match exactly 1)")
        return matches[0]

    def list_paragraphs(self, out=sys.stdout, width: int = 90) -> None:
        for i, p in enumerate(self.paragraphs()):
            style = self._pstyle(p) or "-"
            in_tbl = " [tbl]" if any(a.tag == W_TC for a in p.iterancestors()) else ""
            text = self.para_text(p).replace("\t", " ").replace("\n", " ")
            out.write(f"{i:5d} [{style}]{in_tbl} {text[:width]}\n")

    def _pstyle(self, p: etree._Element) -> str | None:
        ps = p.find(f"{W_PPR}/{W_PSTYLE}")
        return ps.get(W_VAL) if ps is not None else None

    # ----------------------------------------------------------------- formatting sources
    def base_rpr_of(self, p: etree._Element) -> etree._Element | None:
        """rPr of the first text run that is not super/subscript (else the paragraph mark's rPr)."""
        for r in p.iter(W_R):
            if any(anc.tag in (W_DEL, qn("w:moveFrom")) for anc in r.iterancestors(W_DEL, qn("w:moveFrom"))):
                continue
            if r.find(W_T) is None or not "".join(rendered(t) for t in r.findall(W_T)).strip():
                continue
            rpr = r.find(W_RPR)
            if has_vert_align(rpr):
                continue
            return clean_rpr(copy.deepcopy(rpr)) if rpr is not None else None
        ppr = p.find(W_PPR)
        rpr = ppr.find(W_RPR) if ppr is not None else None
        return clean_rpr(copy.deepcopy(rpr)) if rpr is not None else None

    def _longest_run_rpr(self, p: etree._Element) -> etree._Element | None:
        """rPr of the longest text run of the paragraph (its dominant formatting), skipping deleted
        and super/subscript runs."""
        best, best_len = None, -1
        for r in p.iter(W_R):
            if any(anc.tag in (W_DEL, qn("w:moveFrom")) for anc in r.iterancestors(W_DEL, qn("w:moveFrom"))):
                continue
            if has_vert_align(r.find(W_RPR)):
                continue
            n = len("".join(rendered(t) for t in r.findall(W_T)))
            if n > best_len:
                best, best_len = r, n
        if best is None:
            return None
        rpr = best.find(W_RPR)
        return clean_rpr(copy.deepcopy(rpr)) if rpr is not None else None

    def _ppr_copy(self, p: etree._Element | None) -> etree._Element:
        ppr = p.find(W_PPR) if p is not None else None
        ppr = copy.deepcopy(ppr) if ppr is not None else etree.Element(W_PPR)
        strip_ids(ppr)
        for child in list(ppr):
            if _local(child.tag) in ("sectPr", "pPrChange"):
                ppr.remove(child)
        clean_rpr(ppr.find(W_RPR))
        return ppr

    def _is_plain_body_para(self, p: etree._Element) -> bool:
        if p.getparent() is not self.body:
            return False
        style = self._pstyle(p)
        if style not in (None, self.default_pstyle):
            return False
        return bool(self.para_text(p).strip())

    def _is_running_text_para(self, p: etree._Element) -> bool:
        if not self._is_plain_body_para(p):
            return False
        best, best_len = None, -1
        for r in p.iter(W_R):
            if any(anc.tag in (W_DEL, qn("w:moveFrom")) for anc in r.iterancestors(W_DEL, qn("w:moveFrom"))):
                continue
            n = len("".join(rendered(t) for t in r.findall(W_T)))
            if n > best_len:
                best, best_len = r, n
        if best is None or best_len < 80:
            return False
        rpr = best.find(W_RPR)
        if rpr is None:
            return True
        for c in rpr:
            if _local(c.tag) == "vertAlign":
                return False
            if _local(c.tag) in ("b", "i") and c.get(W_VAL, "true") not in ("0", "false", "off"):
                return False
        return True

    def _nearest(self, anchor: etree._Element, pred) -> etree._Element | None:
        paras = list(self.paragraphs())
        try:
            idx = paras.index(anchor)
        except ValueError:
            idx = len(paras)
        for p in reversed(paras[:idx]):
            if pred(p):
                return p
        for p in paras[idx + 1:]:
            if pred(p):
                return p
        return None

    STYLE_IDS = {"heading": ("SMHeading", "Heading1"), "subheading": ("SMSubheading", "Heading2"),
                 "caption": ("Caption", "SMcaption")}

    def paragraph_format(self, anchor: etree._Element, style: str):
        """(pPr, base rPr) for a new paragraph of the given kind, modelled on existing paragraphs."""
        if style == "copy":
            return self._ppr_copy(anchor), self.base_rpr_of(anchor)
        if style == "body":
            # model: the nearest body paragraph that is a real paragraph of running text (its longest
            # run is neither bold nor italic and holds at least 80 characters), so that a bold or
            # italic lead-in line with the Normal style is never taken as the model
            ex = self._nearest(anchor, self._is_running_text_para)
            if ex is None:
                ex = self._nearest(anchor, self._is_plain_body_para)
            return self._ppr_copy(ex), (self._longest_run_rpr(ex) if ex is not None else None)
        if style in self.STYLE_IDS:
            ids = self.STYLE_IDS[style]
            ex = self._nearest(anchor, lambda p: self._pstyle(p) in ids and self.para_text(p).strip())
            if ex is not None:
                base = self._longest_run_rpr(ex) if style == "caption" else self.base_rpr_of(ex)
                return self._ppr_copy(ex), base
            ppr = etree.Element(W_PPR)
            for sid in ids:
                if sid in self.styles:
                    ppr.append(E("w:pStyle", {"w:val": sid}))
                    break
            rpr = etree.Element(W_RPR)
            if style == "heading" and not len(ppr):
                rpr.append(E("w:b")); rpr.append(E("w:bCs"))
            if style == "subheading" and not len(ppr):
                rpr.append(E("w:b")); rpr.append(E("w:bCs")); rpr.append(E("w:i")); rpr.append(E("w:iCs"))
            return ppr, (rpr if len(rpr) else None)
        raise RedlineError(f"unknown paragraph style kind {style!r} "
                           "(use body|subheading|heading|caption|copy)")

    def make_run(self, text: str, fmt, base_rpr: etree._Element | None) -> etree._Element:
        r = etree.Element(W_R)
        rpr = copy.deepcopy(base_rpr) if base_rpr is not None else etree.Element(W_RPR)
        clean_rpr(rpr)
        fmt = fmt or frozenset()
        if "b" in fmt:
            set_ordered_child(rpr, RPR_ORDER, E("w:b"))
            set_ordered_child(rpr, RPR_ORDER, E("w:bCs"))
        if "i" in fmt:
            set_ordered_child(rpr, RPR_ORDER, E("w:i"))
            set_ordered_child(rpr, RPR_ORDER, E("w:iCs"))
        if "sup" in fmt:
            set_ordered_child(rpr, RPR_ORDER, E("w:vertAlign", {"w:val": "superscript"}))
        elif "sub" in fmt:
            set_ordered_child(rpr, RPR_ORDER, E("w:vertAlign", {"w:val": "subscript"}))
        if len(rpr):
            r.append(rpr)
        for part in re.split(r"([\t\n])", text):
            if part == "\t":
                r.append(E("w:tab"))
            elif part == "\n":
                r.append(E("w:br"))
            elif part:
                t = etree.SubElement(r, W_T)
                set_text(t, part)
        return r

    # ----------------------------------------------------------------- OMML via pandoc
    def _math_rpr(self) -> etree._Element:
        for scope in (M_OMATHPARA, M_OMATH):
            for math in self.root.iter(scope):
                for r in math.iter(M_R):
                    rpr = r.find(W_RPR)
                    if rpr is not None:
                        rpr = copy.deepcopy(rpr)
                        for child in list(rpr):
                            if _local(child.tag) in ("lang", "i", "iCs", "b", "bCs", "rPrChange", "ins", "del"):
                                rpr.remove(child)
                        return rpr
        rpr = etree.Element(W_RPR)
        rpr.append(E("w:rFonts", {"w:ascii": "Cambria Math", "w:hAnsi": "Cambria Math"}))
        return rpr

    def _pandoc_docx_body(self, markdown: str) -> etree._Element:
        with tempfile.TemporaryDirectory(prefix="redline_pandoc_") as tmp:
            src = Path(tmp) / "in.md"
            dst = Path(tmp) / "out.docx"
            src.write_text(markdown, encoding="utf-8")
            proc = subprocess.run(["pandoc", "-f", "markdown", "-t", "docx", "-o", str(dst), str(src)],
                                  capture_output=True, text=True)
            if proc.returncode != 0:
                raise RedlineError(f"pandoc failed: {proc.stderr.strip()}")
            with zipfile.ZipFile(dst) as zf:
                doc = etree.fromstring(zf.read("word/document.xml"))
        body = doc.find(W_BODY)
        if body is None:
            raise RedlineError("pandoc produced no document body")
        return body

    def latex_to_omml(self, latex: str, display: bool) -> etree._Element:
        latex = latex.strip()
        if not latex:
            raise RedlineError("empty latex")
        key = (latex, display)
        if key not in self._omml_cache:
            md = ("$$\n" + latex + "\n$$\n") if display else ("$" + latex + "$\n")
            body = self._pandoc_docx_body(md)
            tag = M_OMATHPARA if display else M_OMATH
            el = body.find(f".//{tag}")
            if el is None:
                raise RedlineError(f"pandoc produced no OMML for latex {latex!r}")
            el = copy.deepcopy(el)
            for pr in el.findall(qn("m:oMathParaPr")):
                el.remove(pr)
            fix_omml_order(el)
            self._omml_cache[key] = el
        el = copy.deepcopy(self._omml_cache[key])
        rpr = self._math_rpr()
        for r in el.iter(M_R):
            for old in r.findall(W_RPR):
                r.remove(old)
            pos = 1 if (len(r) and r[0].tag == M_RPR) else 0
            r.insert(pos, copy.deepcopy(rpr))
        return el

    # ----------------------------------------------------------------- emission engine
    class _Emitter:
        """Collects the new paragraph content as ordered segments (equal / delete / insert) and
        builds the XML on flush(); consecutive segments of one kind are merged so unchanged text keeps
        one run per original run and adjacent deletions/insertions share one w:del / w:ins."""

        def __init__(self, rl: "Redliner", base_rpr, context: bool = False):
            self.rl = rl
            self.base_rpr = base_rpr
            self.context = context     # diff mode: new text takes the rPr of the kept text next to it
            self.ctx_rpr = None        # rPr of the last kept (equal) run seen, cleaned; _NONE = run without rPr
            self.pending: list = []    # inserts emitted before any kept run: resolved on the next kept run
            self.out: list = []
            self.segs: list = []  # [mode, payload]

        _NONE = object()

        @staticmethod
        def _run_rpr(a):
            if a.run is None:
                return None
            rpr = a.run.find(W_RPR)
            if has_vert_align(rpr):
                return None
            return clean_rpr(copy.deepcopy(rpr)) if rpr is not None else Redliner._Emitter._NONE

        def _add(self, mode: str, payload: list) -> None:
            if not payload:
                return
            if self.segs and self.segs[-1][0] == mode:
                self.segs[-1][1].extend(payload)
            else:
                self.segs.append([mode, list(payload)])

        def emit_new(self, natoms: list, base=None) -> None:
            if base is None and self.context:
                if self.ctx_rpr is None:          # nothing kept yet: resolve when the first kept run arrives
                    pairs = [(a, None) for a in natoms]
                    if pairs:
                        self._add("insert", pairs)
                        seg = self.segs[-1][1]
                        self.pending.append((seg, len(seg) - len(pairs), len(seg)))
                    return
                base = None if self.ctx_rpr is self._NONE else self.ctx_rpr
            elif base is None:
                base = self.base_rpr
            self._add("insert", [(a, base) for a in natoms])

        def emit_old(self, atoms: list, mode: str) -> None:
            self._add(mode, atoms)
            if self.context and mode == "equal":
                for a in atoms:
                    for fa in a.flat():
                        rpr = self._run_rpr(fa)
                        if rpr is not None:
                            self.ctx_rpr = rpr
                if self.pending and self.ctx_rpr is not None:
                    base = None if self.ctx_rpr is self._NONE else self.ctx_rpr
                    for seg, i, j in self.pending:
                        for k in range(i, j):
                            seg[k] = (seg[k][0], base)
                    self.pending = []

        def flush(self) -> None:
            if self.pending:  # no kept run at all: fall back to the paragraph base
                for seg, i, j in self.pending:
                    for k in range(i, j):
                        seg[k] = (seg[k][0], self.base_rpr)
                self.pending = []
            for mode, payload in self.segs:
                if mode == "insert":
                    ins = self._build_ins(payload)
                    if len(ins):
                        self.out.append(ins)
                else:
                    self.out.extend(self._build(payload, mode))
            self.segs = []

        def _build_ins(self, pairs: list) -> etree._Element:
            ins = self.rl.new_track(W_INS)
            buf, cur = [], None  # cur = (fmt, base)
            for a, base in pairs:
                if a.kind == "obj":
                    if buf:
                        ins.append(self.rl.make_run("".join(buf), cur[0], cur[1]))
                        buf, cur = [], None
                    ins.append(self.rl.latex_to_omml(a.fmt[1], display=False))
                    continue
                key = (a.fmt, base)
                if buf and key != cur:
                    ins.append(self.rl.make_run("".join(buf), cur[0], cur[1]))
                    buf = []
                cur = key
                buf.append(a.text)
            if buf:
                ins.append(self.rl.make_run("".join(buf), cur[0], cur[1]))
            return ins

        def _build(self, atoms: list, mode: str) -> list:
            flat = [a for atom in atoms for a in atom.flat()]
            result: list = []
            i = 0
            while i < len(flat):
                chain = flat[i].chain
                j = i
                while j < len(flat) and flat[j].chain == chain:
                    j += 1
                elems, protected = self._build_group(flat[i:j], mode)
                if mode == "delete" and elems:
                    d = self.rl.new_track(W_DEL)
                    d.extend(elems)
                    elems = [d]
                elems = elems + protected
                for c in reversed(chain):
                    wrapper = etree.Element(c.tag)
                    for k, v in c.attrib.items():
                        wrapper.set(k, v)
                    if c.tag in (W_INS, qn("w:moveTo")):
                        wrapper.set(W_ID, self.rl.next_id())
                    wrapper.extend(elems)
                    elems = [wrapper]
                result.extend(elems)
                i = j
            return result

        def _build_group(self, atoms: list, mode: str):
            elems: list = []
            protected: list = []
            cur_run = cur_r = cur_t = None
            for a in atoms:
                if a.run is None:  # paragraph-level object
                    cur_run = None
                    if a.protected:
                        (protected if mode == "delete" else elems).append(copy.deepcopy(a.src))
                    elif mode == "delete":
                        elems.extend(self.rl._deleted_object(a.src))
                    else:
                        elems.append(copy.deepcopy(a.src))
                    continue
                if a.protected:
                    r = etree.Element(W_R)
                    rpr = a.run.find(W_RPR)
                    if rpr is not None:
                        r.append(copy.deepcopy(rpr))
                    r.append(copy.deepcopy(a.src))
                    (protected if mode == "delete" else elems).append(r)
                    cur_run = None
                    continue
                if a.kind == "obj" and a.drop_on_delete and mode == "delete":
                    continue
                if a.run is not cur_run:
                    cur_run = a.run
                    cur_r = etree.Element(W_R)
                    rpr = cur_run.find(W_RPR)
                    if rpr is not None:
                        cur_r.append(copy.deepcopy(rpr))
                    elems.append(cur_r)
                    cur_t = None
                if a.kind == "char" and a.src.tag == W_T:
                    if cur_t is None:
                        cur_t = etree.SubElement(cur_r, W_T if mode == "equal" else W_DELTEXT)
                        cur_t.text = ""
                    cur_t.text += a.text
                else:
                    cur_t = None
                    el = copy.deepcopy(a.src)
                    if mode == "delete" and el.tag == W_INSTRTEXT:
                        el.tag = W_DELINSTRTEXT
                    cur_r.append(el)
            for r in elems:
                if r.tag == W_R:
                    for t in r:
                        if t.tag in (W_T, W_DELTEXT):
                            set_text(t, t.text or "")
            return elems, protected

    def _deleted_object(self, src: etree._Element) -> list:
        """Copy of a paragraph-level object prepared for placement inside <w:del>."""
        if src.tag == qn("w:fldSimple"):
            runs = [E("w:r")]
            runs[0].append(E("w:fldChar", {"w:fldCharType": "begin"}))
            r = E("w:r")
            t = etree.SubElement(r, W_DELINSTRTEXT)
            set_text(t, src.get(qn("w:instr"), ""))
            runs.append(r)
            r = E("w:r"); r.append(E("w:fldChar", {"w:fldCharType": "separate"})); runs.append(r)
            for child in src:
                child = copy.deepcopy(child)
                self._to_deleted(child)
                runs.append(child)
            r = E("w:r"); r.append(E("w:fldChar", {"w:fldCharType": "end"})); runs.append(r)
            return runs
        el = copy.deepcopy(src)
        self._to_deleted(el)
        return [el]

    @staticmethod
    def _to_deleted(el: etree._Element) -> None:
        for t in el.iter(W_T):
            t.tag = W_DELTEXT
        for t in el.iter(W_INSTRTEXT):
            t.tag = W_DELINSTRTEXT

    def _replace_content(self, p: etree._Element, elems: list) -> None:
        for child in list(p):
            if child.tag != W_PPR:
                p.remove(child)
        p.extend(elems)

    # ----------------------------------------------------------------- diff
    def _diff_emit(self, em, atoms: list, natoms: list) -> None:
        lead_o, units_o = tokenize(atoms)
        lead_n, units_n = tokenize(natoms)
        keys_o = [token_key(u[0]) for u in units_o]
        keys_n = [token_key(u[0]) for u in units_n]
        self._glue(units_n, keys_n, keys_o)
        sm = difflib.SequenceMatcher(None, keys_o, keys_n, autojunk=False)
        ops = self._cleanup_opcodes(sm.get_opcodes(), units_o, keys_o)
        # leading whitespace / objects: edge whitespace of the paragraph is never touched by a diff
        ws_o = any(a.is_gap for a in lead_o)
        if lead_o:
            em.emit_old(lead_o, "equal")
        if lead_n and not ws_o:
            em.emit_new(lead_n)
        for tag, i1, i2, j1, j2 in ops:
            if tag == "equal":
                for k in range(i2 - i1):
                    uo, un = units_o[i1 + k], units_n[j1 + k]
                    em.emit_old(uo[0], "equal")
                    if i1 + k == len(units_o) - 1 and j1 + k == len(units_n) - 1:
                        em.emit_old(uo[1], "equal")  # trailing whitespace of the paragraph
                    else:
                        self._emit_gap(em, uo[1], un[1])
            elif tag == "delete":
                for u in units_o[i1:i2]:
                    em.emit_old(u[0] + u[1], "delete")
            elif tag == "insert":
                for u in units_n[j1:j2]:
                    em.emit_new(u[0] + u[1])
            else:  # replace
                self._emit_replace(em, units_o[i1:i2], units_n[j1:j2])
        em.flush()

    def _emit_replace(self, em, uos: list, uns: list) -> None:
        """Delete old tokens / insert new ones, keeping a shared prefix or suffix of the edge tokens."""
        if len(uos) == 1 and len(uns) == 1:
            if self._try_split(em, uos[0], uns[0]):
                return
        elif uos and uns and self._try_split(em, uos[0], uns[0], prefix_only=True):
            uos, uns = uos[1:], uns[1:]
        for u in uos:
            em.emit_old(u[0] + u[1], "delete")
        for u in uns:
            em.emit_new(u[0] + u[1])

    @staticmethod
    def _glue(units_n, keys_n, keys_o) -> None:
        """Merge consecutive new tokens that spell an old atomic token containing spaces (math, fields)."""
        for ko in keys_o:
            if " " not in ko:
                continue
            parts = ko.split(" ")
            n = len(parts)
            j = 0
            while j + n <= len(keys_n):
                if keys_n[j:j + n] == parts:
                    merged = []
                    for k in range(n):
                        merged.extend(units_n[j + k][0])
                        if k < n - 1:
                            merged.extend(units_n[j + k][1])
                    gap = units_n[j + n - 1][1]
                    units_n[j:j + n] = [[merged, gap]]
                    keys_n[j:j + n] = [ko]
                j += 1

    @staticmethod
    def _cleanup_opcodes(ops, units_o, keys_o):
        """Absorb tiny 'equal' islands (<= 3 chars of plain text) between two changes into one replace."""
        ops = [list(o) for o in ops]
        changed = True
        while changed:
            changed = False
            for idx in range(1, len(ops) - 1):
                tag, i1, i2, j1, j2 = ops[idx]
                if tag != "equal" or ops[idx - 1][0] == "equal" or ops[idx + 1][0] == "equal":
                    continue
                if sum(len(k) for k in keys_o[i1:i2]) > 3:
                    continue
                if any(a.kind != "char" for u in units_o[i1:i2] for a in u[0] + u[1]):
                    continue
                prev, nxt = ops[idx - 1], ops[idx + 1]
                ops[idx - 1:idx + 2] = [["replace", prev[1], nxt[2], prev[3], nxt[4]]]
                changed = True
                break
        return [tuple(o) for o in ops]

    def _emit_gap(self, em, gap_o: list, gap_n: list) -> None:
        ws_o = any(a.is_gap for a in gap_o)
        ws_n = any(a.is_gap for a in gap_n)
        if ws_o == ws_n:
            if gap_o:
                em.emit_old(gap_o, "equal")
        elif ws_o:
            em.emit_old(gap_o, "delete")
        else:
            if gap_o:
                em.emit_old(gap_o, "equal")
            em.emit_new(gap_n)

    def _try_split(self, em, uo, un, prefix_only: bool = False) -> bool:
        """Token replacement: keep a common prefix/suffix as unchanged text (e.g. 'word' -> 'words')."""
        to, tn = uo[0], un[0]
        if any(a.kind != "char" for a in tn):
            return False
        so = [norm_key(a.text) for a in to]
        sn = [norm_key(a.text) for a in tn]
        fo, fn = "".join(so), "".join(sn)
        lim = min(len(fo), len(fn))
        pre = 0
        while pre < lim and fo[pre] == fn[pre]:
            pre += 1
        suf = 0
        while not prefix_only and suf < lim - pre and fo[-1 - suf] == fn[-1 - suf]:
            suf += 1

        def align_prefix(parts, target):
            cum = cnt = 0
            for s in parts:
                if cum + len(s) <= target:
                    cum += len(s); cnt += 1
                else:
                    break
            return cum, cnt

        pre, pa = align_prefix(so, pre)
        suf, sa = align_prefix(list(reversed(so[pa:])), suf)
        if pre + suf < 2 or (pre + suf) * 2 < max(len(fo), len(fn)):
            return False
        _, pn = align_prefix(sn, pre)
        _, sn_cnt = align_prefix(list(reversed(sn[pn:])), suf)
        # formatting for the inserted piece: the neighbouring unchanged run, unless super/subscript
        base = None
        neighbour = to[pa - 1] if pa > 0 else (to[len(to) - sa] if sa > 0 else None)
        if neighbour is not None and neighbour.kind == "char" and neighbour.run is not None:
            rpr = neighbour.run.find(W_RPR)
            if not has_vert_align(rpr):
                base = clean_rpr(copy.deepcopy(rpr)) if rpr is not None else etree.Element(W_RPR)
        if pa:
            em.emit_old(to[:pa], "equal")
        mid_o = to[pa:len(to) - sa]
        mid_n = tn[pn:len(tn) - sn_cnt]
        if mid_o:
            em.emit_old(mid_o, "delete")
        if mid_n:
            em.emit_new(mid_n, base=base)
        if sa:
            em.emit_old(to[len(to) - sa:], "equal")
        self._emit_gap(em, uo[1], un[1])
        return True

    # ----------------------------------------------------------------- paragraph helpers
    def _ppr_rpr(self, p: etree._Element) -> etree._Element:
        ppr = p.find(W_PPR)
        if ppr is None:
            ppr = etree.Element(W_PPR)
            p.insert(0, ppr)
        rpr = ppr.find(W_RPR)
        if rpr is None:
            rpr = set_ordered_child(ppr, PPR_ORDER, etree.Element(W_RPR))
        return rpr

    def _mark_paragraph(self, p: etree._Element, tag: str) -> None:
        """Mark the paragraph mark as inserted/deleted (w:ins then w:del come first in pPr/rPr)."""
        rpr = self._ppr_rpr(p)
        for old in rpr.findall(tag):
            rpr.remove(old)
        pos = 1 if (tag == W_DEL and len(rpr) and rpr[0].tag == W_INS) else 0
        rpr.insert(pos, self.new_track(tag))

    def _can_delete_mark(self, p: etree._Element) -> bool:
        ppr = p.find(W_PPR)
        if ppr is not None and ppr.find(W_SECTPR) is not None:
            return False
        nxt = p.getnext()
        while nxt is not None and nxt.tag in SKIP_SIBLINGS:
            nxt = nxt.getnext()
        if nxt is None:
            return False
        if nxt.tag == W_P:
            return True
        return nxt.tag == W_TBL and self.DELETE_MARK_BEFORE_TABLE

    def _delete_paragraph(self, p: etree._Element, delete_mark: bool = True) -> None:
        em = self._Emitter(self, None)
        em.emit_old(paragraph_atoms(p), "delete")
        em.flush()
        self._replace_content(p, em.out)
        if delete_mark and self._can_delete_mark(p):
            self._mark_paragraph(p, W_DEL)

    def _new_paragraph(self, anchor: etree._Element, markup: str, style: str) -> etree._Element:
        ppr, base = self.paragraph_format(anchor, style)
        p = etree.Element(W_P)
        p.append(ppr)
        self._mark_paragraph(p, W_INS)
        em = self._Emitter(self, base)
        em.emit_new(new_atoms(markup.strip(" \r\n")))
        em.flush()
        p.extend(em.out)
        return p

    def _empty_inserted_paragraph(self, like: etree._Element | None) -> etree._Element:
        p = etree.Element(W_P)
        ppr = self._ppr_copy(like) if like is not None else etree.Element(W_PPR)
        for child in list(ppr):  # keep only the mark formatting; no numbering/style for a spacer
            if _local(child.tag) in ("numPr", "pStyle"):
                ppr.remove(child)
        p.append(ppr)
        self._mark_paragraph(p, W_INS)
        return p

    def _insert_block_after(self, anchor: etree._Element, block: etree._Element) -> None:
        anchor.addnext(block)
        nxt = block.getnext()
        while nxt is not None and nxt.tag in SKIP_SIBLINGS:
            nxt = nxt.getnext()
        if nxt is None or nxt.tag != W_P:
            block.addnext(self._empty_inserted_paragraph(anchor if anchor.tag == W_P else None))

    # ----------------------------------------------------------------- tables
    def _track_table_inserted(self, tbl: etree._Element) -> None:
        for tr in tbl.iter(W_TR):
            trpr = tr.find(W_TRPR)
            if trpr is None:
                trpr = etree.Element(W_TRPR)
                pos = 1 if (len(tr) and tr[0].tag == qn("w:tblPrEx")) else 0
                tr.insert(pos, trpr)
            for old in trpr.findall(W_INS) + trpr.findall(W_DEL):
                trpr.remove(old)
            change = trpr.find(qn("w:trPrChange"))
            if change is not None:
                change.addprevious(self.new_track(W_INS))
            else:
                trpr.append(self.new_track(W_INS))

    def _delete_table(self, tbl: etree._Element) -> None:
        for tr in tbl.iter(W_TR):
            trpr = tr.find(W_TRPR)
            if trpr is None:
                trpr = etree.Element(W_TRPR)
                pos = 1 if (len(tr) and tr[0].tag == qn("w:tblPrEx")) else 0
                tr.insert(pos, trpr)
            if trpr.find(W_DEL) is None:
                change = trpr.find(qn("w:trPrChange"))
                if change is not None:
                    change.addprevious(self.new_track(W_DEL))
                else:
                    trpr.append(self.new_track(W_DEL))
        for p in list(tbl.iter(W_P)):
            self._delete_paragraph(p, delete_mark=False)

    def _text_width(self) -> int:
        sect = self.body.find(W_SECTPR)
        if sect is not None:
            pg, mar = sect.find(qn("w:pgSz")), sect.find(qn("w:pgMar"))
            try:
                width = int(pg.get(qn("w:w")))
                width -= int(mar.get(qn("w:left"), 0)) + int(mar.get(qn("w:right"), 0))
                if width > 1000:
                    return width
            except (AttributeError, TypeError, ValueError):
                pass
        return 9360

    def _equation_template(self, anchor: etree._Element):
        """The nearest existing 2-column equation table (preceding the anchor if possible)."""
        order = list(self.root.iter(W_TBL, W_P))
        try:
            aidx = order.index(anchor)
        except ValueError:
            aidx = len(order)
        before, after = [], []
        for idx, tbl in enumerate(order):
            if tbl.tag != W_TBL:
                continue
            grid = tbl.find(qn("w:tblGrid"))
            if tbl.find(f".//{M_OMATHPARA}") is not None and grid is not None and \
                    len(grid.findall(qn("w:gridCol"))) == 2 and len(tbl.findall(W_TR)) >= 1:
                (before if idx < aidx else after).append(tbl)
        return before[-1] if before else (after[0] if after else None)

    @staticmethod
    def _widen_number_column(tbl: etree._Element, cells: list, number: str) -> None:
        """Make sure the equation-number column is wide enough for e.g. '(11)'."""
        needed = 216 + sum(120 if ch.isdigit() else 80 for ch in number)
        grid = tbl.find(qn("w:tblGrid"))
        cols = grid.findall(qn("w:gridCol")) if grid is not None else []
        try:
            widths = [int(c.get(qn("w:w"))) for c in cols]
        except (TypeError, ValueError):
            return
        if len(widths) != 2 or widths[1] >= needed:
            return
        delta = needed - widths[1]
        cols[0].set(qn("w:w"), str(widths[0] - delta))
        cols[1].set(qn("w:w"), str(needed))
        for tc, w in zip(cells, (widths[0] - delta, needed)):
            tcw = tc.find(f"{W_TCPR}/{qn('w:tcW')}")
            if tcw is not None and tcw.get(qn("w:type")) == "dxa":
                tcw.set(qn("w:w"), str(w))

    def _equation_table(self, omml: etree._Element, number: str, anchor: etree._Element) -> etree._Element:
        template = self._equation_template(anchor)
        if template is not None:
            tbl = strip_ids(copy.deepcopy(template))
            rows = tbl.findall(W_TR)
            for extra in rows[1:]:
                tbl.remove(extra)
            tr = rows[0]
            cells = tr.findall(W_TC)
            if len(cells) != 2:
                template = None
            else:
                self._widen_number_column(tbl, cells, number)
        if template is None:
            tw = self._text_width()
            tbl = etree.Element(W_TBL)
            tblpr = etree.SubElement(tbl, W_TBLPR)
            if "TableGrid" in self.styles:
                tblpr.append(E("w:tblStyle", {"w:val": "TableGrid"}))
            tblpr.append(E("w:tblW", {"w:w": "0", "w:type": "auto"}))
            borders = etree.SubElement(tblpr, qn("w:tblBorders"))
            for side in ("top", "left", "bottom", "right", "insideH", "insideV"):
                borders.append(E("w:" + side, {"w:val": "none", "w:sz": "0", "w:space": "0", "w:color": "auto"}))
            tblpr.append(E("w:tblLook", {"w:val": "04A0", "w:firstRow": "1", "w:lastRow": "0",
                                         "w:firstColumn": "1", "w:lastColumn": "0", "w:noHBand": "0",
                                         "w:noVBand": "1"}))
            grid = etree.SubElement(tbl, qn("w:tblGrid"))
            grid.append(E("w:gridCol", {"w:w": str(tw - 700)}))
            grid.append(E("w:gridCol", {"w:w": "700"}))
            tr = etree.SubElement(tbl, W_TR)
            body_ex = self._nearest(anchor, self._is_plain_body_para)
            base = self.base_rpr_of(body_ex) if body_ex is not None else None
            cells = []
            for width, valign in ((tw - 700, None), (700, "center")):
                tc = etree.SubElement(tr, W_TC)
                tcpr = etree.SubElement(tc, W_TCPR)
                tcpr.append(E("w:tcW", {"w:w": str(width), "w:type": "dxa"}))
                if valign:
                    tcpr.append(E("w:vAlign", {"w:val": valign}))
                p = etree.SubElement(tc, W_P)
                ppr = etree.SubElement(p, W_PPR)
                if base is not None and len(base):
                    ppr.append(copy.deepcopy(base))
                cells.append(tc)
            number_rpr = base
        else:
            number_rpr = None
            for r in cells[1].iter(W_R):
                if r.find(W_T) is not None:
                    number_rpr = clean_rpr(copy.deepcopy(r.find(W_RPR))) if r.find(W_RPR) is not None else None
                    break
        # rows / paragraphs: keep tcPr + first paragraph's pPr, replace the content
        for idx, tc in enumerate(cells):
            paras = tc.findall(W_P)
            first = paras[0] if paras else etree.SubElement(tc, W_P)
            for child in list(tc):
                if child.tag != W_TCPR and child is not first:
                    tc.remove(child)
            ppr = first.find(W_PPR)
            if ppr is not None:
                clean_rpr(ppr.find(W_RPR))
            self._replace_content(first, [])
            self._mark_paragraph(first, W_INS)
            ins = self.new_track(W_INS)
            if idx == 0:
                ins.append(omml)
            else:
                r = etree.SubElement(ins, W_R)
                if number_rpr is not None and len(number_rpr):
                    r.append(copy.deepcopy(number_rpr))
                set_text(etree.SubElement(r, W_T), number)
            first.append(ins)
        self._track_table_inserted(tbl)
        return tbl

    def _table_cell_rpr(self, style: str) -> etree._Element | None:
        candidates = []
        for tbl in self.body.iter(W_TBL):
            st = tbl.find(f"{W_TBLPR}/{qn('w:tblStyle')}")
            candidates.append((0 if (st is not None and st.get(W_VAL) == style) else 1, tbl))
        for _, tbl in sorted(candidates, key=lambda c: c[0]):
            for r in tbl.iter(W_R):
                if r.find(W_T) is not None and "".join(rendered(t) for t in r.findall(W_T)).strip():
                    rpr = clean_rpr(copy.deepcopy(r.find(W_RPR))) if r.find(W_RPR) is not None else None
                    if rpr is not None:
                        for child in list(rpr):
                            if _local(child.tag) in ("b", "bCs", "i", "iCs", "vertAlign", "noProof", "u"):
                                rpr.remove(child)
                    return rpr
        return None

    def _markdown_table(self, markdown: str, style: str, widths=None, font_size=None) -> etree._Element:
        """widths: relative column widths (list of numbers, one per column); font_size: cell font size
        in points (both optional)."""
        body = self._pandoc_docx_body(markdown.strip() + "\n")
        src = body.find(f".//{W_TBL}")
        if src is None:
            raise RedlineError("pandoc did not produce a table from the given markdown")
        rows = []
        for tr in src.findall(W_TR):
            header = tr.find(f"{W_TRPR}/{qn('w:tblHeader')}") is not None
            cells = []
            for tc in tr.findall(W_TC):
                paras = []
                for p in tc.findall(W_P):
                    jc = p.find(f"{W_PPR}/{qn('w:jc')}")
                    pieces = []
                    for r in p.iter(W_R):
                        rpr = r.find(W_RPR)
                        fmt = set()
                        if rpr is not None:
                            if rpr.find(qn("w:b")) is not None:
                                fmt.add("b")
                            if rpr.find(qn("w:i")) is not None:
                                fmt.add("i")
                            va = rpr.find(qn("w:vertAlign"))
                            if va is not None:
                                fmt.add("sup" if va.get(W_VAL) == "superscript" else "sub")
                        text = ""
                        for child in r:
                            if child.tag == W_T:
                                text += rendered(child)
                            elif child.tag == qn("w:tab"):
                                text += "\t"
                            elif child.tag == qn("w:br"):
                                text += "\n"
                        if text:
                            pieces.append((text, frozenset(fmt)))
                    paras.append((jc.get(W_VAL) if jc is not None else None, pieces))
                cells.append(paras)
            rows.append((header, cells))
        if not rows:
            raise RedlineError("empty table")
        ncols = max(len(cells) for _, cells in rows)
        if not any(h for h, _ in rows):
            rows[0] = (True, rows[0][1])
        tw = self._text_width()
        if widths:
            if len(widths) != ncols or any(float(w) <= 0 for w in widths):
                raise RedlineError(f"insert_table_after: 'widths' needs {ncols} positive numbers")
            tot = float(sum(widths))
            col_ws = [int(round(tw * float(w) / tot)) for w in widths]
            col_pcts = [int(round(5000 * float(w) / tot)) for w in widths]
        else:
            col_ws = [tw // ncols] * ncols
            col_pcts = [5000 // ncols] * ncols
        cell_rpr = self._table_cell_rpr(style)
        if font_size:
            if cell_rpr is None:
                cell_rpr = etree.Element(W_RPR)
            hp = str(int(round(float(font_size) * 2)))
            set_ordered_child(cell_rpr, RPR_ORDER, E("w:sz", {"w:val": hp}))
            set_ordered_child(cell_rpr, RPR_ORDER, E("w:szCs", {"w:val": hp}))
        tbl = etree.Element(W_TBL)
        tblpr = etree.SubElement(tbl, W_TBLPR)
        if style and style in self.styles:
            tblpr.append(E("w:tblStyle", {"w:val": style}))
        tblpr.append(E("w:tblW", {"w:w": "5000", "w:type": "pct"}))
        tblpr.append(E("w:jc", {"w:val": "center"}))
        borders = etree.SubElement(tblpr, qn("w:tblBorders"))
        for side, val, sz in (("top", "single", "8"), ("left", "none", "0"), ("bottom", "single", "8"),
                              ("right", "none", "0"), ("insideH", "none", "0"), ("insideV", "none", "0")):
            borders.append(E("w:" + side, {"w:val": val, "w:sz": sz, "w:space": "0", "w:color": "auto"}))
        tblpr.append(E("w:tblLook", {"w:val": "04A0", "w:firstRow": "1", "w:lastRow": "0", "w:firstColumn": "1",
                                     "w:lastColumn": "0", "w:noHBand": "0", "w:noVBand": "1"}))
        grid = etree.SubElement(tbl, qn("w:tblGrid"))
        for ci in range(ncols):
            grid.append(E("w:gridCol", {"w:w": str(col_ws[ci])}))
        for header, cells in rows:
            tr = etree.SubElement(tbl, W_TR)
            trpr = etree.SubElement(tr, W_TRPR)
            if header:
                trpr.append(E("w:tblHeader"))
            trpr.append(E("w:jc", {"w:val": "center"}))
            for ci in range(ncols):
                paras = cells[ci] if ci < len(cells) else [(None, [])]
                tc = etree.SubElement(tr, W_TC)
                tcpr = etree.SubElement(tc, W_TCPR)
                tcpr.append(E("w:tcW", {"w:w": str(col_pcts[ci]), "w:type": "pct"}))
                if header:
                    tcb = etree.SubElement(tcpr, qn("w:tcBorders"))
                    tcb.append(E("w:bottom", {"w:val": "single", "w:sz": "4", "w:space": "0", "w:color": "auto"}))
                tcpr.append(E("w:vAlign", {"w:val": "center"}))
                for jc, pieces in paras:
                    p = etree.SubElement(tc, W_P)
                    ppr = etree.SubElement(p, W_PPR)
                    if jc in ("center", "right", "end"):
                        align = "right" if jc == "end" else jc
                    else:
                        align = "center" if (header or ci > 0) else "left"
                    ppr.append(E("w:jc", {"w:val": align}))
                    mark = copy.deepcopy(cell_rpr) if cell_rpr is not None else etree.Element(W_RPR)
                    if header:
                        set_ordered_child(mark, RPR_ORDER, E("w:b"))
                        set_ordered_child(mark, RPR_ORDER, E("w:bCs"))
                    ppr.append(mark)
                    self._mark_paragraph(p, W_INS)
                    if pieces:
                        ins = self.new_track(W_INS)
                        for text, fmt in pieces:
                            fmt = set(fmt)
                            if header:
                                fmt.add("b")
                            ins.append(self.make_run(text, frozenset(fmt), cell_rpr))
                        p.append(ins)
        self._track_table_inserted(tbl)
        return tbl

    # ----------------------------------------------------------------- operations
    def op_replace(self, anchor: str, new: str, mode: str = "diff") -> None:
        if mode not in ("diff", "replace"):
            raise RedlineError(f"replace: unknown mode {mode!r} (diff|replace)")
        p = self.find_paragraph(anchor)
        atoms = paragraph_atoms(p)
        natoms = new_atoms((new or "").strip(" \r\n"))
        # replace: the new text takes the paragraph's dominant formatting (its longest run), so a caption
        # or a list item whose bold lead-in comes first is replaced by plain text plus the markup;
        # diff: inserted words take the formatting of the kept text next to them.
        if mode == "diff":
            base = self.base_rpr_of(p)
        else:
            base = self._longest_run_rpr(p)
            if base is None:
                base = self.base_rpr_of(p)
        em = self._Emitter(self, base, context=(mode == "diff"))
        if mode == "replace":
            em.emit_old(atoms, "delete")
            em.emit_new(natoms)
            em.flush()
        else:
            self._diff_emit(em, atoms, natoms)
        self._replace_content(p, em.out)

    def op_insert(self, anchor: str, paragraphs: list, before: bool = False) -> None:
        target = self.find_paragraph(anchor)
        if not isinstance(paragraphs, list) or not paragraphs:
            raise RedlineError("insert_after/insert_before: 'paragraphs' must be a non-empty list")
        new_ps = []
        for spec in paragraphs:
            if not isinstance(spec, dict) or "text" not in spec:
                raise RedlineError("each paragraph needs {'text': ..., 'style': ...}")
            new_ps.append(self._new_paragraph(target, spec["text"], spec.get("style", "body")))
        if before:
            if self._open_field_before(target):
                raise RedlineError("insert_before: the anchor paragraph lies inside a field result (e.g. a "
                                   "citation-manager bibliography); anchor on a paragraph outside the field")
            for p in new_ps:
                target.addprevious(p)
        else:
            # never insert inside a field result (a Zotero bibliography spans several paragraphs and a
            # field refresh would wipe the new paragraphs): move past the paragraph that closes the field
            cur = target
            while self._open_field_after(cur):
                nxt = cur.getnext()
                if nxt is None or nxt.tag != W_P:
                    raise RedlineError("insert_after: the anchor paragraph lies inside a field that does not close "
                                       "in a following paragraph")
                cur = nxt
            for p in new_ps:
                cur.addnext(p)
                cur = p

    def _field_depth_through(self, p: etree._Element) -> int:
        """Number of fields still open after paragraph p (begins minus ends, counted from the start of
        p's parent), ignoring field characters inside tracked deletions."""
        depth = 0
        for sib in p.getparent():
            for fc in sib.iter(W_FLDCHAR):
                if any(a.tag == W_DEL for a in fc.iterancestors(W_DEL)):
                    continue
                kind = fc.get(qn("w:fldCharType"))
                if kind == "begin":
                    depth += 1
                elif kind == "end":
                    depth = max(0, depth - 1)
            if sib is p:
                break
        return depth

    def _open_field_after(self, p: etree._Element) -> bool:
        return self._field_depth_through(p) > 0

    def _open_field_before(self, p: etree._Element) -> bool:
        prev = p.getprevious()
        return prev is not None and self._field_depth_through(prev) > 0

    def op_delete(self, anchor: str, preceding_figures: int = 0) -> None:
        """Delete the anchored paragraph; with preceding_figures = N, also delete up to N paragraphs
        immediately before it that hold only figures (drawings/pictures, no text) - a figure's images
        together with its caption."""
        p = self.find_paragraph(anchor)
        figs = []
        prev = p.getprevious()
        while len(figs) < preceding_figures and prev is not None and prev.tag == W_P and self._is_figure_paragraph(prev):
            figs.append(prev)
            prev = prev.getprevious()
        if len(figs) < preceding_figures:
            raise RedlineError(f"delete: only {len(figs)} figure paragraph(s) precede {anchor!r}, {preceding_figures} requested")
        for q in figs:
            self._delete_paragraph(q)
        self._delete_paragraph(p)

    def op_delete_figures_before(self, anchor: str, count: int = 1) -> None:
        """Delete only the `count` figure-only paragraphs immediately before the anchored paragraph
        (a picture being replaced while its caption stays)."""
        p = self.find_paragraph(anchor)
        figs = []
        prev = p.getprevious()
        while len(figs) < count and prev is not None and prev.tag == W_P and self._is_figure_paragraph(prev):
            figs.append(prev)
            prev = prev.getprevious()
        if len(figs) < count:
            raise RedlineError(f"delete_figures_before: only {len(figs)} figure paragraph(s) precede {anchor!r}, {count} requested")
        for q in figs:
            self._delete_paragraph(q)

    def _is_figure_paragraph(self, p: etree._Element) -> bool:
        if self.para_text(p).strip():
            return False
        return any(True for _ in p.iter(qn("w:drawing"), qn("w:pict"), qn("w:object")))

    def op_delete_range(self, from_anchor: str, to_anchor: str) -> None:
        start, end = self.find_paragraph(from_anchor), self.find_paragraph(to_anchor)
        if start.getparent() is not end.getparent():
            raise RedlineError("delete_range: both anchors must be in the same body / table cell")
        siblings = list(start.getparent())
        i, j = siblings.index(start), siblings.index(end)
        if i > j:
            raise RedlineError("delete_range: 'from_anchor' paragraph comes after 'to_anchor' paragraph")
        for el in siblings[i:j + 1]:
            if el.tag == W_P:
                self._delete_paragraph(el)
            elif el.tag == W_TBL:
                self._delete_table(el)

    def op_insert_equation_after(self, anchor: str, latex: str, number: str = "") -> None:
        p = self.find_paragraph(anchor)
        omml = self.latex_to_omml(latex, display=True)
        tbl = self._equation_table(omml, number or "", p)
        self._insert_block_after(p, tbl)

    def op_delete_table(self, anchor: str) -> None:
        p = self.find_paragraph(anchor)
        nxt = p.getnext()
        while nxt is not None and nxt.tag in SKIP_SIBLINGS:
            nxt = nxt.getnext()
        if nxt is None or nxt.tag != W_TBL:
            raise RedlineError(f"delete_table: no table immediately follows the paragraph {anchor!r}")
        self._delete_table(nxt)

    def op_delete_table_containing(self, anchor: str) -> None:
        self._delete_table(self.find_table_containing(anchor))

    def op_insert_table_after(self, anchor: str, markdown: str, style: str = "TableGrid",
                              widths=None, font_size=None) -> None:
        p = self.find_paragraph(anchor)
        tbl = self._markdown_table(markdown, style or "TableGrid", widths, font_size)
        self._insert_block_after(p, tbl)

    def op_comment(self, anchor: str, text: str) -> None:
        p = self.find_paragraph(anchor)
        if not text:
            raise RedlineError("comment: empty text")
        scripts = str(self.scripts_dir)
        if scripts not in sys.path:
            sys.path.insert(0, scripts)
        try:
            import comment as comment_mod  # the docx skill's comment.py
        except ImportError as exc:
            raise RedlineError(f"cannot import comment.py from {scripts}: {exc}") from exc
        cid, _para_id, _msg = comment_mod.add_comment(self.dir, text, author=self.author, initials=self.initials)
        pos = 1 if (len(p) and p[0].tag == W_PPR) else 0
        p.insert(pos, E("w:commentRangeStart", {"w:id": cid}))
        p.append(E("w:commentRangeEnd", {"w:id": cid}))
        r = etree.SubElement(p, W_R)
        if "CommentReference" in self.styles:
            rpr = etree.SubElement(r, W_RPR)
            rpr.append(E("w:rStyle", {"w:val": "CommentReference"}))
        r.append(E("w:commentReference", {"w:id": cid}))

    # ----------------------------------------------------------------- driver
    def apply_op(self, op: dict) -> None:
        if not isinstance(op, dict) or "op" not in op:
            raise RedlineError(f"malformed operation: {op!r}")
        kind = op["op"]

        def need(*keys):
            for k in keys:
                if k not in op:
                    raise RedlineError(f"{kind}: missing field {k!r}")

        if kind == "replace":
            need("anchor", "new")
            self.op_replace(op["anchor"], op["new"], op.get("mode", "diff"))
        elif kind in ("insert_after", "insert_before"):
            need("anchor", "paragraphs")
            self.op_insert(op["anchor"], op["paragraphs"], before=(kind == "insert_before"))
        elif kind == "delete":
            need("anchor")
            self.op_delete(op["anchor"], int(op.get("preceding_figures", 0)))
        elif kind == "delete_figures_before":
            need("anchor")
            self.op_delete_figures_before(op["anchor"], int(op.get("count", 1)))
        elif kind == "delete_range":
            need("from_anchor", "to_anchor")
            self.op_delete_range(op["from_anchor"], op["to_anchor"])
        elif kind == "insert_equation_after":
            need("anchor", "latex")
            self.op_insert_equation_after(op["anchor"], op["latex"], op.get("number", ""))
        elif kind == "delete_table":
            need("anchor")
            self.op_delete_table(op["anchor"])
        elif kind == "delete_table_containing":
            need("anchor")
            self.op_delete_table_containing(op["anchor"])
        elif kind == "insert_table_after":
            need("anchor", "markdown")
            self.op_insert_table_after(op["anchor"], op["markdown"], op.get("style", "TableGrid"),
                                       op.get("widths"), op.get("font_size"))
        elif kind == "comment":
            need("anchor", "text")
            self.op_comment(op["anchor"], op["text"])
        else:
            raise RedlineError(f"unknown op {kind!r}")

    _SATELLITES = ("word/comments.xml", "word/commentsExtended.xml", "word/commentsIds.xml",
                   "word/commentsExtensible.xml", "word/people.xml", "word/_rels/document.xml.rels",
                   "[Content_Types].xml")

    def apply(self, ops: list) -> None:
        """Apply all operations; on any error the in-memory tree is discarded and files restored."""
        if isinstance(ops, dict):
            ops = ops.get("ops", [])
        if not isinstance(ops, list):
            raise RedlineError("ops must be a list of operations")
        snapshot = {rel: ((self.dir / rel).read_bytes() if (self.dir / rel).is_file() else None)
                    for rel in self._SATELLITES}
        backup_root = copy.deepcopy(self.root)
        backup_id = self._id
        try:
            if self.split_fields:
                self.split_field_runs()
            for n, op in enumerate(ops, 1):
                try:
                    self.apply_op(op)
                except RedlineError as exc:
                    raise RedlineError(f"op #{n} ({op.get('op') if isinstance(op, dict) else op!r}): {exc}") from exc
        except Exception:
            for rel, data in snapshot.items():
                path = self.dir / rel
                if data is None:
                    if path.exists():
                        path.unlink()
                else:
                    path.write_bytes(data)
            self.root = backup_root
            self.body = self.root.find(W_BODY)
            self._id = backup_id
            raise

    def split_field_runs(self) -> int:
        """Give every field character / instruction its own run (content and rendering unchanged).

        merge_runs.py merges text and w:fldChar/w:instrText into one run; Word is fine with that,
        but LibreOffice mis-imports such runs inside list paragraphs and leaks the list numbering to
        every following paragraph. Returns the number of runs split."""
        field_tags = (W_FLDCHAR, W_INSTRTEXT, W_DELINSTRTEXT)
        count = 0
        for r in list(self.root.iter(W_R)):
            kids = [c for c in r if c.tag != W_RPR]
            if len(kids) < 2 or not any(c.tag in field_tags for c in kids):
                continue
            rpr = r.find(W_RPR)
            groups: list = []
            for c in kids:
                if c.tag in field_tags or not groups or groups[-1][0].tag in field_tags:
                    groups.append([c])
                else:
                    groups[-1].append(c)
            parent, idx = r.getparent(), r.getparent().index(r)
            parent.remove(r)
            for k, group in enumerate(groups):
                nr = etree.Element(W_R)
                if rpr is not None:
                    nr.append(copy.deepcopy(rpr))
                nr.extend(group)
                parent.insert(idx + k, nr)
            count += 1
        return count

    def serialize(self) -> bytes:
        return (self.xml_decl + etree.tostring(self.root, encoding="unicode")).encode("utf-8")

    def save(self) -> None:
        self.doc_path.write_bytes(self.serialize())


# --------------------------------------------------------------------------- CLI
def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Apply tracked changes to an unpacked .docx (word/document.xml).")
    ap.add_argument("unpacked_dir")
    ap.add_argument("edits", nargs="?", help="JSON file: list of operations (or {'ops': [...]})")
    ap.add_argument("--author", default="Claude")
    ap.add_argument("--date", default=None, help="ISO-8601 UTC date for w:date (default: now)")
    ap.add_argument("--list", action="store_true", help="list paragraphs (index, style, first 90 chars)")
    ap.add_argument("--split-field-runs", action="store_true",
                    help="also give every field code character its own run (LibreOffice-safe output for "
                         "documents processed by merge_runs.py; content unchanged)")
    args = ap.parse_args(argv)
    try:
        rl = Redliner(args.unpacked_dir, author=args.author, date=args.date,
                      split_field_runs=args.split_field_runs)
        if args.list:
            rl.list_paragraphs()
            return 0
        if not args.edits:
            ap.error("edits.json is required unless --list is given")
        ops = json.loads(Path(args.edits).read_text(encoding="utf-8"))
        rl.apply(ops)
        rl.save()
        n = len(ops["ops"]) if isinstance(ops, dict) else len(ops)
        print(f"Applied {n} operation(s) to {rl.doc_path} as {args.author!r}")
        return 0
    except RedlineError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
