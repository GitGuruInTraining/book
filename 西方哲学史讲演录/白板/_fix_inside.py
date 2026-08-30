# -*- coding: utf-8 -*-
"""Widen gaps between cards inside each box, then rebuild .excalidraw."""
from __future__ import print_function
import json
import os
import re

DIR = os.path.dirname(os.path.abspath(__file__))
MIN_H = 240
MIN_V = 180
MIN_BOX = 180
PAD_X, PAD_TOP, PAD_BOT = 48, 104, 56

STROKE = {"1": "#e03131", "2": "#f08c00", "3": "#f59f00", "4": "#2f9e44", "5": "#1971c2", "6": "#9c36b5"}
FILL = {"1": "#ffe3e3", "2": "#fff4e6", "3": "#fff3bf", "4": "#d3f9d8", "5": "#d0ebff", "6": "#f3d9fa"}
CHAPTER_LABEL = {
    "00 自序": "00 自序",
    "01 哲学是什么与哲学有什么用": "01 哲学是什么",
    "02 希腊自然哲学": "02 自然哲学",
    "03 希腊形而上学的源端": "03 形而上学源端",
    "04 希腊怀疑论与道德哲学": "04 怀疑论与道德",
    "05 希腊实在论哲学": "05 两峰（柏 / 亚）",
    "06 希腊哲学的衰颓": "06 希腊化衰颓",
    "07 中世纪基督教哲学": "07 中世纪",
    "08 近代哲学的转向与英国经验论": "08 经验论",
    "09 欧洲大陆唯理论哲学": "09 唯理论",
    "10 18世纪法国启蒙哲学": "10 法国启蒙",
    "11 康德的批判哲学": "11 康德",
    "12 从费希特到黑格尔": "12 费希特 → 黑格尔",
    "13 修订版后记": "13 后记",
}

# 子卡跟着父卡的 x，避免第二排对不齐
ALIGN_UNDER = {
    "知识图谱": {
        "00000000000000e0": "00000000000000e1",  # 火 → 逻各斯
        "0000000000000063": "0000000000000064",  # 种子 → 努斯
        "0000000000000061": "00000000000000e2",  # 原子 → 辩证法
        "0000000000000070": "00000000000000e5",  # 实体 → 四因
        "0000000000000071": "00000000000000e4",  # 共相 → 太一
    },
    "人物关系": {
        "0000000000000028": "00000000000000d1",  # 伊壁鸠鲁 → 斐洛
        "0000000000000029": "000000000000002a",  # 皮浪 → 普罗提诺
    },
}

PREFER = {
    "人物关系": {
        ("0000000000000007", "0000000000000015"): "above",
        ("000000000000001c", "000000000000001e"): "above",
        ("000000000000001d", "0000000000000029"): "above",
        ("000000000000001f", "000000000000002a"): "below",
        ("0000000000000020", "0000000000000031"): "below",
        ("0000000000000041", "0000000000000039"): "above",
        ("0000000000000039", "0000000000000048"): "above",
        ("0000000000000048", "000000000000004a"): "above",
        ("000000000000004a", "0000000000000050"): "below",
        ("0000000000000016", "000000000000001d"): "above",
        ("0000000000000048", "000000000000004a"): "above",
    },
    "知识图谱": {
        ("000000000000005e", "000000000000006c"): "above",
        ("000000000000007a", "000000000000007d"): "below",
        ("000000000000007f", "000000000000007c"): "above",
        ("000000000000007e", "0000000000000088"): "above",
        ("000000000000007c", "0000000000000088"): "below",
        ("0000000000000088", "000000000000008a"): "above",
        ("0000000000000092", "0000000000000094"): "above",
        ("0000000000000096", "0000000000000098"): "above",
        ("00000000000000e1", "000000000000006e"): "below",
        ("00000000000000e1", "00000000000000e2"): "above",
    },
}

