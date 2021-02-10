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

#include "FileDialogAdapter.h"

QString FileDialogAdapter::getExistingDirectory(QWidget *parent, const QString &title, const QString &directory)
{
	return QFileDialog::getExistingDirectory(parent, title, directory, mOptions);
}

QString FileDialogAdapter::getOpenFileName(QWidget *parent, const QString &title, const QString &directory)
{
	return QFileDialog::getOpenFileName(parent, title, directory, nullptr, nullptr, mOptions);
}

QStringList FileDialogAdapter::getOpenFileNames(QWidget *parent, const QString &title, const QString &directory, const QString &filter)
{
	return QFileDialog::getOpenFileNames(parent, title, directory, filter, nullptr, mOptions);
}

QString FileDialogAdapter::getSavePath(QWidget *parent, const QString &title, const QString &path, const QString &filter)
{
	QFileDialog saveDialog(parent, title, path, filter);
	saveDialog.setAcceptMode(QFileDialog::AcceptSave);
	saveDialog.setOptions(mOptions);

	if (saveDialog.exec() == QDialog::Accepted) {
		return saveDialog.selectedFiles().first();
	}

	return {};
}

void FileDialogAdapter::addOption(QFileDialog::Option option)
{
	mOptions |= option;
}
