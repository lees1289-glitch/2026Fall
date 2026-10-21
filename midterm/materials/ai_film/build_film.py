#!/usr/bin/env python3
# 요리 할래말래 - AI 영화 v5 : UI 장면 / 소리 / 조립
# 사용: python3 build_film.py ui [이름...] | audio | assemble | stills [이름...]
import os, sys, math, subprocess, wave, glob, shutil
import numpy as np
from PIL import Image, ImageDraw
from multiprocessing import Pool

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import core
from core import *  # noqa

OUT = os.environ.get('OUT', os.path.join(HERE, '_render'))
UIDIR = os.path.join(OUT, 'ui'); CLIPS = os.path.join(OUT, 'clips')   # CLIPS = Higgsfield 클립(S01.mp4 ...)
for d in (OUT, UIDIR, CLIPS): os.makedirs(d, exist_ok=True)
PALE = (221, 243, 235); SCRBG = (250, 251, 248); GRAYBG = (238, 242, 238)
FOOT_DEFAULT = '비공식 사업 제안 · 화면과 수치는 시연 예시'

# ============================================================ 화면(휴대폰) 틀
SW, SH = 628, 928          # 화면 크기
SX, SY = 646, 36           # 프레임 안 화면 왼쪽 위
PHONE = Lay(660, 960, lambda d: (d.rr((0, 0, 660, 960), 74, DEEP), d.rr((16, 16, 644, 944), 58, (30, 70, 76))))
SMASK = Image.new('L', (SW, SH), 0)
ImageDraw.Draw(SMASK).rounded_rectangle([0, 0, SW - 1, SH - 1], radius=48, fill=255)

def newscr(bg=SCRBG): return Image.new('RGB', (SW, SH), bg)
def frame_with(scr, foot=FOOT_DEFAULT, t=1.0, bg=BG):
    fr = Image.new('RGB', (W, H), bg)
    ImageDraw.Draw(fr).rectangle([0, 0, W, 10], fill=MINT)
    put(fr, PHONE, 960, 500, 1, 1)
    fr.paste(scr, (SX, SY), SMASK)
    put(fr, T(foot, 26, GRAY, False), 960, 1030, 1, prog(t, 0.1, 0.5))
    return fr

def cardL(w, h, fill=WHITE, outline=LINE, ow=3, r=26):
    return Lay(w, h, lambda d: d.rr((ow, ow, w - ow, h - ow), r, fill, outline, ow))
_card_cache = {}
def card(w, h, fill=WHITE, outline=LINE, ow=3, r=26):
    k = (w, h, fill, outline, ow, r)
    if k not in _card_cache: _card_cache[k] = cardL(*k)
    return _card_cache[k]
def popv(t, a, d=0.45):
    p = prog(t, a, a + d); return 0.7 + 0.3 * eob(p), min(1, p * 3)
def pput(im, lay, x, y, t, a, d=0.45, base_=1.0, al=1.0):
    s, a_ = popv(t, a, d); put(im, lay, x, y, s * base_, a_ * al)

_rows = {}
def rowlay(label, value, w=560, h=110, vcol=DEEP, size=34):
    k = (label, value, w, h, vcol, size)
    if k not in _rows:
        def fn(d):
            d.rr((3, 3, w - 3, h - 3), 24, WHITE, LINE, 3)
            d.tx((30, h / 2), label, size, DEEP, 'lm'); d.tx((w - 30, h / 2), value, size + 4, vcol, 'rm')
        _rows[k] = Lay(w, h, fn)
    return _rows[k]
_btn = {}
def btn(text, w=560, h=84, col=MINT, size=36):
    k = (text, w, h, col, size)
    if k not in _btn:
        _btn[k] = Lay(w, h, lambda d: (d.rr((0, 0, w, h), h / 2, col), d.tx((w / 2, h / 2), text, size, WHITE)))
    return _btn[k]
def ripple(im, x, y, t, a0, col=MINT):
    p = prog(t, a0, a0 + 0.5)
    if 0 < p < 1:
        r = int(20 + 70 * p); al = 1 - p
        L = Lay(2 * r + 12, 2 * r + 12, lambda d: d.el((6, 6, 2 * r + 6, 2 * r + 6), None, col, 6))
        put(im, L, x, y, 1, al)
def side(fr, t, text, a0, y=500, x=1560, size=56, col=YEL, tc=DEEP):
    if t < a0: return
    pput(fr, chip(text, size, col, tc, 44, int(size * 1.9)), x, y, t, a0, 0.5)

def appbar(scr, t, title='요리 할래말래'):
    put(scr, T(title, 32, DEEP), SW / 2, 56, 1, prog(t, 0, 0.3))
    put(scr, Lay(540, 4, lambda d: d.rr((0, 0, 540, 4), 2, LINE)), SW / 2, 96, 1, prog(t, 0, 0.3))