KG_MEMBERS = {
    "000000000000005d": ["000000000000005e", "000000000000005f", "0000000000000060",
                         "00000000000000e0", "0000000000000062", "0000000000000063",
                         "0000000000000061", "00000000000000e3", "0000000000000064",
                         "00000000000000e1", "00000000000000e2"],
    "000000000000006b": ["000000000000006c", "000000000000006d", "000000000000006e",
                         "000000000000006f", "0000000000000070", "0000000000000071",
                         "00000000000000e4", "00000000000000e5"],
    "0000000000000078": ["0000000000000079", "000000000000007a", "000000000000007b",
                         "000000000000007c", "000000000000007d", "000000000000007e",
                         "000000000000007f"],
    "0000000000000087": ["0000000000000088", "0000000000000089",
                         "000000000000008a", "000000000000008b"],
    "0000000000000091": ["0000000000000092", "0000000000000093", "0000000000000094",
                         "0000000000000095", "0000000000000096", "0000000000000097",
                         "0000000000000098"],
    "00000000000000a0": ["00000000000000a1", "00000000000000a2", "00000000000000a3"],
}

SEED = 9000
INDEX_N = 0


def load(name):
    with open(os.path.join(DIR, name + ".canvas"), "r", encoding="utf-8") as f:
        return json.load(f)


