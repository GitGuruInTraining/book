# -*- coding: utf-8 -*-
"""Reroute covered edges on canvases, then rebuild raw .excalidraw files."""
from __future__ import print_function
import json
import os
import re

DIR = os.path.dirname(os.path.abspath(__file__))

# from -> to : (fromSide, toSide)
REROUTE = {
    "人物关系": {
        ("0000000000000007", "0000000000000015"): ("bottom", "bottom"),  # 赫拉克利特 → 巴门尼德
        ("000000000000001c", "000000000000001e"): ("top", "top"),        # 普罗泰戈拉 → 苏格拉底
        ("000000000000001d", "0000000000000029"): ("bottom", "top"),     # 高尔吉亚 → 皮浪
        ("000000000000001f", "000000000000002a"): ("bottom", "left"),    # 柏拉图 → 普罗提诺
        ("0000000000000020", "0000000000000031"): ("bottom", "bottom"),  # 亚里士多德 → 托马斯
        ("0000000000000041", "0000000000000039"): ("top", "top"),        # 笛卡尔 → 洛克
        ("0000000000000039", "0000000000000048"): ("top", "top"),        # 洛克 → 伏尔泰
        ("0000000000000048", "000000000000004a"): ("top", "top"),        # 伏尔泰 → 卢梭
        ("000000000000004a", "0000000000000050"): ("bottom", "bottom"),  # 卢梭 → 康德
    },
    "知识图谱": {
        ("000000000000005e", "000000000000006c"): ("top", "top"),        # 本原 → 形而上学
        ("000000000000007a", "000000000000007d"): ("bottom", "bottom"),  # 白板说 → 存在就是被感知
        ("000000000000007f", "000000000000007c"): ("top", "top"),        # 思维与存在 → 我思
        ("000000000000007e", "0000000000000088"): ("top", "top"),        # 印象与观念 → 先天综合判断
        ("000000000000007c", "0000000000000088"): ("top", "top"),        # 我思 → 先天综合判断
        ("0000000000000088", "000000000000008a"): ("top", "top"),        # 先天综合判断 → 范畴
        ("0000000000000092", "0000000000000094"): ("top", "top"),        # 绝对命令 → 绝对自我
        ("0000000000000096", "0000000000000098"): ("top", "top"),        # 绝对精神 → 密涅瓦
        ("00000000000000e1", "000000000000006e"): ("bottom", "bottom"),  # 逻各斯 → 存在
        ("00000000000000e1", "00000000000000e2"): ("top", "top"),        # 逻各斯 → 辩证法
    },
    "全书线索": {
        ("00000000000000b0", "00000000000000b3"): ("bottom", "top"),     # 08 → 康德
        ("00000000000000b1", "00000000000000b3"): ("bottom", "top"),     # 09 → 康德
        ("00000000000000b2", "00000000000000b3"): ("bottom", "top"),     # 10 → 康德
    },
}

DROP_EDGES = {
    "全书线索": {"00000000000000bc"},  # 06 → 07 斜穿
}

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
SEED = 9000
INDEX_N = 0


def load(name):
    with open(os.path.join(DIR, name + ".canvas"), "r", encoding="utf-8") as f:
        return json.load(f)


def save(name, data):
    with open(os.path.join(DIR, name + ".canvas"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, ensure_ascii=False, indent="\t")
        f.write("\n")


def patch_canvas(name):
    data = load(name)
    routes = REROUTE.get(name, {})
    drop = DROP_EDGES.get(name, set())
    data["edges"] = [e for e in data.get("edges", []) if e["id"] not in drop]
    for e in data["edges"]:
        key = (e["fromNode"], e["toNode"])
        if key in routes:
            e["fromSide"], e["toSide"] = routes[key]
    if name == "全书线索":
        # 康德一排单独放下，经验／理性／启蒙从上方进来
        by = {n["id"]: n for n in data["nodes"]}
        row3 = 929
        for nid in ("00000000000000b3", "00000000000000b4", "00000000000000b5"):
            by[nid]["y"] = row3
            by[nid]["color"] = "6"
    save(name, data)
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


def attach(rect, kind, eid):
    rect.setdefault("boundElements", []).append({"id": eid, "type": kind})


def side_pt(node, side):
    x, y, w, h = node["x"], node["y"], node["width"], node["height"]
    return {
        "left": (x, y + h / 2.0), "right": (x + w, y + h / 2.0),
        "top": (x + w / 2.0, y), "bottom": (x + w / 2.0, y + h),
    }.get(side or "right", (x + w, y + h / 2.0))


def note_name(path):
    return os.path.splitext(os.path.basename(path.replace("\\", "/")))[0]


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
        pad, top = 36, 56
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
        extra_text("D1", n06["x"] + 8, n06["y"] + n06["height"] + 16, "↓ 转入中世纪", 16, "#1971c2"),
    ]


