/*
 *  Copyright (C) 2017 Damir Porobic <https://github.com/damirporobic>
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
 *
 */

#include "PathHelper.h"

bool PathHelper::isPathValid(const QString &path)
{
	return !path.isNull() && !path.isEmpty();
}

bool PathHelper::isPipePath(const QString &path)
{
	return path == QLatin1String("-");
}

QString PathHelper::extractParentDirectory(const QString& path)
{
    return path.section(QLatin1Char('/'), 0, -2);
}

QString PathHelper::extractFilename(const QString& path)
{
	auto filename = extractFilenameWithFormat(path);
	if (filename.contains(QLatin1Char('.'))) {
        return filename.section(QLatin1Char('.'), 0, -2);
    } else {
        return filename;
    }
}

QString PathHelper::extractFilenameWithFormat(const QString &path)
{
	return path.section(QLatin1Char('/'), -1);
}

QString PathHelper::extractFormat(const QString& path)
{
	auto filename = extractFilenameWithFormat(path);
	if (filename.contains(QLatin1Char('.'))) {
        return path.section(QLatin1Char('.'), -1);
    } else {
        return {};
    }
}

