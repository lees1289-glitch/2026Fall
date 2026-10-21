#!/usr/bin/env python3
# 요리 할래말래 - 모션그래픽 90초 v3 (코드로 그린 2D 모션그래픽 + 합성 음악/효과음)
# 사용: python3 build_v3.py stills | render
import os, sys, math, subprocess, wave
import numpy as np
from PIL import Image, ImageDraw
from multiprocessing import Pool

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import core
from core import *  # noqa  (색상, 폰트, 이징, Lay/T/chip, 일러스트, M03~M05 장면)

TOT = 90.0
core.TOT = TOT
core.N = int(core.SR * TOT)
core.SFX_L = np.zeros(core.N, np.float32)
core.SFX_R = np.zeros(core.N, np.float32)
core.MUS = np.zeros(core.N, np.float32)
OUT = os.environ.get('OUT', os.path.join(os.path.dirname(__file__), '_render'))
os.makedirs(OUT, exist_ok=True)
PALE = (221, 243, 235)
DARK_BAR = (36, 92, 98, 240)

# ---------------------------------------------------------------- 공통
def pop(t, a, d=0.45):
    p = prog(t, a, a + d)
    return 0.7 + 0.3 * eob(p), min(1, p * 3)

def pop_put(fr, lay, x, y, t, a, d=0.45, base=1.0, al=1.0):
    s, a_ = pop(t, a, d)
    put(fr, lay, x, y, s * base, a_ * al)

_sub2 = {}
def sublay2(text, dark=False):
    k = (text, dark)
    if k in _sub2: return _sub2[k]
    size, maxw = 44, 1640
    if tw(text, size, False) <= maxw: lines = [text]
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
    fill = DARK_BAR if dark else (23, 55, 61, 238)
    def fn(d):
        d.rr((0, 0, w, h), 26, fill)
        for i, l in enumerate(lines):
            d.tx((w / 2, 18 + 32 + i * 64), l, size, BG, 'mm', False)
    _sub2[k] = Lay(w, h, fn)
    return _sub2[k]

CUR = {}
def vfinish(fr, t, sub=None, t_end=None):
    sc = CUR; dark = sc.get('dark', False)
    foot = T('비공식 사업 제안 · 화면과 수치는 시연 예시', 28, (150, 184, 180) if dark else GRAY, False)
    put(fr, foot, 960, 1022, 1, prog(t, 0.3, 0.7))
    for (a, b, txt) in sc['caps']:
        if a <= t < b:
            sl = sublay2(txt, dark)
            p = prog(t, a, a + 0.3) * (1 - prog(t, b - 0.15, b))
            put(fr, sl, 960, 925 + (1 - eo3(prog(t, a, a + 0.3))) * 18, 1, p)
    d = ImageDraw.Draw(fr)
    if sc.get('in_wipe', True):
        pw = prog(t, 0, 0.55)
        if pw < 1:
            x = int(W * eio(pw))
            d.rectangle([x, 0, W, H], fill=MINT)
            if 0 < x < W - 1: d.rectangle([x, 0, x + 36, H], fill=DEEP)
    if sc.get('out_wipe', True):
        pe = prog(t, sc['dur'] - 0.45, sc['dur'])
        if pe > 0:
            x = int(W * eio(pe))
            d.rectangle([0, 0, x, H], fill=MINT)
            if 0 < x < W - 1: d.rectangle([x - 36, 0, x, H], fill=DEEP)
    return fr
core.finish = vfinish

def jar_lay(name, col, outline=None):
    w, h = 170, 210
    def fn(d):
        d.rr((20, 40, 150, 200), 28, col, outline, 4 if outline else 0)
        d.rr((38, 12, 132, 52), 10, DEEP)
        d.rr((34, 96, 136, 156), 12, WHITE)
        d.tx((85, 127), name, 32, DEEP)
        d.rr((30, 62, 42, 176), 6, (255, 255, 255, 70))
    return Lay(w, h, fn)
JARS = [jar_lay('고추장', (190, 62, 42)), jar_lay('간장', (84, 52, 34)), jar_lay('설탕', (238, 234, 224), LINE)]

def price_card(kind):
    w, h = 790, 400
    def fn(d):
        d.rr((4, 4, w - 4, h - 4), 30, WHITE, LINE, 4)
        if kind == 0:
            d.rr((30, 28, 280, 90), 31, MINT); d.tx((155, 59), '재료 전부 구매', 38, WHITE)
            d.tx((w / 2, 290), '메뉴 재료를 모두 새로 구매', 34, GRAY, 'mm', False)
        else:
            d.rr((30, 28, 230, 90), 31, DEEP); d.tx((130, 59), '배달 한 끼', 38, WHITE)
            d.tx((w / 2, 290), '메뉴 + 배달비', 34, GRAY, 'mm', False)
    return Lay(w, h, fn)
PC = [price_card(0), price_card(1)]
VS = chip('VS', 40, DEEP, WHITE, 26, 78)
QMARK = Lay(90, 90, lambda d: (d.el((4, 4, 86, 86), YEL, DYEL, 4), d.tx((45, 46), '?', 54, DEEP)))

