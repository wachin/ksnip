"""Each installed model card opens its model folder in the file manager.

Run with:  QT_QPA_PLATFORM=offscreen python -m pytest tests_py/test_model_manager_folders.py
"""

from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest


pytest.importorskip("PyQt6", reason="PyQt6 is a required dependency")

from PyQt6.QtWidgets import QApplication  # noqa: E402

from ksnip_py import download_manager as dm  # noqa: E402


@pytest.fixture(scope="module")
def application():
    return QApplication.instance() or QApplication([])


def _dialog_with_checks_done() -> dm.DownloadManagerDialog:
    dialog = dm.DownloadManagerDialog()
    assert dialog._checker_worker is not None
    dialog._checker_worker.wait(5000)
    QApplication.processEvents()
    return dialog


def _capture_opened(monkeypatch) -> list[str]:
    opened: list[str] = []
    monkeypatch.setattr(
        dm.QDesktopServices,
        "openUrl",
        staticmethod(lambda url: opened.append(url.toLocalFile()) or True),
    )
    return opened


def test_paddle_models_point_at_the_paddlex_cache(application, tmp_path, monkeypatch):
    cache = tmp_path / ".paddlex" / "official_models"
    cache.mkdir(parents=True)
    monkeypatch.setattr(dm.Path, "home", staticmethod(lambda: tmp_path))

    assert dm.DownloadManagerDialog._paddle_models_directory() == cache
    dialog = _dialog_with_checks_done()
    for model_id in ("paddleocr-line", "paddleocr-structure", "paddleocr-formula"):
        assert dialog._cards[model_id]._model.folder() == cache
    dialog.deleteLater()


def test_legacy_paddleocr_cache_is_used_when_paddlex_is_absent(
    application, tmp_path, monkeypatch
):
    legacy = tmp_path / ".paddleocr"
    legacy.mkdir()
    monkeypatch.setattr(dm.Path, "home", staticmethod(lambda: tmp_path))

    assert dm.DownloadManagerDialog._paddle_models_directory() == legacy


def test_missing_cache_and_script_have_no_folder(application, tmp_path, monkeypatch):
    monkeypatch.setattr(dm.Path, "home", staticmethod(lambda: tmp_path))

    assert dm.DownloadManagerDialog._paddle_models_directory() is None
    assert dm.DownloadManagerDialog._external_script_directory() is None


def test_open_in_file_manager_asks_the_desktop(application, tmp_path, monkeypatch):
    opened = _capture_opened(monkeypatch)
    folder = tmp_path / "models"
    folder.mkdir()

    assert dm.open_in_file_manager(folder) is True
    assert [Path(item) for item in opened] == [folder]
    assert dm.open_in_file_manager(None) is False
    assert dm.open_in_file_manager(tmp_path / "missing") is False
    assert [Path(item) for item in opened] == [folder]


def test_installed_card_shows_the_folder_button_and_opens_it(
    application, tmp_path, monkeypatch
):
    cache = tmp_path / ".paddlex" / "official_models"
    cache.mkdir(parents=True)
    monkeypatch.setattr(dm.Path, "home", staticmethod(lambda: tmp_path))
    opened = _capture_opened(monkeypatch)

    dialog = _dialog_with_checks_done()
    card = dialog._cards["paddleocr-line"]

    card.set_installed_status(False)
    assert card.folder_btn.isHidden()

    card.set_installed_status(True)
    assert not card.folder_btn.isHidden()
    assert str(cache) in card.folder_btn.toolTip()

    card.folder_btn.click()
    QApplication.processEvents()
    assert [Path(item) for item in opened] == [cache]
    dialog.deleteLater()


def test_card_without_a_folder_never_shows_the_button(application, tmp_path, monkeypatch):
    monkeypatch.setattr(dm.Path, "home", staticmethod(lambda: tmp_path))

    dialog = _dialog_with_checks_done()
    card = dialog._cards["external-ocr-script"]

    card.set_installed_status(True)
    assert card.folder_btn.isHidden()
    dialog.deleteLater()
