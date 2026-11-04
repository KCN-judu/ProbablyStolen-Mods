"""Renders the documentation diagrams in the mod cover style (DESIGN.md, Diagrams), in English and Chinese.

    python design/diagrams.py design/out/diagrams
    python design/diagrams.py ../ProbablyStolen-BetterKeyBindings/BetterKeyBindings/doc/attachments

Each diagram is drawn on a 400 px wide logical canvas, as tall as its content, and scaled x2 with nearest-neighbour.
English is set in the cover alphabet, Chinese in Cubic 11, as on the video slides. The English file is <id>.png and
the Chinese one <id>.zh_CN.png, the names the documentation links to.
"""
import os
import sys
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from types import MappingProxyType
from typing import Final, Literal, TypeAlias

from PIL import Image

import covers as C
import slides as S
from slides import Lang
from typed import split_ids, take_option

W: Final = 400
SCALE: Final = 2
MARGIN: Final = 8
PAD: Final = 6
# Line pitch inside a plate, per language: the cover alphabet is 7 px tall, Cubic 11 is 11 px.
PITCH: Final[Mapping[Lang, int]] = MappingProxyType({"en": 11, "zh": 14})
GLYPH: Final[Mapping[Lang, int]] = MappingProxyType({"en": 7, "zh": 11})

Line: TypeAlias = tuple[str, C.Color]
Lines: TypeAlias = Sequence[Line]
BoxKind: TypeAlias = Literal["plate", "slot", "planned", "lit"]
Diagram: TypeAlias = Callable[[C.Canvas, Lang], int]


# Text width in px for the language's face (the cover alphabet for English, Cubic 11 for Chinese); see slides.width.
def width(lang: Lang, s: str) -> int:
    return S.width(lang, s, 1)


def text(cv: C.Canvas, lang: Lang, x: int, y: int, s: str, color: C.Color) -> None:
    # Chinese glyphs sit 2 px lower in their 11 px line than the cover alphabet in its 7 px one; centre both.
    S.draw_text(cv, lang, x, y, s, color, 1)


# Fails the render instead of letting text run over its box: layout is fixed pixels, so an overflow must be fixed in the wording.
def fits(lang: Lang, s: str, room: int, where: str) -> None:
    w = width(lang, s)
    if w > room:
        raise SystemExit(f"{where}: '{s}' is {w} px wide; there are {room}")


def dotted_frame(cv: C.Canvas, x: int, y: int, w: int, h: int, color: C.Color) -> None:
    for i in range(0, w, 2):
        cv.put(x + i, y, color); cv.put(x + i, y + h - 1, color)
    for j in range(0, h, 2):
        cv.put(x, y + j, color); cv.put(x + w - 1, y + j, color)


# Height of a box holding n lines, from the language's line pitch.
def box_height(lang: Lang, n_lines: int) -> int:
    return 2 * PAD + (n_lines - 1) * PITCH[lang] + GLYPH[lang]


def box(cv: C.Canvas, lang: Lang, x: int, y: int, w: int, lines: Lines, kind: BoxKind = "plate", where: str = "",
        accent: C.Color = C.AMBER) -> int:
    """A plate (or slot) holding lines of (text, colour). Returns its height.

    kind "planned" is a dotted outline on the ground: something designed but not built yet."""
    h = box_height(lang, len(lines))
    if kind == "plate":
        cv.plate(x, y, w, h, rivets=False)
    elif kind == "slot":
        cv.slot(x, y, w, h)
    elif kind == "planned":
        dotted_frame(cv, x, y, w, h, C.FAINT)
    elif kind == "lit":
        cv.plate(x, y, w, h, rivets=False)
        cv.vline(x + 1, y + 1, h - 2, accent)
        cv.vline(x + 2, y + 1, h - 2, accent)
    for i, (s, color) in enumerate(lines):
        fits(lang, s, w - 2 * PAD - (3 if kind == "lit" else 0), where)
        text(cv, lang, x + PAD + (3 if kind == "lit" else 0), y + PAD + i * PITCH[lang], s, color)
    return h


