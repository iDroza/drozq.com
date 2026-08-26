#!/usr/bin/env python3
"""Panda no-op detector + patch generator.

The Panda CSS soup each page inherits from /index.html only defines the
utility classes referenced by the homepage at the time the page was
scaffolded. Any other arbitrary utility a page uses (bd_1px_solid_#e5e5e5,
md:p_28px, grid-tc_1fr_1fr_1fr, ...) matches NO rule and silently renders
nothing: cards lose their borders, grids stack, headings keep mobile sizes
at desktop. This bit /faq/ (max-w_780px), then /process/ (the five-steps
"cards" rendered as naked circles for weeks).

Modes:
  --check   Report every visual-intent class used in page markup (outside
            the funnel markers) that no <style> block on that page defines.
            Exit 1 if any exist. Run this after building or editing a page.
  --css     Print the patch stylesheet generated from the union of no-ops.
  --apply   Install/refresh <style id="drozq-panda-patch"> (the generated
            stylesheet) just before </head> on every template page.

The patch block compiles the missing utilities into real CSS, restoring
each page's original intended design with zero markup changes. After
--apply, --check passes because the patch block's definitions count.
"""
import re, glob, os, sys
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BP = {"xs": 480, "sm": 640, "md": 768, "lg": 992, "xl": 1200}
PATCH_ID = "drozq-panda-patch"
PATCH_RE = re.compile(r'\s*<style id="' + PATCH_ID + r'">.*?</style>', re.S)

VISUAL = ("bd_", "bd-", "bx-sh_", "bg_", "bg-c_", "max-w_", "min-w_", "w_", "h_", "min-h_", "max-h_",
          "grid", "bdr", "p_", "pt_", "pb_", "pl_", "pr_", "px_", "py_", "m_", "mt_", "mb_", "ml_", "mr_",
          "fs_", "lh_", "fw_", "ls_", "c_", "gap_", "top_", "bottom_", "left_", "right_", "inset_",
          "d_", "flex", "ai_", "jc_", "ta_", "op_", "z_", "ov_", "pos_", "obj-", "tw_", "va_", "as_",
          "col-", "row-", "bt_", "bb_", "bl_", "br_", "sh_", "tt_", "td_", "ws_", "wb_", "cursor_",
          "trs_", "anim_", "trf_", "ring")

PROPS = {
    "p": lambda v: f"padding: {v};",
    "pt": lambda v: f"padding-top: {v};",
    "pb": lambda v: f"padding-bottom: {v};",
    "pl": lambda v: f"padding-left: {v};",
    "pr": lambda v: f"padding-right: {v};",
    "px": lambda v: f"padding-left: {v}; padding-right: {v};",
    "py": lambda v: f"padding-top: {v}; padding-bottom: {v};",
    "m": lambda v: f"margin: {v};",
    "mt": lambda v: f"margin-top: {v};",
    "mb": lambda v: f"margin-bottom: {v};",
    "ml": lambda v: f"margin-left: {v};",
    "mr": lambda v: f"margin-right: {v};",
    "w": lambda v: f"width: {v};",
    "h": lambda v: f"height: {v};",
    "max-w": lambda v: f"max-width: {v};",
    "min-w": lambda v: f"min-width: {v};",
    "min-h": lambda v: f"min-height: {v};",
    "max-h": lambda v: f"max-height: {v};",
    "fs": lambda v: f"font-size: {v};",
    "lh": lambda v: f"line-height: {v};",
    "fw": lambda v: f"font-weight: {v};",
    "ls": lambda v: f"letter-spacing: {v};",
    "c": lambda v: f"color: {v};",
    "bg": lambda v: f"background: {v};",
    "bg-c": lambda v: f"background-color: {v};",
    "bd": lambda v: f"border: {v};",
    "bd-c": lambda v: f"border-color: {v};",
    "bd-t": lambda v: f"border-top: {v};",
    "bd-b": lambda v: f"border-bottom: {v};",
    "bd-l": lambda v: f"border-left: {v};",
    "bd-r": lambda v: f"border-right: {v};",
    "bx-sh": lambda v: f"box-shadow: {v};",
    "bdr": lambda v: f"border-radius: {v};",
    "op": lambda v: f"opacity: {v};",
    "gap": lambda v: f"gap: {v};",
    "gap_x": lambda v: f"column-gap: {v};",
    "gap_y": lambda v: f"row-gap: {v};",
    "grid-tc": lambda v: f"grid-template-columns: {v};",
    "grid-tr": lambda v: f"grid-template-rows: {v};",
    "as": lambda v: f"align-self: {v};",
    "ai": lambda v: f"align-items: {v};",
    "jc": lambda v: f"justify-content: {v};",
    "ta": lambda v: f"text-align: {v};",
    "d": lambda v: f"display: {v};",
    "trs": lambda v: f"transition: {v};",
    "trf": lambda v: f"transform: {v};",
    "obj-p": lambda v: f"object-position: {v};",
    "obj-f": lambda v: f"object-fit: {v};",
    "ov": lambda v: f"overflow: {v};",
    "pos": lambda v: f"position: {v};",
    "va": lambda v: f"vertical-align: {v};",
    "top": lambda v: f"top: {v};",
    "bottom": lambda v: f"bottom: {v};",
    "left": lambda v: f"left: {v};",
    "right": lambda v: f"right: {v};",
    "z": lambda v: f"z-index: {v};",
}