# 체크 행
_chk = {}
def chkrow(name, on, w=560, h=96):
    k = (name, on, w, h)
    if k not in _chk:
        def fn(d):
            d.rr((3, 3, w - 3, h - 3), 24, PALE if on else WHITE, MINT if on else LINE, 4)
            d.rr((24, h / 2 - 24, 72, h / 2 + 24), 12, MINT if on else WHITE, MINT if on else LINE, 4)
            if on: d.ln([(34, h / 2), (44, h / 2 + 11), (62, h / 2 - 12)], WHITE, 7)
            d.tx((96, h / 2), name, 38, DEEP, 'lm')
        _chk[k] = Lay(w, h, fn)
    return _chk[k]

# ============================================================ U02 배달 결제 (3초)
def u02(t):
    s = newscr()
    put(s, chip('배달 주문 · 가상 시연 화면', 26, DEEP, WHITE, 24, 50), SW / 2, 60, 1, prog(t, 0, 0.3))
    for i, (lab, val, y) in enumerate((('제육볶음 1인분', '13,000원', 210), ('배달비', '3,000원', 340))):
        p = eo3(prog(t, 0.2 + 0.25 * i, 0.6 + 0.25 * i))
        put(s, rowlay(lab, val), SW / 2 + (1 - p) * 120, y, 1, p)
    put(s, Lay(540, 4, lambda d: d.rr((0, 0, 540, 4), 2, LINE)), SW / 2, 430, 1, prog(t, 0.7, 1.0))
    p = prog(t, 1.0, 1.5)
    put(s, T('합계', 34, GRAY), 130, 500, 1, p)
    v = int(round(16000 * eo3(prog(t, 1.0, 1.6)) / 100) * 100)
    put(s, T(f'{v:,}원', 104, DEEP), SW / 2, 610, 0.85 + 0.15 * eob(p), min(1, p * 2))
    pb = prog(t, 1.6, 2.0)
    pulse = 1 + 0.025 * math.sin((t - 1.6) * 7) if t > 1.8 else 1
    put(s, btn('주문하기', 560, 92, DEEP, 40), SW / 2, 790, pulse * (0.85 + 0.15 * eob(pb)), min(1, pb * 3))
    return frame_with(s, '가격은 시연 예시 · 비공식 가상 화면', t)

# ============================================================ U04 검색 → 서비스 (6초)
QUERY = '제육볶음 배달 vs 직접 요리 비용'
def u04(t):
    s = newscr()
    xa = -(eio(prog(t, 3.1, 3.6))) * SW          # 검색 화면이 왼쪽으로
    xb = (1 - eio(prog(t, 3.1, 3.6))) * SW        # 홈 화면이 오른쪽에서
    if xa > -SW:
        a = Image.new('RGB', (SW, SH), SCRBG)
        put(a, card(560, 84, WHITE, MINT, 4, 42), SW / 2, 150, 1, 1)
        put(a, Lay(40, 40, lambda d: (d.el((4, 4, 28, 28), None, GRAY, 4), d.ln([(24, 24), (34, 34)], GRAY, 4))), 70, 150, 1, 1)
        n = int(len(QUERY) * clamp((t - 0.15) / 1.3)) if t > 0.15 else 0
        if n: putL(a, T(QUERY[:n], 26, DEEP, False), 100, 150, 1, 1)
        for i, y in enumerate((300, 640)):
            put(a, Lay(560, 160, lambda d: (d.rr((3, 3, 557, 157), 22, WHITE, LINE, 3), d.rr((24, 30, 300, 48), 9, (225, 230, 226)), d.rr((24, 70, 520, 84), 7, (236, 240, 236)), d.rr((24, 100, 460, 114), 7, (236, 240, 236)))), SW / 2, y, 1, prog(t, 1.4 + 0.1 * i, 1.8 + 0.1 * i))
        pr = prog(t, 1.7, 2.2)
        sc = (0.94 if 2.6 < t < 2.8 else 1.0)
        put(a, card(560, 210, WHITE, MINT, 5, 26), SW / 2, 470, (0.92 + 0.08 * eob(pr)) * sc, min(1, pr * 3))
        put(a, T('요리 할래말래', 40, DEEP), SW / 2, 430, sc, min(1, pr * 3))
        put(a, T('메뉴와 보유 재료로 비용·시간 비교', 24, GRAY, False), SW / 2, 485, sc, min(1, pr * 3))
        put(a, chip('시연 검색 결과', 22, PALE, DMINT, 20, 40), SW / 2, 540, sc, min(1, pr * 3))
        ripple(a, SW / 2, 470, t, 2.6)
        s.paste(a, (int(xa), 0))
    if xb < SW:
        b = Image.new('RGB', (SW, SH), SCRBG)
        appbar(b, 99)
        putL(b, T('먹고 싶은 메뉴', 28, GRAY, False), 44, 160, 1, 1)
        put(b, card(560, 96, WHITE, MINT, 4, 30), SW / 2, 235, 1, 1)
        putL(b, T('제육볶음', 44, DEEP), 66, 235, 1, 1)
        put(b, BOWL_P, SW / 2, 480, 1.3 * (0.9 + 0.1 * eob(prog(t, 3.6, 4.2))), prog(t, 3.5, 4.0))
        put(b, T('보유 재료를 입력해 비교합니다', 26, GRAY, False), SW / 2, 680, 1, prog(t, 4.0, 4.5))
        pr = (0.95 if 5.4 < t < 5.6 else 1)
        put(b, btn('비교하기', 560, 92, MINT, 40), SW / 2, 800, pr, 1)
        ripple(b, SW / 2, 800, t, 5.4)
        s.paste(b, (int(xb), 0))
    return frame_with(s, '검색 결과는 시연용 연출 · 실제 검색 순위가 아닙니다', t)

