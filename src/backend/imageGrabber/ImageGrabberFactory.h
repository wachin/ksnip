/*
 * Copyright (C) 2017 Damir Porobic <https://github.com/damirporobic>
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

#ifndef KSNIP_IMAGEGRABBERFACTORY_H
#define KSNIP_IMAGEGRABBERFACTORY_H

#if defined(__APPLE__)
#include "MacImageGrabber.h"
#endif

#if defined(UNIX_X11)
#include "X11ImageGrabber.h"
#include "GnomeX11ImageGrabber.h"
#include "KdeWaylandImageGrabber.h"
#include "GnomeWaylandImageGrabber.h"
#include "WaylandImageGrabber.h"
#include "src/common/platform/PlatformChecker.h"
#include "src/backend/config/KsnipConfigProvider.h"
#endif

#if  defined(_WIN32)
#include "WinImageGrabber.h"
#endif

class ImageGrabberFactory
{
public:
    static AbstractImageGrabber *createImageGrabber();
};

#endif // KSNIP_IMAGEGRABBERFACTORY_H