def save(name, data):
    with open(os.path.join(DIR, name + ".canvas"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, ensure_ascii=False, indent="\t")
        f.write("\n")


def note_name(path):
    return os.path.splitext(os.path.basename(path.replace("\\", "/")))[0]


def box(n):
    return n["x"], n["y"], n["x"] + n["width"], n["y"] + n["height"]


def overlap_gap(a, b):
    ax1, ay1, ax2, ay2 = box(a)
    bx1, by1, bx2, by2 = box(b)
    ox = min(ax2, bx2) - max(ax1, bx1)
    oy = min(ay2, by2) - max(ay1, by1)
    if ox > 0 and oy > 0:
        return -min(ox, oy)
    if ox > 0:
        return -oy
    if oy > 0:
        return -ox
    return 9999


def cluster_rows(cards, tol=60):
    rows = []
    for c in sorted(cards, key=lambda n: (n["y"], n["x"])):
        placed = False
        for row in rows:
            if abs(c["y"] - row[0]["y"]) <= tol:
                row.append(c)
                placed = True
                break
        if not placed:
            rows.append([c])
    return rows


def spread_row(cards):
    cards = sorted(cards, key=lambda c: c["x"])
    for i in range(1, len(cards)):
        need = cards[i - 1]["x"] + cards[i - 1]["width"] + MIN_H
        if cards[i]["x"] < need:
            dx = need - cards[i]["x"]
            for c in cards[i:]:
                c["x"] += dx
    return cards


def spread_rows_vertical(rows):
    rows = sorted(rows, key=lambda r: min(c["y"] for c in r))
    for i in range(1, len(rows)):
        prev_bot = max(c["y"] + c["height"] for c in rows[i - 1])
        cur_top = min(c["y"] for c in rows[i])
        if cur_top < prev_bot + MIN_V:
            dy = prev_bot + MIN_V - cur_top
            for later in rows[i:]:
                for c in later:
                    c["y"] += dy
    return rows


def members_of(data, explicit=None):
    by = {n["id"]: n for n in data["nodes"]}
    groups = [n for n in data["nodes"] if n["type"] == "group"]
    if explicit:
        return groups, {gid: [by[i] for i in ids if i in by] for gid, ids in explicit.items()}
    files = [n for n in data["nodes"] if n["type"] == "file"]
    members = {g["id"]: [] for g in groups}
    for f in files:
        cx, cy = f["x"] + f["width"] / 2.0, f["y"] + f["height"] / 2.0
        hits = [g for g in groups
                if g["x"] <= cx <= g["x"] + g["width"] and g["y"] <= cy <= g["y"] + g["height"]]
        if not hits:
            continue
        hits.sort(key=lambda g: g["width"] * g["height"])
        members[hits[0]["id"]].append(f)
    return groups, members


def refit(g, cards):
    if not cards:
        return
    g["x"] = min(c["x"] for c in cards) - PAD_X
    g["y"] = min(c["y"] for c in cards) - PAD_TOP
    g["width"] = max(c["x"] + c["width"] for c in cards) - g["x"] + PAD_X
    g["height"] = max(c["y"] + c["height"] for c in cards) - g["y"] + PAD_BOT


def spread_inside(data, name, explicit=None):
    groups, members = members_of(data, explicit)
    by = {n["id"]: n for n in data["nodes"]}
    align = ALIGN_UNDER.get(name, {})
    for g in groups:
        cards = members.get(g["id"], [])
        if not cards:
            continue
        rows = cluster_rows(cards)
        for row in rows:
            spread_row(row)
        spread_rows_vertical(rows)
        for pid, cid in align.items():
            if pid in by and cid in by and by[cid] in cards and by[pid] in cards:
                p, c = by[pid], by[cid]
                c["x"] = p["x"] + (p["width"] - c["width"]) / 2.0
        refit(g, cards)

    # 霍尔巴赫放到狄德罗和卢梭中间的下方
    if name == "人物关系":
        d, r, h = by.get("0000000000000049"), by.get("000000000000004a"), by.get("00000000000000d4")
        if d and r and h:
            h["x"] = (d["x"] + d["width"] + r["x"]) / 2.0 - h["width"] / 2.0
            h["y"] = d["y"] + d["height"] + MIN_V
            for g in groups:
                if g.get("label") == "法国启蒙":
                    refit(g, members[g["id"]])

    # 分组框若因撑开而相碰，把右边／下边的整组推开
    groups_sorted = sorted(groups, key=lambda g: (g["y"], g["x"]))
    changed, guard = True, 0
    while changed and guard < 20:
        changed = False
        guard += 1
        for i, a in enumerate(groups_sorted):
            for b in groups_sorted[i + 1:]:
                gap = overlap_gap(a, b)
                if gap >= MIN_BOX:
                    continue
                need = MIN_BOX - gap
                same_row = not (a["y"] + a["height"] < b["y"] or b["y"] + b["height"] < a["y"])
                dx, dy = (need, 0) if same_row and b["x"] >= a["x"] else (0, need)
                for n in [b] + members.get(b["id"], []):
                    n["x"] += dx
                    n["y"] += dy
                refit(b, members.get(b["id"], []))
                changed = True
                print("  push box", b.get("label"), (dx, dy))

    print(" inside gaps", name)
    for g in groups:
        cards = members.get(g["id"], [])
        rows = cluster_rows(cards)
        for row in rows:
            row = sorted(row, key=lambda c: c["x"])
            for i in range(1, len(row)):
                gap = row[i]["x"] - (row[i - 1]["x"] + row[i - 1]["width"])
                if gap < MIN_H:
                    print("  TIGHT-H", g.get("label"), note_name(row[i - 1]["file"]),
                          note_name(row[i]["file"]), gap)
        if len(rows) >= 2:
            rows = sorted(rows, key=lambda r: min(c["y"] for c in r))
            for i in range(1, len(rows)):
                gap = min(c["y"] for c in rows[i]) - max(c["y"] + c["height"] for c in rows[i - 1])
                if gap < MIN_V:
                    print("  TIGHT-V", g.get("label"), gap)
    print(" box gaps", name)
    for i, a in enumerate(groups):
        for b in groups[i + 1:]:
            g = overlap_gap(a, b)
            if g < MIN_BOX:
                print("  TIGHT-BOX", a.get("label"), b.get("label"), g)
    return data


def patch_clue(data):
    files = [n for n in data["nodes"] if n["type"] == "file"]
    rows = cluster_rows(files, tol=40)
    for row in rows:
        spread_row(row)
    return data


def next_seed():
    global SEED
    SEED += 1
    return SEED


def next_index():
    global INDEX_N
    INDEX_N += 1
    return "d" + format(INDEX_N, "x")


def base_el(eid, typ, x, y, w, h, stroke="#1e1e1e", fill="transparent",
            fill_style="solid", sw=2, roughness=1, roundness=None,
            link=None, locked=False, group_ids=None):
    return {
        "id": eid, "type": typ, "x": float(x), "y": float(y),
        "width": float(w), "height": float(h), "angle": 0,
        "strokeColor": stroke, "backgroundColor": fill, "fillStyle": fill_style,
        "strokeWidth": sw, "strokeStyle": "solid", "roughness": roughness,
        "opacity": 100, "groupIds": list(group_ids or []), "frameId": None,
        "index": next_index(), "roundness": roundness, "seed": next_seed(),
        "version": 3, "versionNonce": next_seed(), "isDeleted": False,
        "boundElements": [], "updated": 1, "link": link, "locked": locked,
        "customData": None,
    }


def text_width(text, font_size):
    w = 0.0
    for ch in text:
        w += font_size * (1.05 if ord(ch) > 127 else 0.58)
    return max(24.0, w)


def make_text(eid, x, y, text, font_size=18, color="#1e1e1e",
              align="left", w=None, h=None, locked=False, group_ids=None):
    lines = text.split("\n")
    if w is None:
        w = max(text_width(line, font_size) for line in lines) + 8
    if h is None:
        h = font_size * 1.35 * max(1, len(lines))
    el = base_el(eid, "text", x, y, w, h, stroke=color, fill="transparent",
                 sw=1, roughness=0, locked=locked, group_ids=group_ids)
    el.update({
        "text": text, "fontSize": font_size, "fontFamily": 5,
        "textAlign": align, "verticalAlign": "top", "containerId": None,
        "originalText": text, "autoResize": True, "lineHeight": 1.25,
    })
    return el


def side_pt(node, side):
    x, y, w, h = node["x"], node["y"], node["width"], node["height"]
    return {
        "left": (x, y + h / 2.0), "right": (x + w, y + h / 2.0),
        "top": (x + w / 2.0, y), "bottom": (x + w / 2.0, y + h),
    }.get(side or "right", (x + w, y + h / 2.0))


def display_name(canvas_name, path):
    name = note_name(path)
    if canvas_name == "全书线索":
        return CHAPTER_LABEL.get(name, name)
    return name


def extra_text(eid, x, y, text, size=16, color="#5c5c5c"):
    return make_text(eid, x, y, text, font_size=size, color=color)


def extra_box(eid, x, y, w, h, color, label):
    rect = base_el(eid, "rectangle", x, y, w, h, stroke=STROKE[color],
                   fill=FILL[color], fill_style="hachure", sw=2, roughness=1,
                   roundness={"type": 3})
    lab = make_text(eid + "L", x + 16, y + 10, label, font_size=20, color=STROKE[color])
    return [rect, lab]


def clue_era_boxes(canvas):
    files = [n for n in canvas["nodes"] if n["type"] == "file"]
    by_name = {note_name(n["file"]): n for n in files}

    def box_for(names, color, label, eid):
        nodes = [by_name[k] for k in names if k in by_name]
        pad, top = 48, 64
        x = min(n["x"] for n in nodes) - pad
        y = min(n["y"] for n in nodes) - top
        w = max(n["x"] + n["width"] for n in nodes) - x + pad
        h = max(n["y"] + n["height"] for n in nodes) - y + pad
        return extra_box(eid, x, y, w, h, color, label)

    n06 = by_name["06 希腊哲学的衰颓"]
    return [
        box_for(
            ["00 自序", "01 哲学是什么与哲学有什么用", "02 希腊自然哲学",
             "03 希腊形而上学的源端", "04 希腊怀疑论与道德哲学",
             "05 希腊实在论哲学", "06 希腊哲学的衰颓"],
            "4", "希腊", "E1"),
        box_for(
            ["07 中世纪基督教哲学", "08 近代哲学的转向与英国经验论",
             "09 欧洲大陆唯理论哲学", "10 18世纪法国启蒙哲学"],
            "5", "中世 → 启蒙", "E2"),
        box_for(
            ["11 康德的批判哲学", "12 从费希特到黑格尔", "13 修订版后记"],
            "6", "德国古典", "E3"),
        extra_text("D1", n06["x"] + 8, n06["y"] + n06["height"] + 24, "↓ 转入中世纪", 16, "#1971c2"),
    ]


def inset_rect(n, pad=4):
    return (n["x"] + pad, n["y"] + pad,
            n["x"] + n["width"] - pad, n["y"] + n["height"] - pad)


def point_in_rect(px, py, r):
    return r[0] < px < r[2] and r[1] < py < r[3]


def seg_hits_rect(x1, y1, x2, y2, r, samples=48):
    hits = 0
    for i in range(1, samples):
        t = i / float(samples)
        if point_in_rect(x1 + (x2 - x1) * t, y1 + (y2 - y1) * t, r):
            hits += 1
    return hits >= 2


def polyline_blockers(pts, cards, skip_ids):
    names = []
    for nid, n in cards.items():
        if nid in skip_ids:
            continue
        r = inset_rect(n)
        for i in range(len(pts) - 1):
            if seg_hits_rect(pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1], r):
                names.append(note_name(n["file"]))
                break
    return names