# ============================================================ U05 보유 재료 → 금액 (4초)
def u05(t):
    s = newscr(); appbar(s, t)
    fa = 1 - prog(t, 1.6, 2.0)
    if fa > 0:
        put(s, T('보유 재료를 확인합니다', 36, DEEP), SW / 2, 170, 1, prog(t, 0, 0.3) * fa)
        for i, n in enumerate(('고추장', '간장', '설탕')):
            on = int(t >= 0.4 + 0.4 * i)
            bump = 1 + 0.05 * math.sin(math.pi * prog(t, 0.4 + 0.4 * i, 0.7 + 0.4 * i)) if on else 1
            put(s, chkrow(n, on), SW / 2, 300 + 120 * i, bump, prog(t, 0, 0.4 + 0.1 * i) * fa)
    fb = prog(t, 1.7, 2.1)
    if fb > 0:
        put(s, T('추가 구매 금액', 32, GRAY), SW / 2, 230, 1, fb)
        v = lerp(18200, 11500, eio(prog(t, 2.0, 2.9)))
        v = int(round(v / 100) * 100)
        put(s, T(f'{v:,}원', 112, DMINT if t > 2.9 else DEEP), SW / 2, 370, 1, fb)
        pput(s, chip('보유 양념 6,700원 제외', 30, YEL, DEEP, 30, 60), SW / 2, 480, t, 2.9)
        put(s, T('최소주문 충족 전', 30, GRAY, False), SW / 2, 580, 1, prog(t, 3.1, 3.5))
    f = frame_with(s, '재료 가격은 시연 예시 · 밥·식용유·소금은 보유로 가정', t)
    side(f, t, '추가 구매 11,500원', 3.0, 500)
    return f

# ============================================================ U06 장바구니 (6초)
def barL(v):
    w = 520; fw = max(0, v / 15000 * w)
    def fn(d):
        d.rr((0, 0, w, 44), 22, (251, 240, 205), YEL, 3)
        if fw > 2: d.rr((0, 0, fw, 44), 22, MINT)
    return Lay(w, 44, fn)
def u06(t):
    s = newscr(); appbar(s, t, '장바구니')
    fill = 11500 + 3500 * eio(prog(t, 2.7, 3.5))
    v = int(round(fill / 100) * 100)
    put(s, T('장바구니 합계', 28, GRAY, False), SW / 2, 160, 1, prog(t, 0, 0.3))
    put(s, T(f'{v:,}원', 96, DMINT if v >= 15000 else DEEP), SW / 2, 250, 1, prog(t, 0, 0.3))
    put(s, T('최소주문 15,000원', 30, DEEP), SW / 2, 345, 1, prog(t, 0.2, 0.5))
    put(s, barL(fill), SW / 2, 400, 1, prog(t, 0.2, 0.6))
    if t < 3.5:
        pput(s, chip('3,500원 부족', 32, YEL, DEEP, 32, 60), SW / 2, 480, t, 0.5, 0.45, 1, 1 - prog(t, 3.0, 3.4))
    else:
        pput(s, chip('최소주문 충족', 32, MINT, WHITE, 32, 60), SW / 2, 480, t, 3.5)
    if t >= 1.2:
        pr = 0.94 if 2.6 < t < 2.85 else 1.0
        a = 1 - prog(t, 3.6, 4.0)
        pput(s, card(560, 120, WHITE, YEL, 5, 26), SW / 2, 590, t, 1.2, 0.5, pr, a)
        pput(s, T('계란  3,500원 추가', 38, DEEP), SW / 2, 590, t, 1.3, 0.5, pr, a)
        ripple(s, SW / 2, 590, t, 2.6, YEL)
    if t >= 4.0:
        for i, (lay, lab) in enumerate(((BOWL_P, '제육'), (BOWL_P, '제육'), (BOWL_R, '볶음밥'))):
            x = 154 + 160 * i
            p = prog(t, 4.0 + 0.2 * i, 4.5 + 0.2 * i)
            put(s, lay, x, 620, 0.55 * (0.5 + 0.5 * eob(p)), min(1, p * 3))
            put(s, T(lab, 28, GRAY), x, 705, 1, min(1, p * 3))
        pput(s, chip('제육 2끼 + 볶음밥 1끼 계획', 28, DEEP, WHITE, 28, 58), SW / 2, 800, t, 4.9)
    f = frame_with(s, '계획 없는 추가 구매는 절약이 아닙니다 · 가격은 시연 예시', t)
    side(f, t, '15,000원', 3.4, 450, 1560, 72)
    return f

