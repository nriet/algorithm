/*=========================================================================

  Program:   Visualization Toolkit
  Module:    vtkMap.h

  Copyright (c) Ken Martin, Will Schroeder, Bill Lorensen
  All rights reserved.
  See Copyright.txt or http://www.kitware.com/Copyright.htm for details.

   This software is distributed WITHOUT ANY WARRANTY; without even
   the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
   PURPOSE.  See the above copyright notice for more information.

=========================================================================*/

#ifndef __vtkMercator_h
#define __vtkMercator_h

#include <cmath>

#define WEB_MERCATOR_EXTENT 20037508.34

#define RAD_TO_DEG(rad)  rad * 57.29577951308232
#define DEG_TO_RAD(deg)	 deg * 0.0174532925199432958

using namespace std;

enum ProjectType
{
  ArcGis = 0,
  WebMercator = 1
};

class MercatorConvert
{
  //by default visual studio doesn't provide the M_PI define as it is a
  //non standard function, but with the around defines it does. It is far to
  //complicated to make sure everything gets included in the right order for
  //that to happen for a header only class. Instead we provide our own
  //M_PI define if it isn't already defined. The value we have chose is the
  //one that math.h uses on compilers that support M_PI.
  static double m_pi()
  {
#ifndef M_PI
    return 3.14159265358979323846;
#else
    return M_PI;
#endif
  }

public:
  
  //----------------------------------------------------------------------------
  static int long2tilex(double lon, int z)
  {
    return (int)(floor((lon + 180.0) / 360.0 * std::pow(2.0, z)));
  }

  //----------------------------------------------------------------------------
  static int lat2tiley(double lat, int z)
  {
    return (int)(floor(
      (1.0 -
        log(tan(lat * m_pi() / 180.0) + 1.0 / cos(lat * m_pi() / 180.0)) /
          m_pi()) /
      2.0 * std::pow(2.0, z)));
  }

  //----------------------------------------------------------------------------
  static double tilex2long(int x, int z)
  {
    return x / std::pow(2.0, z) * 360.0 - 180;
  }

  //----------------------------------------------------------------------------
  static double tiley2lat(int y, int z)
  {
    double n = m_pi() - 2.0 * m_pi() * y / std::pow(2.0, z);
    return 180.0 / m_pi() * atan(0.5 * (exp(n) - exp(-n)));
  }

  //----------------------------------------------------------------------------
  static double y2lat(double a)
  {
    return 180 / m_pi() * (2 * atan(exp(a * m_pi() / 180.0)) - m_pi() / 2.0);
  }

  //----------------------------------------------------------------------------
  static double lat2y(double a)
  {
    return 180.0 / m_pi() * log(tan(m_pi() / 4.0 + a * (m_pi() / 180.0) / 2.0));
  }

  //----------------------------------------------------------------------------
  // Clips input value to valid latitude
  static double validLatitude(double lat)
  {
    // Truncated value from y2lat(90):
    const double MAX_LATITUDE = 66.513;
    if (lat > MAX_LATITUDE)
    {
      return MAX_LATITUDE;
    }
    else if (lat < -MAX_LATITUDE)
    {
      return -MAX_LATITUDE;
    }

    return lat;
  }

  //----------------------------------------------------------------------------
  // Clips input value to valid latitude
  static double validLongitude(double lon)
  {
    const double MAX_LONGITUDE = 179.999;
    if (lon > MAX_LONGITUDE)
    {
      return MAX_LONGITUDE;
    }
    else if (lon < -MAX_LONGITUDE)
    {
      return -MAX_LONGITUDE;
    }

    return lon;
  }

  //----------------------------------------------------------------------------
  // Convert coodinate from web-mercator (EPSG:3857) to VTK map coordinates
  static double web2vtk(double webMercatorCoord)
  {
    return 180.0 * webMercatorCoord / WEB_MERCATOR_EXTENT;
  }

  //----------------------------------------------------------------------------
  // Convert coodinate from VTK map coordinates to web-mercator (EPSG:3857)
  static double vtk2web(double vtkCoord)
  {
    return vtkCoord / 180.0 * WEB_MERCATOR_EXTENT;
  }

  static int ArcGis_long2tilex(double lon,int orgX, int colN,double resolution)
  {
    return (int)(floor(abs(orgX - lon) / (colN * 1.0 * resolution)));
  }

  static int ArcGis_lat2tilex(double lat, int orgY,int rowN, double resolution)
  {
    return (int)(floor(abs(orgY - lat) / (rowN * 1.0 * resolution)));
  }

  static void webMercator2lonLat(float merclon,float merclat,double* lon,double* lat)
  {
    double x = merclon / WEB_MERCATOR_EXTENT * 180.0;
    double y = merclat / WEB_MERCATOR_EXTENT * 180.0;
    y = 180.0 / m_pi() * (2.0 * atan(exp(y * m_pi() / 180.0)) - m_pi() / 2.0);
    *lon = x;
    *lat = y;
  }

  static void lonLat2WebMercator(float lon,float lat,double* merclon,double* merclat)
  {
    double x = lon * WEB_MERCATOR_EXTENT / 180.0;
    double y = log(tan((90.0 + lat) * m_pi() / 360.0)) / (m_pi() / 180.0);
    y = y * WEB_MERCATOR_EXTENT / 180.0;
    *merclon = x;
    *merclat = y;
  }

protected:
  MercatorConvert() {}
  virtual ~MercatorConvert() {}
};

#endif // __vtkMercator_h
