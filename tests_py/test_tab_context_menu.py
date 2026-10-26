from __future__ import annotations

import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtWidgets import QApplication

from ksnip_py.main_window import MainWindow


class TabContextMenuTest(unittest.TestCase):
    def setUp(self):
        self.app = QApplication.instance() or QApplication([])
        self.window = MainWindow()
        # Start from a clean slate so tab counts are deterministic.
        self.window._context_tab_index = 0
        self.window._tab_ctx_close_all()
        self.assertEqual(self.window.tabs.count(), 0)

    def _open(self, title):
        return self.window.new_tab(title=title)

    def test_tab_bar_uses_custom_context_menu(self):
        self.assertEqual(
            self.window.tabs.tabBar().contextMenuPolicy(),
            Qt.ContextMenuPolicy.CustomContextMenu,
        )
        labels = [a.text() for a in self.window.tab_context_menu.actions() if a.text()]
        for expected in ("Close", "Close Other", "Save", "Save As...", "Save All",
                         "Rename", "Open Directory", "Copy", "Copy Path", "Delete"):
            self.assertIn(expected, labels)

    def test_close_left_keeps_target_and_right(self):
        self._open("A"); self._open("B"); self._open("C")
        self.window._context_tab_index = 1
        self.window._tab_ctx_close_left()
        self.assertEqual(self.window.tabs.count(), 2)

    def test_close_right_on_last_tab_closes_nothing(self):
        self._open("A"); self._open("B"); self._open("C")
        self.window._context_tab_index = self.window.tabs.count() - 1
        self.window._tab_ctx_close_right()
        self.assertEqual(self.window.tabs.count(), 3)

    def test_close_others_keeps_only_target(self):
        self._open("A"); self._open("B"); self._open("C")
        self.window._context_tab_index = 1
        self.window._tab_ctx_close_others()
        self.assertEqual(self.window.tabs.count(), 1)
        self.assertEqual(self.window.tabs.tabText(0), "B")

    def test_close_all_removes_everything(self):
        self._open("A"); self._open("B")
        self.window._context_tab_index = 0
        self.window._tab_ctx_close_all()
        self.assertEqual(self.window.tabs.count(), 0)

    def test_context_menu_disables_irrelevant_actions(self):
        self._open("A"); self._open("B")
        self.window._context_tab_index = 0
        self.window._update_tab_context_actions(0)
        self.assertFalse(self.window._ctx_close_left.isEnabled())
        self.assertTrue(self.window._ctx_close_right.isEnabled())
        self.assertTrue(self.window._ctx_close_others.isEnabled())

    def test_show_menu_ignores_click_outside_tabs(self):
        self._open("A")
        try:
            self.window._show_tab_context_menu(QPoint(0, 0))
        except Exception as exc:  # pragma: no cover
            self.fail(f"_show_tab_context_menu raised: {exc}")


if __name__ == "__main__":
    unittest.main()