# ============================================================ U07 비교 (8초)
def u07(t):
    s = newscr(); appbar(s, t, '비교 결과')
    p1 = eo3(prog(t, 0.2, 0.7)); p2 = eo3(prog(t, 0.5, 1.0))
    put(s, card(560, 410, WHITE, LINE, 3, 28), SW / 2 - (1 - p1) * 120, 330, 1, p1)
    put(s, chip('요리', 28, MINT, WHITE, 30, 52), 102, 156, 1, p1)
    pput(s, T('오늘 15,000원', 64, DEEP), SW / 2, 232, t, 1.0)
    for i in range(3):
        a = prog(t, 1.6 + 0.1 * i, 2.1 + 0.1 * i)
        put(s, (BOWL_R if i == 2 else BOWL_P), 154 + 160 * i, 355, 0.42 * (0.6 + 0.4 * eob(a)), min(1, a * 3))
        p_ = eio(prog(t, 2.2 + 0.2 * i, 2.9 + 0.2 * i)); q = eio(prog(t, 3.7, 4.2))
        x = lerp(lerp(SW / 2, 154 + 160 * i, p_), SW / 2, q); y = lerp(250, 440, p_)
        put(s, chip('5,000원', 24, YEL, DEEP, 14, 42), x, y, 1, min(1, p_ * 3) * (1 - q))
    pput(s, chip('평균 5,000원', 34, MINT, WHITE, 36, 60), SW / 2, 452, t, 3.9)
    put(s, T('3끼 계획 · 식사까지 35분', 26, GRAY, False), SW / 2, 512, 1, prog(t, 4.6, 5.0))
    put(s, card(560, 190, WHITE, LINE, 3, 28), SW / 2 + (1 - p2) * 120, 640, 1, p2)
    put(s, chip('배달', 28, DEEP, WHITE, 30, 52), 102, 580, 1, p2)
    pput(s, T('오늘 16,000원', 56, DEEP), SW / 2, 640, t, 1.2)
    put(s, T('1끼 · 식사까지 28분', 26, GRAY, False), SW / 2, 702, 1, prog(t, 4.8, 5.2))
    pput(s, chip('오늘 지출 1,000원 적게', 28, YEL, DEEP, 30, 54), SW / 2, 778, t, 6.0)
    pput(s, chip('식사까지 7분 더', 28, YEL, DEEP, 30, 54), SW / 2, 826, t, 6.3)
    pr = 0.95 if 7.4 < t < 7.65 else 1
    put(s, btn('요리로 선택하기', 560, 60, MINT, 32), SW / 2, 892, pr, prog(t, 6.6, 7.0))
    ripple(s, SW / 2, 892, t, 7.4)
    # 2026-10-21 revision: enlarge the comparison cards without changing timing.
    f = Image.new('RGB', (W, H), BG)
    ImageDraw.Draw(f).rectangle([0, 0, W, 10], fill=MINT)
    put(f, T('오늘의 비용과 시간을 비교합니다', 62, DEEP), 960, 105, 1, prog(t, 0, 0.4))
    # Extract the original animated cards, then enlarge them side by side.
    cooking = s.crop((30, 120, 598, 540)).resize((738, 546), Image.Resampling.LANCZOS)
    delivery = s.crop((30, 540, 598, 740)).resize((738, 260), Image.Resampling.LANCZOS)
    f.paste(cooking, (140, 210)); f.paste(delivery, (1042, 210))
    pput(f, chip('오늘 결제액 ≠ 한 끼 평균', 42, MINT, WHITE, 36, 76), 1411, 550, t, 3.9)
    pput(f, T('오늘 지출 1,000원 적게', 44, DEEP), 1411, 650, t, 6.0)
    pput(f, T('식사까지 7분 더', 40, DEEP), 1411, 720, t, 6.3)
    put(f, btn('요리로 선택하기', 660, 90, MINT, 40), 960, 900, pr, prog(t, 6.6, 7.0))
    ripple(f, 960, 900, t, 7.4)
    put(f, T('가정: 보유 재료 비용 제외 · 세 끼 모두 소비 · 장보기 배송비 0원 · 수치는 시연 예시', 27, GRAY, False), 960, 1030, 1, prog(t, 0.1, 0.5))
    return f