# ---------------------------------------------------------------- M01 (0-8)
CAPS01 = [(0.3, 4.1, '재료는 18,200원이며, 배달 한 끼는 16,000원입니다.'), (4.1, 8.0, '집에 있는 양념은 구매에서 제외합니다.')]
def m01(t):
    fr = base(); title(fr, t, '가격표로 요리와 배달을 비교합니다')
    k = eio(prog(t, 4.1, 4.9))              # 카드 축소/상승
    sc = lerp(1.0, 0.66, k); cy = lerp(380, 270, k)
    for i, (x0, sx) in enumerate([(520, -420), (1400, 2340)]):
        p = eob(prog(t, 0.2 + 0.15 * i, 0.9 + 0.15 * i), 1.2)
        x = lerp(sx, lerp(x0, 960 + (x0 - 960) * 0.66 * 0.96 / 0.66 * 0.66, k), p)
        put(fr, PC[i], x, cy, sc, min(1, prog(t, 0.2, 0.5)))
        v = [18200, 16000][i]
        cv = int(round(v * eo3(prog(t, 0.7, 1.7)) / 100) * 100)
        put(fr, T(f'{cv:,}원', 112, DEEP), x, cy - 12 * sc + 4, sc, min(1, prog(t, 0.6, 0.9)))
    put(fr, VS, 960, cy, sc, prog(t, 0.9, 1.3))
    if 2.4 <= t < 4.1 or t >= 2.4:
        s, a = pop(t, 2.4); a *= 1 - k
        put(fr, chip('배달이 더 싸 보이는데…', 36, YEL, DEEP, 34, 64), 1400 * (1 - k) + 1290 * k, cy + 235 * sc + 30 * (1 - k) * 0 + 8, s, a)
    if t >= 4.1:
        p = prog(t, 4.1, 4.6)
        put(fr, chip('보유 양념을 확인합니다', 62, YEL, DEEP, 70, 110), 960, 535 - (1 - eob(p)) * -30, 0.7 + 0.3 * eob(p), min(1, p * 3))
        shelf = prog(t, 4.8, 5.2)
        if shelf > 0:
            put(fr, Lay(1000, 24, lambda d: d.rr((0, 0, 1000, 24), 12, (205, 190, 160))), 960, 790, 1, shelf)
        for i, (jar, x) in enumerate(zip(JARS, [720, 960, 1200])):
            a0 = 5.0 + 0.4 * i
            p = prog(t, a0, a0 + 0.5)
            bob = 4 * math.sin((t - a0) * 4) * (1 if t > a0 + 0.5 else 0)
            put(fr, jar, x, 690 - (1 - eob(p, 2.0)) * 120 + bob, 0.95, min(1, p * 3))
        if t >= 6.9:
            s, a = pop(t, 6.9)
            put(fr, QMARK, 1510, 150, s * (1 + 0.06 * math.sin((t - 6.9) * 7)), a)
    return vfinish(fr, t)

# ---------------------------------------------------------------- M02 (8-16)
CAPS02 = [(0.6, 4.0, '먹고 싶은 메뉴와 보유 재료를 입력합니다.'), (4.0, 8.0, '비용과 시간을 비교해 선택을 돕습니다.')]
FIELD = Lay(1260, 120, lambda d: d.rr((3, 3, 1257, 117), 30, WHITE, MINT, 5))
CURSOR = Lay(8, 74, lambda d: d.rr((0, 0, 8, 74), 4, MINT))
def chk_lay(name, on):
    w, h = 300, 100
    def fn(d):
        d.rr((3, 3, w - 3, h - 3), 24, PALE if on else WHITE, MINT if on else LINE, 4)
        d.el((24, 26, 72, 74), MINT if on else WHITE, MINT if on else LINE, 4)
        if on: d.ln([(34, 51), (45, 62), (63, 38)], WHITE, 7)
        d.tx((92, 50), name, 40, DEEP, 'lm')
    return Lay(w, h, fn)
CHK = {(n, o): chk_lay(n, o) for n in ('고추장', '간장', '설탕') for o in (0, 1)}
def feat_lay(label, sub, icon):
    w, h = 360, 250
    def fn(d):
        d.rr((4, 4, w - 4, h - 4), 28, WHITE, LINE, 4)
        if icon == 'coin':
            d.el((135, 26, 225, 116), YEL, DYEL, 6); d.tx((180, 71), '₩', 52, DEEP)
        elif icon == 'clock':
            d.el((135, 26, 225, 116), WHITE, DEEP, 7)
            d.ln([(180, 71), (180, 42)], DEEP, 7); d.ln([(180, 71), (200, 82)], DEEP, 7)
        d.tx((w / 2, 160), label, 48, DEEP); d.tx((w / 2, 210), sub, 28, GRAY, 'mm', False)
    return Lay(w, h, fn)
FEATS = [feat_lay('비용', '재료비 · 최소주문', 'coin'), feat_lay('시간', '장보기 · 조리 · 배달', 'clock'),
         feat_lay('끼니 수', '몇 끼 먹는지', None)]
