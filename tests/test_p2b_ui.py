# -*- coding: utf-8 -*-
"""P2-4/P2-5 离线单测（纯逻辑，不建窗口、不抓屏、不碰 adb）。

被测行为：
1) _panel_place 三档落点（right/down/inner + auto 选择）：
   - right 放得下 -> 客户区右侧外、整体在屏内；
   - down 的 x 必须**水平居中在客户区下方**（旧实现 x=tx+tw+gap，客户区靠右时会
     整个推出屏幕右侧 —— 本文件用 tx=700 的负例锁死这个回归）；
   - down 高度按**主屏工作区底**算（不盖任务栏），不足 PANEL_MIN_H 判不可用；
   - 显式档位放不下时降级（不生成越界窗口），auto 顺序 右→下→内。
2) FirstRunHint 首启角标一次性：
   - 旧实现「画角标同帧写 .first_run_done」-> 只闪 1 帧；新实现只在可见帧累计满
     dwell 秒后才落 flag；落盘失败继续提示；flag 已存在/已有数据不再提示。
"""
import inspect
import os
import shutil
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from clashlab.overlay import runtime


class _FakeUser32:
    """替身：只实现 _panel_place 用到的 GetSystemMetrics（0=宽, 1=高）。"""

    def __init__(self, sw=1920, sh=1080):
        self.sw = sw
        self.sh = sh

    def GetSystemMetrics(self, idx):
        return self.sw if idx == 0 else self.sh


class TestPanelPlace(unittest.TestCase):
    """1280x720 客户区 / 1920x1080 主屏 + 工作区底 1032（任务栏 48px）的真实口径。"""

    def _place(self, tx, ty, tw, th, pref, sw=1920, sh=1080, work_bottom=1032):
        with mock.patch.object(runtime, "user32", _FakeUser32(sw, sh)), \
                mock.patch.object(runtime, "_primary_workarea_bottom",
                                  lambda _sh: work_bottom):
            return runtime._panel_place(tx, ty, tw, th, pref)

    def test_right_fits_exactly_at_client_right(self):
        x, y, w, h, zone = self._place(96, 93, 1280, 720, "right")
        self.assertEqual(zone, "right")
        self.assertEqual((x, y, w, h), (1384.0, 93, 440.0, 720))
        self.assertLessEqual(x + w, 1920)      # 整体在主屏内
        self.assertLessEqual(y + h, 1080)

    def test_right_not_fit_falls_back_but_never_offscreen(self):
        # 客户区 [500,1780] 整体在主屏内，但右侧 +448 放不下 -> 必须降级，
        # 且外置档（right/down）不得返回屏幕外窗口；inner 档按设计=客户区矩形。
        x, y, w, h, zone = self._place(500, 0, 1280, 720, "right")
        self.assertIn(zone, ("down", "inner"))
        self.assertLessEqual(x + w, 1920)
        self.assertLessEqual(y + h, 1080)

    def test_down_x_is_centered_under_client_not_at_right_old_bug(self):
        # 旧实现 down 的 x=tx+tw+8=1988 -> 整个面板横向出屏；新实现必须居中且不出屏
        x, y, w, h, zone = self._place(96, 0, 1280, 720, "down",
                                       sh=1200, work_bottom=1160)
        self.assertEqual(zone, "down")
        self.assertAlmostEqual(x, 96 + (1280 - 440) / 2.0)   # 516
        self.assertGreaterEqual(x, 0)
        self.assertLessEqual(x + w, 1920)
        self.assertAlmostEqual(y, 0 + 720 + 8)               # 728
        self.assertAlmostEqual(h, 1160 - 728)                # 432 = 工作区底 - y

    def test_down_uses_workarea_bottom_not_screen_bottom(self):
        x, y, w, h, zone = self._place(96, 0, 1280, 720, "down",
                                       sh=1200, work_bottom=1160)
        self.assertEqual(zone, "down")
        self.assertAlmostEqual(y + h, 1160)   # 不覆盖任务栏
        self.assertNotAlmostEqual(y + h, 1200)

    def test_down_unusable_height_falls_back(self):
        # 本机实测：客户区底 813 / 工作区底 1032 -> 只剩 211 < PANEL_MIN_H(360)
        x, y, w, h, zone = self._place(96, 93, 1280, 720, "down")
        self.assertNotEqual(zone, "down")
        self.assertGreaterEqual(runtime.PANEL_MIN_H, 300)
        self.assertLessEqual(x + w, 1920)
        self.assertLessEqual(y + h, 1080)

    def test_auto_picks_right_when_it_fits(self):
        x, y, w, h, zone = self._place(96, 93, 1280, 720, "auto")
        self.assertEqual(zone, "right")

    def test_auto_picks_down_when_right_does_not_fit(self):
        x, y, w, h, zone = self._place(700, 0, 1280, 720, "auto",
                                       sh=1200, work_bottom=1160)
        self.assertEqual(zone, "down")
        self.assertLessEqual(x + w, 1920)

    def test_auto_falls_to_inner_strip_when_neither_fits(self):
        """右/下都放不下 -> inner 回退「客户区右侧 440 宽条带」，且条带夹进主屏
        （客户区本身部分出屏时也不生成越界窗口）。"""
        x, y, w, h, zone = self._place(700, 700, 1280, 720, "auto")
        self.assertEqual(zone, "inner")
        self.assertEqual(w, runtime.PANEL_PW)
        self.assertGreaterEqual(x, 0)
        self.assertGreaterEqual(y, 0)
        self.assertLessEqual(x + w, 1920)
        self.assertLessEqual(y + h, 1080)

    def test_inner_is_right_strip_not_whole_client(self):
        """P2-5b：inner=客户区右侧 PANEL_PW 宽条带（窗口即面板）。
        旧实现返回整客户区 1280x720：左侧 840x720 被不透明底板盖住且拦截鼠标。"""
        x, y, w, h, zone = self._place(96, 93, 1280, 720, "inner")
        self.assertEqual(zone, "inner")
        self.assertEqual((x, y, w, h), (936.0, 93, 440.0, 720))
        self.assertEqual(x + w, 96 + 1280)     # 贴客户区右缘
        self.assertLess(w, 1280)               # 不再覆盖整个客户区
        # 客户区比条带窄时：条带宽=客户区宽，不越界
        x2, y2, w2, h2, z2 = self._place(0, 0, 300, 200, "inner")
        self.assertEqual(z2, "inner")
        self.assertEqual((x2, y2, w2, h2), (0, 0, 300, 200))

    def test_right_clamps_vertically_into_screen(self):
        x, y, w, h, zone = self._place(96, -50, 1280, 720, "right")
        self.assertEqual(zone, "right")
        self.assertGreaterEqual(y, 0)
        self.assertLessEqual(y + h, 1080)