# ============================================================ U09 레시피 (2초)
def u09(t):
    s = newscr(); appbar(s, t, '레시피 안내')
    put(s, T('제육볶음', 44, DEEP), SW / 2, 170, 1, prog(t, 0, 0.3))
    for i, (n, st) in enumerate((('재료 준비하기', 2), ('고기와 채소 볶기', 1), ('그릇에 담기', 0))):
        y = 300 + 120 * i
        bg = {0: GRAYBG, 1: (255, 244, 210), 2: PALE}[st]
        sc = 1 + (0.03 * math.sin(t * 8) if st == 1 else 0)
        put(s, Lay(560, 96, lambda d, st=st, n=n, bg=bg: (d.rr((3, 3, 557, 93), 24, bg, YEL if st == 1 else None, 4 if st == 1 else 0),
            d.el((24, 24, 72, 72), MINT if st == 2 else WHITE, MINT if st == 2 else LINE, 4),
            d.ln([(34, 49), (44, 59), (62, 38)], WHITE, 6) if st == 2 else d.tx((48, 48), str(i + 1), 28, GRAY),
            d.tx((96, 48), n, 36, DEEP, 'lm'))), SW / 2, y, sc, prog(t, 0.05 * i, 0.3 + 0.05 * i))
    put(s, chip('볶는 중', 30, YEL, DEEP, 30, 56), SW / 2, 700, 1, prog(t, 0.5, 0.8))
    return frame_with(s, '화면은 시연 예시 · 계량과 익힘 기준은 검증 전 제공하지 않습니다', t)

# ============================================================ U11 남은 재료 (5초)
def u11(t):
    s = newscr(); appbar(s, t)
    put(s, T('남은 재료를 확인합니다', 40, DEEP), SW / 2, 170, 1, prog(t, 0, 0.3))
    put(s, T('남아 있는 재료를 직접 선택합니다', 24, GRAY, False), SW / 2, 225, 1, prog(t, 0.1, 0.4))
    for i, n in enumerate(('돼지고기', '양파', '대파', '계란')):
        a = 1.0 + 0.55 * i
        on = int(t >= a)
        bump = 1 + 0.05 * math.sin(math.pi * prog(t, a, a + 0.3)) if on else 1
        put(s, chkrow(n, on), SW / 2, 330 + 115 * i, bump, prog(t, 0.1 * i, 0.4 + 0.1 * i))
        ripple(s, 70, 330 + 115 * i, t, a)
    pr = 0.95 if 3.6 < t < 3.85 else 1
    put(s, btn('직접 선택 후 저장', 560, 88, DMINT if pr < 1 else MINT, 36), SW / 2, 850, pr, prog(t, 0.6, 1.0))
    ripple(s, SW / 2, 850, t, 3.6)
    if t >= 3.9:
        pput(s, chip('저장됨 ✓', 32, DEEP, WHITE, 36, 62), SW / 2, 780, t, 3.9)
    return frame_with(s, '남은 재료는 직접 입력합니다 · 정확한 잔량을 자동으로 알지 못합니다', t)

# ============================================================ U12 다음 한 끼 (2초)
def u12(t):
    s = newscr(); appbar(s, t)
    put(s, chip('다음 날', 30, DEEP, WHITE, 34, 58), SW / 2, 170, 1, prog(t, 0, 0.25))
    pput(s, card(560, 520, WHITE, MINT, 5, 32), SW / 2, 520, t, 0.1, 0.4)
    pput(s, BOWL_R, SW / 2, 470, t, 0.3, 0.4, 1.5)
    pput(s, T('남은 재료로 볶음밥', 44, DEEP), SW / 2, 640, t, 0.5)
    pput(s, T('재료가 충분히 남았다면 추가 구매 없이', 24, GRAY, False), SW / 2, 700, t, 0.7)
    return frame_with(s, '다음 요리가 가능한지는 남은 양을 확인해야 합니다', t)

# ============================================================ U14 마라탕 (6초)
def u14(t):
    s = newscr(); appbar(s, t, '오늘의 추천')
    put(s, T('마라탕', 56, DEEP), SW / 2, 175, 1, prog(t, 0, 0.3))
    put(s, T('오늘의 조건', 28, GRAY, False), SW / 2, 270, 1, prog(t, 0.2, 0.5))
    pput(s, chip('오늘 1끼만', 38, MINT, WHITE, 44, 78), SW / 2, 350, t, 0.6)
    pput(s, chip('조리 부담 줄이기', 38, MINT, WHITE, 44, 78), SW / 2, 450, t, 1.5)
    if t >= 2.6:
        pput(s, card(560, 190, (255, 248, 226), YEL, 6, 30), SW / 2, 640, t, 2.6, 0.5)
        pput(s, T('오늘 한 끼는', 30, GRAY, False), SW / 2, 590, t, 2.8)
        pput(s, T('배달 추천', 66, DEEP), SW / 2, 665, t, 2.9)
    pr = 0.95 if 5.4 < t < 5.65 else 1
    put(s, btn('배달로 선택하기', 560, 88, DEEP, 38), SW / 2, 840, pr, prog(t, 3.6, 4.0))
    ripple(s, SW / 2, 840, t, 5.4, DEEP)
    return frame_with(s, '추천 화면은 시연 예시 · 실제 조건 분석 기능이 완성된 것이 아닙니다', t)

# ============================================================ U15 타이틀 (6초)
def u15(t):
    fr = Image.new('RGB', (W, H), MINT)
    s = eob(prog(t, 0.0, 0.4), 1.4)
    put(fr, T('요리 할래말래', 150, WHITE), 960, 470, 0.85 + 0.15 * s, min(1, prog(t, 0, 0.25) * 2))
    put(fr, T('오늘의 비용과 시간을 비교하는 서비스', 48, (230, 250, 245), False), 960, 600, 1, prog(t, 0.4, 0.8))
    put(fr, T('비공식 사업 제안 · 수치는 시연 예시', 28, (210, 242, 235), False), 960, 1010, 1, prog(t, 0.6, 1.0))
    return fr

