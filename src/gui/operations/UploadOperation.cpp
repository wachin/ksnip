/*
 * Copyright (C) 2019 Damir Porobic <damir.porobic@gmx.com>
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
 */

#include "UploadOperation.h"

UploadOperation::UploadOperation(const QImage &image, CaptureUploader *uploader)
{
	mImage = image;
	mUploader = uploader;
	mConfig = KsnipConfigProvider::instance();
}

bool UploadOperation::execute()
{
	if (!mImage.isNull() && proceedWithUpload()) {
		mUploader->upload(mImage);
		return true;
	}
	return false;
}

bool UploadOperation::proceedWithUpload() const
{
	return mConfig->imgurConfirmBeforeUpload() ? getProceedWithUpload() : true;
}

bool UploadOperation::getProceedWithUpload() const
{
	return MessageBoxHelper::yesNo(tr("Imgur Upload"),
		                           tr("You are about to upload the screenshot to a imgur.com, do you want to proceed?"));
}
