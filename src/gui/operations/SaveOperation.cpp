/*
 * Copyright (C) 2019 Damir Porobic <damir.porobic@gmx.com>
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

#include "SaveOperation.h"

#include <utility>

SaveOperation::SaveOperation(QWidget *parent, QImage image, bool isInstantSave, IToastService *toastService, IRecentImageService *recentImageService) :
	mParent(parent),
	mImage(std::move(image)),
	mIsInstantSave(isInstantSave),
	mToastService(toastService),
	mRecentImageService(recentImageService),
	mConfig(KsnipConfigProvider::instance())
{
    Q_ASSERT(mParent != nullptr);
}

SaveOperation::SaveOperation(QWidget *parent, const QImage &image, bool isInstantSave, const QString &pathToImageSource, IToastService *toastService, IRecentImageService *recentImageService) :
	SaveOperation(parent, image, isInstantSave, toastService, recentImageService)
{
	mPathToImageSource = pathToImageSource;
}

SaveResultDto SaveOperation::execute()
{
	auto path = getSavePath();

	if(!mIsInstantSave){
		auto title = tr("Save As");
		auto filter = tr("Images") + QLatin1String(" (*.png *.gif *.jpg);;") + tr("All Files") + QLatin1String("(*)");
		auto fileDialogAdapter = FileDialogAdapterFactory::create();
		auto selectedSavePath = fileDialogAdapter->getSavePath(mParent, title, path, filter);

		if (selectedSavePath.isNull()) {
			return SaveResultDto(false, path);
		}

		path = selectedSavePath;
	}

	auto saveResult = save(path);
	updateSaveDirectoryIfRequired(path, saveResult);

	if (saveResult.isSuccessful) {
		mRecentImageService->storeImagePath(path);
	}

	return saveResult;
}

void SaveOperation::updateSaveDirectoryIfRequired(const QString &path, const SaveResultDto &saveResult) const
{
	if(!mIsInstantSave && saveResult.isSuccessful && mConfig->rememberLastSaveDirectory()){
		auto directory = PathHelper::extractParentDirectory(path);
		mConfig->setSaveDirectory(directory);
	}
}

QString SaveOperation::getSavePath() const
{
	return PathHelper::isPathValid(mPathToImageSource) ? mPathToImageSource : mSavePathProvider.savePath();
}

SaveResultDto SaveOperation::save(const QString &path)
{
	auto successful = mImageSaver.save(mImage, path);
	if(successful) {
		notify(tr("Image Saved"), tr("Saved to"), path, NotificationTypes::Information);
	} else {
		notify(tr("Saving Image Failed"), tr("Failed to save image to"), path, NotificationTypes::Critical);
	}
	return SaveResultDto(successful, path);
}

void SaveOperation::notify(const QString &title, const QString &message, const QString &path, NotificationTypes notificationType) const
{
	auto parentDirectory = PathHelper::extractParentDirectory(path);
	NotifyOperation operation(mToastService, title, message + QLatin1String(" ") + path, parentDirectory, notificationType);
	operation.execute();
}