UI = {  # 이름: (함수, 길이)
    'U02': (u02, 3), 'U04': (u04, 6), 'U05': (u05, 4), 'U06': (u06, 6), 'U07': (u07, 8),
    'U09': (u09, 2), 'U11': (u11, 5), 'U12': (u12, 2), 'U14': (u14, 6), 'U15': (u15, 6),
}

# ============================================================ 타임라인 (콘티 v5)
# (이름, 길이, 종류, 원본, 설명)
TL = [
    ('S01', 6, 'AI', 'S01', '먹고 싶은 저녁'),
    ('S02a', 3, 'UI', 'U02', '배달 결제 화면'),
    ('S02b', 3, 'AI', 'S02', '결제 앞에서 멈춥니다'),
    ('S03', 6, 'AI', 'S03', '요리를 떠올리지만'),
    ('S04', 6, 'UI', 'U04', '검색에서 서비스로'),
    ('S05a', 2, 'AI', 'S05A', '양념 세 병'),
    ('S05b', 4, 'UI', 'U05', '집에 있는 것은 빼고'),
    ('S06', 6, 'UI', 'U06', '내일 먹을 것까지'),
    ('S07', 8, 'UI', 'U07', '비교하고 고릅니다'),
    ('S08', 5, 'AI', 'S08', '재료가 도착합니다'),
    ('S09a', 2, 'UI', 'U09', '레시피 안내'),
    ('S09b', 3.5, 'AI', 'S09A', '팬 조리'),
    ('S09c', 1.5, 'AI', 'S09B', '완성한 제육과 밥'),
    ('S10a', 3, 'AI', 'S10A', '직접 만든 한 끼'),
    ('S10b', 3, 'AI', 'S10B', '다음 몫 보관'),
    ('S11', 5, 'UI', 'U11', '남은 것은 직접 체크'),
    ('S12a', 2, 'UI', 'U12', '다음 한 끼로'),
    ('S12b', 4, 'AI', 'S12A', '다음 날 볶음밥'),
    ('S13', 5, 'AI', 'S13', '다른 날의 조건'),
    ('S14', 6, 'UI', 'U14', '오늘은 배달'),
    ('S15', 6, 'UI', 'U15', '선택을 돕는 서비스'),
]
assert abs(sum(x[1] for x in TL) - 90) < 1e-6
OVERLAY = {'S13': ('며칠 뒤', 0.2, 1.8)}      # AI 컷 위에 올리는 글자

# ============================================================ UI 렌더링
def _fb(args):
    name, n = args
    fn, dur = UI[name]
    return fn(min(n / FPS, dur - 1e-3)).tobytes()

def render_ui(names):
    for nm in names:
        fn, dur = UI[nm]; outp = os.path.join(UIDIR, nm + '.mp4')
        cmd = ['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS),
               '-i', '-', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '18', '-preset', 'veryfast', '-an', outp]
        p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        with Pool(2) as pool:
            for b in pool.imap(_fb, [(nm, n) for n in range(int(dur * FPS))], chunksize=6):
                p.stdin.write(b)
        p.stdin.close(); p.wait(); print('ui', nm, flush=True)