def files():
    out = [os.path.join(ROOT, "index.html"), os.path.join(ROOT, "404.html")]
    out += sorted(glob.glob(os.path.join(ROOT, "*", "index.html")))
    # /active/ and /dashboard/ are standalone ops shells (own CSS, no Panda soup); never patch them.
    out = [f for f in out if os.path.basename(os.path.dirname(f)) not in ("active", "dashboard")]
    out += sorted(glob.glob(os.path.join(ROOT, "*", "*", "index.html")))
    return [f for f in out if "node_modules" not in f and os.path.isfile(f)]

def html_unescape(t):
    return (t.replace("&amp;", "&").replace("&quot;", '"')
             .replace("&gt;", ">").replace("&lt;", "<").replace("&#39;", "'"))

def css_escape(cls):
    return "".join(ch if re.match(r"[A-Za-z0-9_-]", ch) else "\\" + ch for ch in cls)

def split_variants(tok):
    """Split on ':' at bracket depth 0: 'md:p_28px' -> ['md','p_28px']."""
    parts, buf, depth = [], "", 0
    for ch in tok:
        if ch in "([":
            depth += 1
        elif ch in ")]":
            depth -= 1
        if ch == ":" and depth == 0:
            parts.append(buf); buf = ""
        else:
            buf += ch
    parts.append(buf)
    return parts

def decode_value(v):
    return v.replace("_", " ")

def utility_to_decl(util):
    """'bd_1px_solid_#e5e5e5' -> 'border: 1px solid #e5e5e5;'"""
    if util.startswith("gap_x_"):
        return PROPS["gap_x"](decode_value(util[len("gap_x_"):]))
    if util.startswith("gap_y_"):
        return PROPS["gap_y"](decode_value(util[len("gap_y_"):]))
    m = re.match(r"([a-z-]+(?:-[a-z]+)*)_(.+)$", util)
    if not m:
        return None
    prefix, val = m.groups()
    fn = PROPS.get(prefix)
    return fn(decode_value(val)) if fn else None

def token_to_rule(tok):
    """Translate one class token into (media_condition_or_None, selector, declaration)."""
    parts = split_variants(tok)
    util = parts[-1]
    decl = utility_to_decl(util)
    if decl is None:
        return None
    media = None
    suffix = ""
    for var in parts[:-1]:
        if var in BP:
            media = f"screen and (min-width: {BP[var]}px)"
        elif var == "hover":
            suffix += ":hover"
        elif var.startswith("[@media_") and var.endswith("]"):
            media = decode_value(var[len("[@media_"):-1])
        elif var.startswith("[&") and var.endswith("]"):
            inner = var[2:-1]           # ':hover' or '_img' or ':disabled'
            suffix += inner.replace("_", " ")
        else:
            return None
    selector = "." + css_escape(tok) + suffix
    return (media, selector, decl)

def scan(verbose=False, ignore_patch=False):
    """Return {file: {token: count}} of visual-intent classes with no definition.

    ignore_patch=True treats the existing <style id="drozq-panda-patch"> block as
    absent, so --apply / --css regenerate the FULL union of no-ops. Without it a
    re-apply saw the current patch as "defined", built a block holding only the
    newly missing tokens, and overwrote the full patch with it (2026-08-26)."""
    report = {}
    for f in files():
        d = open(f, encoding="utf-8-sig").read()
        defined = set()
        style_ranges = []
        # Since 2026-08-26 the compiled Panda soup lives in /media/css/panda.css
        # (scripts/extract_panda_css.py); a self-hosted stylesheet <link> counts
        # as defined exactly like an inline <style> block.
        for lm in re.finditer(r'<link rel="stylesheet" href="(/media/css/[^"?]+)', d):
            css_file = os.path.join(ROOT, *lm.group(1).lstrip("/").split("/"))
            if os.path.exists(css_file):
                for cm in re.finditer(r"\.((?:\\.|[A-Za-z0-9_-])+)", open(css_file, encoding="utf-8").read()):
                    defined.add(re.sub(r"\\(.)", r"\1", cm.group(1)))
        for m in re.finditer(r"<style[^>]*>(.*?)</style>", d, flags=re.S):
            style_ranges.append((m.start(), m.end()))
            if ignore_patch and m.group(0).startswith('<style id="' + PATCH_ID + '">'):
                continue
            for cm in re.finditer(r"\.((?:\\.|[A-Za-z0-9_-])+)", m.group(1)):
                defined.add(re.sub(r"\\(.)", r"\1", cm.group(1)))
        zones = []
        for a, b in (("DROZQ_FUNNEL_HTML_BEGIN", "DROZQ_FUNNEL_HTML_END"),
                     ("DROZQ_FUNNEL_JS_BEGIN", "DROZQ_FUNNEL_JS_END")):
            i, j = d.find(a), d.find(b)
            if i >= 0:
                zones.append((i, j))
        script_ranges = [(m.start(), m.end()) for m in re.finditer(r"<script\b.*?</script>", d, flags=re.S)]
        body, last = [], 0
        for s, e in sorted(zones + script_ranges + style_ranges):
            body.append(d[last:s]); last = max(last, e)
        body.append(d[last:])
        body = "".join(body)

        noop = defaultdict(int)
        for m in re.finditer(r'class="([^"]+)"', body):
            for tok in html_unescape(m.group(1)).split():
                if tok in defined:
                    continue
                base = split_variants(tok)[-1]
                if any(base.startswith(p) for p in VISUAL):
                    noop[tok] += 1
        if noop:
            report[f] = dict(noop)
    return report

