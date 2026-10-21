#!/usr/bin/env python3
# 요리 할래말래 - 핵심 장면 미리보기 (M04 장바구니 / M05 비용 비교 / M06 시간 비교)
import os, sys, math, subprocess, wave
import numpy as np
from functools import lru_cache
from PIL import Image, ImageDraw, ImageFont

W, H, FPS = 1920, 1080, 24
TOT = 29.0
MINT = (21, 184, 167); DEEP = (23, 55, 61); BG = (245, 247, 242); YEL = (241, 199, 101)
WHITE = (255, 255, 255); GRAY = (96, 116, 114); LINE = (214, 222, 216)
PORK = (188, 84, 56); GREEN = (84, 168, 96); RICE = (238, 208, 122)
DYEL = (200, 148, 30); DMINT = (12, 140, 128)
OUT = os.environ.get('OUT', os.path.join(os.path.dirname(__file__), '_render')); os.makedirs(OUT, exist_ok=True)

# ---------------- fonts ----------------
FD = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'fonts'))
FB = os.path.join(FD, 'NotoSansCJKkr-Bold.otf')
FR = os.path.join(FD, 'NotoSansCJKkr-Regular.otf')
def _kr(path):
    for i in range(8):
        try:
            f = ImageFont.truetype(path, 20, index=i)
            if 'KR' in ' '.join(f.getname()):
                return i
        except Exception:
            break
    return 0
IB, IR = _kr(FB), _kr(FR)
@lru_cache(None)
def F(size, bold=True):
    return ImageFont.truetype(FB if bold else FR, int(round(size)), index=IB if bold else IR)
def tw(text, size, bold=True):
    return F(size, bold).getlength(text)

# ---------------- easing ----------------
def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def prog(t, a, b): return clamp((t - a) / (b - a))
def eo3(p): return 1 - (1 - p) ** 3
def eio(p): return p * p * (3 - 2 * p)
def eob(p, s=1.6):
    p -= 1
    return 1 + (s + 1) * p ** 3 + s * p ** 2
def lerp(a, b, x): return a + (b - a) * x

# ---------------- supersampled layers ----------------
S = 2
class SD:
    def __init__(s, d): s.d = d
    def rr(s, b, r, fill=None, outline=None, w=0):
        x0, y0, x1, y1 = [v * S for v in b]
        if x1 <= x0 or y1 <= y0: return
        r = min(r * S, (x1 - x0) / 2, (y1 - y0) / 2)
        s.d.rounded_rectangle([x0, y0, x1, y1], radius=r, fill=fill, outline=outline, width=int(w * S))
    def el(s, b, fill=None, outline=None, w=0):
        s.d.ellipse([v * S for v in b], fill=fill, outline=outline, width=int(w * S))
    def ch(s, b, a0, a1, fill):
        s.d.chord([v * S for v in b], a0, a1, fill=fill)
    def tx(s, xy, t, size, fill, anchor='mm', bold=True):
        s.d.text((xy[0] * S, xy[1] * S), t, font=F(size * S, bold), fill=fill, anchor=anchor)
    def ln(s, pts, fill, w):
        s.d.line([(x * S, y * S) for x, y in pts], fill=fill, width=max(1, int(w * S)), joint='curve')
    def dash(s, p0, p1, fill, w, on=14, off=10):
        (x0, y0), (x1, y1) = p0, p1
        L = math.hypot(x1 - x0, y1 - y0)
        if L == 0: return
        ux, uy = (x1 - x0) / L, (y1 - y0) / L
        d = 0
        while d < L:
            e = min(d + on, L)
            s.ln([(x0 + ux * d, y0 + uy * d), (x0 + ux * e, y0 + uy * e)], fill, w)
            d += on + off

class Lay:
    def __init__(s, w, h, fn):
        w, h = int(w), int(h)
        im = Image.new('RGBA', (w * S, h * S), (0, 0, 0, 0))
        fn(SD(ImageDraw.Draw(im)))
        s.im, s.w, s.h, s._one = im, w, h, None
    def get(s, sc):
        nw, nh = max(1, int(round(s.w * sc))), max(1, int(round(s.h * sc)))
        if nw == s.w and nh == s.h:
            if s._one is None:
                s._one = s.im.resize((nw, nh), Image.LANCZOS)
            return s._one
        return s.im.resize((nw, nh), Image.LANCZOS)