def stills(names):
    for nm in names:
        fn, dur = UI[nm]
        sheet = Image.new('RGB', (1920, 1080))
        for i, f in enumerate((0.2, 0.45, 0.7, 0.95)):
            im = fn(dur * f).resize((960, 540), Image.LANCZOS)
            sheet.paste(im, ((i % 2) * 960, (i // 2) * 540))
        sheet.save(os.path.join(HERE, f'qa_{nm}.png'))
    print('stills ok')

# ============================================================ 소리
SR = core.SR
core.TOT = 90.0; TOT = 90.0
core.N = int(SR * TOT)
core.SFX_L = np.zeros(core.N, np.float32); core.SFX_R = np.zeros(core.N, np.float32); core.MUS = np.zeros(core.N, np.float32)
rng = np.random.default_rng(11)
def lp(x, n): return np.convolve(x, np.ones(n) / n, mode='same').astype(np.float32)
def sfx(t0, x, pan=0.0, g=1.0): core.sfx(t0, x, pan, g)
def rumble(t0):
    n = int(1.0 * SR); t = np.arange(n) / SR
    x = lp(rng.standard_normal(n), 300) * 4
    env = np.sin(np.pi * t) ** 2 * (0.6 + 0.4 * np.sin(2 * np.pi * 9 * t))
    sfx(t0, (x * env * 0.6).astype(np.float32))
def notify(t0): sfx(t0, core.tone(988, 0.12, k=12, g=0.22)); sfx(t0 + 0.13, core.tone(1319, 0.35, k=7, g=0.22))
def rustle(t0, d=0.9):
    for _ in range(16): sfx(t0 + rng.random() * (d - 0.1), core.noise(0.06, 25, 0.08))
def sizzle(t0, d):
    n = int(d * SR); t = np.arange(n) / SR
    x = np.diff(rng.standard_normal(n + 1)); mod = lp(np.abs(rng.standard_normal(n)), 900) * 9
    env = np.minimum(1, t / 0.4) * np.minimum(1, (d - t) / 0.5)
    sfx(t0, (x * mod * env * 0.018).astype(np.float32))
    for _ in range(int(d * 14)): sfx(t0 + rng.random() * d, core.noise(0.012, 200, 0.12))
def clink(t0, f=3300): sfx(t0, core.mixn(core.tone(f, 0.3, k=14, g=0.16), core.tone(f * 1.5, 0.2, k=20, g=0.07)))
def door(t0): sfx(t0, core.mixn(core.tone(110, 0.25, k=14, g=0.35, glide=70), core.noise(0.08, 40, 0.22)))
def hum(t0, d):
    n = int(d * SR); t = np.arange(n) / SR
    env = np.minimum(1, t / 0.4) * np.minimum(1, (d - t) / 0.4)
    sfx(t0, (np.sin(2 * np.pi * 100 * t) * 0.03 * env + np.sin(2 * np.pi * 50 * t) * 0.02 * env).astype(np.float32))
def sigh(t0):
    n = int(1.1 * SR); t = np.arange(n) / SR
    x = lp(rng.standard_normal(n), 24) * 3
    sfx(t0, (x * np.sin(np.pi * t / 1.1) ** 2 * 0.28).astype(np.float32))
def thud(t0): sfx(t0, core.mixn(core.tone(80, 0.3, k=10, g=0.4, glide=50), core.noise(0.1, 30, 0.2)))
def key(t0): sfx(t0, core.mixn(core.tone(1800 + 120 * rng.random(), 0.02, k=120, g=0.10), core.noise(0.01, 200, 0.08)))

def film_sfx():
    A = core
    # S1-S3
    hum(12.0, 6.0); rumble(0.8); A.s_tap(6.3, 1240); notify(6.0)
    door(12.2); sigh(16.2)
    # S4 (18-24): 입력, 클릭
    for i in range(17): key(18.15 + 0.08 * i)
    A.s_tap(20.6, 1240); A.s_swipe(21.1); A.s_tap(23.4, 1240); A.s_pop(21.7, 560)
    # S5 (24-30)
    clink(24.4, 2800)
    for i in range(3): A.s_tap(26.4 + 0.4 * i, 1240 + 60 * i)
    A.s_swipe(25.7); A.s_pop(27.3, 620)
    for i in range(8): A.s_tick(28.0 + 0.1 * i, 1700 - 60 * i)
    A.s_confirm(28.95)
    # S6 (30-36)
    A.s_pop(30.3, 560); A.s_warn(30.5); A.s_pop(31.3, 700)
    A.s_tap(32.6, 1040); A.s_thump(32.65)
    for i in range(8): A.s_tick(32.7 + 0.1 * i, 1400 + 60 * i)
    A.s_confirm(34.2)
    for i, f in enumerate((560, 660, 780)): A.s_pop(34.0 + 0.2 * i, f)
    # S7 (36-44)
    A.s_swipe(36.0); A.s_swipe(36.35, 0.2); A.s_pop(37.0, 640)
    for i in range(3): A.s_pop(37.6 + 0.2 * i, 880 + 80 * i)
    A.s_swipe(38.3); A.s_accent(39.95); A.s_pop(40.4, 620); A.s_pop(40.8, 520)
    A.s_accent(42.0); A.s_tap(43.45, 1040); A.s_confirm(43.5)
    # S8 (44-49)
    notify(44.2); rustle(45.3, 1.0); A.s_thump(46.5); A.s_tap(47.6, 900)
    # S9 (49-56)
    A.s_tap(49.5, 1040); A.s_pop(49.9, 600)
    sizzle(51.0, 4.4); clink(55.3, 2600)
    # S10 (56-62)
    clink(56.9, 3000); clink(57.3, 2800); sigh(58.1)
    clink(59.4, 3600); door(60.9)
    # S11 (62-67)
    for i in range(4): A.s_tap(63.0 + 0.55 * i, 1240 + 60 * i)
    A.s_tap(65.65, 1040); A.s_confirm(65.7); A.s_pop(65.95, 700)
    # S12 (67-73)
    notify(67.2); A.s_pop(67.8, 640); clink(71.6, 2900)
    # S13 (73-78)
    thud(74.2); sigh(75.0)
    # S14 (78-84)
    A.s_pop(78.6, 620); A.s_pop(79.5, 700); A.s_accent(80.7); A.s_pop(81.0, 560)
    A.s_tap(83.5, 1040); A.s_confirm(83.55)
    # S15 (84-90)
    A.s_hit(84.0); A.s_accent(84.35); A.s_confirm(84.5)

def film_inten(t):
    xs = [0, 6, 12, 18, 19, 24, 36, 44, 49, 56, 62, 67, 72.5, 73, 78, 79, 84, 87, 90]
    ys = [0.10, 0.12, 0.18, 0.18, 0.45, 0.60, 0.70, 0.38, 0.30, 0.34, 0.50, 0.55, 0.40, 0.10, 0.10, 0.50, 0.75, 0.50, 0.25]
    return float(np.interp(t, xs, ys))
core.inten = film_inten

def build_audio(path):
    film_sfx(); core.music()
    t = np.arange(core.N) / SR
    env = np.minimum(1, t / 0.4) * np.minimum(1, np.maximum(0, (TOT - t) / 1.5))
    m = core.MUS * env * 0.55
    L = m + core.SFX_L; R = m + core.SFX_R
    pk = max(np.abs(L).max(), np.abs(R).max())
    if pk > 0.9: L, R = L * 0.9 / pk, R * 0.9 / pk
    L, R = np.tanh(L * 1.05), np.tanh(R * 1.05)
    pcm = (np.clip(np.stack([L, R], 1), -1, 1) * 32767).astype('<i2')
    with wave.open(path, 'wb') as wf:
        wf.setnchannels(2); wf.setsampwidth(2); wf.setframerate(SR); wf.writeframes(pcm.tobytes())
    print('audio peak', float(pk), 'rms', float(np.sqrt(np.mean(pcm.astype(np.float64) ** 2)) / 32768))

# ============================================================ 조립
def slate_png(name, dur, desc, path):
    im = Image.new('RGB', (W, H), (44, 58, 62))
    d = ImageDraw.Draw(im)
    d.rectangle([60, 60, W - 60, H - 60], outline=(120, 150, 150), width=4)
    put(im, T('AI 컷 자리표시', 44, (160, 190, 188), False), 960, 380, 1, 1)
    put(im, T(name, 150, WHITE), 960, 520, 1, 1)
    put(im, T(f'{desc} · {dur:g}초', 52, (210, 230, 226), False), 960, 680, 1, 1)
    im.save(path)

def norm(src, dur, out, loop_img=False, overlay=None):
    vf = 'scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,fps=24,tpad=stop_mode=clone:stop_duration=10,format=yuv420p'
    cmd = ['ffmpeg', '-y', '-loglevel', 'error']
    if loop_img: cmd += ['-loop', '1', '-framerate', '24']
    cmd += ['-i', src]
    if overlay:
        text, a, b = overlay
        ov = os.path.join(OUT, '_ov.png'); im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        c = chip(text, 44, (23, 55, 61, 235), WHITE, 40, 80)
        im.paste(c.get(1), (110, 880), c.get(1)); im.save(ov)
        cmd += ['-i', ov, '-filter_complex', f'[0:v]{vf}[v];[v][1:v]overlay=0:0:enable=between(t\\,{a}\\,{b})[o]', '-map', '[o]']
    else:
        cmd += ['-vf', vf]
    cmd += ['-t', f'{dur}', '-an', '-c:v', 'libx264', '-crf', '18', '-preset', 'veryfast', out]
    subprocess.run(cmd, check=True)

def assemble(final=None):
    tmp = os.path.join(OUT, '_seg'); shutil.rmtree(tmp, ignore_errors=True); os.makedirs(tmp)
    listing, missing = [], []
    for name, dur, kind, srcname, desc in TL:
        seg = os.path.join(tmp, name + '.mp4')
        if kind == 'UI':
            norm(os.path.join(UIDIR, srcname + '.mp4'), dur, seg)
        else:
            cands = glob.glob(os.path.join(CLIPS, srcname + '.*'))
            if cands:
                norm(cands[0], dur, seg, overlay=OVERLAY.get(name))
            else:
                missing.append(srcname)
                png = os.path.join(tmp, name + '.png'); slate_png(srcname, dur, desc, png)
                norm(png, dur, seg, loop_img=True)
        listing.append(f"file '{seg}'\n")
    lst = os.path.join(tmp, 'list.txt'); open(lst, 'w').write(''.join(listing))
    vid = os.path.join(tmp, 'video.mp4')
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', lst, '-c', 'copy', vid], check=True)
    wav = os.path.join(OUT, 'film_audio_v5.wav')
    if not os.path.exists(wav): build_audio(wav)
    final = final or os.path.join(OUT, 'yori_film_90s_v5_preview.mp4' if missing else 'ai_film_90s.mp4')
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', vid, '-i', wav, '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k',
                    '-t', '90', '-movflags', '+faststart', final], check=True)
    shutil.rmtree(tmp, ignore_errors=True)
    print('done', final, '| 자리표시 컷:', missing or '없음')

if __name__ == '__main__':
    mode = sys.argv[1]; args = sys.argv[2:]
    if mode == 'ui': render_ui(args or list(UI))
    elif mode == 'stills': stills(args or list(UI))
    elif mode == 'audio': build_audio(os.path.join(OUT, 'film_audio_v5.wav'))
    elif mode == 'assemble': assemble()