def m02(t):
    fr = base(); title(fr, t, '요리 할래말래')
    pa = eo3(prog(t, 0.2, 0.7))
    putL(fr, T('먹고 싶은 메뉴', 34, GRAY), 330, 150, 1, pa)
    put(fr, FIELD, 960, 235 - (1 - pa) * 24, 1, pa)
    txt = '제육볶음'[:min(4, max(0, int((t - 0.6) / 0.3)))] if t >= 0.9 else ''
    if txt: putL(fr, T(txt, 70, DEEP), 380, 238, 1, 1)
    if t < 2.6 and int(t * 2.5) % 2 == 0 and t > 0.5:
        put(fr, CURSOR, 380 + tw(txt, 70) + 14, 238, 1, 1)
    if t >= 2.3:
        putL(fr, T('집에 있는 재료', 34, GRAY), 330, 345, 1, prog(t, 2.3, 2.7))
    for i, (n, x) in enumerate(zip(('고추장', '간장', '설탕'), (480, 960, 1440))):
        a0 = 2.5 + 0.12 * i
        on = int(t >= 2.9 + 0.4 * i)
        s, a = pop(t, a0)
        bump = 1 + 0.08 * math.sin(math.pi * prog(t, 2.9 + 0.4 * i, 3.25 + 0.4 * i)) if on else 1
        put(fr, CHK[(n, on)], x, 425, s * bump, a)
    if t >= 4.3:
        pop_put(fr, chip('비교합니다', 40, YEL, DEEP, 40, 66), 960, 525, t, 4.3)
    for i, (lay, x) in enumerate(zip(FEATS, (560, 960, 1360))):
        a0 = 4.7 + 0.35 * i
        s, a = pop(t, a0)
        bob = 5 * math.sin((t - a0) * 3) if t > a0 + 0.6 else 0
        put(fr, lay, x, 690 + bob, s, a)
        if i == 2: put(fr, BOWL_P, x, 655 + bob, 0.5 * s, a)
    return vfinish(fr, t)

# ---------------------------------------------------------------- M06 (45-55) 마라탕
CAPS06 = [(0.6, 3.6, '마라탕 재료 구매액을 28,000원으로 가정합니다.'),
          (3.6, 5.2, '구매한 재료로 두 끼를 모두 먹는 조건입니다.'),
          (5.2, 7.0, '한 끼 평균은 14,000원으로, 배달보다 900원 낮습니다.'),
          (7.0, 8.2, '이번에는 한 끼만 먹는 조건입니다.'),
          (8.2, 10.0, '조리 부담을 줄이는 배달도 좋은 선택입니다.')]
def ctl_lay(sel):
    w, h = 520, 470
    def fn(d):
        d.rr((4, 4, w - 4, h - 4), 30, WHITE, LINE, 4)
        d.tx((w / 2, 44), '구매한 재료로 먹는 끼니', 32, GRAY, 'mm', False)
        for j, lab in enumerate(('1끼만', '2끼 모두')):
            y0 = 90 + 140 * j; on = (sel == j)
            d.rr((36, y0, 484, y0 + 120), 26, MINT if on else (240, 244, 240), None, 0)
            d.tx((340, y0 + 60), lab, 46, WHITE if on else GRAY)
        d.tx((w / 2, 393), '요리 약 50분', 32, DEEP, 'mm', False)
        d.tx((w / 2, 435), '배달 약 30분', 32, DEEP, 'mm', False)
    return Lay(w, h, fn)
CTL = [ctl_lay(0), ctl_lay(1)]
BASE_Y, SCL = 700, 0.016
def bar_lay(h, col, label):
    w = 260; hh = max(4, int(h))
    def fn(d):
        d.rr((0, 0, w, hh), 24, col)
        if hh > 90: d.tx((w / 2, 50), label, 54, WHITE)
    return Lay(w, hh, fn)
def m06m(t):
    fr = base(); title(fr, t, '몇 끼를 먹느냐에 따라')
    s = clamp(eio(prog(t, 3.6, 4.0)) - eio(prog(t, 7.0, 7.4)))
    pc = eo3(prog(t, 0.2, 0.7))
    put(fr, CTL[0], 360, 430, 1, pc * (1 - s)); put(fr, CTL[1], 360, 430, 1, pc * s)
    put(fr, BOWL_P, 215, 340, 0.42, pc)
    put(fr, BOWL_P, 215, 480, 0.42, pc); put(fr, BOWL_P, 295, 480, 0.42, pc)
    # 막대
    sb = clamp(eio(prog(t, 4.0, 5.2)) - eio(prog(t, 7.2, 8.2)))
    v = lerp(28000, 14000, sb) * eo3(prog(t, 0.5, 1.7))
    cx1, cx2 = 1000, 1460
    h1 = v * SCL
    pg = eo3(prog(t, 1.0, 2.0)); h2 = 14900 * SCL * pg
    put(fr, Lay(1100, 6, lambda d: d.rr((0, 0, 1100, 6), 3, GRAY)), 1230, BASE_Y + 3, 1, pc)
    if h1 > 8:
        L = bar_lay(h1, MINT, f'{int(round(v / 100) * 100):,}원')
        put(fr, L, cx1, BASE_Y - L.h / 2, 1, 1)
    if h2 > 8:
        L = bar_lay(h2, DEEP, '14,900원')
        put(fr, L, cx2, BASE_Y - L.h / 2, 1, 1)
    put(fr, T('요리 · 한 끼 평균', 36, DEEP), cx1, BASE_Y + 42, 1, pc)
    put(fr, T('배달 · 한 끼', 36, DEEP), cx2, BASE_Y + 42, 1, pc)
    if t >= 2.0:
        ya = BASE_Y - 14900 * SCL
        pl = prog(t, 2.0, 2.6)
        x1 = 760 + (1700 - 760) * pl
        for xx in np.arange(760, x1, 30):
            put(fr, Lay(18, 5, lambda d: d.rr((0, 0, 18, 5), 2, DYEL)), xx + 9, ya, 1, 1)
    if t >= 5.3 and t < 7.0:
        pop_put(fr, chip('배달보다 900원 낮음', 38, YEL, DEEP, 36, 64), cx1, BASE_Y - 14000 * SCL - 46, t, 5.3)
    if t >= 8.2:
        pop_put(fr, chip('한 끼만 계획 → 배달도 좋은 선택', 40, YEL, DEEP, 44, 70), 1230, 815, t, 8.2)
    return vfinish(fr, t)