def put(fr, lay, cx, cy, sc=1.0, al=1.0):
    if al <= 0.01 or sc <= 0.02: return
    im = lay.get(sc)
    if al < 0.99:
        im = im.copy()
        a = im.getchannel('A').point(lambda v: int(v * al))
        im.putalpha(a)
    fr.paste(im, (int(round(cx - im.width / 2)), int(round(cy - im.height / 2))), im)
def putL(fr, lay, xl, cy, sc=1.0, al=1.0): put(fr, lay, xl - 12 + lay.w / 2, cy, sc, al)
def putR(fr, lay, xr, cy, sc=1.0, al=1.0): put(fr, lay, xr + 12 - lay.w / 2, cy, sc, al)

_tl = {}
def T(text, size, fill, bold=True):
    k = (text, size, fill, bold)
    if k not in _tl:
        w = int(tw(text, size, bold)) + 24; h = int(size * 1.5)
        def fn(d): d.tx((w / 2, h / 2), text, size, fill, 'mm', bold)
        _tl[k] = Lay(w, h, fn)
    return _tl[k]
_chips = {}
def chip(text, size, fill, tc, padx=40, h=None):
    k = (text, size, fill, tc, padx, h)
    if k not in _chips:
        w = int(tw(text, size)) + padx * 2; hh = h or int(size * 1.9)
        def fn(d):
            d.rr((0, 0, w, hh), hh / 2, fill)
            d.tx((w / 2, hh / 2), text, size, tc)
        _chips[k] = Lay(w, hh, fn)
    return _chips[k]

# ---------------- common frame parts ----------------
def base():
    fr = Image.new('RGB', (W, H), BG)
    ImageDraw.Draw(fr).rectangle([0, 0, W, 10], fill=MINT)
    return fr

def title(fr, t, text):
    p = eob(prog(t, 0.1, 0.7)); a = prog(t, 0.1, 0.5)
    put(fr, T(text, 60, DEEP), 960, 62 + (1 - p) * 30, 1, a)

_sub = {}
def sublay(text):
    if text in _sub: return _sub[text]
    size, maxw = 44, 1640
    if tw(text, size, False) <= maxw:
        lines = [text]
    elif '. ' in text:
        a, b = text.split('. ', 1); lines = [a + '.', b]
    else:
        words, lines, cur = text.split(' '), [], ''
        for w_ in words:
            tr = (cur + ' ' + w_).strip()
            if tw(tr, size, False) <= maxw: cur = tr
            else: lines.append(cur); cur = w_
        lines.append(cur)
    lw = max(tw(l, size, False) for l in lines)
    w, h = int(lw) + 110, len(lines) * 64 + 36
    def fn(d):
        d.rr((0, 0, w, h), 26, (23, 55, 61, 238))
        for i, l in enumerate(lines):
            d.tx((w / 2, 18 + 32 + i * 64), l, size, BG, 'mm', False)
    _sub[text] = Lay(w, h, fn)
    return _sub[text]

FOOT = None
def finish(fr, t, sub, t_end=None):
    global FOOT
    if FOOT is None: FOOT = T('비공식 사업 제안 · 화면과 수치는 시연 예시', 28, GRAY, False)
    sl = sublay(sub); p = prog(t, 0.5, 0.9)
    put(fr, sl, 960, 975 - sl.h / 2 + (1 - eo3(p)) * 20, 1, p)
    put(fr, FOOT, 960, 1022, 1, prog(t, 0.3, 0.7))
    d = ImageDraw.Draw(fr)
    pw = prog(t, 0, 0.55)
    if pw < 1:
        x = int(W * eio(pw))
        d.rectangle([x, 0, W, H], fill=MINT)
        if 0 < x < W - 1: d.rectangle([x, 0, x + 36, H], fill=DEEP)
    if t_end:
        pe = prog(t, t_end - 0.45, t_end)
        if pe > 0:
            x = int(W * eio(pe))
            d.rectangle([0, 0, x, H], fill=MINT)
            if 0 < x < W - 1: d.rectangle([x - 36, 0, x, H], fill=DEEP)
    return fr