class TestFirstRunHint(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="p2b_first_run_")
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)
        self.flag = runtime.first_run_flag_path(self.root)

    def test_flag_path_is_out_overlay_dot_file(self):
        self.assertEqual(os.path.basename(self.flag), ".first_run_done")
        self.assertEqual(os.path.dirname(self.flag).replace("/", "\\"),
                         os.path.join(self.root, "out", "overlay").replace("/", "\\"))

    def test_first_launch_shows_then_flags_after_dwell(self):
        hint = runtime.FirstRunHint(self.root, dwell_s=6.0)
        drawn = []
        for i in range(0, 21):          # 0.5s 步进，模拟 60fps 的可见帧序列
            drawn.append(hint.tick(i * 0.5, has_data=False))
        # 前 6s 内（12 个 tick）都要画
        self.assertTrue(all(drawn[:12]), drawn)
        # 满 6s 后落 flag 并停止绘制
        self.assertTrue(os.path.exists(self.flag), "满 dwell 后必须落 .first_run_done")
        self.assertFalse(drawn[12], "满 dwell 那一帧起不再画角标")
        self.assertFalse(hint.tick(15.0, has_data=False))

    def test_second_launch_never_shows_again(self):
        first = runtime.FirstRunHint(self.root, dwell_s=6.0)
        for i in range(0, 14):
            first.tick(i * 0.5, has_data=False)
        self.assertTrue(first.done and os.path.exists(self.flag))
        with open(self.flag, "r", encoding="utf-8") as f:
            content_before = f.read()

        second = runtime.FirstRunHint(self.root, dwell_s=6.0)
        self.assertTrue(second.done)
        for i in range(0, 20):
            self.assertFalse(second.tick(i * 0.5, has_data=False),
                             "flag 已存在时第二次启动不得再出现角标")
        with open(self.flag, "r", encoding="utf-8") as f:
            content_after = f.read()
        self.assertEqual(content_after, content_before, "第二次启动不得重写 flag")

    def test_has_data_suppresses_without_writing_flag(self):
        hint = runtime.FirstRunHint(self.root, dwell_s=1.0)
        for i in range(0, 10):
            self.assertFalse(hint.tick(i * 0.5, has_data=True))
        self.assertFalse(os.path.exists(self.flag))

    def test_write_failure_keeps_hint_visible_and_retries(self):
        hint = runtime.FirstRunHint(self.root, dwell_s=1.0, retry_s=0.5)
        with mock.patch.object(runtime, "mark_first_run_done", lambda _root: False):
            last = None
            for i in range(0, 12):
                last = hint.tick(i * 0.5, has_data=False)
            self.assertTrue(last, "落盘失败时必须继续提示，不能静默丢掉首启提示")
            self.assertFalse(os.path.exists(self.flag))
        # 恢复落盘能力后一次 tick 就应成功关闭
        self.assertFalse(hint.tick(9.0, has_data=False))
        self.assertTrue(os.path.exists(self.flag))

    def test_flag_write_is_atomic_no_tmp_left(self):
        self.assertTrue(runtime.mark_first_run_done(self.root))
        self.assertTrue(os.path.exists(self.flag))
        self.assertFalse(os.path.exists(self.flag + ".tmp"))
        with open(self.flag, "r", encoding="utf-8") as f:
            self.assertIn("first-run hint shown", f.read())

    def test_status_badge_calls_extracted_helper(self):
        """P2-4 的接线必须存在。_draw_status_badge 的渲染主体归 p2-render-owner，
        允许他把这一行调用挪到别的绘制分支（如 C10 避让后），但不允许悄悄删掉首启角标。"""
        src_all = inspect.getsource(runtime)
        self.assertIn("def _draw_first_run_hint", src_all)
        self.assertIn("_draw_first_run_hint(imgui, rt, dl)", src_all)
        self.assertTrue(hasattr(runtime, "FirstRunHint"))


if __name__ == "__main__":
    unittest.main()