# ---------------------------------------------------------------- M07 (55-64) 남은 재료
CAPS07 = [(0.6, 2.7, '레시피 안내에 따라 요리합니다.'), (2.7, 5.7, '남은 재료는 직접 확인해 저장합니다.'),
          (5.7, 9.0, '재료가 충분하면 다음 날 볶음밥을 만들 수 있습니다.')]
def panel_lay(head, active=False):
    w, h = 540, 580
    def fn(d):
        d.rr((4, 4, w - 4, h - 4), 30, WHITE, MINT if active else LINE, 6 if active else 4)
        d.tx((w / 2, 52), head, 40, DEEP)
    return Lay(w, h, fn)
PANELS = [panel_lay('오늘의 요리'), panel_lay('남은 재료를 확인합니다'), panel_lay('내일의 한 끼')]
PANELS_A = [panel_lay('오늘의 요리', True), panel_lay('남은 재료를 확인합니다', True), panel_lay('내일의 한 끼', True)]
def step_lay(n, name, st):
    w, h = 460, 88
    def fn(d):
        bg = {0: (240, 244, 240), 1: (255, 244, 210), 2: PALE}[st]
        d.rr((3, 3, w - 3, h - 3), 22, bg, YEL if st == 1 else None, 4 if st == 1 else 0)
        d.el((24, 20, 68, 64), MINT if st == 2 else WHITE, MINT if st == 2 else LINE, 4)
        if st == 2: d.ln([(34, 43), (43, 52), (58, 33)], WHITE, 6)
        else: d.tx((46, 42), str(n), 28, GRAY)
        d.tx((90, 44), name, 38, DEEP, 'lm')
    return Lay(w, h, fn)
STEPS = {(i, st): step_lay(i + 1, n, st) for i, n in enumerate(('준비하기', '볶기', '담기')) for st in (0, 1, 2)}
def item_lay(name, on):
    w, h = 460, 80
    def fn(d):
        d.rr((3, 3, w - 3, h - 3), 20, PALE if on else (240, 244, 240))
        d.rr((22, 18, 66, 62), 10, MINT if on else WHITE, MINT if on else LINE, 4)
        if on: d.ln([(31, 41), (41, 51), (57, 30)], WHITE, 6)
        d.tx((88, 41), name, 38, DEEP, 'lm')
    return Lay(w, h, fn)
ITEMS = {(n, o): item_lay(n, o) for n in ('돼지고기', '양파', '대파', '계란') for o in (0, 1)}
BTN = [Lay(440, 76, lambda d, c=c: (d.rr((0, 0, 440, 76), 38, c), d.tx((220, 38), '직접 선택 후 저장', 36, WHITE))) for c in (MINT, DMINT)]
CLOCK = Lay(160, 160, lambda d: (d.el((8, 8, 152, 152), (240, 244, 240), LINE, 6), d.ln([(80, 80), (80, 38)], GRAY, 7), d.ln([(80, 80), (108, 96)], GRAY, 7)))
def arrow_lay(p):
    def fn(d):
        x1 = 10 + 100 * p
        d.ln([(10, 40), (x1, 40)], MINT, 8)
        if p > 0.85: d.ln([(x1 - 22, 18), (x1, 40), (x1 - 22, 62)], MINT, 8)
    return Lay(120, 80, fn)
def m07(t):
    fr = base(); title(fr, t, '남은 재료, 다음 한 끼로')
    xs, cy = (330, 960, 1590), 520
    act = 0 if t < 2.7 else (1 if t < 5.7 else 2)
    for i, x in enumerate(xs):
        a0 = 0.1 + 0.15 * i
        p = eob(prog(t, a0, a0 + 0.55), 1.2)
        L = PANELS_A[i] if act == i else PANELS[i]
        put(fr, L, x, cy + (1 - p) * 40, 1.0 + (0.015 if act == i else 0), min(1, p * 2.5))
    top = cy - 290
    # 패널1: 레시피
    for i in range(3):
        a = (0.7, 1.4, 2.0)[i]
        st = 2 if t >= a + 0.7 else (1 if t >= a else 0)
        bump = 1 + 0.05 * math.sin(math.pi * prog(t, a + 0.7, a + 1.0)) if st == 2 else 1
        put(fr, STEPS[(i, st)], xs[0], top + 150 + i * 104, bump, prog(t, 0.4 + 0.1 * i, 0.8 + 0.1 * i))
    putL(fr, T('레시피 안내를 따라 진행', 28, GRAY, False), xs[0] - 175, top + 535, 1, prog(t, 0.6, 1.0))
    # 패널2: 체크리스트
    for i, n in enumerate(('돼지고기', '양파', '대파', '계란')):
        a = 3.2 + 0.4 * i
        on = int(t >= a)
        bump = 1 + 0.06 * math.sin(math.pi * prog(t, a, a + 0.3)) if on else 1
        put(fr, ITEMS[(n, on)], xs[1], top + 140 + i * 92, bump, prog(t, 0.6 + 0.1 * i, 1.0 + 0.1 * i))
    pr = t >= 5.0 and t < 5.25
    put(fr, BTN[1 if pr else 0], xs[1], top + 535, 0.95 if pr else 1, prog(t, 1.0, 1.4))
    # 화살표
    for k, (xa, a0) in enumerate(((645, 2.4), (1275, 5.4))):
        p = eio(prog(t, a0, a0 + 0.5))
        if p > 0.02: put(fr, arrow_lay(p), xa + 25, cy, 1, 1)
    # 패널3: 내일의 한 끼
    if t < 5.7:
        put(fr, CLOCK, xs[2], cy - 10, 1, 1)
        put(fr, T('다음 한 끼를 계획합니다', 36, GRAY, False), xs[2], cy + 110, 1, 1)
    else:
        s, a = pop(t, 5.7, 0.55)
        put(fr, BOWL_R, xs[2], cy - 20 + 4 * math.sin((t - 5.7) * 3), 1.3 * s, a)
        pop_put(fr, T('돼지고기 볶음밥', 46, DEEP), xs[2], cy + 125, t, 6.1)
        pop_put(fr, chip('재료가 충분히 남았다면', 30, YEL, DEEP, 28, 54), xs[2], cy + 195, t, 6.5)
    return vfinish(fr, t)