# ---------------- illustrations ----------------
def bowl_fn(kind):
    def fn(d):
        food = PORK if kind == 'pork' else RICE
        d.el((28, 48, 172, 118), food)
        if kind == 'pork':
            for (x, y, w_, h_) in [(52, 62, 38, 20), (95, 56, 40, 22), (128, 74, 34, 20), (70, 84, 36, 20)]:
                d.rr((x, y, x + w_, y + h_), 9, (214, 110, 70))
            for (x, y) in [(60, 58), (108, 78), (140, 66), (86, 100)]:
                d.rr((x, y, x + 16, y + 8), 4, GREEN)
        else:
            for (x, y, c) in [(60, 66, (250, 235, 160)), (100, 58, (240, 150, 90)), (130, 70, GREEN),
                              (80, 92, (250, 235, 160)), (118, 92, GREEN), (145, 92, (240, 150, 90)), (50, 84, GREEN)]:
                d.el((x, y, x + 16, y + 12), c)
        d.ch((12, 26, 188, 186), 0, 180, MINT)
        d.rr((8, 96, 192, 110), 7, DEEP)
    return fn
BOWL_P = Lay(200, 196, bowl_fn('pork'))
BOWL_R = Lay(200, 196, bowl_fn('rice'))

# ====================================================================
# M04  장바구니 구성  (10s)
# ====================================================================
SUB04 = '있는 양념은 제외하고, 다음 끼니에 쓸 계란을 더해 세 끼를 계획합니다.'
ING = [('돼지고기', '7,500원'), ('양파', '2,000원'), ('대파', '2,000원'),
       ('고추장', '3,200원'), ('간장', '2,000원'), ('설탕', '1,500원')]
def card_lay(name, price, hl=False, egg=False):
    w, h = 240, 130
    def fn(d):
        on = hl or egg
        d.rr((3, 3, w - 3, h - 3), 22, WHITE, YEL if on else LINE, 5 if on else 3)
        d.tx((w / 2, 48), name, 40, DEEP)
        d.tx((w / 2, 92), price, 30 if egg else 32, DYEL if egg else DMINT)
    return Lay(w, h, fn)
CARDS = [card_lay(n, p, hl=(i >= 3)) for i, (n, p) in enumerate(ING)]
EGG = card_lay('계란', '3,500원 추가', egg=True)
Y0 = 300
X6 = [300 + 264 * i for i in range(6)]
X3 = [696, 960, 1224]
X4 = [564, 828, 1092, 1356]
BAR_W, BAR_X0 = 880, 900
W11 = 11500 / 15000 * BAR_W

def barlay(vb):
    fw = vb / 15000 * BAR_W
    def fn(d):
        d.rr((0, 0, BAR_W, 50), 25, (251, 240, 205), YEL, 3)
        if fw > W11 + 1:
            d.rr((0, 0, fw, 50), 25, YEL)
            d.rr((0, 0, W11, 50), 25, MINT)
            d.rr((W11 - 30, 0, W11, 50), 0, MINT)
        elif fw > 2:
            d.rr((0, 0, fw, 50), 25, MINT)
    return Lay(BAR_W, 50, fn)

def total04(t):
    v = lerp(18200, 11500, eio(prog(t, 1.6, 2.4)))
    v = lerp(v, 15000, eio(prog(t, 6.2, 7.1)))
    return int(round(v / 100) * 100)

