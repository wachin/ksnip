/*
 * Copyright (C) 2020 Damir Porobic <damir.porobic@gmx.com>
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 51 Franklin Street, Fifth Floor,
 * Boston, MA 02110-1301, USA.
 */

#ifndef KSNIP_KIMAGEANNOTATORADAPTER_H
#define KSNIP_KIMAGEANNOTATORADAPTER_H

#include <kImageAnnotator/KImageAnnotator.h>

#include "IImageAnnotator.h"

using kImageAnnotator::KImageAnnotator;

class KImageAnnotatorAdapter : public IImageAnnotator
{
	Q_OBJECT
public:
	explicit KImageAnnotatorAdapter();
	~KImageAnnotatorAdapter() override;
	QImage image() const override;
	QImage imageAt(int index) const override;
	QAction *undoAction() override;
	QAction *redoAction() override;
	QSize sizeHint() const override;
	void showAnnotator() override;
	void showCropper() override;
	void showScaler() override;
	void showCanvasModifier() override;
	void setSettingsCollapsed(bool isCollapsed) override;
	void hide() override;
	void close() override;
	bool isVisible() const override;
	QWidget* widget() const override;

public slots:
	void loadImage(const QPixmap &pixmap) override;
	int addTab(const QPixmap &pixmap, const QString &title, const QString &toolTip) override;
	void updateTabInfo(int index, const QString &title, const QString &toolTip) override;
	void insertImageItem(const QPointF &position, const QPixmap &pixmap) override;
	void setTextFont(const QFont &font) override;
	void setNumberFont(const QFont &font) override;
	void setItemShadowEnabled(bool enabled) override;
	void setSmoothPathEnabled(bool enabled) override;
	void setSaveToolSelection(bool enabled) override;
	void setSmoothFactor(int factor) override;
	void setSwitchToSelectToolAfterDrawingItem(bool enabled) override;
	void setNumberToolSeedChangeUpdatesAllItems(bool enabled) override;
	void setTabBarAutoHide(bool enabled) override;
	void removeTab(int index) override;
	void setStickers(const QStringList &stickerPaths, bool keepDefault) override;
	void addTabContextMenuActions(const QList<QAction*> & actions) override;
	void setCanvasColor(const QColor &color) override;

private:
	KImageAnnotator *mKImageAnnotator;
};


#endif //KSNIP_KIMAGEANNOTATORADAPTER_H