def corridor_y(src, dst, files, prefer, used):
    x1 = src["x"] + src["width"] / 2.0
    x2 = dst["x"] + dst["width"] / 2.0
    lo, hi = min(x1, x2), max(x1, x2)
    band_top = min(src["y"], dst["y"]) - 40
    band_bot = max(src["y"] + src["height"], dst["y"] + dst["height"]) + 40
    relevant = [src, dst]
    for n in files.values():
        if n is src or n is dst:
            continue
        if n["x"] + n["width"] < lo - 8 or n["x"] > hi + 8:
            continue
        if n["y"] + n["height"] < band_top or n["y"] > band_bot:
            continue
        relevant.append(n)
    if prefer == "above":
        y = min(n["y"] for n in relevant) - 56
        while any(abs(y - u) < 18 for u in used):
            y -= 20
    else:
        y = max(n["y"] + n["height"] for n in relevant) + 56
        while any(abs(y - u) < 18 for u in used):
            y += 20
    return y


def elbow_pts(src, dst, prefer, cy):
    if prefer == "above":
        x1, y1 = side_pt(src, "top")
        x2, y2 = side_pt(dst, "top")
    else:
        x1, y1 = side_pt(src, "bottom")
        x2, y2 = side_pt(dst, "bottom")
    return [(x1, y1), (x1, cy), (x2, cy), (x2, y2)]


