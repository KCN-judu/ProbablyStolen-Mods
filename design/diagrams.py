"""Renders the documentation diagrams in the mod cover style (DESIGN.md, Diagrams), in English and Chinese.

    python design/diagrams.py design/out/diagrams
    python design/diagrams.py ../ProbablyStolen-BetterKeyBindings/BetterKeyBindings/doc/attachments

Each diagram is drawn on a 400 px wide logical canvas, as tall as its content, and scaled x2 with nearest-neighbour.
English is set in the cover alphabet, Chinese in Cubic 11, as on the video slides. The English file is <id>.png and
the Chinese one <id>.zh_CN.png, the names the documentation links to.
"""
import os
import sys
from PIL import Image

import covers as C
import slides as S

W, SCALE = 400, 2
MARGIN = 8
PAD = 6
# Line pitch inside a plate, per language: the cover alphabet is 7 px tall, Cubic 11 is 11 px.
PITCH = {"en": 11, "zh": 14}
GLYPH = {"en": 7, "zh": 11}


class Canvas(C.Canvas):
    """A cover canvas of any height."""

    def __init__(self, h):
        self.w, self.h = W, h
        self.img = Image.new("RGB", (W, h), C.BG0)
        self.px = self.img.load()

    def put(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            self.px[x, y] = c


def width(lang, s):
    return S.width(lang, s, 1)


def text(cv, lang, x, y, s, color):
    # Chinese glyphs sit 2 px lower in their 11 px line than the cover alphabet in its 7 px one; centre both.
    S.draw_text(cv, lang, x, y, s, color, 1)


def fits(lang, s, room, where):
    w = width(lang, s)
    if w > room:
        sys.exit(f"{where}: '{s}' is {w} px wide; there are {room}")


def box(cv, lang, x, y, w, lines, kind="plate", where=""):
    """A plate (or slot) holding lines of (text, colour). Returns its height."""
    h = 2 * PAD + (len(lines) - 1) * PITCH[lang] + GLYPH[lang]
    if kind == "plate":
        cv.plate(x, y, w, h, rivets=False)
    elif kind == "slot":
        cv.slot(x, y, w, h)
    elif kind == "lit":
        cv.plate(x, y, w, h, rivets=False)
        cv.vline(x + 1, y + 1, h - 2, C.AMBER)
        cv.vline(x + 2, y + 1, h - 2, C.AMBER)
    for i, (s, color) in enumerate(lines):
        fits(lang, s, w - 2 * PAD - (3 if kind == "lit" else 0), where)
        text(cv, lang, x + PAD + (3 if kind == "lit" else 0), y + PAD + i * PITCH[lang], s, color)
    return h


def title(cv, lang, s):
    h = 2 * PAD + GLYPH[lang]
    cv.plate(MARGIN, MARGIN, W - 2 * MARGIN, h)
    cv.rect(MARGIN + 1, MARGIN + 1, 3, h - 2, C.AMBER)
    fits(lang, s, W - 2 * MARGIN - 2 * PAD - 6, "title")
    text(cv, lang, MARGIN + PAD + 6, MARGIN + PAD, s, C.AMBER)
    return MARGIN + h


def arrow_down(cv, x, y0, y1, color):
    cv.vline(x, y0, y1 - y0 - 3, color)
    for i in range(3):
        cv.hline(x - 2 + i, y1 - 3 + i, 5 - 2 * i, color)


def arrow_right(cv, x0, x1, y, color):
    cv.hline(x0, y, x1 - x0 - 3, color)
    for i in range(3):
        cv.vline(x1 - 3 + i, y - 2 + i, 5 - 2 * i, color)


def blocked(cv, x0, x1, y):
    # A cut line: a dotted path ending in a red cross.
    for x in range(x0, x1 - 8, 2):
        cv.put(x, y, C.FAINT)
    cx = x1 - 5
    for i in range(5):
        cv.put(cx - 2 + i, y - 2 + i, C.RED)
        cv.put(cx + 2 - i, y - 2 + i, C.RED)


def label(cv, lang, x, y, s, color):
    text(cv, lang, x, y - GLYPH[lang] // 2, s, color)


def note_lines(cv, lang, y, lines):
    for s in lines:
        fits(lang, s, W - 2 * MARGIN, "note")
        text(cv, lang, MARGIN, y, s, C.MUTED)
        y += PITCH[lang]
    return y


# ---------------------------------------------------------------- binding capture

CAPTURE = {
    "en": {
        "title": "WHILE A BINDING WAITS FOR A KEY",
        "inputs": ["KEYS", "MOUSE BUTTONS", "WHEEL"],
        "gate": [("THE MOD'S GATE", C.AMBER), ("EVERY PRESS", C.CREAM_DIM), ("GOES ONE WAY", C.CREAM_DIM)],
        "binding": [("THE BINDING", C.CREAM), ("TAKES IT", C.AMBER), ("CTRL + E", C.AMBER)],
        "others": ["THE GAME", "OPTIONS WINDOW", "OTHER MODS"],
        "notes": ["NOBODY ELSE SEES THE PRESS, THE KEY HELD,",
                  "OR ITS RELEASE, EVEN AFTER THE BINDING IS SET.",
                  "KEYS DOWN BEFORE THE WAIT BEGAN STAY WITH",
                  "WHOEVER SAW THEM GO DOWN."],
    },
    "zh": {
        "title": "绑定等待按键时",
        "inputs": ["按键", "鼠标按键", "滚轮"],
        "gate": [("模组的输入闸门", C.AMBER), ("每次按下", C.CREAM_DIM), ("只走一条路", C.CREAM_DIM)],
        "binding": [("正在设置的绑定", C.CREAM), ("独占这次输入", C.AMBER), ("Ctrl + E", C.AMBER)],
        "others": ["游戏", "选项窗口", "其他模组"],
        "notes": ["其他读取方看不到这次按下、按住和松开，",
                  "即使松开发生在绑定确定之后。",
                  "等待开始前就按住的键不受影响，",
                  "仍交给看到它按下的读取方。"],
    },
}


def capture(cv, lang):
    t = CAPTURE[lang]
    y0 = title(cv, lang, t["title"]) + 16
    # Inputs on the left, the gate in the middle, who gets the press on the right.
    ix, iw = MARGIN, 116
    gx, gw = 144, 110
    rx, rw = 274, W - MARGIN - 274
    heights, ys = [], []
    y = y0
    for s in t["inputs"]:
        ys.append(y)
        heights.append(box(cv, lang, ix, y, iw, [(s, C.CREAM)], "slot", "input"))
        y += heights[-1] + 8
    inputs_bottom = y - 8
    gh = 2 * PAD + 2 * PITCH[lang] + GLYPH[lang]
    gy = y0 + (inputs_bottom - y0 - gh) // 2
    gmid = gy + gh // 2
    box(cv, lang, gx, gy, gw, t["gate"], "lit", "gate")
    # Every input joins one line into the gate.
    bus = gx - 8
    mids = [y + h // 2 for y, h in zip(ys, heights)]
    for m in mids:
        cv.hline(ix + iw + 2, m, bus - ix - iw - 2, C.MUTED)
    cv.vline(bus, mids[0], mids[-1] - mids[0] + 1, C.MUTED)
    arrow_right(cv, bus, gx - 2, gmid, C.MUTED)
    # Out of the gate, one way leads to the binding being set; every other one is cut.
    out = gx + gw + 8
    cv.hline(gx + gw + 2, gmid, out - gx - gw - 1, C.AMBER)
    by = y0
    bh = box(cv, lang, rx, by, rw, t["binding"], "lit", "binding")
    bmid = by + bh // 2
    cv.vline(out, bmid, gmid - bmid + 1, C.AMBER)
    arrow_right(cv, out, rx - 2, bmid, C.AMBER)
    y = by + bh + 10
    last = gmid
    for s in t["others"]:
        h = box(cv, lang, rx, y, rw, [(s, C.FAINT)], "slot", "others")
        blocked(cv, out + 2, rx - 2, y + h // 2)
        last = y + h // 2
        y += h + 6
    for yy in range(gmid + 2, last + 1, 2):
        cv.put(out, yy, C.FAINT)
    y = max(y, inputs_bottom) + 12
    return note_lines(cv, lang, y, t["notes"]) + MARGIN


# ---------------------------------------------------------------- deciding a press in play

PRESS = {
    "en": {
        "title": "WHEN A KEY GOES DOWN IN PLAY",
        "start": [("A KEY, MOUSE BUTTON OR NOTCH", C.CREAM), ("WITH THE MODIFIERS HELD", C.CREAM_DIM)],
        "step1": [("1  ONLY BINDINGS THAT APPLY HERE", C.CREAM), ("ROTATE, FLIP AND RESET:", C.MUTED),
                  ("ONLY WHILE AN ITEM IS DRAGGED", C.MUTED)],
        "step2": [("2  ONE WITH EXACTLY", C.CREAM), ("THOSE MODIFIERS?", C.CREAM)],
        "step3": [("3  DROP MODIFIERS: THE ONES", C.CREAM), ("KEEPING THE MOST OF THEM?", C.CREAM),
                  ("A TIE: ALL OF THEM", C.MUTED)],
        "game": [("NONE: THE GAME GETS IT", C.TEAL), ("UNTOUCHED, BY ITS OWN RULES.", C.CREAM_DIM),
                 ("THE WHEEL SCROLLS AS USUAL.", C.CREAM_DIM)],
        "result": [("THOSE BINDINGS", C.AMBER), ("TRIGGER", C.AMBER), ("", C.CREAM), ("NOBODY ELSE", C.CREAM_DIM),
                   ("SEES THE PRESS.", C.CREAM_DIM), ("A NOTCH DOES", C.CREAM_DIM), ("NOT SCROLL.", C.CREAM_DIM)],
        "yes": "YES", "no": "NO",
        "notes": ["DECIDED ONCE, AS THE KEY GOES DOWN. THE PRESS",
                  "STAYS WITH THE SAME BINDINGS UNTIL IT IS",
                  "RELEASED, EVEN IF A MODIFIER IS LET GO FIRST."],
    },
    "zh": {
        "title": "游戏中按下按键时",
        "start": [("按键、鼠标按键或滚轮的一格", C.CREAM), ("以及当时按住的修饰键", C.CREAM_DIM)],
        "step1": [("1 只看当前场景适用的绑定", C.CREAM), ("旋转、翻转、复位：", C.MUTED),
                  ("只在拖动物品时适用", C.MUTED)],
        "step2": [("2 有修饰键完全一致的", C.CREAM), ("绑定吗？", C.CREAM)],
        "step3": [("3 去掉修饰键：找保留得", C.CREAM), ("最多的绑定？", C.CREAM),
                  ("一样多时：全部", C.MUTED)],
        "game": [("都没有：交给游戏", C.TEAL), ("原样交还，按游戏的规则处理。", C.CREAM_DIM),
                 ("滚轮照常滚动。", C.CREAM_DIM)],
        "result": [("这些绑定", C.AMBER), ("触发", C.AMBER), ("", C.CREAM), ("其他读取方", C.CREAM_DIM),
                   ("看不到这次", C.CREAM_DIM), ("按下；滚轮的", C.CREAM_DIM), ("这一格不滚动。", C.CREAM_DIM)],
        "yes": "是", "no": "否",
        "notes": ["只在按下时判定一次。直到松开为止，这次按下",
                  "都归同一组绑定，即使先松开了修饰键。"],
    },
}


def press(cv, lang):
    t = PRESS[lang]
    y = title(cv, lang, t["title"]) + 16
    lx, lw = MARGIN, 236
    rx, rw = 274, W - MARGIN - 274
    mid = lx + lw // 2
    h = box(cv, lang, lx, y, lw, t["start"], "slot", "start")
    arrow_down(cv, mid, y + h + 2, y + h + 12, C.MUTED)
    y += h + 14
    h = box(cv, lang, lx, y, lw, t["step1"], "plate", "step 1")
    arrow_down(cv, mid, y + h + 2, y + h + 12, C.MUTED)
    y += h + 14
    y2 = y
    h2 = box(cv, lang, lx, y, lw, t["step2"], "plate", "step 2")
    arrow_down(cv, mid, y + h2 + 2, y + h2 + 16, C.MUTED)
    label(cv, lang, mid + 6, y + h2 + 9, t["no"], C.MUTED)
    y += h2 + 18
    y3 = y
    h3 = box(cv, lang, lx, y, lw, t["step3"], "plate", "step 3")
    arrow_down(cv, mid, y + h3 + 2, y + h3 + 16, C.MUTED)
    label(cv, lang, mid + 6, y + h3 + 9, t["no"], C.MUTED)
    y += h3 + 18
    hg = box(cv, lang, lx, y, lw, t["game"], "slot", "game")
    bottom = y + hg
    # The result spans the two questions that can answer yes.
    rh = 2 * PAD + (len(t["result"]) - 1) * PITCH[lang] + GLYPH[lang]
    ry = max(y2, (y2 + y3 + h3) // 2 - rh // 2)
    box(cv, lang, rx, ry, rw, t["result"], "lit", "result")
    for yy, hh in ((y2, h2), (y3, h3)):
        ay = yy + hh // 2
        arrow_right(cv, lx + lw + 2, rx - 2, ay, C.AMBER)
        label(cv, lang, lx + lw + 6, ay - 7, t["yes"], C.AMBER)
    y = max(bottom, ry + rh) + 12
    return note_lines(cv, lang, y, t["notes"]) + MARGIN


DIAGRAMS = {"binding-capture": capture, "press-decision": press}


def render(draw, lang):
    cv = Canvas(1000)
    h = draw(cv, lang)
    cv.img = cv.img.crop((0, 0, W, h))
    return cv.img.resize((W * SCALE, h * SCALE), Image.NEAREST)


def main(argv):
    """python design/diagrams.py [out]"""
    out = argv[0] if argv else os.path.join(os.path.dirname(os.path.abspath(__file__)), "out", "diagrams")
    os.makedirs(out, exist_ok=True)
    for name, draw in DIAGRAMS.items():
        for lang, suffix in (("en", ""), ("zh", ".zh_CN")):
            img = render(draw, lang)
            path = os.path.join(out, name + suffix + ".png")
            img.save(path, optimize=True)
            print(path, "%dx%d" % img.size)


if __name__ == "__main__":
    main(sys.argv[1:])