def build_css(tokens):
    plain, medias = [], defaultdict(list)
    untranslatable = []
    for tok in sorted(tokens):
        rule = token_to_rule(tok)
        if rule is None:
            untranslatable.append(tok)
            continue
        media, sel, decl = rule
        line = f"{sel} {{ {decl} }}"
        if media:
            medias[media].append(line)
        else:
            plain.append(line)
    css = ["/* Compiled by scripts/panda_patch.py: utilities used in page markup that the"]
    css.append("   inherited Panda soup never defined. Do not hand-edit; re-run --apply. */")
    css.extend(plain)
    for media in sorted(medias):
        css.append(f"@media {media} {{")
        css.extend("  " + l for l in medias[media])
        css.append("}")
    return "\n".join(css), untranslatable

def apply_patch():
    report = scan(ignore_patch=True)
    union = set()
    for noop in report.values():
        union.update(noop)
    css, untranslatable = build_css(union)
    if untranslatable:
        print("UNTRANSLATABLE tokens (fix token_to_rule or style by hand):")
        for t in untranslatable:
            print("   ", t)
        sys.exit(2)
    block = f'<style id="{PATCH_ID}">\n{css}\n</style>'
    changed = 0
    for f in files():
        raw = open(f, "rb").read()
        bom = raw.startswith(b"\xef\xbb\xbf")
        d = raw.decode("utf-8-sig")
        fz = [d.find(x) for x in ("DROZQ_FUNNEL_HTML_BEGIN", "DROZQ_FUNNEL_HTML_END",
                                  "DROZQ_FUNNEL_JS_BEGIN", "DROZQ_FUNNEL_JS_END")]
        funnel_before = (d[fz[0]:fz[1]] + d[fz[2]:fz[3]]) if fz[0] >= 0 else ""
        d2 = PATCH_RE.sub("", d)
        head_end = d2.find("</head>")
        assert head_end > 0, f
        d2 = d2[:head_end] + block + "\n" + d2[head_end:]
        if fz[0] >= 0:
            fz2 = [d2.find(x) for x in ("DROZQ_FUNNEL_HTML_BEGIN", "DROZQ_FUNNEL_HTML_END",
                                        "DROZQ_FUNNEL_JS_BEGIN", "DROZQ_FUNNEL_JS_END")]
            assert funnel_before == d2[fz2[0]:fz2[1]] + d2[fz2[2]:fz2[3]], f"funnel changed: {f}"
        if d2 != d:
            data = d2.encode("utf-8")
            open(f, "wb").write((b"\xef\xbb\xbf" + data) if bom else data)
            changed += 1
            print("PATCHED", os.path.relpath(f, ROOT))
    print(f"\n{changed} file(s) updated; patch covers {len(union)} utility classes.")

def check():
    report = scan()
    if not report:
        print("OK: no uncompiled visual utility classes on any page.")
        return 0
    for f, noop in sorted(report.items(), key=lambda kv: -sum(kv[1].values())):
        print(f"{os.path.relpath(f, ROOT)}: {len(noop)} uncompiled visual class(es)")
        for tok, n in sorted(noop.items()):
            print(f"    {tok}  x{n}")
    return 1

if __name__ == "__main__":
    if "--apply" in sys.argv:
        apply_patch()
    elif "--css" in sys.argv:
        report = scan(ignore_patch=True)
        union = set()
        for noop in report.values():
            union.update(noop)
        css, bad = build_css(union)
        print(css)
        if bad:
            print("\n/* UNTRANSLATABLE: */")
            for t in bad:
                print("/*", t, "*/")
    else:
        sys.exit(check())