def m04(t):
    fr = base()
    title(fr, t, '장바구니 구성')
    v = total04(t)
    putL(fr, T('구매 금액', 36, GRAY), 140, 440, 1, prog(t, 0.4, 0.9))
    txt = ('총 ' if t >= 7.1 else '') + f'{v:,}원'
    putL(fr, T(txt, 120, DMINT if t >= 7.1 else DEEP), 140, 545, 1, prog(t, 0.5, 1.0))
    # ingredient cards
    for i in range(6):
        p = prog(t, 0.15 + 0.08 * i, 0.6 + 0.08 * i)
        sc = 0.6 + 0.4 * eob(p, 1.2); al = min(1, p * 2.5); y = Y0
        if i < 3:
            e1 = eio(prog(t, 1.9, 2.6)); e2 = eio(prog(t, 6.0, 7.0))
            x = lerp(lerp(X6[i], X3[i], e1), X4[i], e2)
        else:
            x = X6[i]; k = i - 3
            r = prog(t, 0.7 + 0.35 * k, 1.25 + 0.35 * k)
            y = Y0 + 90 * eo3(r); al *= (1 - r); sc *= 1 - 0.15 * r
        put(fr, CARDS[i], x, y, sc, al)
    # egg card
    if t >= 4.0:
        j = eio(prog(t, 6.0, 7.0))
        ex = lerp(lerp(2150, 1400, eo3(prog(t, 4.0, 4.8))), X4[3], j)
        ey = lerp(765, Y0, j)
        sc = lerp(1.15, 1.0, j)
        if t >= 7.0: sc *= 1 + 0.10 * math.sin(math.pi * prog(t, 7.0, 7.4))
        put(fr, EGG, ex, ey, sc, min(1, prog(t, 4.0, 4.3) * 1.5))
    # chips (0-3s)
    ca = 1 - prog(t, 3.0, 3.4)
    pA = prog(t, 1.5, 1.95)
    put(fr, chip('보유 양념 6,700원 제외', 40, YEL, DEEP), 1340, 500, 0.7 + 0.3 * eob(pA), min(1, pA * 3) * ca)
    pB = prog(t, 2.4, 2.85)
    put(fr, chip('18,200원 → 11,500원', 44, MINT, WHITE), 1340, 590, 0.7 + 0.3 * eob(pB), min(1, pB * 3) * ca)
    # minimum-order bar
    if t >= 3.2:
        ra = 1 - prog(t, 7.8, 8.2)
        pa = prog(t, 3.2, 3.6)
        vb = 11500 * eo3(prog(t, 3.2, 3.9)) if t < 6.2 else v
        put(fr, barlay(vb), BAR_X0 + BAR_W / 2, 565, 1, pa * ra)
        putR(fr, T('최소주문 15,000원', 36, DEEP), 1780, 500, 1, pa * ra)
        pc = prog(t, 3.9, 4.35); fo = 1 - prog(t, 6.2, 6.7)
        put(fr, chip('3,500원 부족', 38, YEL, DEEP), 1630, 635, 0.7 + 0.3 * eob(pc), min(1, pc * 3) * fo * ra)
        pd = prog(t, 7.2, 7.65)
        put(fr, chip('최소주문 충족', 40, MINT, WHITE), 1600, 635, 0.7 + 0.3 * eob(pd), min(1, pd * 3) * ra)
    # plan (8-10s)
    if t >= 8.1:
        pb = prog(t, 8.1, 8.55)
        put(fr, chip('제육 2끼 + 볶음밥 1끼 계획', 42, DEEP, WHITE), 1340, 495, 0.7 + 0.3 * eob(pb), min(1, pb * 3))
        for i, (lay, lab) in enumerate([(BOWL_P, '제육'), (BOWL_P, '제육'), (BOWL_R, '볶음밥')]):
            p = prog(t, 8.4 + 0.2 * i, 8.85 + 0.2 * i)
            cx = 1110 + 230 * i
            put(fr, lay, cx, 625, 0.8 * (0.5 + 0.5 * eob(p)), min(1, p * 3))
            put(fr, T(lab, 34, GRAY), cx, 740, 1, min(1, p * 3))
    return finish(fr, t, SUB04, 10)

# ====================================================================
# M05  비용 비교  (10s)
# ====================================================================
SUB05 = '장보기는 오늘 만오천 원, 세 끼 계획의 평균은 오천 원. 오늘 결제액과 한 끼 평균을 구분합니다.'
def big_card(kind):
    w, h = 790, 440
    def fn(d):
        d.rr((4, 4, w - 4, h - 4), 30, WHITE, LINE, 4)
        if kind == 'cook':
            d.rr((30, 24, 170, 80), 28, MINT); d.tx((100, 52), '요리', 40, WHITE)
            d.tx((w / 2, 125), '오늘 15,000원', 84, DEEP); d.tx((w / 2, 212), '3끼 계획', 38, GRAY)
        else:
            d.rr((30, 24, 170, 80), 28, DEEP); d.tx((100, 52), '배달', 40, WHITE)
            d.tx((w / 2, 125), '오늘 16,000원', 84, DEEP); d.tx((w / 2, 212), '1끼', 38, GRAY)
    return Lay(w, h, fn)
CARD_COOK, CARD_DELI = big_card('cook'), big_card('deli')