def route_edge(src, dst, from_side, to_side, files, prefer, used):
    p1 = side_pt(src, from_side)
    p2 = side_pt(dst, to_side)
    straight = [p1, p2]
    skip = {src["id"], dst["id"]}
    if prefer is None and not polyline_blockers(straight, files, skip):
        return straight, None
    order = [prefer or "above", "below" if prefer != "below" else "above"]
    best, best_cy = None, None
    for pref in order:
        cy = corridor_y(src, dst, files, pref, used)
        pts = elbow_pts(src, dst, pref, cy)
        hits = polyline_blockers(pts, files, skip)
        if not hits:
            return pts, cy
        if best is None:
            best, best_cy = pts, cy
    return best, best_cy


def convert(canvas_name, canvas, extras=None, skip_text_ids=None):
    global SEED, INDEX_N
    SEED = {"人物关系": 44000, "知识图谱": 46000, "全书线索": 48000}[canvas_name]
    INDEX_N = 0
    nodes = canvas.get("nodes", [])
    edges = canvas.get("edges", [])
    skip_t = set(skip_text_ids or [])
    prefers = PREFER.get(canvas_name, {})
    elements, card = [], {}
    files = {n["id"]: n for n in nodes if n["type"] == "file"}

    for n in nodes:
        if n["type"] != "group":
            continue
        color = n.get("color")
        elements.append(base_el(
            "g" + n["id"], "rectangle", n["x"], n["y"], n["width"], n["height"],
            stroke=STROKE.get(color, "#868e96"), fill=FILL.get(color, "#f1f3f5"),
            fill_style="hachure", sw=2, roughness=1, roundness={"type": 3},
        ))
        if n.get("label"):
            elements.append(make_text(
                "gl" + n["id"], n["x"] + 16, n["y"] + 12, n["label"],
                font_size=20, color=STROKE.get(color, "#495057")))

    for item in extras or []:
        elements.extend(item if isinstance(item, list) else [item])

    for n in nodes:
        if n["type"] != "file":
            continue
        color = n.get("color")
        name = note_name(n["file"])
        label = display_name(canvas_name, n["file"])
        gid = ["k" + n["id"]]
        rect = base_el(
            "c" + n["id"], "rectangle", n["x"], n["y"], n["width"], n["height"],
            stroke=STROKE.get(color, "#1e1e1e"), fill=FILL.get(color, "#ffffff"),
            fill_style="solid", sw=1.5, roughness=1, roundness={"type": 3},
            link="[[" + name + "]]", group_ids=gid,
        )
        tw, th = text_width(label, 16) + 8, 16 * 1.35
        txt = make_text(
            "t" + n["id"], n["x"] + (n["width"] - tw) / 2.0,
            n["y"] + (n["height"] - th) / 2.0, label, font_size=16,
            align="center", w=tw, h=th, locked=True, group_ids=gid,
        )
        elements.extend([rect, txt])
        card[n["id"]] = {
            "id": n["id"], "x": n["x"], "y": n["y"],
            "width": n["width"], "height": n["height"], "file": n["file"],
        }

    for n in nodes:
        if n["type"] != "text" or n["id"] in skip_t:
            continue
        body = re.sub(r"^#+\s*", "", (n.get("text") or "").replace("\r\n", "\n").strip(), flags=re.M)
        elements.append(make_text("x" + n["id"], n["x"], n["y"], body, font_size=18, w=n["width"], h=n["height"]))

    leftover = []
    used_cy = []
    for e in edges:
        src_n, dst_n = card.get(e["fromNode"]), card.get(e["toNode"])
        if not src_n or not dst_n:
            continue
        key = (e["fromNode"], e["toNode"])
        pts, cy = route_edge(src_n, dst_n, e.get("fromSide"), e.get("toSide"),
                             files, prefers.get(key), used_cy)
        if cy is not None:
            used_cy.append(cy)
        x0, y0 = pts[0]
        rel = [[p[0] - x0, p[1] - y0] for p in pts]
        color = STROKE.get(e.get("color"), "#495057")
        max_x = max(abs(p[0]) for p in rel) or 1
        max_y = max(abs(p[1]) for p in rel) or 1
        arrow = base_el("a" + e["id"], "arrow", x0, y0, max_x, max_y,
                        stroke=color, fill="transparent", sw=2, roughness=1,
                        roundness=None if len(pts) > 2 else {"type": 2})
        arrow.update({
            "points": rel, "lastCommittedPoint": None,
            "startBinding": None, "endBinding": None,
            "startArrowhead": None, "endArrowhead": "arrow",
            "elbowed": len(pts) > 2,
        })
        elements.append(arrow)
        if e.get("label"):
            if len(pts) >= 4:
                mx = (pts[1][0] + pts[2][0]) / 2.0
                my = pts[1][1] - 22
            else:
                mx = (pts[0][0] + pts[-1][0]) / 2.0
                my = (pts[0][1] + pts[-1][1]) / 2.0 - 22
            lw = text_width(e["label"], 14) + 10
            elements.append(make_text(
                "l" + e["id"], mx - lw / 2.0, my, e["label"], font_size=14, color=color))
        hit = polyline_blockers(pts, files, {e["fromNode"], e["toNode"]})
        if hit:
            leftover.append((e.get("label") or e["id"],
                             note_name(src_n["file"]), note_name(dst_n["file"]), hit))

    scene = {
        "type": "excalidraw", "version": 2,
        "source": "https://github.com/zsviczian/obsidian-excalidraw-plugin/releases/tag/2.26.4",
        "elements": elements,
        "appState": {"gridSize": 20, "viewBackgroundColor": "#fffef7"},
        "files": {},
    }
    with open(os.path.join(DIR, canvas_name + ".excalidraw"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(scene, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print("drew", canvas_name, "covers", len(leftover))
    for row in leftover:
        print("  LINE", row[1], "->", row[2], "[" + row[0] + "]", "covers", ", ".join(row[3]))
    return leftover


if __name__ == "__main__":
    leftover = []
    print("==== 人物关系")
    ppl = spread_inside(load("人物关系"), "人物关系")
    save("人物关系", ppl)
    leftover += convert("人物关系", ppl, extras=[
        extra_text("T2", -20, min(n["y"] for n in ppl["nodes"] if n["type"] == "file") - 80,
                   "人物关系", 28, "#1e1e1e"),
        extra_text("L2", 220, min(n["y"] for n in ppl["nodes"] if n["type"] == "file") - 74,
                   "橙师承　红对打　绿合题　紫叫醒", 16),
    ])
    print("==== 知识图谱")
    kg = spread_inside(load("知识图谱"), "知识图谱", explicit=KG_MEMBERS)
    save("知识图谱", kg)
    leftover += convert("知识图谱", kg, skip_text_ids={"000000000000005c"}, extras=[
        extra_text("T3", -40, min(n["y"] for n in kg["nodes"] if n["type"] == "file") - 40,
                   "概念知识图谱（精选）", 28, "#1e1e1e"),
    ])
    print("==== 全书线索")
    clue = patch_clue(load("全书线索"))
    save("全书线索", clue)
    leftover += convert("全书线索", clue, skip_text_ids={"00000000000000a7"}, extras=[
        extra_text("T1", 0, min(n["y"] for n in clue["nodes"] if n["type"] == "file") - 90,
                   "全书线索", 28, "#1e1e1e"),
    ] + clue_era_boxes(clue))
    print("TOTAL leftover", len(leftover))