# ---------------------------------------------------------------- M08 (64-72)
CAPS08 = [(0.6, 4.0, '혼자 식사하며 비용과 시간을 고민하는 사람을 돕습니다.'), (4.0, 8.0, '구매 연결 수수료를 수익 가설로 검토합니다.')]
PERSON = Lay(240, 300, lambda d: (d.el((70, 10, 170, 110), MINT), d.rr((30, 125, 210, 290), 70, MINT)))
def node_lay(head, sub, dashed=False):
    w, h = 360, 220
    def fn(d):
        if dashed:
            d.rr((4, 4, w - 4, h - 4), 30, (255, 248, 226), YEL, 6)
        else:
            d.rr((4, 4, w - 4, h - 4), 30, WHITE, LINE, 4)
        d.tx((w / 2, 86), head, 46, DEEP); d.tx((w / 2, 150), sub, 28, GRAY, 'mm', False)
    return Lay(w, h, fn)
NODES = [node_lay('이용자', '메뉴 · 재료 입력'), node_lay('요리 할래말래', '비용 · 시간 비교'),
         node_lay('구매 링크', '선택 후 이동'), node_lay('수수료', '수익 가설 · 미확정', True)]
def m08(t):
    fr = base()
    ta = 1 - prog(t, 3.5, 3.9)
    if ta > 0:
        put(fr, T('사업의 대상 사용자를 살펴봅니다', 60, DEEP), 960, 62 + (1 - eob(prog(t, 0.1, 0.7))) * 30, 1, prog(t, 0.1, 0.5) * ta)
        s = eob(prog(t, 0.3, 0.9), 1.3)
        put(fr, PERSON, 960, 330, 1.15 * s, min(1, prog(t, 0.3, 0.6)) * ta)
        pop_put(fr, chip('혼자 생활하는 2030세대', 40, YEL, DEEP, 44, 76), 1330, 300, t, 0.9, 0.5, 1, ta)
        # 식탁 + 한 그릇
        put(fr, Lay(520, 20, lambda d: d.rr((0, 0, 520, 20), 10, (205, 190, 160))), 960, 540, 1, prog(t, 0.6, 1.0) * ta)
        put(fr, BOWL_R, 960, 495, 0.55, prog(t, 0.8, 1.2) * ta)
        pop_put(fr, T('혼자 먹는 한 끼도, 계획 있게', 66, DEEP), 960, 650, t, 1.0, 0.5, 1, ta)
        for i, (lab, x) in enumerate(zip(('식비가 고민', '시간이 부족', '재료가 남음'), (560, 960, 1360))):
            pop_put(fr, chip(lab, 40, PALE, DEEP, 44, 76), x, 770, t, 1.6 + 0.35 * i, 0.45, 1, ta)
    tb = prog(t, 3.9, 4.4)
    if tb > 0:
        put(fr, T('수익 가설', 60, DEEP), 960, 62 + (1 - eo3(tb)) * 20, 1, tb)
        xs = (300, 740, 1180, 1620)
        for i, x in enumerate(xs):
            a0 = 4.3 + 0.5 * i
            pop_put(fr, NODES[i], x, 380, t, a0, 0.5)
            if i < 3:
                p = eio(prog(t, a0 + 0.25, a0 + 0.7))
                if p > 0.02:
                    put(fr, arrow_lay(p), (x + xs[i + 1]) / 2, 380, 0.85, 1)
        pop_put(fr, chip('확정 아님 · 실제 제휴 · 고객 · 매출 없음', 36, YEL, DEEP, 40, 66), 960, 600, t, 6.6)
        pop_put(fr, T('검증 후 연동 · 제휴를 검토합니다', 34, GRAY, False), 960, 690, t, 7.0)
    return vfinish(fr, t)

# ---------------------------------------------------------------- M09 (72-84)
CAPS09 = [(0.6, 4.0, '먼저 메뉴·가격·레시피 데이터를 정리합니다.'), (4.0, 8.0, '시연 프로토타입의 비교 기능을 검증합니다.'),
          (8.0, 12.0, '이용자 테스트 후 연동과 제휴를 검토합니다.')]