def bracket(p):
    pts_l = [(535, 635), (535, 700), (640, 700)]
    pts_r = [(1385, 635), (1385, 700), (1280, 700)]
    def part(pts, f):
        segs = [(pts[i], pts[i + 1]) for i in range(len(pts) - 1)]
        tot = sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in segs); run = f * tot; out = [pts[0]]
        for a, b in segs:
            L = math.hypot(b[0] - a[0], b[1] - a[1])
            if run >= L: out.append(b); run -= L
            else:
                out.append((a[0] + (b[0] - a[0]) * run / L, a[1] + (b[1] - a[1]) * run / L)); break
        return out
    def fn(d):
        for pts in (pts_l, pts_r):
            q = part(pts, p)
            d.ln([(x - 500, y - 620) for x, y in q], DYEL, 6)
    return Lay(920, 100, fn)

def m05(t):
    fr = base()
    title(fr, t, '비용 비교')
    pl = eob(prog(t, 0.15, 0.85), 1.2); pr = eob(prog(t, 0.3, 1.0), 1.2)
    put(fr, CARD_COOK, lerp(-400, 535, pl), 415, 1, min(1, prog(t, 0.15, 0.5)))
    put(fr, CARD_DELI, lerp(2300, 1385, pr), 415, 1, min(1, prog(t, 0.3, 0.65)))
    # banner
    pb = prog(t, 3.0, 3.45)
    put(fr, chip('오늘 결제액 ≠ 한 끼 평균', 40, YEL, DEEP), 960, lerp(118, 138, eo3(pb)), 1, min(1, pb * 2.5))
    # bowls on cooking side
    for i, lay in enumerate([BOWL_P, BOWL_P, BOWL_R]):
        p = prog(t, 3.3 + 0.25 * i, 3.75 + 0.25 * i)
        put(fr, lay, 385 + 150 * i, 497, 0.55 * (0.5 + 0.5 * eob(p)), min(1, p * 3))
    # 15,000원 -> three 5,000원 chips -> merge into average pill
    for i in range(3):
        p1 = eio(prog(t, 3.5 + 0.15 * i, 4.1 + 0.15 * i)); q = eio(prog(t, 4.4, 4.85))
        x = lerp(lerp(535, 385 + 150 * i, p1), 535, q); y = lerp(320, 585, p1)
        al = min(1, p1 * 3) * (1 - q)
        put(fr, chip('5,000원', 28, YEL, DEEP, 14, 46), x, y, 1, al)
    p = prog(t, 4.1, 4.55)
    put(fr, BOWL_P, 1385, 497, 0.55 * (0.5 + 0.5 * eob(p)), min(1, p * 3))
    # average pill
    pa = prog(t, 4.4, 4.9)
    pulse = 1 + 0.04 * math.sin(2 * math.pi * (t - 4.9) * 1.2) if 4.9 < t < 6.0 else 1
    put(fr, chip('평균 5,000원', 52, MINT, WHITE, 48, 66), 535, 590, (0.6 + 0.4 * eob(pa)) * pulse, min(1, pa * 3))
    # difference bracket + badge
    if t >= 6.0:
        put(fr, bracket(eio(prog(t, 6.0, 6.8))), 960, 670, 1, 1)
        pg = prog(t, 6.6, 7.1)
        put(fr, chip('오늘 지출 차이 1,000원', 54, YEL, DEEP, 50, 88), 960, 700, 0.7 + 0.3 * eob(pg), min(1, pg * 3))
        put(fr, T('계획대로 소비 · 기존 재료비 제외 · 장보기 배송비 0원 가정', 30, GRAY, False), 960, 778, 1, prog(t, 7.2, 7.7))
    return finish(fr, t, SUB05, 10)

# ====================================================================
# M06  시간 비교  (9s)
# ====================================================================
SUB06 = '장보기 대기와 조리 시간을 합쳐, 식사까지 걸리는 시간도 비교합니다.'
X0, PX = 380, 36
Y1, Y2 = 270, 460
def mins1(t): return 20 * eio(prog(t, 0.3, 2.9))
def mins2(t): return 15 * eio(prog(t, 3.1, 4.9))
def mins3(t): return 28 * eio(prog(t, 5.1, 6.9))

def grid_fn(d):
    for k in range(8):
        x = 80 + 180 * k
        d.ln([(x, 0), (x, 395)], LINE, 2)
        d.tx((x, 432), str(5 * k), 28, GRAY)
    d.ln([(80, 395), (1376, 395)], GRAY, 3)
    d.tx((1420, 432), '분', 30, GRAY)
GRID = Lay(1500, 460, grid_fn)