# The title plate across the top; returns the y where content may start.
def title(cv: C.Canvas, lang: Lang, s: str, accent: C.Color = C.AMBER) -> int:
    h = 2 * PAD + GLYPH[lang]
    cv.plate(MARGIN, MARGIN, W - 2 * MARGIN, h)
    cv.rect(MARGIN + 1, MARGIN + 1, 3, h - 2, accent)
    fits(lang, s, W - 2 * MARGIN - 2 * PAD - 6, "title")
    text(cv, lang, MARGIN + PAD + 6, MARGIN + PAD, s, accent)
    return MARGIN + h


def arrow_down(cv: C.Canvas, x: int, y0: int, y1: int, color: C.Color, dotted: bool = False) -> None:
    # A dotted arrow is a way that is planned but not built; unlike a cut line it keeps its head.
    for y in range(y0, y1 - 3):
        if not dotted or (y - y0) % 2 == 0:
            cv.put(x, y, color)
    for i in range(3):
        cv.hline(x - 2 + i, y1 - 3 + i, 5 - 2 * i, color)


# Same as arrow_down, pointing right.
def arrow_right(cv: C.Canvas, x0: int, x1: int, y: int, color: C.Color, dotted: bool = False) -> None:
    for x in range(x0, x1 - 3):
        if not dotted or (x - x0) % 2 == 0:
            cv.put(x, y, color)
    for i in range(3):
        cv.vline(x1 - 3 + i, y - 2 + i, 5 - 2 * i, color)


def blocked(cv: C.Canvas, x0: int, x1: int, y: int) -> None:
    # A cut line: a dotted path ending in a red cross.
    for x in range(x0, x1 - 8, 2):
        cv.put(x, y, C.FAINT)
    cx = x1 - 5
    for i in range(5):
        cv.put(cx - 2 + i, y - 2 + i, C.RED)
        cv.put(cx + 2 - i, y - 2 + i, C.RED)


