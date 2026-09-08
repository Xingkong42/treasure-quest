#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
寻宝奇兵 Treasure Quest
一个暗夜鎏金风格的逻辑解谜寻宝游戏(PySide6)。

规则:
  · 在 n×n 的棋盘上放置 n 枚宝石;
  · 每行、每列恰好一枚宝石;
  · 每块领地(颜色区域)恰好一枚宝石;
  · 任意两枚宝石不能相邻(横、竖、斜八个方向)。

操作:
  · 左键点击:放置 / 收回宝石;
  · 右键点击:打 / 消除排除记号;
  · 支持撤销、提示、清空、四种难度,胜利后有金尘庆祝。

模式:
  · 标准 · 唯一解:谜题经过唯一性收敛,答案唯一,纯逻辑可推;
  · 休闲 · 任意解:任意满足规则的完整布局即可获胜。

运行:
  pip install PySide6
  python treasure_quest.py            # 正常游戏
  python treasure_quest.py --selftest # 离屏自测
  python treasure_quest.py --smoke    # 1.5 秒冒烟启动
"""

from __future__ import annotations

import math
import random
import sys
import time
from collections import deque
from string import Template

from PySide6.QtCore import (Qt, QElapsedTimer, QPointF, QRectF, QThread,
                            QTimer, Signal)
from PySide6.QtGui import (QBrush, QColor, QIcon, QImage, QLinearGradient,
                           QPainter, QPen, QPixmap, QPolygonF,
                           QRadialGradient)
from PySide6.QtWidgets import (QApplication, QComboBox, QDialog, QFrame,
                               QHBoxLayout, QLabel, QMainWindow,
                               QPushButton, QSizePolicy, QVBoxLayout,
                               QWidget)

# ------------------------------------------------------------ 主题配色(暗夜鎏金)
PALETTE = [
    "#C96A5B",  # 赤陶
    "#D89A5B",  # 琥珀
    "#C9B458",  # 暗金
    "#7FA05B",  # 苔绿
    "#5BA88F",  # 青玉
    "#5B93A8",  # 灰蓝
    "#6B7FB3",  # 靛蓝
    "#9A6FB0",  # 紫晶
    "#B05B7E",  # 玫紫
    "#C97A93",  # 灰玫瑰
    "#A98B6B",  # 驼色
    "#7E8C99",  # 石板灰
]

# ------------------------------------------------------------ 主题系统
# 每套主题:QSS 字符串键 + 棋盘绘制色(hex 字符串或 (r,g,b[,a]) 元组)。
THEMES = {
    # —— 云白蓝:白色中透着淡蓝的日间主题(默认)——
    "day": {
        "window_top": "#F7FAFE", "window_mid": "#EDF3FA", "window_bot": "#E2EBF5",
        "title": "#2F4E73", "title_en": "#93A7BF", "subtitle": "#5F738C",
        "card_qss": "rgba(255, 255, 255, 235)", "card_border": "#FFFFFF",
        "cap": "#8B9BAF", "big": "#2E3E54", "text": "#51637B",
        "rules": "#5A6C84", "howto": "#93A3B8",
        "btn_border": "#C9D6E5", "btn_text": "#4E6076",
        "btn_hover_border": "#3E6FA3", "btn_hover_text": "#2C5A8C",
        "btn_pressed": "rgba(62, 111, 163, 28)",
        "primary_border": "#3E6FA3", "primary_text": "#2C5A8C",
        "primary_hover": "rgba(62, 111, 163, 32)",
        "ghost_text": "#7B8CA2", "ghost_hover_text": "#4E6076",
        "ghost_hover_border": "#A9BCD2",
        "combo_bg": "#FFFFFF", "combo_border": "#C9D6E5", "combo_text": "#4E6076",
        "combo_view_bg": "#FFFFFF", "combo_view_sel": "#E4EEF9",
        "combo_view_sel_text": "#2C5A8C",
        "dialog_bg": "#F7FAFD", "dialog_border": "#D9E4F0",
        "win_mark": "#3E6FA3", "win_title": "#2F4E73", "win_info": "#5F738C",
        "sep": "#D8E2EE",
        "board_bg": "#FBFDFF", "board_edge": "#A3BAD1",
        "board_shadow": (60, 90, 130, 55),
        "grid_line": (48, 76, 112, 110),
        "region_border": "#5A7DA6",
        "hover": (62, 111, 163, 34),
        "vignette": (70, 100, 140, 55),
        "mark": (74, 90, 112, 130),
        "gem_top": "#E8F5FF", "gem_mid": "#7FC0EE",
        "gem_bot": "#2C6FA8", "gem_edge": "#1E4E7E",
        "gem_aura": (90, 160, 220, 80), "gem_aura_warn": (200, 80, 60, 100),
        "gem_warn_ring": "#C75450",
        "icon_bg": "#E8F0F8",
        "msg_win": "#2C5A8C", "msg_warn": "#C0603F", "msg_text": "#51637B",
    },
    # —— 暗夜鎏金:深色石板配金色宝石的夜间主题 ——
    "night": {
        "window_top": "#0F141C", "window_mid": "#151C27", "window_bot": "#1A2230",
        "title": "#D9B95C", "title_en": "#6B7688", "subtitle": "#8A93A6",
        "card_qss": "rgba(23, 30, 42, 200)", "card_border": "#2A3342",
        "cap": "#768093", "big": "#E8E3D5", "text": "#A9B2C3",
        "rules": "#9AA3B5", "howto": "#6B7688",
        "btn_border": "#3A4556", "btn_text": "#C8CFDB",
        "btn_hover_border": "#C8A44D", "btn_hover_text": "#E9CE7E",
        "btn_pressed": "rgba(200, 164, 77, 25)",
        "primary_border": "#C8A44D", "primary_text": "#E9CE7E",
        "primary_hover": "rgba(200, 164, 77, 30)",
        "ghost_text": "#8A93A6", "ghost_hover_text": "#C8CFDB",
        "ghost_hover_border": "#4E5B70",
        "combo_bg": "#1F2733", "combo_border": "#3A4556", "combo_text": "#C8CFDB",
        "combo_view_bg": "#1F2733", "combo_view_sel": "#2A3547",
        "combo_view_sel_text": "#E9CE7E",
        "dialog_bg": "#171E2A", "dialog_border": "#2A3342",
        "win_mark": "#D9B95C", "win_title": "#D9B95C", "win_info": "#A9B2C3",
        "sep": "#2A3342",
        "board_bg": "#161D28", "board_edge": "#C8A44D",
        "board_shadow": (0, 0, 0, 110),
        "grid_line": (10, 14, 20, 70),
        "region_border": "#C8A44D",
        "hover": (217, 185, 92, 36),
        "vignette": (0, 0, 0, 90),
        "mark": (230, 226, 211, 130),
        "gem_top": "#FFF3C4", "gem_mid": "#F0C75E",
        "gem_bot": "#B8860B", "gem_edge": "#8A6A14",
        "gem_aura": (255, 224, 138, 75), "gem_aura_warn": (217, 83, 79, 110),
        "gem_warn_ring": "#D9534F",
        "icon_bg": "#1B2330",
        "msg_win": "#D9B95C", "msg_warn": "#E07A5F", "msg_text": "#A9B2C3",
    },
}

THEME_NAME = "day"      # 默认主题:云白蓝
THEME = THEMES[THEME_NAME]

THEME_LABEL = {"day": "云白蓝", "night": "暗夜鎏金"}


def apply_theme(name: str):
    """切换当前主题(棋盘绘制与 QSS 均自此取色)。"""
    global THEME_NAME, THEME
    THEME_NAME = name
    THEME = THEMES[name]


def _qc(v):
    """hex 字符串或 (r,g,b[,a]) 元组 → QColor。"""
    if isinstance(v, tuple):
        return QColor(*v)
    return QColor(v)

# 格子状态
EMPTY, GEM, MARK = 0, 1, 2


def _enumerate_solutions(regions, n, cap=2):
    """枚举领地划分上的完整布局(行/列/领地/八向不相邻约束)。
    rid=-1 的格子视为尚未归属任何领地,不可放置;至多返回 cap 个解,
    每个解为按行列号列表。位掩码加速 +「剩余行数必须足以填满剩余
    列与剩余领地」强剪枝 + 失败子树记忆化(加速唯一性证明)。"""
    full = (1 << n) - 1
    row_ok = []
    for pc in range(n):
        m = 0
        for c in range(n):
            if abs(c - pc) > 1:
                m |= 1 << c
        row_ok.append(m)
    row_regs = [regions[r] for r in range(n)]
    sols: list[list[int]] = []
    cur: list[int] = []
    dead: set = set()

    def solve(r, col_mask, reg_mask, prev_c) -> int:
        if r == n:
            if reg_mask == full:
                sols.append(list(cur))
                return 1
            return 0
        if (n - r) < n - col_mask.bit_count():
            return 0
        if (n - r) < n - reg_mask.bit_count():
            return 0
        key = (r, col_mask, reg_mask, prev_c)
        if key in dead:
            return 0
        allow = full if prev_c < 0 else row_ok[prev_c]
        allow &= ~col_mask & full
        regs = row_regs[r]
        total = 0
        while allow:
            bit = allow & (-allow)
            allow ^= bit
            c = bit.bit_length() - 1
            rid = regs[c]
            if rid < 0:
                continue
            rbit = 1 << rid
            if reg_mask & rbit:
                continue
            cur.append(c)
            total += solve(r + 1, col_mask | bit, reg_mask | rbit, c)
            cur.pop()
            if len(sols) >= cap:
                return total
        if total == 0:
            dead.add(key)
        return total

    solve(0, 0, 0, -1)
    return sols


# ================================================================ 谜题逻辑
class Puzzle:
    """生成棋盘区域划分与一份参考解(用于提示与胜利无关的校验)。"""

    def __init__(self, n: int, rng: random.Random | None = None,
                 unique: bool = True):
        self.n = n
        self.rng = rng or random.Random()
        # 标准模式(unique=True):随机生长后用「热度挖格 + 精调回溯」
        # 收敛到唯一解;精调卡住时先局部扰动再收敛,仍失败才换盘重试。
        for _ in range(8):
            self.solution = self._make_solution()
            self.regions = self._grow_regions()
            if not unique or self._make_unique():
                break
            for _ in range(3):
                self._perturb(self.rng.choice((3, 6, 9)))
                if self._make_unique():
                    break
            else:
                continue
            break
        self.palette = PALETTE[:]
        self.rng.shuffle(self.palette)

    # ---- 参考解:随机回溯,行优先,约束 = 列唯一 + 八邻域不相邻 ----
    def _make_solution(self):
        n = self.n
        for _ in range(64):  # 极小概率失败时换随机流重来
            cols = [False] * n
            placed: list[tuple[int, int]] = []
            budget = 60000

            def feasible(r, c):
                for pr, pc in placed:
                    if abs(pr - r) <= 1 and abs(pc - c) <= 1:
                        return False
                return True

            def backtrack(r):
                nonlocal budget
                budget -= 1
                if budget < 0:
                    return False
                if r == n:
                    return True
                cand = [c for c in range(n) if not cols[c]]
                self.rng.shuffle(cand)
                for c in cand:
                    if feasible(r, c):
                        cols[c] = True
                        placed.append((r, c))
                        if backtrack(r + 1):
                            return True
                        placed.pop()
                        cols[c] = False
                return False

            if backtrack(0):
                return list(placed)
        raise RuntimeError("生成参考解失败(理论上几乎不可能)")

    def _neighbors(self, r, c):
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < self.n and 0 <= nc < self.n:
                yield nr, nc

    def _territory_quotas(self, n):
        """领地大小配额:约三分之二领地 1~3 格(小领地是约束推理的
        起点,单格领地更是绝对锚点),其余分摊剩余面积。刻意偏斜,
        避免「每领地都 n 格」的松构造。"""
        quotas = [0] * n
        small = [i for i in range(n) if i % 3 != 2]
        for i in small:
            quotas[i] = self.rng.randint(1, 3)
        rest = n * n - sum(quotas)
        big = [i for i in range(n) if quotas[i] == 0]
        for j, i in enumerate(big):
            quotas[i] = rest // len(big) + (1 if j < rest % len(big) else 0)
        return quotas

    # ---- 区域:以参考解的每枚宝藏为种子,做多源随机生长 ----
    # 这样天然保证:每块区域恰好包含一枚参考解宝藏,且区域连通。
    def _grow_regions(self):
        n = self.n
        region = [[-1] * n for _ in range(n)]
        for i, (r, c) in enumerate(self.solution):
            region[r][c] = i
        quotas = self._territory_quotas(n)
        counts = [1] * n
        frontiers = [{nb for nb in self._neighbors(r, c)
                      if region[nb[0]][nb[1]] == -1}
                     for (r, c) in self.solution]
        remaining = n * n - n
        while remaining > 0:
            order = [i for i in range(n)
                     if counts[i] < quotas[i] and frontiers[i]]
            if not order:
                break
            self.rng.shuffle(order)
            progressed = False
            for i in order:
                f = {(r, c) for (r, c) in frontiers[i]
                     if region[r][c] == -1}
                frontiers[i] = f
                if not f or counts[i] >= quotas[i]:
                    continue
                # 紧凑偏置:优先吞并与种子近的格,长出团状领地
                sr, sc = self.solution[i]
                cand_l = sorted(f)
                weights = [1.0 / (1 + abs(rr - sr) + abs(cc - sc))
                           for (rr, cc) in cand_l]
                r, c = self.rng.choices(cand_l, weights=weights, k=1)[0]
                f.discard((r, c))
                region[r][c] = i
                counts[i] += 1
                remaining -= 1
                progressed = True
                for nr, nc in self._neighbors(r, c):
                    if region[nr][nc] == -1:
                        f.add((nr, nc))
                if remaining == 0:
                    break
            if not progressed:
                break
        # 兜底:理论上不会触发的孤立格,并入相邻区域
        changed = True
        while changed:
            changed = False
            for r in range(n):
                for c in range(n):
                    if region[r][c] == -1:
                        for nr, nc in self._neighbors(r, c):
                            if region[nr][nc] != -1:
                                region[r][c] = region[nr][nc]
                                changed = True
                                break
        return region

    # ---- 唯一解收敛:枚举解 → 重生长分歧领地,直至只剩一个解 ----
    def _solutions(self, cap: int = 2):
        """枚举当前领地划分上的完整布局,至多 cap 个;解为按行列号列表。"""
        return _enumerate_solutions(self.regions, self.n, cap)

    def _perturb(self, k: int):
        """随机扰动:把 k 个非参考解格挖到随机相邻领地(保持挖出方
        连通),用于跳出精调搜索的局部极小。"""
        n = self.n
        ref_cells = set(self.solution)
        moved = 0
        guard = 0
        while moved < k and guard < 60:
            guard += 1
            b = (self.rng.randrange(n), self.rng.randrange(n))
            if b in ref_cells:
                continue
            L = self.regions[b[0]][b[1]]
            if not self._territory_connected_excluding(L, b):
                continue
            mids = [self.regions[nr][nc] for nr, nc in self._neighbors(*b)
                    if self.regions[nr][nc] != L]
            if not mids:
                continue
            self.regions[b[0]][b[1]] = self.rng.choice(mids)
            moved += 1

    def _territory_connected_excluding(self, rid: int, cell) -> bool:
        """领地 rid 挖去 cell 后是否仍四向连通。"""
        n = self.n
        regions = self.regions
        cells = [(r, c) for r in range(n) for c in range(n)
                 if regions[r][c] == rid and (r, c) != cell]
        if not cells:
            return True
        seen = {cells[0]}
        dq = deque([cells[0]])
        while dq:
            cr, cc = dq.popleft()
            for nr, nc in self._neighbors(cr, cc):
                nxt = (nr, nc)
                if (nxt != cell and regions[nr][nc] == rid
                        and nxt not in seen):
                    seen.add(nxt)
                    dq.append(nxt)
        return len(seen) == len(cells)

    def _make_unique(self, t_limit: float = 0.5) -> bool:
        """两阶段迭代收紧,直至谜题唯一解。

        粗调(解数>16):批量挖走「热度最高」的非参考解选择格,快速
        压低解数;精调(解数≤16):枚举全部解,沿「解数下降 + 传播
        梯度」做有界回溯。参考解的宝石格永不移动,因此始终完好。
        t_limit 限定本次尝试的墙钟预算,防止个别谜题拖垮生成。"""
        t0 = time.perf_counter()
        deadline = t0 + t_limit
        n = self.n
        ref_cells = set(self.solution)
        last_k = None
        stall = 0
        for _ in range(80):
            if time.perf_counter() > deadline:
                return False
            sols = self._solutions(cap=16)
            if len(sols) <= 1:
                return True
            if len(sols) <= 16:
                return self._refine_dfs(depth=24, budget=[900],
                                        deadline=deadline)
            if len(sols) == last_k:
                stall += 1
                if stall >= 6:          # 批量挖格已无进展,转精调
                    return self._refine_dfs(depth=24, budget=[900],
                                            deadline=deadline)
            else:
                stall = 0
                last_k = len(sols)
            heat = {}
            for s in sols:
                if {(r, s[r]) for r in range(n)} == ref_cells:
                    continue
                for r in range(n):
                    b = (r, s[r])
                    if b not in ref_cells:      # 只统计可挖的格
                        heat[b] = heat.get(b, 0) + 1
            if not heat:
                return False
            # 每轮批量挖走热度前 4 的格子(逐个保持挖出方连通)
            moved = 0
            for b, _ in sorted(heat.items(), key=lambda kv: -kv[1]):
                if moved >= 4:
                    break
                L = self.regions[b[0]][b[1]]
                if not self._territory_connected_excluding(L, b):
                    continue
                mids = [self.regions[nr][nc]
                        for nr, nc in self._neighbors(*b)
                        if self.regions[nr][nc] != L]
                if not mids:
                    continue
                self.rng.shuffle(mids)
                self.regions[b[0]][b[1]] = mids[0]
                moved += 1
            if moved == 0:
                return False
        return False

    def _refine_dfs(self, depth, budget, sols=None, deadline=None) -> bool:
        """精调搜索:解集已小(≤16),对干扰解的偏离格做有界回溯——
        优先走「解数严格下降」的挖格,无下降时按传播强制数梯度横走;
        深度、枚举预算与墙钟截止封顶,防震荡防拖垮生成。"""
        n = self.n
        if sols is None:
            sols = self._solutions(cap=16)
        if len(sols) <= 1:
            return True
        if depth <= 0 or budget[0] <= 0:
            return False
        if deadline is not None and time.perf_counter() > deadline:
            return False
        k0 = len(sols)
        ref_cells = set(self.solution)
        cands = []
        seen = set()
        for s in sols:
            if {(r, s[r]) for r in range(n)} == ref_cells:
                continue
            for r in range(n):
                b = (r, s[r])
                if b not in ref_cells and b not in seen:
                    seen.add(b)
                    cands.append(b)
        self.rng.shuffle(cands)
        moves = []
        for b in cands:
            L = self.regions[b[0]][b[1]]
            if not self._territory_connected_excluding(L, b):
                continue
            for M in (self.regions[nr][nc] for nr, nc in self._neighbors(*b)
                      if self.regions[nr][nc] != L):
                self.regions[b[0]][b[1]] = M
                fc = self._propagate_forced(self.regions)
                moves.append((fc, b, M))
                self.regions[b[0]][b[1]] = L
        if not moves:
            return False
        moves.sort(key=lambda t: -t[0])
        for _, b, M in moves[:4]:
            self.regions[b[0]][b[1]] = M
            budget[0] -= 1
            nxt = self._solutions(cap=16)
            if len(nxt) < k0 or depth > 6:
                if self._refine_dfs(depth - 1, budget, nxt):
                    return True
            self.regions[b[0]][b[1]] = L
            if budget[0] <= 0:
                return False
        return False

    def _propagate_forced(self, regions) -> int:
        """约束传播(单候选强制 + 放置排除):返回可被纯逻辑确定的
        格数,作为「接近唯一解」的廉价代理;出现矛盾则返回 0。"""
        n = self.n
        cand = {(r, c) for r in range(n) for c in range(n)
                if regions[r][c] != -1}
        forced = set()

        def excl(cell):
            r, c = cell
            rid = regions[r][c]
            out = set()
            for cc in range(n):
                out.add((r, cc))
                out.add((cc, c))
            for nr in (r - 1, r, r + 1):
                for nc in (c - 1, c, c + 1):
                    out.add((nr, nc))
            for (rr, cc) in cand:
                if regions[rr][cc] == rid:
                    out.add((rr, cc))
            out.discard(cell)
            return out

        while True:
            groups = {}
            for cell in cand:
                r, c = cell
                groups.setdefault(("r", r), []).append(cell)
                groups.setdefault(("c", c), []).append(cell)
                groups.setdefault(("t", regions[r][c]), []).append(cell)
            newly = []
            dead = False
            for cells in groups.values():
                free = [x for x in cells if x not in forced]
                nf = len(cells) - len(free)
                if len(free) == 1:
                    newly.append(free[0])
                elif len(free) == 0 and nf == 0:
                    dead = True     # 该组已无任何可能宝石
                elif nf >= 2:
                    dead = True     # 同组两格都被强制,矛盾
            if dead:
                return 0
            newly = [x for x in dict.fromkeys(newly) if x not in forced]
            if not newly:
                break
            for cell in newly:
                if cell in forced:
                    continue
                cand.difference_update(excl(cell))
                forced.add(cell)
        return len(forced)

    def region_of(self, r, c):
        return self.regions[r][c]

    def region_color(self, rid: int) -> QColor:
        return QColor(self.palette[rid % len(self.palette)])

    # ---- 冲突检测:返回两两违规的格子集合 ----
    def conflicts(self, cells):
        bad = set()
        cells = list(cells)
        for i in range(len(cells)):
            for j in range(i + 1, len(cells)):
                a, b = cells[i], cells[j]
                if (a[0] == b[0] or a[1] == b[1]
                        or (abs(a[0] - b[0]) <= 1 and abs(a[1] - b[1]) <= 1)
                        or self.region_of(*a) == self.region_of(*b)):
                    bad.add(a)
                    bad.add(b)
        return bad

    def conflict_reason(self, a, b) -> str:
        if a[0] == b[0]:
            return "同一行已存在宝石"
        if a[1] == b[1]:
            return "同一列已存在宝石"
        if abs(a[0] - b[0]) <= 1 and abs(a[1] - b[1]) <= 1:
            return "宝石相邻(含对角)"
        return "每块领地仅限一枚宝石"

    def is_solved(self, cells) -> bool:
        return len(set(cells)) == self.n and not self.conflicts(cells)


# ================================================================ 棋盘控件
class BoardWidget(QWidget):
    """负责棋盘绘制与交互,纯控件,不含窗口业务。"""

    changed = Signal(int, str)   # (已放宝石数, 状态栏消息)
    solved = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(360, 360)
        self.setSizePolicy(QSizePolicy.Policy.Expanding,
                           QSizePolicy.Policy.Expanding)
        self.setMouseTracking(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        self.puzzle: Puzzle | None = None
        self.grid: list[list[int]] = []
        self.bad: set = set()
        self.undo_stack: list[tuple[int, int, int]] = []
        self.hover: tuple[int, int] | None = None
        self.locked = False
        self.hints_used = 0

        # 胜利金尘
        self._confetti: list[dict] = []
        self._confetti_timer = QTimer(self)
        self._confetti_timer.setInterval(33)
        self._confetti_timer.timeout.connect(self._tick_confetti)
        self._rng = random.Random()

    # ---------- 几何 ----------
    def _board_rect(self) -> QRectF:
        m = 14.0
        side = max(min(self.width(), self.height()) - 2 * m, 40.0)
        ox = (self.width() - side) / 2
        oy = (self.height() - side) / 2
        return QRectF(ox, oy, side, side)

    def _cell_at(self, pos: QPointF):
        if self.puzzle is None:
            return None
        rect = self._board_rect()
        n = self.puzzle.n
        c = int((pos.x() - rect.x()) / (rect.width() / n))
        r = int((pos.y() - rect.y()) / (rect.height() / n))
        if 0 <= r < n and 0 <= c < n:
            return r, c
        return None

    # ---------- 对外操作 ----------
    def new_game(self, puzzle: Puzzle):
        self.puzzle = puzzle
        self.restart()

    def restart(self):
        n = self.puzzle.n if self.puzzle else 0
        self.grid = [[EMPTY] * n for _ in range(n)]
        self.bad = set()
        self.undo_stack.clear()
        self.hover = None
        self.locked = False
        self.hints_used = 0
        self._stop_confetti()
        self.update()
        self.changed.emit(0, "寻找线索,放置宝石。")

    def _gem_count(self) -> int:
        if self.puzzle is None:
            return 0
        return sum(row.count(GEM) for row in self.grid)

    def set_cell(self, r, c, state, record=True) -> bool:
        old = self.grid[r][c]
        if old == state:
            return False
        self.grid[r][c] = state
        if record:
            self.undo_stack.append((r, c, old))
        return True

    def hint(self):
        if self.locked or self.puzzle is None:
            return
        cand = [(r, c) for (r, c) in self.puzzle.solution
                if self.grid[r][c] != GEM]
        if not cand:
            self.changed.emit(self._gem_count(),
                              "参考位已全部放置,请处理冲突标记。")
            return
        r, c = self._rng.choice(cand)
        self.set_cell(r, c, GEM)
        self.hints_used += 1
        self._after_change(r, c, "gem")

    def undo(self):
        if self.locked or self.puzzle is None:
            return
        if not self.undo_stack:
            self.changed.emit(self._gem_count(), "没有可撤销的操作。")
            return
        r, c, old = self.undo_stack.pop()
        self.grid[r][c] = old
        self._after_change(r, c, "undo")

    def clear_all(self):
        if self.locked or self.puzzle is None:
            return
        n = self.puzzle.n
        self.grid = [[EMPTY] * n for _ in range(n)]
        self.bad = set()
        self.undo_stack.clear()
        self.update()
        self.changed.emit(0, "棋盘已清空。")

    # ---------- 交互 ----------
    def mousePressEvent(self, e):
        if self.locked or self.puzzle is None:
            return
        cell = self._cell_at(e.position())
        if cell is None:
            return
        r, c = cell
        if e.button() == Qt.MouseButton.LeftButton:
            new = EMPTY if self.grid[r][c] == GEM else GEM
        elif e.button() == Qt.MouseButton.RightButton:
            new = EMPTY if self.grid[r][c] != EMPTY else MARK
        else:
            return
        if not self.set_cell(r, c, new):
            return
        self._after_change(r, c, "gem" if new == GEM else
                           ("mark" if new == MARK else "undo"))

    def mouseMoveEvent(self, e):
        cell = self._cell_at(e.position())
        if cell != self.hover:
            self.hover = cell
            self.update()

    def leaveEvent(self, e):
        self.hover = None
        self.update()

    def _after_change(self, r, c, action):
        n = self.puzzle.n
        gems = [(rr, cc) for rr in range(n) for cc in range(n)
                if self.grid[rr][cc] == GEM]
        self.bad = self.puzzle.conflicts(gems)
        count = len(gems)

        if count == n and not self.bad:
            self.locked = True
            self.start_confetti()
            self.changed.emit(count, "谜题告破!")
            self.solved.emit()
        elif self.bad:
            other = None
            if (r, c) in self.bad:
                for b in self.bad:
                    if b != (r, c):
                        other = b
                        break
            if other is not None:
                msg = "冲突 · " + self.puzzle.conflict_reason((r, c), other)
            else:
                msg = "存在冲突,请查看红色标记。"
            self.changed.emit(count, msg)
        elif action == "gem":
            self.changed.emit(count, f"已放置 {count} / {n}")
        elif action == "mark":
            self.changed.emit(count, "已标记排除")
        else:
            self.changed.emit(count, f"已放置 {count} / {n}")
        self.update()

    # ---------- 绘制 ----------
    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        if self.puzzle is None:
            p.end()
            return
        rect = self._board_rect()
        n = self.puzzle.n
        cell = rect.width() / n

        # 石板底:投影 + 主题面板 + 主题细边
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(_qc(THEME["board_shadow"]))
        p.drawRoundedRect(rect.adjusted(2, 12, 2, 12), 10, 10)
        p.setBrush(_qc(THEME["board_bg"]))
        p.setPen(QPen(_qc(THEME["board_edge"]), 1.2))
        p.drawRoundedRect(rect.adjusted(-10, -10, 10, 10), 8, 8)

        # 区域填色
        p.setPen(Qt.PenStyle.NoPen)
        for r in range(n):
            for c in range(n):
                p.setBrush(self.puzzle.region_color(
                    self.puzzle.region_of(r, c)))
                p.drawRect(QRectF(rect.x() + c * cell, rect.y() + r * cell,
                                  cell + 0.6, cell + 0.6))

        # 细网格
        p.setPen(QPen(_qc(THEME["grid_line"]), max(1.0, cell * 0.018)))
        p.setBrush(Qt.BrushStyle.NoBrush)
        for i in range(1, n):
            x = rect.x() + i * cell
            p.drawLine(QPointF(x, rect.top()), QPointF(x, rect.bottom()))
            y = rect.y() + i * cell
            p.drawLine(QPointF(rect.left(), y), QPointF(rect.right(), y))

        # 区域主题色边界
        p.setPen(QPen(_qc(THEME["region_border"]),
                      max(1.8, cell * 0.05), Qt.PenStyle.SolidLine,
                      Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
        for r in range(n):
            for c in range(n):
                x0 = rect.x() + c * cell
                y0 = rect.y() + r * cell
                rid = self.puzzle.region_of(r, c)
                if r == 0 or self.puzzle.region_of(r - 1, c) != rid:
                    p.drawLine(QPointF(x0, y0), QPointF(x0 + cell, y0))
                if r == n - 1 or self.puzzle.region_of(r + 1, c) != rid:
                    p.drawLine(QPointF(x0, y0 + cell),
                               QPointF(x0 + cell, y0 + cell))
                if c == 0 or self.puzzle.region_of(r, c - 1) != rid:
                    p.drawLine(QPointF(x0, y0), QPointF(x0, y0 + cell))
                if c == n - 1 or self.puzzle.region_of(r, c + 1) != rid:
                    p.drawLine(QPointF(x0 + cell, y0),
                               QPointF(x0 + cell, y0 + cell))

        # 悬停高亮
        if self.hover is not None and not self.locked:
            r, c = self.hover
            if self.grid[r][c] == EMPTY:
                p.setPen(Qt.PenStyle.NoPen)
                p.setBrush(_qc(THEME["hover"]))
                p.drawRoundedRect(QRectF(rect.x() + c * cell + 2,
                                         rect.y() + r * cell + 2,
                                         cell - 4, cell - 4), 4, 4)

        # 排除标记与宝石
        for r in range(n):
            for c in range(n):
                st = self.grid[r][c]
                if st == MARK:
                    self._draw_mark(p, rect, r, c, cell)
                elif st == GEM:
                    self._draw_gem(p, rect, r, c, cell,
                                   warn=(r, c) in self.bad)

        # 渐晕:压暗四角,聚焦棋盘
        vign = QRadialGradient(QPointF(self.width() / 2, self.height() / 2),
                               max(self.width(), self.height()) * 0.75)
        vign_in = _qc(THEME["vignette"])
        vign_in.setAlpha(0)
        vign.setColorAt(0.55, vign_in)
        vign.setColorAt(1.0, _qc(THEME["vignette"]))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(vign))
        p.drawRect(self.rect())
        # 金尘粒子
        if self._confetti:
            self._paint_confetti(p)
        p.end()

    def _draw_gem(self, p, rect, r, c, cell, warn=False):
        x = rect.x() + c * cell + cell / 2
        y = rect.y() + r * cell + cell / 2
        w = cell * 0.58
        h = cell * 0.55
        # 辉光:主题光晕,冲突时转为警示色
        base = _qc(THEME["gem_aura_warn"] if warn else THEME["gem_aura"])
        aura_edge = QColor(base)
        aura_edge.setAlpha(0)
        aura = QRadialGradient(x, y, cell * 0.52)
        aura.setColorAt(0.0, base)
        aura.setColorAt(1.0, aura_edge)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(aura))
        p.drawEllipse(QPointF(x, y), cell * 0.52, cell * 0.52)
        # 宝石本体
        poly = QPolygonF([
            QPointF(x, y - h * 0.50),
            QPointF(x + w * 0.50, y - h * 0.10),
            QPointF(x, y + h * 0.50),
            QPointF(x - w * 0.50, y - h * 0.10),
        ])
        grad = QLinearGradient(x, y - h * 0.5, x, y + h * 0.5)
        grad.setColorAt(0.0, _qc(THEME["gem_top"]))
        grad.setColorAt(0.45, _qc(THEME["gem_mid"]))
        grad.setColorAt(1.0, _qc(THEME["gem_bot"]))
        p.setBrush(QBrush(grad))
        p.setPen(QPen(_qc(THEME["gem_edge"]), max(1.0, cell * 0.035)))
        p.drawPolygon(poly)
        # 切面棱线
        p.setPen(QPen(QColor(255, 255, 255, 60), max(0.8, cell * 0.02)))
        p.drawLine(QPointF(x - w * 0.5, y - h * 0.10), QPointF(x, y + h * 0.5))
        p.drawLine(QPointF(x + w * 0.5, y - h * 0.10), QPointF(x, y + h * 0.5))
        # 顶部棱高光
        p.setPen(QPen(QColor(255, 244, 200, 140), max(1.0, cell * 0.025)))
        p.drawLine(QPointF(x - w * 0.5, y - h * 0.10), QPointF(x, y - h * 0.5))
        p.drawLine(QPointF(x, y - h * 0.5), QPointF(x + w * 0.5, y - h * 0.10))
        # 高光
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(255, 255, 255, 200))
        p.drawEllipse(QPointF(x - w * 0.15, y - h * 0.20), w * 0.10, h * 0.08)
        if warn:
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.setPen(QPen(_qc(THEME["gem_warn_ring"]), max(1.6, cell * 0.045),
                          Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            p.drawEllipse(QPointF(x, y), cell * 0.42, cell * 0.42)

    def _draw_mark(self, p, rect, r, c, cell):
        x = rect.x() + c * cell + cell / 2
        y = rect.y() + r * cell + cell / 2
        d = cell * 0.16
        p.setPen(QPen(_qc(THEME["mark"]), max(1.6, cell * 0.045),
                      Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        p.drawLine(QPointF(x - d, y - d), QPointF(x + d, y + d))
        p.drawLine(QPointF(x - d, y + d), QPointF(x + d, y - d))

    # ---------- 胜利金尘粒子 ----------
    def start_confetti(self):
        """自下而上缓缓升起、飘散淡出的金色微粒。"""
        w = max(self.width(), 10)
        h = self.height()
        colors = ["#FFE9A8", "#F0C75E", "#D9B95C", "#FFF6D8", "#C8A44D"]
        self._confetti = [{
            "x": self._rng.uniform(0, w),
            "y": self._rng.uniform(h * 0.35, h + 10),
            "vy": self._rng.uniform(-130, -45),
            "amp": self._rng.uniform(6, 18),
            "freq": self._rng.uniform(0.8, 2.0),
            "phase": self._rng.uniform(0, 6.283),
            "r": self._rng.uniform(1.2, 3.2),
            "life": self._rng.uniform(1.6, 2.8),
            "t": 0.0,
            "color": self._rng.choice(colors),
        } for _ in range(90)]
        self._confetti_timer.start()

    def _tick_confetti(self):
        dt = 0.033
        alive = False
        for s in self._confetti:
            s["t"] += dt
            s["y"] += s["vy"] * dt
            sway = math.sin(s["phase"] + s["t"] * s["freq"] * 6.283)
            s["x"] += sway * s["amp"] * dt
            if s["t"] < s["life"] and s["y"] > -20:
                alive = True
        if not alive:
            self._stop_confetti()
        self.update()

    def _stop_confetti(self):
        if self._confetti_timer.isActive():
            self._confetti_timer.stop()
        if self._confetti:
            self._confetti = []
            self.update()

    def _paint_confetti(self, p):
        for s in self._confetti:
            alpha = max(0.0, 1.0 - s["t"] / s["life"])
            pos = QPointF(s["x"], s["y"])
            glow = QColor(s["color"])
            glow.setAlpha(int(70 * alpha))
            core = QColor(s["color"])
            core.setAlpha(int(210 * alpha))
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(glow)
            p.drawEllipse(pos, s["r"] * 3, s["r"] * 3)
            p.setBrush(core)
            p.drawEllipse(pos, s["r"], s["r"])


# ================================================================ 胜利对话框
class WinDialog(QDialog):
    def __init__(self, time_str: str, hints: int, parent=None):
        super().__init__(parent)
        self.replay = False
        self.setWindowTitle("谜题告破")
        v = QVBoxLayout(self)
        v.setContentsMargins(34, 28, 34, 24)
        v.setSpacing(10)

        mark = QLabel("✦")
        mark.setObjectName("winMark")
        mark.setAlignment(Qt.AlignmentFlag.AlignCenter)

        t = QLabel("谜题告破")
        t.setObjectName("winTitle")
        t.setAlignment(Qt.AlignmentFlag.AlignCenter)

        info = QLabel(f"用时 {time_str}   ·   提示 {hints} 次")
        info.setObjectName("winInfo")
        info.setAlignment(Qt.AlignmentFlag.AlignCenter)

        row = QHBoxLayout()
        row.setSpacing(10)
        again = QPushButton("再来一局")
        again.setObjectName("primary")
        again.clicked.connect(self._again)
        close = QPushButton("留在棋盘")
        close.setObjectName("ghost")
        close.clicked.connect(self.reject)
        row.addWidget(again, 1)
        row.addWidget(close, 1)

        v.addWidget(mark)
        v.addWidget(t)
        v.addWidget(info)
        v.addSpacing(4)
        v.addLayout(row)

    def _again(self):
        self.replay = True
        self.accept()


# ================================================================ 主窗口
QSS_TEMPLATE = Template("""
* { font-family: "Microsoft YaHei UI", "PingFang SC", "Segoe UI", sans-serif; }
#root {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 $window_top, stop:0.5 $window_mid, stop:1 $window_bot);
}
#title {
    font-family: "Georgia", "STZhongsong", "SimSun", serif;
    font-size: 34px; font-weight: 600; color: $title;
    letter-spacing: 10px;
}
#title-en { font-size: 11px; color: $title_en; letter-spacing: 8px; }
#subtitle { font-size: 13px; color: $subtitle; letter-spacing: 1px; }
#card {
    background: $card_qss;
    border: 1px solid $card_border;
    border-radius: 10px;
}
#cap { font-size: 11px; color: $cap; letter-spacing: 4px; }
#big { font-family: "Georgia", serif; font-size: 22px; color: $big; }
#msg { font-size: 13px; color: $text; }
#rules { font-size: 13px; color: $rules; }
#howto { font-size: 12px; color: $howto; }
#sep { border: none; border-top: 1px solid $sep; }
QPushButton {
    background: transparent; color: $btn_text;
    border: 1px solid $btn_border; border-radius: 8px;
    padding: 9px 12px; font-size: 14px;
}
QPushButton:hover { border-color: $btn_hover_border; color: $btn_hover_text; }
QPushButton:pressed { background: $btn_pressed; }
#primary { border-color: $primary_border; color: $primary_text; }
#primary:hover { background: $primary_hover; }
#ghost { color: $ghost_text; }
#ghost:hover { color: $ghost_hover_text; border-color: $ghost_hover_border; }
QComboBox {
    background: $combo_bg; border: 1px solid $combo_border;
    border-radius: 8px; padding: 8px 10px;
    font-size: 13px; color: $combo_text;
}
QComboBox::drop-down { border: none; width: 24px; }
QComboBox QAbstractItemView {
    background: $combo_view_bg; color: $combo_text;
    selection-background-color: $combo_view_sel;
    selection-color: $combo_view_sel_text;
    border: 1px solid $combo_border;
}
QDialog { background: $dialog_bg; border: 1px solid $dialog_border; }
#winMark { font-size: 30px; color: $win_mark; }
#winTitle {
    font-family: "Georgia", "STZhongsong", "SimSun", serif;
    font-size: 24px; font-weight: 600; color: $win_title;
    letter-spacing: 10px;
}
#winInfo { font-size: 14px; color: $win_info; }
""")


def build_qss(theme: dict) -> str:
    """按主题字典生成完整 QSS。"""
    return QSS_TEMPLATE.substitute(theme)

DIFF_SIZES = (6, 8, 10, 12)


class PuzzleWorker(QThread):
    """后台谜题雕刻线程:UI 永不为生成耗时阻塞。"""

    ready = Signal(object)

    def __init__(self, n: int, unique: bool, parent=None):
        super().__init__(parent)
        self.n = n
        self.unique = unique

    def run(self):
        self.ready.emit(Puzzle(self.n, unique=self.unique))


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("寻宝奇兵 · Treasure Quest")
        self.resize(1080, 740)
        self.setMinimumSize(940, 660)
        self._build_ui()
        self.new_game(DIFF_SIZES[1])

    def _build_ui(self):
        root = QWidget()
        root.setObjectName("root")
        self.setCentralWidget(root)
        outer = QVBoxLayout(root)
        outer.setContentsMargins(18, 12, 18, 14)
        outer.setSpacing(8)

        title = QLabel("寻宝奇兵")
        title.setObjectName("title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_en = QLabel("TREASURE QUEST")
        title_en.setObjectName("title-en")
        title_en.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub = QLabel("每行 · 每列 · 每块领地,各藏一枚宝石,且互不相邻(含对角)")
        sub.setObjectName("subtitle")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        outer.addWidget(title)
        outer.addWidget(title_en)
        outer.addWidget(sub)

        body = QHBoxLayout()
        body.setSpacing(14)
        outer.addLayout(body, 1)

        self.board = BoardWidget()
        body.addWidget(self.board, 1)

        side = QFrame()
        side.setObjectName("card")
        side.setFixedWidth(300)
        sv = QVBoxLayout(side)
        sv.setContentsMargins(16, 16, 16, 16)
        sv.setSpacing(10)

        def stat_column(cap_text, value_label):
            box = QVBoxLayout()
            box.setSpacing(2)
            cap = QLabel(cap_text)
            cap.setObjectName("cap")
            box.addWidget(cap)
            box.addWidget(value_label)
            return box

        self.time_label = QLabel("00:00")
        self.time_label.setObjectName("big")
        self.count_label = QLabel("0 / 8")
        self.count_label.setObjectName("big")
        info_row = QHBoxLayout()
        info_row.setSpacing(12)
        info_row.addLayout(stat_column("用时", self.time_label))
        info_row.addStretch(1)
        info_row.addLayout(stat_column("进度", self.count_label))
        sv.addLayout(info_row)

        sep1 = QFrame()
        sep1.setObjectName("sep")
        sep1.setFrameShape(QFrame.Shape.HLine)
        sv.addWidget(sep1)

        self.msg = QLabel("寻找线索,放置宝石。")
        self.msg.setObjectName("msg")
        self.msg.setWordWrap(True)
        self.msg.setMinimumHeight(64)
        self.msg.setAlignment(Qt.AlignmentFlag.AlignTop
                              | Qt.AlignmentFlag.AlignLeft)
        sv.addWidget(self.msg)

        def btn(text, slot, obj=None):
            b = QPushButton(text)
            b.clicked.connect(slot)
            if obj:
                b.setObjectName(obj)
            return b

        sv.addWidget(btn("新的一局", self.new_random, "primary"))
        row1 = QHBoxLayout()
        row1.setSpacing(8)
        row1.addWidget(btn("提示", lambda: self.board.hint()))
        row1.addWidget(btn("撤销", lambda: self.board.undo()))
        sv.addLayout(row1)
        row2 = QHBoxLayout()
        row2.setSpacing(8)
        row2.addWidget(btn("清空", lambda: self.board.clear_all()))
        self.diff = QComboBox()
        self.diff.addItems(["新手 · 6×6", "进阶 · 8×8",
                            "困难 · 10×10", "大师 · 12×12"])
        self.diff.setCurrentIndex(1)
        self.diff.currentIndexChanged.connect(self.on_difficulty)
        row2.addWidget(self.diff, 1)
        sv.addLayout(row2)
        self.mode = QComboBox()
        self.mode.addItems(["标准 · 唯一解", "休闲 · 任意解"])
        self.mode.currentIndexChanged.connect(self.on_mode_changed)
        sv.addWidget(self.mode)

        sep2 = QFrame()
        sep2.setObjectName("sep")
        sep2.setFrameShape(QFrame.Shape.HLine)
        sv.addWidget(sep2)

        self.rules = QLabel()
        self.rules.setObjectName("rules")
        self._set_rules_text()
        sv.addWidget(self.rules)

        howto = QLabel("左键 放置 / 收回 · 右键 排除标记")
        howto.setObjectName("howto")
        sv.addWidget(howto)

        self.theme_btn = QPushButton()
        self.theme_btn.setObjectName("ghost")
        self.theme_btn.clicked.connect(self.toggle_theme)
        self._sync_theme_btn()
        sv.addWidget(self.theme_btn)
        sv.addStretch(1)
        body.addWidget(side)

        # 计时
        self.clock = QElapsedTimer()
        self.timer = QTimer(self)
        self.timer.setInterval(500)
        self.timer.timeout.connect(self._tick_time)

        # 信号
        self.board.changed.connect(self.on_changed)
        self.board.solved.connect(self.on_solved)

        # 后台谜题雕刻
        self._worker = None
        self._pending = None

    def closeEvent(self, event):
        # 等待雕刻线程收尾,避免退出时线程仍在运行
        if self._worker is not None and self._worker.isRunning():
            self._worker.wait(3000)
        super().closeEvent(event)

    # ---------- 槽 ----------
    def new_random(self):
        self.new_game(DIFF_SIZES[self.diff.currentIndex()])

    def new_game(self, n: int):
        unique = self.mode.currentIndex() == 0
        self._pending = (n, unique)
        if self._worker is not None and self._worker.isRunning():
            self.statusBar().showMessage("谜题雕刻中,稍候…", 3000)
            return
        self._start_worker()

    def _start_worker(self):
        n, unique = self._pending
        self._pending = None
        self._worker = PuzzleWorker(n, unique, self)
        self._worker.ready.connect(self._on_puzzle_ready)
        self._worker.finished.connect(self._on_worker_finished)
        self.statusBar().showMessage("正在雕刻谜题…", 2000)
        self._worker.start()

    def _on_puzzle_ready(self, puzzle: Puzzle):
        if self._worker is not None:
            self._worker = None
        self.board.new_game(puzzle)
        self.clock.restart()
        self.timer.start()
        self.time_label.setText("00:00")
        self.count_label.setText(f"0 / {puzzle.n}")

    def _on_worker_finished(self):
        w = self.sender()
        if w is not None:
            w.deleteLater()
        if w is self._worker:
            self._worker = None
        if self._pending is not None and self._worker is None:
            self._start_worker()

    def on_difficulty(self, idx: int):
        self.new_game(DIFF_SIZES[idx])

    def on_mode_changed(self, idx: int):
        self.new_random()

    # ---------- 主题 ----------
    def _set_rules_text(self):
        dot = THEME["region_border"]
        self.rules.setText(
            f'<span style="color:{dot}">◆</span> 每行恰好一枚宝石<br>'
            f'<span style="color:{dot}">◆</span> 每列恰好一枚宝石<br>'
            f'<span style="color:{dot}">◆</span> 每块领地恰好一枚<br>'
            f'<span style="color:{dot}">◆</span> 宝石之间八向不相邻')

    def _sync_theme_btn(self):
        target = "night" if THEME_NAME == "day" else "day"
        side = "夜间" if target == "night" else "日间"
        self.theme_btn.setText(f"切换{side}主题 · {THEME_LABEL[target]}")

    def toggle_theme(self):
        apply_theme("night" if THEME_NAME == "day" else "day")
        app = QApplication.instance()
        if app:
            app.setStyleSheet(build_qss(THEME))
            app.setWindowIcon(make_icon())
        self._sync_theme_btn()
        self._set_rules_text()
        color = THEME["msg_win"] if self.board.locked else THEME["msg_text"]
        self.msg.setStyleSheet(f"color: {color};")
        self.board.update()

    def on_changed(self, count: int, msg: str):
        n = self.board.puzzle.n if self.board.puzzle else 0
        self.count_label.setText(f"{count} / {n}")
        self.msg.setText(msg)
        if self.board.locked:
            color = THEME["msg_win"]
        elif msg.startswith("冲突") or msg.startswith("存在冲突"):
            color = THEME["msg_warn"]
        else:
            color = THEME["msg_text"]
        self.msg.setStyleSheet(f"color: {color};")

    def on_solved(self):
        elapsed = int(self.clock.elapsed() / 1000)
        time_str = f"{elapsed // 60:02d}:{elapsed % 60:02d}"
        self.time_label.setText(time_str)
        self.timer.stop()
        hints = self.board.hints_used
        QTimer.singleShot(1100, lambda: self._show_win(time_str, hints))

    def _show_win(self, time_str: str, hints: int):
        dlg = WinDialog(time_str, hints, self)
        dlg.exec()
        if dlg.replay:
            self.new_random()

    def _tick_time(self):
        if self.board.locked:
            return
        s = int(self.clock.elapsed() / 1000)
        self.time_label.setText(f"{s // 60:02d}:{s % 60:02d}")


# ================================================================ 图标
def make_icon() -> QIcon:
    pm = QPixmap(64, 64)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(_qc(THEME["icon_bg"]))
    p.drawEllipse(2, 2, 60, 60)
    poly = QPolygonF([QPointF(32, 10), QPointF(52, 25),
                      QPointF(32, 54), QPointF(12, 25)])
    grad = QLinearGradient(0, 10, 0, 54)
    grad.setColorAt(0, _qc(THEME["gem_top"]))
    grad.setColorAt(0.45, _qc(THEME["gem_mid"]))
    grad.setColorAt(1, _qc(THEME["gem_bot"]))
    p.setBrush(QBrush(grad))
    p.setPen(QPen(_qc(THEME["gem_edge"]), 2.4))
    p.drawPolygon(poly)
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QColor(255, 255, 255, 190))
    p.drawEllipse(QPointF(25, 21), 4, 3)
    p.end()
    return QIcon(pm)


# ================================================================ 自测
def run_selftest() -> int:
    """离屏自测:谜题约束、区域连通、渲染、交互、冲突、撤销、提示。"""
    app = QApplication.instance() or QApplication(sys.argv)
    try:  # 让中文输出在各类控制台下不乱码
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    rng = random.Random(20260101)
    failures: list[str] = []

    def check(name, fn):
        try:
            fn()
            print(f"  [ok] {name}")
        except AssertionError as exc:
            failures.append(f"{name}: {exc}")
            print(f"  [FAIL] {name}: {exc}")

    def test_puzzle():
        for n in (6, 8, 10, 12):
            for _ in range(6):
                pz = Puzzle(n, rng, unique=False)
                sol = pz.solution
                assert len(sol) == n and len(set(sol)) == n, "宝藏数量异常"
                assert len({r for r, _ in sol}) == n, "行约束失败"
                assert len({c for _, c in sol}) == n, "列约束失败"
                for i in range(n):
                    for j in range(i + 1, n):
                        a, b = sol[i], sol[j]
                        dr, dc = abs(a[0] - b[0]), abs(a[1] - b[1])
                        assert dr > 1 or dc > 1, f"八邻域冲突 {a}-{b}"
                rids = {pz.region_of(r, c) for r, c in sol}
                assert len(rids) == n, "每区域一枚宝藏失败"
                for rid in rids:
                    cells = {(r, c) for r in range(n) for c in range(n)
                             if pz.region_of(r, c) == rid}
                    start = next(iter(cells))
                    seen = {start}
                    dq = deque([start])
                    while dq:
                        cr, cc = dq.popleft()
                        for dr2, dc2 in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                            nb = (cr + dr2, cc + dc2)
                            if nb in cells and nb not in seen:
                                seen.add(nb)
                                dq.append(nb)
                    assert seen == cells, f"n={n} 区域 {rid} 不连通"

    def test_render():
        board = BoardWidget()
        board.resize(760, 760)
        img = QImage(760, 760, QImage.Format.Format_ARGB32)
        for name in ("day", "night"):
            apply_theme(name)
            board.new_game(Puzzle(8, rng))
            img.fill(0xFFFFFFFF)
            board.render(img)
            assert not img.isNull(), f"{name} 主题渲染结果为空"
            board.new_game(Puzzle(12, rng))
            board.render(img)
        apply_theme("day")  # 恢复默认主题

    def test_win_flow():
        board = BoardWidget()
        board.resize(640, 640)
        pz = Puzzle(6, rng)
        board.new_game(pz)
        won = []
        board.solved.connect(lambda: won.append(1))
        for (r, c) in pz.solution:
            if board.set_cell(r, c, GEM):
                board._after_change(r, c, "gem")
        assert won, "放置全部参考解未触发胜利"
        assert board.locked, "胜利后未锁定输入"

    def test_conflict_undo():
        board = BoardWidget()
        board.resize(560, 560)
        pz = Puzzle(6, rng)
        board.new_game(pz)
        r0, c0 = pz.solution[0]
        board.set_cell(r0, c0, GEM)
        board._after_change(r0, c0, "gem")
        c1 = (c0 + 3) % pz.n
        board.set_cell(r0, c1, GEM)
        board._after_change(r0, c1, "gem")
        assert board.bad, "同行冲突未检出"
        board.undo()
        assert not board.bad, "撤销后冲突应消失"

    def test_hint():
        board = BoardWidget()
        board.resize(560, 560)
        board.new_game(Puzzle(6, rng))
        board.hint()
        assert board._gem_count() == 1, "提示应放置一枚宝石"
        assert board.hints_used == 1, "提示计数异常"

    def test_unique():
        for n, k in ((6, 3), (8, 2), (10, 2), (12, 1)):
            for _ in range(k):
                pz = Puzzle(n, rng, unique=True)
                sols = pz._solutions(cap=2)
                assert len(sols) == 1, f"n={n} 谜题非唯一解(共 {len(sols)} 解)"
                # 收紧后领地仍须连通,且参考解仍是合法解
                for rid in range(n):
                    cells = {(r, c) for r in range(n) for c in range(n)
                             if pz.region_of(r, c) == rid}
                    start = next(iter(cells))
                    seen = {start}
                    dq = deque([start])
                    while dq:
                        cr, cc = dq.popleft()
                        for dr2, dc2 in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                            nb = (cr + dr2, cc + dc2)
                            if nb in cells and nb not in seen:
                                seen.add(nb)
                                dq.append(nb)
                    assert seen == cells, f"n={n} 收紧后区域 {rid} 不连通"
                rids = {pz.region_of(r, c) for r, c in pz.solution}
                assert len(rids) == n, "参考解领地约束被破坏"

    print("寻宝奇兵 自测开始")
    check("谜题生成(行列/八邻域/每区域一枚/区域连通)", test_puzzle)
    check("唯一解模式(6/8/10/12 收敛且领地连通)", test_unique)
    check("棋盘渲染(8x8 与 12x12 离屏绘制)", test_render)
    check("交互(放置参考解触发胜利并锁定)", test_win_flow)
    check("冲突检测与撤销", test_conflict_undo)
    check("提示功能", test_hint)
    if failures:
        print(f"自测失败 {len(failures)} 项")
        return 1
    print("全部自测通过")
    return 0


# ================================================================ 入口
def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(build_qss(THEME))
    app.setWindowIcon(make_icon())
    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(run_selftest())
    if "--smoke" in sys.argv:
        _app = QApplication(sys.argv)
        _app.setStyleSheet(build_qss(THEME))
        _app.setWindowIcon(make_icon())
        _win = MainWindow()
        _win.show()
        QTimer.singleShot(1500, _app.quit)
        sys.exit(_app.exec())
    main()