def seg(w, color, text, tc, sql=False, sqr=False, h=120):
    w = int(round(w))
    def fn(d):
        d.rr((0, 0, w, h), 20, color)
        if sql: d.rr((0, 0, min(30, w), h), 0, color)
        if sqr: d.rr((max(0, w - 30), 0, w, h), 0, color)
        if text: d.tx((28, h / 2), text, 44, tc, 'lm')
    return Lay(w, h, fn)

def guide_fn(d):
    d.rr((8, 205, 260, 325), 0, (255, 244, 210, 150))
    d.dash((8, 15), (8, 325), DYEL, 3); d.dash((260, 15), (260, 325), DYEL, 3)
    d.dash((8, 205), (260, 205), DYEL, 3); d.dash((8, 325), (260, 325), DYEL, 3)
GUIDE = Lay(268, 340, guide_fn)

def m06(t):
    fr = base()
    title(fr, t, '식사까지 걸리는 시간')
    put(fr, GRID, 1050, 420, 1, prog(t, 0.1, 0.5))
    put(fr, T('요리', 52, DEEP), 250, Y1, 1, prog(t, 0.2, 0.6))
    put(fr, T('배달', 52, DEEP), 250, Y2, 1, prog(t, 0.2, 0.6))
    m1, m2, m3 = mins1(t), mins2(t), mins3(t)
    if m1 * PX >= 6:
        put(fr, seg(m1 * PX, MINT, '장보기 20분', WHITE, sqr=m2 > 0.05), X0 + m1 * PX / 2, Y1)
    if m2 * PX >= 6:
        put(fr, seg(m2 * PX, YEL, '조리 15분', DEEP, sql=True), X0 + 20 * PX + m2 * PX / 2, Y1)
    if m3 * PX >= 6:
        put(fr, seg(m3 * PX, DEEP, '배달 28분', WHITE), X0 + m3 * PX / 2, Y2)
    if t >= 4.9:
        p = prog(t, 4.9, 5.3)
        putL(fr, T('= 35분', 54, DEEP), 1665, Y1, 1, p)
    if t >= 5.0:
        put(fr, T('손질·가열·담기 포함 · 설거지 제외', 32, GRAY, False), 960, 695, 1, prog(t, 5.0, 5.5))
    if t >= 7.0:
        put(fr, GUIDE, 1514, 360, 1, prog(t, 7.0, 7.4))
        pg = prog(t, 7.4, 7.85)
        put(fr, chip('요리 7분 더', 38, DEEP, WHITE, 40, 62), 1514, 365, 0.7 + 0.3 * eob(pg), min(1, pg * 3))
    return finish(fr, t, SUB06, None)

# ====================================================================
# audio
# ====================================================================
SR = 44100
N = int(SR * TOT)
rng = np.random.default_rng(7)
SFX_L = np.zeros(N, np.float32); SFX_R = np.zeros(N, np.float32)
MUS = np.zeros(N, np.float32)

def add(buf, t0, x, g=1.0):
    i = int(t0 * SR)
    if i < 0 or i >= len(buf): return
    x = x[:len(buf) - i]
    buf[i:i + len(x)] += x * g
def sfx(t0, x, pan=0.0, g=1.0):
    add(SFX_L, t0, x, g * (1 - max(0, pan))); add(SFX_R, t0, x, g * (1 + min(0, pan)))

def tone(f, d, k=8, g=0.4, glide=None, tri=False):
    n = int(d * SR); t = np.arange(n) / SR
    fa = f + (glide - f) * (t / d) if glide else np.full(n, float(f))
    ph = 2 * np.pi * np.cumsum(fa) / SR
    w = (2 / np.pi) * np.arcsin(np.sin(ph)) if tri else np.sin(ph)
    return (w * np.exp(-t * k) * np.minimum(1, t / 0.004) * g).astype(np.float32)
def noise(d, k=20, g=0.2):
    n = int(d * SR); x = np.diff(rng.standard_normal(n + 1)); t = np.arange(n) / SR
    return (x * np.exp(-t * k) * g).astype(np.float32)
def swish(d=0.3, g=0.5):
    n = int(d * SR); x = np.convolve(rng.standard_normal(n), np.ones(9) / 9, mode='same')
    e = np.sin(np.pi * np.linspace(0, 1, n)) ** 2
    return (x * e * g).astype(np.float32)
def mixn(*xs):
    n = max(len(x) for x in xs); o = np.zeros(n, np.float32)
    for x in xs: o[:len(x)] += x
    return o