def convert(canvas_name, canvas, extras=None, skip_text_ids=None):
    global SEED, INDEX_N
    SEED = abs(hash(canvas_name + "route")) % 8000 + 9000
    INDEX_N = 0
    nodes = canvas.get("nodes", [])
    edges = canvas.get("edges", [])
    skip_t = set(skip_text_ids or [])
    elements, card = [], {}

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
        rid, tid = "c" + n["id"], "t" + n["id"]
        rect = base_el(
            rid, "rectangle", n["x"], n["y"], n["width"], n["height"],
            stroke=STROKE.get(color, "#1e1e1e"), fill=FILL.get(color, "#ffffff"),
            fill_style="solid", sw=1.5, roughness=1, roundness={"type": 3},
            link="[[" + name + "]]", group_ids=gid,
        )
        tw, th = text_width(label, 16) + 8, 16 * 1.35
        txt = make_text(
            tid, n["x"] + (n["width"] - tw) / 2.0,
            n["y"] + (n["height"] - th) / 2.0, label, font_size=16,
            align="center", w=tw, h=th, locked=True, group_ids=gid,
        )
        elements.extend([rect, txt])
        card[n["id"]] = {"id": rid, "el": rect, "x": n["x"], "y": n["y"],
                         "width": n["width"], "height": n["height"]}

    for n in nodes:
        if n["type"] != "text" or n["id"] in skip_t:
            continue
        body = re.sub(r"^#+\s*", "", (n.get("text") or "").replace("\r\n", "\n").strip(), flags=re.M)
        elements.append(make_text("x" + n["id"], n["x"], n["y"], body, font_size=18, w=n["width"], h=n["height"]))

    for e in edges:
        src_n, dst_n = card.get(e["fromNode"]), card.get(e["toNode"])
        if not src_n or not dst_n:
            continue
        x1, y1 = side_pt(src_n, e.get("fromSide"))
        x2, y2 = side_pt(dst_n, e.get("toSide"))
        aid = "a" + e["id"]
        color = STROKE.get(e.get("color"), "#495057")
        arrow = base_el(aid, "arrow", x1, y1, max(abs(x2 - x1), 1), max(abs(y2 - y1), 1),
                        stroke=color, fill="transparent", sw=2, roughness=1, roundness={"type": 2})
        arrow.update({
            "points": [[0, 0], [x2 - x1, y2 - y1]], "lastCommittedPoint": None,
            "startBinding": {"elementId": src_n["id"], "focus": 0, "gap": 6},
            "endBinding": {"elementId": dst_n["id"], "focus": 0, "gap": 6},
            "startArrowhead": None, "endArrowhead": "arrow", "elbowed": False,
        })
        attach(src_n["el"], "arrow", aid)
        attach(dst_n["el"], "arrow", aid)
        elements.append(arrow)
        if e.get("label"):
            lw = text_width(e["label"], 14) + 10
            elements.append(make_text(
                "l" + e["id"], (x1 + x2) / 2.0 - lw / 2.0, (y1 + y2) / 2.0 - 22,
                e["label"], font_size=14, color=color))

    scene = {
        "type": "excalidraw", "version": 2,
        "source": "https://github.com/zsviczian/obsidian-excalidraw-plugin/releases/tag/2.26.4",
        "elements": elements,
        "appState": {"gridSize": 20, "viewBackgroundColor": "#fffef7"},
        "files": {},
    }
    out = os.path.join(DIR, canvas_name + ".excalidraw")
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        json.dump(scene, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print("drew", canvas_name)


if __name__ == "__main__":
    ppl = patch_canvas("人物关系")
    kg = patch_canvas("知识图谱")
    clue = patch_canvas("全书线索")
    convert("人物关系", ppl, extras=[
        extra_text("T2", -20, min(n["y"] for n in ppl["nodes"]) - 80, "人物关系", 28, "#1e1e1e"),
        extra_text("L2", 220, min(n["y"] for n in ppl["nodes"]) - 74, "橙师承　红对打　绿合题　紫叫醒", 16),
    ])
    convert("知识图谱", kg, skip_text_ids={"000000000000005c"}, extras=[
        extra_text("T3", -40, min(n["y"] for n in kg["nodes"]) - 40, "概念知识图谱（精选）", 28, "#1e1e1e"),
    ])
    convert("全书线索", clue, skip_text_ids={"00000000000000a7"}, extras=[
        extra_text("T1", 0, min(n["y"] for n in clue["nodes"] if n["type"] == "file") - 90, "全书线索", 28, "#1e1e1e"),
    ] + clue_era_boxes(clue))