RX = [330, 750, 1170, 1590]
def road_node(n, st):
    def fn(d):
        col = {0: (225, 231, 226), 1: MINT, 2: MINT}[st]
        d.el((4, 4, 84, 84), col)
        d.tx((44, 45), str(n), 36, WHITE if st else GRAY)
    return Lay(88, 88, fn)
RN = {(n, st): road_node(n, st) for n in range(1, 5) for st in (0, 1, 2)}
def detail_lay(head, lines, dashed=False):
    w, h = 380, 320
    def fn(d):
        if dashed: d.rr((4, 4, w - 4, h - 4), 28, (255, 248, 226), YEL, 6)
        else: d.rr((4, 4, w - 4, h - 4), 28, WHITE, LINE, 4)
        d.tx((w / 2, 52), head, 40, DEEP)
        for i, l in enumerate(lines):
            d.el((26, 118 + i * 66 - 8, 42, 118 + i * 66 + 8), MINT if not dashed else YEL)
            d.tx((58, 118 + i * 66), l, 32, DEEP, 'lm', False)
    return Lay(w, h, fn)
DET = [detail_lay('데이터 정리', ['메뉴 목록', '재료 가격', '레시피 단계']),
       detail_lay('비교 기능 검증', ['재료비 − 보유 재료', '최소주문 충족', '끼니 수 평균']),
       detail_lay('이용자 테스트', ['혼자 사는 이용자', '사용 경험 · 이해도', '→ 개선 반영']),
       detail_lay('연동 · 제휴 검토', ['검증 결과 확인 후', '확정된 파트너 없음', '실제 연동은 이후'], True)]
LABS = ['데이터 정리', '비교 기능 검증', '이용자 테스트', '연동 · 제휴']
def m09(t):
    fr = base(); title(fr, t, '사업 실행 계획')
    put(fr, chip('향후 계획 · 현재는 시연 프로토타입 단계', 34, YEL, DEEP, 36, 60), 960, 150, 1, prog(t, 0.3, 0.7))
    LY = 290
    pl = prog(t, 0.2, 0.8)
    put(fr, Lay(1260, 10, lambda d: d.rr((0, 0, 1260, 10), 5, LINE)), 960, LY, 1, pl)
    starts = (0.5, 4.0, 8.0, 10.6)
    mk = [RX[0]]
    # 진행선
    t_marks = [(0.5, RX[0]), (3.6, RX[0]), (4.4, RX[1]), (7.6, RX[1]), (8.4, RX[2]), (10.2, RX[2]), (11.0, RX[3])]
    mx = RX[0]
    for (ta_, xa), (tb_, xb) in zip(t_marks, t_marks[1:]):
        if t >= tb_: mx = xb
        elif t > ta_: mx = lerp(xa, xb, eio(prog(t, ta_, tb_))); break
    w = max(4, mx - RX[0])
    put(fr, Lay(int(w), 10, lambda d: d.rr((0, 0, int(w), 10), 5, MINT)), RX[0] + w / 2, LY, 1, pl)
    for i in range(4):
        st = 2 if t >= starts[i] + (3.2 if i < 3 else 99) else (1 if t >= starts[i] else 0)
        s, a = pop(t, 0.2 + 0.1 * i)
        sc = 1.0 + (0.12 * math.sin(math.pi * prog(t, starts[i], starts[i] + 0.5)))
        put(fr, RN[(i + 1, st)], RX[i], LY, s * sc, a)
        put(fr, T(LABS[i], 34, DEEP if st else GRAY), RX[i], LY + 76, 1, a)
        if t >= starts[i] + 0.2:
            pop_put(fr, DET[i], RX[i], 650, t, starts[i] + 0.2, 0.5)
    return vfinish(fr, t)

# ---------------------------------------------------------------- M10 (84-90)
CAPS10 = [(0.6, 3.0, '비교와 선택부터 다음 식사까지 돕습니다.'), (3.0, 6.0, '요리 할래말래입니다.')]
def m10(t):
    fr = Image.new('RGB', (W, H), DEEP)
    ImageDraw.Draw(fr).rectangle([0, 0, W, 10], fill=MINT)
    put(fr, T('오늘의 조건에 맞는 한 끼', 56, (200, 225, 220), False), 960, 290, 1, prog(t, 0.5, 1.0))
    s = eob(prog(t, 0.7, 1.5), 1.4)
    put(fr, T('요리 할래말래', 150, WHITE), 960, 440, 0.8 + 0.2 * s, min(1, prog(t, 0.7, 1.1)))
    for x, lay, a0 in ((330, BOWL_P, 1.0), (1590, BOWL_R, 1.2)):
        put(fr, lay, x, 440 + 8 * math.sin(t * 2.4 + x), 0.95, prog(t, a0, a0 + 0.5))
    for i, (lab, col, tc, x) in enumerate((('비용', MINT, WHITE, 760), ('재료', YEL, DEEP, 960), ('시간', MINT, WHITE, 1160))):
        pop_put(fr, chip(lab, 44, col, tc, 46, 80), x, 600, t, 1.8 + 0.3 * i)
    return vfinish(fr, t)