def label(cv: C.Canvas, lang: Lang, x: int, y: int, s: str, color: C.Color) -> None:
    text(cv, lang, x, y - GLYPH[lang] // 2, s, color)


# Muted explanatory lines under a diagram; returns the next free y.
def note_lines(cv: C.Canvas, lang: Lang, y: int, lines: Sequence[str]) -> int:
    for s in lines:
        fits(lang, s, W - 2 * MARGIN, "note")
        text(cv, lang, MARGIN, y, s, C.MUTED)
        y += PITCH[lang]
    return y


# ---------------------------------------------------------------- binding capture

@dataclass(frozen=True)
class CaptureText:
    title: str
    inputs: Sequence[str]
    gate: Lines
    binding: Lines
    others: Sequence[str]
    notes: Sequence[str]


CAPTURE: Final[Mapping[Lang, CaptureText]] = MappingProxyType({
    "en": CaptureText(
        title="WHILE A BINDING WAITS FOR A KEY",
        inputs=["KEYS", "MOUSE BUTTONS", "WHEEL"],
        gate=[("THE MOD'S GATE", C.AMBER), ("EVERY PRESS", C.CREAM_DIM), ("GOES ONE WAY", C.CREAM_DIM)],
        binding=[("THE BINDING", C.CREAM), ("TAKES IT", C.AMBER), ("CTRL + E", C.AMBER)],
        others=["THE GAME", "OPTIONS WINDOW", "OTHER MODS"],
        notes=["NOBODY ELSE SEES THE PRESS, THE KEY HELD,",
                  "OR ITS RELEASE, EVEN AFTER THE BINDING IS SET.",
                  "KEYS DOWN BEFORE THE WAIT BEGAN STAY WITH",
                  "WHOEVER SAW THEM GO DOWN."],
    ),
    "zh": CaptureText(
        title="绑定等待按键时",
        inputs=["按键", "鼠标按键", "滚轮"],
        gate=[("模组的输入闸门", C.AMBER), ("每次按下", C.CREAM_DIM), ("只走一条路", C.CREAM_DIM)],
        binding=[("正在设置的绑定", C.CREAM), ("独占这次输入", C.AMBER), ("Ctrl + E", C.AMBER)],
        others=["游戏", "选项窗口", "其他模组"],
        notes=["其他读取方看不到这次按下、按住和松开，",
                  "即使松开发生在绑定确定之后。",
                  "等待开始前就按住的键不受影响，",
                  "仍交给看到它按下的读取方。"],
    ),
})


# Diagram of Better Key Bindings' input gate while a binding waits for a key: all inputs go through the gate, only the binding
# receives the press, every other reader is cut off.
def capture(cv: C.Canvas, lang: Lang) -> int:
    t = CAPTURE[lang]
    y0 = title(cv, lang, t.title) + 16
    # Inputs on the left, the gate in the middle, who gets the press on the right.
    ix, iw = MARGIN, 116
    gx, gw = 144, 110
    rx, rw = 274, W - MARGIN - 274
    heights = [box_height(lang, 1) for _ in t.inputs]
    ys = [y0 + i * (heights[0] + 8) for i in range(len(heights))]
    for s, iy in zip(t.inputs, ys):
        box(cv, lang, ix, iy, iw, [(s, C.CREAM)], "slot", "input")
    inputs_bottom = y0 + len(heights) * (heights[0] + 8) - 8
    gh = box_height(lang, 3)
    gy = y0 + (inputs_bottom - y0 - gh) // 2
    gmid = gy + gh // 2
    box(cv, lang, gx, gy, gw, t.gate, "lit", "gate")
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
    bh = box(cv, lang, rx, by, rw, t.binding, "lit", "binding")
    bmid = by + bh // 2
    cv.vline(out, bmid, gmid - bmid + 1, C.AMBER)
    arrow_right(cv, out, rx - 2, bmid, C.AMBER)
    y = by + bh + 10
    last = gmid
    for s in t.others:
        h = box(cv, lang, rx, y, rw, [(s, C.FAINT)], "slot", "others")
        blocked(cv, out + 2, rx - 2, y + h // 2)
        last = y + h // 2
        y += h + 6
    for yy in range(gmid + 2, last + 1, 2):
        cv.put(out, yy, C.FAINT)
    y = max(y, inputs_bottom) + 12
    return note_lines(cv, lang, y, t.notes) + MARGIN


# ---------------------------------------------------------------- deciding a press in play

@dataclass(frozen=True)
class PressText:
    title: str
    start: Lines
    step1: Lines
    step2: Lines
    step3: Lines
    game: Lines
    result: Lines
    yes: str
    no: str
    notes: Sequence[str]


PRESS: Final[Mapping[Lang, PressText]] = MappingProxyType({
    "en": PressText(
        title="WHEN A KEY GOES DOWN IN PLAY",
        start=[("A KEY, MOUSE BUTTON OR NOTCH", C.CREAM), ("WITH THE MODIFIERS HELD", C.CREAM_DIM)],
        step1=[("1  ONLY BINDINGS THAT APPLY HERE", C.CREAM), ("ROTATE, FLIP AND RESET:", C.MUTED),
                  ("ONLY WHILE AN ITEM IS DRAGGED", C.MUTED)],
        step2=[("2  ONE WITH EXACTLY", C.CREAM), ("THOSE MODIFIERS?", C.CREAM)],
        step3=[("3  DROP MODIFIERS: THE ONES", C.CREAM), ("KEEPING THE MOST OF THEM?", C.CREAM),
                  ("A TIE: ALL OF THEM", C.MUTED)],
        game=[("NONE: THE GAME GETS IT", C.TEAL), ("UNTOUCHED, BY ITS OWN RULES.", C.CREAM_DIM),
                 ("THE WHEEL SCROLLS AS USUAL.", C.CREAM_DIM)],
        result=[("THOSE BINDINGS", C.AMBER), ("TRIGGER", C.AMBER), ("", C.CREAM), ("NOBODY ELSE", C.CREAM_DIM),
                   ("SEES THE PRESS.", C.CREAM_DIM), ("A NOTCH DOES", C.CREAM_DIM), ("NOT SCROLL.", C.CREAM_DIM)],
        yes="YES", no="NO",
        notes=["DECIDED ONCE, AS THE KEY GOES DOWN. THE PRESS",
                  "STAYS WITH THE SAME BINDINGS UNTIL IT IS",
                  "RELEASED, EVEN IF A MODIFIER IS LET GO FIRST."],
    ),
    "zh": PressText(
        title="游戏中按下按键时",
        start=[("按键、鼠标按键或滚轮的一格", C.CREAM), ("以及当时按住的修饰键", C.CREAM_DIM)],
        step1=[("1 只看当前场景适用的绑定", C.CREAM), ("旋转、翻转、复位：", C.MUTED),
                  ("只在拖动物品时适用", C.MUTED)],
        step2=[("2 有修饰键完全一致的", C.CREAM), ("绑定吗？", C.CREAM)],
        step3=[("3 去掉修饰键：找保留得", C.CREAM), ("最多的绑定？", C.CREAM),
                  ("一样多时：全部", C.MUTED)],
        game=[("都没有：交给游戏", C.TEAL), ("原样交还，按游戏的规则处理。", C.CREAM_DIM),
                 ("滚轮照常滚动。", C.CREAM_DIM)],
        result=[("这些绑定", C.AMBER), ("触发", C.AMBER), ("", C.CREAM), ("其他读取方", C.CREAM_DIM),
                   ("看不到这次", C.CREAM_DIM), ("按下；滚轮的", C.CREAM_DIM), ("这一格不滚动。", C.CREAM_DIM)],
        yes="是", no="否",
        notes=["只在按下时判定一次。直到松开为止，这次按下",
                  "都归同一组绑定，即使先松开了修饰键。"],
    ),
})


# Diagram of how Better Key Bindings decides a press in play: which bindings apply, exact modifier match, then the closest
# match with fewer modifiers; two steps can answer yes and lead to the result, otherwise the game gets the press.
def press(cv: C.Canvas, lang: Lang) -> int:
    t = PRESS[lang]
    y = title(cv, lang, t.title) + 16
    lx, lw = MARGIN, 236
    rx, rw = 274, W - MARGIN - 274
    mid = lx + lw // 2
    h = box(cv, lang, lx, y, lw, t.start, "slot", "start")
    arrow_down(cv, mid, y + h + 2, y + h + 12, C.MUTED)
    y += h + 14
    h = box(cv, lang, lx, y, lw, t.step1, "plate", "step 1")
    arrow_down(cv, mid, y + h + 2, y + h + 12, C.MUTED)
    y += h + 14
    y2 = y
    h2 = box(cv, lang, lx, y, lw, t.step2, "plate", "step 2")
    arrow_down(cv, mid, y + h2 + 2, y + h2 + 16, C.MUTED)
    label(cv, lang, mid + 6, y + h2 + 9, t.no, C.MUTED)
    y += h2 + 18
    y3 = y
    h3 = box(cv, lang, lx, y, lw, t.step3, "plate", "step 3")
    arrow_down(cv, mid, y + h3 + 2, y + h3 + 16, C.MUTED)
    label(cv, lang, mid + 6, y + h3 + 9, t.no, C.MUTED)
    y += h3 + 18
    hg = box(cv, lang, lx, y, lw, t.game, "slot", "game")
    bottom = y + hg
    # The result spans the two questions that can answer yes.
    rh = box_height(lang, len(t.result))
    ry = max(y2, (y2 + y3 + h3) // 2 - rh // 2)
    box(cv, lang, rx, ry, rw, t.result, "lit", "result")
    for yy, hh in ((y2, h2), (y3, h3)):
        ay = yy + hh // 2
        arrow_right(cv, lx + lw + 2, rx - 2, ay, C.AMBER)
        label(cv, lang, lx + lw + 6, ay - 7, t.yes, C.AMBER)
    y = max(bottom, ry + rh) + 12
    return note_lines(cv, lang, y, t.notes) + MARGIN


# ---------------------------------------------------------------- texture packs: the whole design

@dataclass(frozen=True)
class ArchText:
    title: str
    game: str
    kit: str
    packs: Lines
    others: Lines
    step1: Lines
    step2: Lines
    step3: Lines
    step4: Lines
    atlas: Lines
    scene: Lines
    modspr: Lines
    gamefiles: Lines
    modfolders: Lines
    inventory: Lines
    schema: Lines
    catalog: Lines
    export: Lines
    builder: Lines
    pack: Lines
    notes: Sequence[str]


ARCH: Final[Mapping[Lang, ArchText]] = MappingProxyType({
    "en": ArchText(
        title="TEXTURE PACKS: HOW IT FITS TOGETHER",
        game="IN THE GAME", kit="CREATOR KIT",
        packs=[("PACK MODS", C.CREAM), ("TEXTURES/", C.MUTED)],
        others=[("OTHER MODS", C.CREAM), ("PICTURES", C.MUTED)],
        step1=[("1  THE GAME'S LOADER", C.CREAM), ("DECODES EACH MOD'S FILES", C.MUTED)],
        step2=[("2  FILE NAME -> IDENTITY", C.CREAM), ("ORIGIN X LOCATOR", C.MUTED)],
        step3=[("3  THE MANAGER'S ORDER", C.CREAM), ("TOP WINS, EACH ON OR OFF", C.MUTED)],
        step4=[("4  CHECK, THEN CHOOSE", C.CREAM), ("BEST USABLE PICTURE", C.MUTED)],
        atlas=[("ATLAS SPRITES", C.CREAM), ("RENDERHANDLER HOOKS", C.MUTED)],
        scene=[("SCENE TEXTURES", C.CREAM), ("COPIED ON SCENE LOAD", C.MUTED)],
        modspr=[("OTHER MODS' PICTURES", C.CREAM), ("ITEMS, PAPER, CODE", C.MUTED)],
        gamefiles=[("GAME FILES", C.CREAM)],
        modfolders=[("MOD FOLDERS", C.CREAM)],
        inventory=[("INVENTORY.PY", C.CREAM), ("FACTS", C.MUTED)],
        schema=[("SCHEMA.PY", C.CREAM), ("SCHEMA.TSV", C.MUTED)],
        catalog=[("CATALOG.CS", C.CREAM), ("CATALOG.TSV", C.MUTED)],
        export=[("EXPORT, PLACEHOLDERS", C.CREAM), ("ORIGINALS TO DRAW OVER", C.MUTED)],
        builder=[("PACKBUILDER", C.CREAM), ("CHECKS NAMES AND SIZES", C.MUTED)],
        pack=[("A PACK MOD", C.CREAM), ("INTO THE MODS FOLDER", C.MUTED)],
        notes=["THE KIT HOLDS NO GAME ART: CREATORS EXPORT",
                  "THE PICTURES FROM THEIR OWN GAME."],
    ),
    "zh": ArchText(
        title="材质包：整体架构",
        game="游戏内", kit="创作者套件",
        packs=[("材质包 Mod", C.CREAM), ("Textures/", C.MUTED)],
        others=[("其他 Mod", C.CREAM), ("它们的图片", C.MUTED)],
        step1=[("1 游戏的加载器", C.CREAM), ("解码各 Mod 的文件", C.MUTED)],
        step2=[("2 文件名 -> 身份", C.CREAM), ("来源 × 定位", C.MUTED)],
        step3=[("3 管理器的顺序", C.CREAM), ("上面的优先，可逐个开关", C.MUTED)],
        step4=[("4 先校验，再选择", C.CREAM), ("选最靠上的可用图", C.MUTED)],
        atlas=[("图集精灵", C.CREAM), ("RenderHandler 钩子", C.MUTED)],
        scene=[("场景贴图", C.CREAM), ("每次进场景时拷入", C.MUTED)],
        modspr=[("其他 Mod 的图片", C.CREAM), ("Items、Paper、代码", C.MUTED)],
        gamefiles=[("游戏文件", C.CREAM)],
        modfolders=[("Mod 文件夹", C.CREAM)],
        inventory=[("inventory.py", C.CREAM), ("客观事实", C.MUTED)],
        schema=[("schema.py", C.CREAM), ("schema.tsv", C.MUTED)],
        catalog=[("Catalog.cs", C.CREAM), ("catalog.tsv", C.MUTED)],
        export=[("导出、占位图", C.CREAM), ("用来照着画的原图", C.MUTED)],
        builder=[("PackBuilder", C.CREAM), ("校验文件名和尺寸", C.MUTED)],
        pack=[("一个材质包 Mod", C.CREAM), ("放进 Mods 文件夹", C.MUTED)],
        notes=["套件不含游戏美术：创作者从自己的游戏里导出原图。"],
    ),
})


# Diagram of Texture Packs' structure: the game's side on the left (inputs, steps, ways pictures reach the screen), the kit on the right.
def architecture(cv: C.Canvas, lang: Lang) -> int:
    t = ARCH[lang]
    accent = C.PINK
    y = title(cv, lang, t.title, accent) + 12
    lx, rx, cw = MARGIN, 208, 184           # two columns: the game on the left, the kit on the right
    text(cv, lang, lx, y, t.game, accent)
    text(cv, lang, rx, y, t.kit, accent)
    top = y + GLYPH[lang] + 8

    left = game_column(cv, lang, t, lx, cw, top, accent)
    right = kit_column(cv, lang, t, rx, cw, top, accent)
    y = max(left, right) + 12
    return note_lines(cv, lang, y, t.notes) + MARGIN


def game_column(cv: C.Canvas, lang: Lang, t: ArchText, x: int, w: int, top: int, accent: C.Color) -> int:
    """Inputs, the four steps, and the three ways the chosen pictures reach the screen. Returns the bottom."""
    mid = x + w // 2
    # Two inputs side by side: texture packs, and the pictures of other mods.
    sw = (w - 8) // 2
    y = top
    ha = box(cv, lang, x, y, sw, t.packs, "slot", "packs")
    hb = box(cv, lang, x + sw + 8, y, sw, t.others, "slot", "others")
    row = max(ha, hb)
    arrow_down(cv, x + sw // 2, y + ha + 2, y + row + 12, C.MUTED)
    arrow_down(cv, x + sw + 8 + sw // 2, y + hb + 2, y + row + 12, C.MUTED)
    y += row + 14
    for key, lines in (("step1", t.step1), ("step2", t.step2), ("step3", t.step3)):
        h = box(cv, lang, x, y, w, lines, "plate", key)
        arrow_down(cv, mid, y + h + 2, y + h + 12, C.MUTED)
        y += h + 14
    h = box(cv, lang, x, y, w, t.step4, "plate", "step4")
    # Out of step 4, one line runs down the left edge to each way out: solid to the built ones, dotted on.
    join = y + h + 6
    bus = x + 5
    cv.vline(mid, y + h + 1, join - y - h, accent)
    cv.hline(bus, join, mid - bus + 1, accent)
    y = join + 6
    ox, ow = x + 14, w - 14
    built_end = join
    outs: Sequence[tuple[str, Lines, BoxKind]] = (("atlas", t.atlas, "lit"), ("scene", t.scene, "lit"),
                                                  ("modspr", t.modspr, "lit"))
    for key, lines, kind in outs:
        h = box(cv, lang, ox, y, ow, lines, kind, key, accent)
        m = y + h // 2
        planned = kind == "planned"
        arrow_right(cv, bus, ox - 2, m, C.FAINT if planned else accent, dotted=planned)
        if planned:
            for yy in range(built_end + 2, m, 2):
                cv.put(bus, yy, C.FAINT)
        else:
            cv.vline(bus, built_end, m - built_end + 1, accent)
            built_end = m
        y += h + 6
    return y - 6


def kit_column(cv: C.Canvas, lang: Lang, t: ArchText, x: int, w: int, top: int, accent: C.Color) -> int:
    """The creator kit: the game's catalog and the mods' schemas, merged into export and the builder."""
    sw = (w - 8) // 2
    ax, bx = x, x + sw + 8                 # two sub-columns: the game, other mods
    am, bm, mid = ax + sw // 2, bx + sw // 2, x + w // 2
    y = top
    ha = box(cv, lang, ax, y, sw, t.gamefiles, "slot", "game files")
    hb = box(cv, lang, bx, y, sw, t.modfolders, "slot", "mod folders")
    row = max(ha, hb)
    arrow_down(cv, am, y + ha + 2, y + row + 12, C.MUTED)
    arrow_down(cv, bm, y + hb + 2, y + row + 12, C.MUTED)
    y += row + 14
    hi = box(cv, lang, ax, y, sw, t.inventory, "plate", "inventory")
    hs = box(cv, lang, bx, y, sw, t.schema, "plate", "schema")
    schema_bottom = y + hs
    arrow_down(cv, am, y + hi + 2, y + hi + 12, C.MUTED)
    y += hi + 14
    hc = box(cv, lang, ax, y, sw, t.catalog, "plate", "catalog")
    y += hc + 14
    # Both feed the export: the catalog directly, the schemas past the catalog's row.
    arrow_down(cv, am, y - 12, y - 2, C.MUTED)
    arrow_down(cv, bm, schema_bottom + 2, y - 2, C.MUTED)
    for key, lines in (("export", t.export), ("builder", t.builder)):
        h = box(cv, lang, x, y, w, lines, "plate", key)
        arrow_down(cv, mid, y + h + 2, y + h + 12, accent if key == "builder" else C.MUTED)
        y += h + 14
    h = box(cv, lang, x, y, w, t.pack, "lit", "pack", accent)
    return y + h


DIAGRAMS: Final[Mapping[str, Diagram]] = MappingProxyType({
    "binding-capture": capture,
    "press-decision": press,
    "texture-packs-architecture": architecture,
})


# The canvas is taller than any diagram; each diagram returns its height and the image is cropped to it before scaling.
def render(draw: Diagram, lang: Lang) -> Image.Image:
    cv = C.Canvas(W, 1400)
    h = draw(cv, lang)
    return cv.img.crop((0, 0, W, h)).resize((W * SCALE, h * SCALE), Image.Resampling.NEAREST)


@dataclass(frozen=True)
class Options:
    out: str
    only: frozenset[str] | None


def parse_options(argv: Sequence[str]) -> Options:
    only_arg, rest = take_option(argv, "--only")
    only = split_ids(only_arg)
    if only is not None and only - DIAGRAMS.keys():
        raise SystemExit("unknown diagram id(s): " + ", ".join(sorted(only - DIAGRAMS.keys())))
    default_out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out", "diagrams")
    return Options(rest[0] if rest else default_out, only)


def main(argv: Sequence[str]) -> None:
    """python design/diagrams.py [out] [--only ID[,ID...]]

    --only renders the diagrams named, so one mod's diagrams can go into its own doc/attachments."""
    opts = parse_options(argv)
    os.makedirs(opts.out, exist_ok=True)
    langs: tuple[tuple[Lang, str], ...] = (("en", ""), ("zh", ".zh_CN"))
    for name, draw in DIAGRAMS.items():
        if opts.only is not None and name not in opts.only:
            continue
        for lang, suffix in langs:
            img = render(draw, lang)
            path = os.path.join(opts.out, name + suffix + ".png")
            img.save(path, optimize=True)
            print(path, "%dx%d" % img.size)


if __name__ == "__main__":
    main(sys.argv[1:])