def s_swipe(t0, pan=0.0): sfx(t0, mixn(swish(0.28, 0.55), tone(320, 0.22, k=9, g=0.07, glide=900)), pan)
def s_hit(t0): sfx(t0, mixn(tone(75, 0.42, k=7, g=0.4, glide=45), swish(0.4, 0.5)))
def s_pop(t0, f=620, pan=0.0): sfx(t0, mixn(tone(f, 0.13, k=30, g=0.34, glide=f * 1.6), tone(f * 2, 0.07, k=60, g=0.09)), pan)
def s_tap(t0, f=1040): sfx(t0, mixn(tone(f, 0.09, k=45, g=0.28), tone(f * 1.5, 0.06, k=70, g=0.1)))
def s_confirm(t0):
    sfx(t0, tone(784, 0.2, k=13, g=0.3)); sfx(t0 + 0.09, tone(1175, 0.34, k=9, g=0.3))
def s_accent(t0): sfx(t0, mixn(tone(659, 0.38, k=7, g=0.3), tone(988, 0.38, k=7, g=0.14)))
def s_warn(t0): sfx(t0, mixn(tone(330, 0.2, k=13, g=0.3, glide=290), tone(247, 0.22, k=12, g=0.18)))
def s_thump(t0): sfx(t0, mixn(tone(190, 0.22, k=17, g=0.42, glide=95), noise(0.03, 60, 0.1))); s_pop(t0 + 0.05, 520)
def s_tick(t0, f=1700): sfx(t0, mixn(tone(f, 0.03, k=140, g=0.15), noise(0.012, 200, 0.08)))

def crossings(fn, t0, t1):
    out, last = [], 0
    for tv in np.arange(t0, t1 + 0.01, 1 / 240):
        k = int(fn(tv) + 1e-9)
        while k > last: last += 1; out.append(float(tv))
    return out

def sfx_all():
    # M04 (0-10)
    s_swipe(0.0); s_hit(0.0)
    for tt in (0.7, 1.05, 1.4): s_swipe(tt, -0.2)
    s_pop(1.5, 560); s_tap(1.65); s_tap(2.35); s_pop(2.4, 700)
    s_swipe(3.2); s_warn(3.9); s_swipe(4.0, 0.2)
    s_thump(6.0); s_tap(6.2); s_tap(7.1, 1240); s_confirm(7.2)
    s_pop(8.1, 520)
    for i, f in enumerate((560, 660, 780)): s_pop(8.4 + 0.2 * i, f)
    # M05 (10-20)
    s_swipe(10.0); s_hit(10.0); s_swipe(10.15, -0.3); s_swipe(10.3, 0.3)
    s_swipe(13.0)
    for i, f in enumerate((560, 660, 780)): s_pop(13.3 + 0.25 * i, f)
    s_pop(14.1, 600); s_accent(14.4)
    s_swipe(16.0); s_pop(16.6, 520); s_accent(16.65)
    # M06 (20-29)
    s_swipe(20.0); s_hit(20.0)
    for i, tt in enumerate(crossings(mins1, 0.3, 2.9)): s_tick(20 + tt, 1500 + 15 * i)
    for i, tt in enumerate(crossings(mins2, 3.1, 4.9)): s_tick(20 + tt, 1900 + 15 * i)
    for i, tt in enumerate(crossings(mins3, 5.1, 6.9)): s_tick(20 + tt, 1300 + 15 * i)
    s_pop(24.9, 640); s_pop(27.4, 560); s_confirm(27.45)

def inten(t):
    xs = [0, 1, 10, 16, 16.5, 20, 20.5, 27, 29]
    ys = [0.15, 0.35, 0.85, 0.85, 0.25, 0.25, 0.3, 0.4, 0.3]
    return float(np.interp(t, xs, ys))

