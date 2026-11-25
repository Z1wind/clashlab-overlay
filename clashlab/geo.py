# -*- coding: utf-8 -*-
"""等距网格坐标系统：四十四乘四十四，屏幕与瓦片双向映射。

坐标约定（与 gold H 实测一致，符号勿翻转）：
- 原点 (0,0) = 地图菱形顶点（画面最上点）；
- gx 轴沿「顶点 → 右腰」方向（右下），gy 轴沿「顶点 → 左腰」方向（左下）；
- 四角顺序：(0,0) 顶 / (n,0) 右 / (n,n) 底 / (0,n) 左；
- 像素 x 向右增、y 向下增。
映射数学（单应）已与 gold H 逐点核对一致；偏差来自 quad 输入选错区域，
不是轴向/正负号/比例因子反转（反证见 out/snap/compare_final.md）。
"""
import numpy as np
import cv2


def tile_to_screen(gx, gy, cx, cy, kx, ky, n=44):
    """公式解：gx 沿右下、gy 沿左下，原点在地图顶点。"""
    return (cx + (gx - gy) * kx, cy + (gx + gy - n) * ky)


def screen_to_tile(sx, sy, cx, cy, kx, ky, n=44):
    a = (sx - cx) / kx
    b = (sy - cy) / ky
    return ((a + b + n) / 2.0, (b - a + n) / 2.0)


def order_diamond(quad):
    """把四个点整理成 上、右、下、左 的顺序。"""
    pts = np.array(quad, dtype=np.float32).reshape(-1, 2)
    if len(pts) != 4:
        raise ValueError("需要四个角点")
    center = pts.mean(axis=0)
    ang = np.arctan2(pts[:, 1] - center[1], pts[:, 0] - center[0])
    pts = pts[np.argsort(ang)]          # 逆时针（图像坐标 y 向下时为顺时针视觉）
    top_idx = int(np.argmin(pts[:, 1]))
    pts = np.roll(pts, -top_idx, axis=0)
    # roll 后第一个是最高点；若第二点在左，说明方向反了
    if pts[1, 0] < pts[0, 0]:
        pts = pts[[0, 3, 2, 1]]
    return pts


class Calib:
    """用四个地图角点（或已确认锚点对）求单应矩阵，承担缩放、透视与窗口非等比。"""

    def __init__(self, H, n=44, quad=None):
        self.H = H
        self.n = n
        self.quad = np.array(quad, dtype=np.float32) if quad is not None else None

    @classmethod
    def from_quad(cls, quad, n=44):
        """四角（任意顺序）→ 单应。src 角点与 上/右/下/左 一一对应。"""
        pts = order_diamond(quad)
        src = np.array([[0, 0], [n, 0], [n, n], [0, n]], dtype=np.float32)
        H = cv2.getPerspectiveTransform(src, pts)
        return cls(H, n=n, quad=pts)

    @classmethod
    def from_quad_norm(cls, norm_quad, tw, th, n=44):
        """v9-② 视口适配构造层：quad 为相对客户区的归一化四点（0–1），
        按当前客户区 (tw, th) 还原像素后走与 from_quad 完全相同的单应求解。

        换算语义（tile_to_px / px_to_tile / sanity）一行未动；这里只负责把
        归一化 quad 撒到当前视口，再委托 from_quad。
        """
        q = np.asarray(norm_quad, dtype=np.float32).reshape(-1, 2)
        q[:, 0] *= float(tw)
        q[:, 1] *= float(th)
        return cls.from_quad(q.tolist(), n=n)

    @classmethod
    def from_anchors(cls, pairs, n=44):
        """由已确认 (tile, px) 锚点对最小二乘拟合 tile→px 单应。

        用途：自动 quad 不可信（草地轮廓选错区域）时，用人工/已验证锚点
        重建映射，不再把错误 quad 喂给正确的单应。
        pairs: [(gx, gy, px, py), ...] 或 [([gx,gy], [px,py]), ...]，≥4 对。
        """
        src, dst = [], []
        for p in pairs:
            if isinstance(p[0], (list, tuple)):
                (gx, gy), (px, py) = p
            else:
                gx, gy, px, py = p
            src.append([float(gx), float(gy)])
            dst.append([float(px), float(py)])
        if len(src) < 4:
            raise ValueError("锚点对至少需要 4 对才能拟合单应")
        src = np.array(src, dtype=np.float32)
        dst = np.array(dst, dtype=np.float32)
        H, _ = cv2.findHomography(src, dst, method=0)
        if H is None:
            raise ValueError("锚点对退化，无法拟合单应")
        return cls(H, n=n)

    def tile_to_px(self, gx, gy):
        v = np.array([gx, gy, 1.0], dtype=np.float64)
        p = self.H @ v
        return float(p[0] / p[2]), float(p[1] / p[2])

    def px_to_tile(self, x, y):
        Hinv = np.linalg.inv(self.H)
        v = np.array([x, y, 1.0], dtype=np.float64)
        p = Hinv @ v
        return float(p[0] / p[2]), float(p[1] / p[2])

    def sanity(self, frame_shape=None):
        """菱形/单应几何自检：凸、对角比例、质心居中。

        返回 (ok, reasons)。只做纯几何检查，不读图、不调检测。
        注意：几何自检只能拦明显畸形，拦不住「quad 落在画面另一区域」的
        区域选错；那种情况必须靠已验证参考标定或锚点拟合。
        """
        reasons = []
        if self.quad is None:
            return False, ["无 quad 记录，无法自检"]
        q = np.asarray(self.quad, dtype=np.float64)
        hull = cv2.convexHull(q.astype(np.float32))
        if len(hull) != 4:
            reasons.append("quad 非凸")
        d_v = float(np.linalg.norm(q[0] - q[2]))
        d_h = float(np.linalg.norm(q[1] - q[3]))
        if d_v > 1 and d_h > 1:
            ratio = max(d_v, d_h) / min(d_v, d_h)
            if ratio > 2.2:
                reasons.append(f"对角比例 {ratio:.2f} 偏离等距菱形（期望≈1）")
        if frame_shape is not None:
            fh, fw = frame_shape[:2]
            ctr = q.mean(axis=0)
            if abs(ctr[0] - fw / 2.0) > fw * 0.35 or abs(ctr[1] - fh / 2.0) > fh * 0.35:
                reasons.append(f"质心 ({ctr[0]:.0f},{ctr[1]:.0f}) 偏离画面中心")
        return len(reasons) == 0, reasons

    def reproj_error(self):
        if self.quad is None:
            return 0.0
        errs = []
        for (gx, gy), (px, py) in zip([(0, 0), (self.n, 0), (self.n, self.n), (0, self.n)], self.quad):
            x, y = self.tile_to_px(gx, gy)
            errs.append(((x - px) ** 2 + (y - py) ** 2) ** 0.5)
        return float(np.mean(errs))

    def grid_points(self, step=2):
        n = self.n
        for gx in range(0, n + 1, step):
            for gy in range(0, n + 1, step):
                yield gx, gy, self.tile_to_px(gx, gy)

    def to_dict(self):
        return {"n": self.n, "H": self.H.tolist()}

    @classmethod
    def from_dict(cls, d):
        return cls(np.array(d["H"], dtype=np.float64), n=d.get("n", 44))
