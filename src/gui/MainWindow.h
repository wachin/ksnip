/*
 *  Copyright (C) 2016 Damir Porobic <https://github.com/damirporobic>
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU Lesser General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU Lesser General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 51 Franklin Street, Fifth Floor,
 * Boston, MA 02110-1301, USA.
 *
 */

#ifndef KSNIP_MAINWINDOW_H
#define KSNIP_MAINWINDOW_H

#include <QtWidgets>

#include <functional>

#include <kImageAnnotator/KImageAnnotator.h>

#include "gui/aboutDialog/AboutDialog.h"
#include "src/gui/settingsDialog/SettingsDialog.h"
#include "src/widgets/CustomToolButton.h"
#include "src/widgets/MainToolBar.h"
#include "src/backend/imageGrabber/AbstractImageGrabber.h"
#include "src/backend/config/KsnipConfigProvider.h"
#include "src/backend/uploader/CaptureUploader.h"
#include "src/backend/CapturePrinter.h"
#include "src/common/loader/IconLoader.h"
#include "src/common/enum/RunMode.h"
#include "src/gui/operations/SaveOperation.h"
#include "src/gui/operations/AddWatermarkOperation.h"
#include "src/gui/operations/CanDiscardOperation.h"
#include "src/gui/operations/UploadOperation.h"
#include "src/gui/operations/HandleUploadResponseOperation.h"
#include "src/gui/globalHotKeys/GlobalHotKeyHandler.h"
#include "src/gui/TrayIcon.h"

using kImageAnnotator::KImageAnnotator;

class MainWindow : public QMainWindow
{
    Q_OBJECT
public:
    explicit MainWindow(AbstractImageGrabber *imageGrabber, RunMode mode = RunMode::GUI);
    ~MainWindow() override;
    void showEmpty();
    void show();
    void captureScreenshot(CaptureModes captureMode, bool captureCursor, int delay);

public slots:
    void showCapture(const CaptureDto &capture);
	void triggerNewCapture(CaptureModes captureMode);
	void quit();

protected:
    void moveEvent(QMoveEvent *event) override;
    void closeEvent(QCloseEvent *event) override;
	void changeEvent(QEvent *event) override;
    QMenu *createPopupMenu() override;
    QSize sizeHint() const override;

private:
    AbstractImageGrabber *mImageGrabber;
    RunMode mMode;
    bool mIsUnsaved;
    bool mHidden;
    Qt::WindowState mSelectedWindowState;
    bool mWindowStateChangeLock;
    QAction *mUploadToImgurAction;
    QAction *mPrintAction;
    QAction *mPrintPreviewAction;
    QAction *mQuitAction;
    QAction *mSettingsDialogAction;
    QAction *mAboutAction;
    QAction *mOpenImageAction;
    QAction *mScaleAction;
    QAction *mAddWatermarkAction;
    MainToolBar *mToolBar;
    QClipboard *mClipboard;
    KsnipConfig *mConfig;
    CapturePrinter *mCapturePrinter;
    CaptureUploader *mCaptureUploader;
    KImageAnnotator *mKImageAnnotator;
    SavePathProvider mSavePathProvider;
    GlobalHotKeyHandler *mGlobalHotKeyHandler;
    TrayIcon *mTrayIcon;

    void setSaveable(bool enabled);
    void setEnablements(bool enabled);
    void loadSettings();
    void setHidden(bool isHidden);
    bool hidden() const;
    void capture(CaptureModes captureMode);
    void initGui();
	void loadCapture(const CaptureDto &capture);
	void processInstantCapture(const CaptureDto &capture);
	void showDialog(const std::function<void ()>& showDialogMethod);

private slots:
    void saveCapture();
    void copyCaptureToClipboard();
    void upload();
    void uploadFinished(const QString &response);
    void printClicked();
    void printPreviewClicked();
    void instantSave();
    void loadImageFromFile();
    void screenshotChanged();
    bool discardChanges();
    void setupImageAnnotator();
    void captureDelayChanged(int delay);
    void addWatermark();
    void showSettingsDialog();
    void showAboutDialog();
    void showScaleDialog();
	void setPosition(const QPoint &lastPosition);
	void handleGuiStartup();
};

#endif // KSNIP_MAINWINDOW_H