# ---------------------------------------------------------------- 장면표
CAPS_CORE = {
    'M03': [(0.6, 4.1, '보유 양념을 제외한 추가 구매액은 11,500원입니다.'), (4.1, 10.0, '다음 끼니에 쓸 계란을 더해 최소주문을 채웁니다.')],
    'M04': [(0.6, 3.7, '오늘 결제액은 15,000원입니다.'), (3.7, 7.4, '제육 두 끼와 볶음밥 한 끼를 모두 먹으면 평균 5,000원입니다.'),
            (7.4, 10.0, '오늘 결제액과 한 끼 평균은 다릅니다.')],
    'M05': [(0.6, 4.8, '장보기 대기 20분과 조리 15분을 합하면 35분입니다.'), (4.8, 9.0, '배달은 28분이며, 요리에는 7분이 더 걸립니다.')],
}
SCENES = [
    dict(n='M01', s=0, e=8, fn=m01, caps=CAPS01, in_wipe=False),
    dict(n='M02', s=8, e=16, fn=m02, caps=CAPS02),
    dict(n='M03', s=16, e=26, fn=core.m04, caps=CAPS_CORE['M03']),
    dict(n='M04', s=26, e=36, fn=core.m05, caps=CAPS_CORE['M04']),
    dict(n='M05', s=36, e=45, fn=core.m06, caps=CAPS_CORE['M05']),
    dict(n='M06', s=45, e=55, fn=m06m, caps=CAPS06),
    dict(n='M07', s=55, e=64, fn=m07, caps=CAPS07),
    dict(n='M08', s=64, e=72, fn=m08, caps=CAPS08),
    dict(n='M09', s=72, e=84, fn=m09, caps=CAPS09),
    dict(n='M10', s=84, e=90, fn=m10, caps=CAPS10, dark=True, out_wipe=False),
]
for sc in SCENES: sc['dur'] = sc['e'] - sc['s']

def frame_at(t):
    global CUR
    for sc in SCENES:
        if sc['s'] <= t < sc['e'] or sc is SCENES[-1]:
            CUR = sc
            return sc['fn'](min(t - sc['s'], sc['dur'] - 1e-3))

# ---------------------------------------------------------------- 오디오
def at(s, t): return SC_START[s] + t
SC_START = {sc['n']: sc['s'] for sc in SCENES}

def sfx_all():
    A = core
    def sw(t, p=0.0): A.s_swipe(t, p)
    for n in SC_START: sw(SC_START[n]);
    # M01
    A.s_hit(0.15); sw(0.2, -0.2); sw(0.35, 0.2)
    for i in range(10): A.s_tick(0.75 + 0.09 * i, 1500 + 40 * i)
    A.s_pop(2.4, 620); A.s_accent(4.1); A.s_warn(4.2)
    for i, f in enumerate((520, 620, 740)): A.s_pop(5.0 + 0.4 * i, f)
    A.s_pop(6.9, 880)
    # M02
    b = 8
    for i in range(4): A.s_tap(b + 0.9 + 0.3 * i, 980 + 60 * i)
    for i in range(3): A.s_pop(b + 2.5 + 0.12 * i, 520 + 60 * i)
    for i in range(3): A.s_tap(b + 2.9 + 0.4 * i, 1240); A.s_confirm(b + 2.95 + 0.4 * i) if False else None
    A.s_pop(b + 4.3, 700);
    for i, f in enumerate((560, 660, 780)): A.s_pop(b + 4.7 + 0.35 * i, f)
    A.s_confirm(b + 5.8)
    # M03 / M04 / M05: 기존 장면의 효과음(오프셋 적용)
    def shifted(off, fnc):
        orig = (A.sfx,)
        def sfx2(t0, x, pan=0.0, g=1.0): orig[0](t0 + off, x, pan, g)
        A.sfx = sfx2
        try: fnc()
        finally: A.sfx = orig[0]
    def cart():
        A.s_hit(0.0); [A.s_swipe(tt, -0.2) for tt in (0.7, 1.05, 1.4)]
        A.s_pop(1.5, 560); A.s_tap(1.65); A.s_tap(2.35); A.s_pop(2.4, 700)
        A.s_swipe(3.2); A.s_warn(3.9); A.s_swipe(4.0, 0.2)
        A.s_thump(6.0); A.s_tap(6.2); A.s_tap(7.1, 1240); A.s_confirm(7.2)
        A.s_pop(8.1, 520)
        for i, f in enumerate((560, 660, 780)): A.s_pop(8.4 + 0.2 * i, f)
    def cost():
        A.s_hit(0.0); A.s_swipe(0.15, -0.3); A.s_swipe(0.3, 0.3)
        for i in range(3): A.s_pop(3.5 + 0.15 * i, 880 + 80 * i)
        A.s_swipe(4.4)
        A.s_pop(4.5, 600); A.s_accent(4.7)
        A.s_swipe(6.0); A.s_pop(6.6, 520); A.s_accent(6.65)
    def tim():
        A.s_hit(0.0)
        for i, tt in enumerate(A.crossings(A.mins1, 0.3, 2.9)): A.s_tick(tt, 1500 + 15 * i)
        for i, tt in enumerate(A.crossings(A.mins2, 3.1, 4.9)): A.s_tick(tt, 1900 + 15 * i)
        for i, tt in enumerate(A.crossings(A.mins3, 5.1, 6.9)): A.s_tick(tt, 1300 + 15 * i)
        A.s_pop(4.9, 640); A.s_pop(7.4, 560); A.s_confirm(7.45)
    shifted(16, cart); shifted(26, cost); shifted(36, tim)
    # M06
    b = 45
    A.s_swipe(b + 0.5); A.s_pop(b + 1.6, 600); A.s_pop(b + 2.0, 520); A.s_swipe(b + 2.0, 0.2)
    A.s_tap(b + 3.6, 1240); A.s_swipe(b + 4.0, 0.3); A.s_confirm(b + 5.2); A.s_accent(b + 5.3)
    A.s_tap(b + 7.0, 1040); A.s_swipe(b + 7.2, -0.3); A.s_pop(b + 7.8, 560)
    # M07
    b = 55
    for tt in (1.4, 2.0, 2.6): A.s_tap(b + tt, 1240)
    for i in range(4): A.s_tap(b + 3.2 + 0.4 * i, 1240 + 60 * i)
    A.s_thump(b + 5.0); sw(b + 5.4); A.s_confirm(b + 5.7); A.s_pop(b + 6.1, 700); A.s_pop(b + 6.5, 820)
    # M08
    b = 64
    A.s_pop(b + 0.4, 520)
    for i in range(3): A.s_pop(b + 1.6 + 0.35 * i, 620 + 60 * i)
    for i in range(4): A.s_pop(b + 4.3 + 0.5 * i, 520 + 50 * i)
    A.s_pop(b + 6.6, 700); A.s_accent(b + 6.7)
    # M09
    b = 72
    for i, tt in enumerate((0.2, 0.3, 0.4, 0.5)): A.s_pop(b + tt, 500 + 50 * i)
    for tt in (0.5, 4.0, 8.0, 10.6): A.s_confirm(b + tt)
    for tt in (0.7, 4.2, 8.2, 10.8): sw(b + tt)
    # M10
    b = 84
    A.s_hit(b); A.s_accent(b + 0.9); A.s_confirm(b + 1.0)
    for i in range(3): A.s_pop(b + 1.8 + 0.3 * i, 640 + 90 * i)
    A.s_confirm(b + 3.0); A.s_accent(b + 3.1)

