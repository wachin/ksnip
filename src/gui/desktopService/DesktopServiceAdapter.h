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

#ifndef KSNIP_DESKTOPSERVICEADAPTER_H
#define KSNIP_DESKTOPSERVICEADAPTER_H

#include <QDesktopServices>
#include <QUrl>

#if defined(UNIX_X11)
#include <QProcess>

#include "src/common/platform/PlatformChecker.h"
#endif

#include "IDesktopService.h"

class DesktopServiceAdapter : public IDesktopService
{
public:
	explicit DesktopServiceAdapter() = default;
	~DesktopServiceAdapter() override = default;
	void openFile(const QString &path) override;

#if defined(UNIX_X11)
private:
	QProcess mXdgOpenProcess;
#endif
};

#endif //KSNIP_DESKTOPSERVICEADAPTER_H