def music():
    BEAT = 0.6; CD = 4 * BEAT
    CH = [[220, 261.63, 329.63], [174.61, 220, 261.63], [196, 261.63, 329.63], [196, 246.94, 293.66]]
    RT = [110, 87.31, 130.81, 98]
    for ci in range(int(TOT / CD) + 2):
        t0 = ci * CD; dur = CD + 0.5; n = int(dur * SR); tt = np.arange(n) / SR
        e = np.minimum(1, tt / 0.35) * np.minimum(1, np.maximum(0, (dur - tt) / 0.5))
        w = sum(np.sin(2 * np.pi * f * tt) + 0.3 * np.sin(2 * np.pi * 2 * f * tt) for f in CH[ci % 4])
        add(MUS, t0, (w * e * 0.05 * (0.6 + inten(t0))).astype(np.float32))
    for b in range(int(TOT / BEAT)):
        tb = b * BEAT; ci = int(tb // CD) % 4; it = inten(tb)
        if b % 2 == 0 and it > 0.3:
            add(MUS, tb, tone(RT[ci], 0.55, k=3.5, g=0.26 * min(1, it * 1.2), tri=True))
        if it > 0.7:
            add(MUS, tb + 0.3, tone(RT[ci] * 2, 0.2, k=9, g=0.11, tri=True))
        if it > 0.55:
            add(MUS, tb, tone(120, 0.2, k=22, g=0.5, glide=48))
            add(MUS, tb + 0.3, noise(0.05, 70, 0.3))
    for s in range(int(TOT / 0.3)):
        ts = s * 0.3; it = inten(ts)
        if it > 0.4 and s % 4 != 3:
            ch = CH[int(ts // CD) % 4]
            add(MUS, ts, tone(ch[s % 3] * 2, 0.22, k=11, g=0.09 * it, tri=True))

def build_audio(path):
    sfx_all(); music()
    t = np.arange(N) / SR
    env = np.minimum(1, t / 0.4) * np.minimum(1, np.maximum(0, (TOT - t) / 1.2))
    m = MUS * env * 0.62
    L = m + SFX_L; R = m + SFX_R
    pk = max(np.abs(L).max(), np.abs(R).max())
    if pk > 0.9: L, R = L * 0.9 / pk, R * 0.9 / pk
    L, R = np.tanh(L * 1.05), np.tanh(R * 1.05)
    pcm = np.stack([L, R], 1)
    pcm = (np.clip(pcm, -1, 1) * 32767).astype('<i2')
    with wave.open(path, 'wb') as wf:
        wf.setnchannels(2); wf.setsampwidth(2); wf.setframerate(SR); wf.writeframes(pcm.tobytes())
    print('audio peak', float(pk))

# ====================================================================
def frame_at(t):
    if t < 10: return m04(t)
    if t < 20: return m05(t - 10)
    return m06(t - 20)

def stills():
    shots = {'m04': (m04, [1.3, 4.6, 7.6, 9.6]), 'm05': (m05, [1.5, 4.9, 7.2, 9.6]), 'm06': (m06, [2.0, 4.7, 6.6, 8.6])}
    for name, (fn, ts) in shots.items():
        sheet = Image.new('RGB', (1920, 1080))
        for i, tv in enumerate(ts):
            im = fn(tv).resize((960, 540), Image.LANCZOS)
            sheet.paste(im, ((i % 2) * 960, (i // 2) * 540))
        sheet.save(fOUT + '/qa_{name}.png')
    print('stills ok', IB, IR)

def srt():
    def ts(x):
        h = int(x // 3600); m = int(x % 3600 // 60); s = int(x % 60); ms = int(round((x - int(x)) * 1000))
        return f'{h:02d}:{m:02d}:{s:02d},{ms:03d}'
    items = [(0.5, 9.5, SUB04), (10.5, 19.5, SUB05), (20.5, 28.5, SUB06)]
    with open(f'{OUT}/yori_core_scenes_preview.srt', 'w', encoding='utf-8') as f:
        for i, (a, b, s) in enumerate(items, 1):
            f.write(f'{i}\n{ts(a)} --> {ts(b)}\n{s}\n\n')

def render():
    wav = OUT + '/audio.wav'
    build_audio(wav)
    outp = f'{OUT}/yori_core_scenes_preview.mp4'
    cmd = ['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS),
           '-i', '-', '-i', wav, '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '18', '-preset', 'medium',
           '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart', '-shortest', outp]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=open(OUT + '/ffmpeg.log', 'w'))
    nf = int(TOT * FPS)
    for n in range(nf):
        p.stdin.write(frame_at(n / FPS).tobytes())
        if n % 120 == 0: print('frame', n, '/', nf, flush=True)
    p.stdin.close(); p.wait()
    srt()
    print('done', outp)

if __name__ == '__main__':
    {'stills': stills, 'render': render}[sys.argv[1]]()