def inten(t):
    xs = [0, 4, 8, 12, 16, 26, 36, 45, 55, 64, 72, 78, 84, 88, 90]
    ys = [0.12, 0.30, 0.40, 0.55, 0.85, 0.85, 0.80, 0.60, 0.50, 0.35, 0.50, 0.70, 0.85, 0.45, 0.20]
    return float(np.interp(t, xs, ys))
core.inten = inten

def build_audio(path):
    core.sfx_all = None
    sfx_all(); core.music()
    t = np.arange(core.N) / core.SR
    env = np.minimum(1, t / 0.4) * np.minimum(1, np.maximum(0, (TOT - t) / 1.5))
    m = core.MUS * env * 0.62
    L = m + core.SFX_L; R = m + core.SFX_R
    pk = max(np.abs(L).max(), np.abs(R).max())
    if pk > 0.9: L, R = L * 0.9 / pk, R * 0.9 / pk
    L, R = np.tanh(L * 1.05), np.tanh(R * 1.05)
    pcm = (np.clip(np.stack([L, R], 1), -1, 1) * 32767).astype('<i2')
    with wave.open(path, 'wb') as wf:
        wf.setnchannels(2); wf.setsampwidth(2); wf.setframerate(core.SR); wf.writeframes(pcm.tobytes())
    print('audio peak', float(pk), 'rms', float(np.sqrt(np.mean(pcm.astype(np.float64) ** 2)) / 32768))

# ---------------------------------------------------------------- 자막 / 출력
def ts(x):
    h = int(x // 3600); m = int(x % 3600 // 60); s = int(x % 60); ms = int(round((x - int(x)) * 1000))
    if ms == 1000: s += 1; ms = 0
    return f'{h:02d}:{m:02d}:{s:02d},{ms:03d}'
def write_srt(path):
    n = 0
    with open(path, 'w', encoding='utf-8') as f:
        for sc in SCENES:
            for (a, b, txt) in sc['caps']:
                n += 1
                f.write(f'{n}\n{ts(sc["s"] + a)} --> {ts(sc["s"] + b)}\n{txt}\n\n')

def _fb(n): return frame_at(n / FPS).tobytes()

def render():
    wav = os.path.join(OUT, '_audio.wav'); build_audio(wav)
    outp = os.path.join(OUT, 'motion_graphic_90s.mp4')
    cmd = ['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS),
           '-i', '-', '-i', wav, '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '18', '-preset', 'medium',
           '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart', '-t', str(TOT), outp]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=open(os.path.join(OUT, 'ffmpeg.log'), 'w'))
    nf = int(TOT * FPS)
    with Pool(2) as pool:
        for i, b in enumerate(pool.imap(_fb, range(nf), chunksize=6)):
            p.stdin.write(b)
            if i % 144 == 0: print('frame', i, '/', nf, flush=True)
    p.stdin.close(); p.wait()
    write_srt(os.path.join(OUT, 'subtitles_v3.srt'))
    os.remove(wav)
    print('done', outp)

def stills():
    sel = sys.argv[2:] or [sc['n'] for sc in SCENES]
    for sc in SCENES:
        if sc['n'] not in sel: continue
        d = sc['dur']
        ts_ = [d * f for f in (0.2, 0.45, 0.7, 0.92)]
        sheet = Image.new('RGB', (1920, 1080))
        for i, tv in enumerate(ts_):
            im = frame_at(sc['s'] + tv).resize((960, 540), Image.LANCZOS)
            sheet.paste(im, ((i % 2) * 960, (i // 2) * 540))
        sheet.save(os.path.join(OUT, f'qa_{sc["n"]}.png'))
    print('stills ok')

if __name__ == '__main__':
    {'stills': stills, 'render': render}[sys.argv[1]]()
