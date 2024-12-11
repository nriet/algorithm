#pragma once

#include <struct_WeatherRadar.h>
#include <Grid.h>
#include <struct_RadarProduction_Grid.h>
#include "WRADStdData.h"
#include "struct_WeatherRadarProduct.h"
#include "WRADStdProduct.h"
#include "struct_RadarProduction_Recognition.h"
#include "Recognition.h"

class DataConvertor
{
public:
    DataConvertor();
    // recognition product
    bool RecognitionNormalToice(s_Pro_Rec::RecognitionProduct&, Recognition::RecognitionProduct&);
    bool RecognitionIceToNormal(Recognition::RecognitionProduct&, s_Pro_Rec::RecognitionProduct&);
    // grid product
    bool GridNormalToIce(s_Pro_Grid::RadarProduct&, Product::Grid::GridProduct&);
    bool GridIceToNormal(Product::Grid::GridProduct&, s_Pro_Grid::RadarProduct&);

    // std data
    bool WRadStdDataHeaderIceToNormal(WRADStdFormat::Data::Version10::GenericHeader&, GENERICHEADER&);
    bool WRadStdDataSiteConfIceToNormal(WRADStdFormat::Data::Version10::SiteConfiguration&, SITECONFIG&);
    bool WRadStdDataTaskConfIceToNormal(WRADStdFormat::Data::Version10::TaskConfiguration&, TASKCONFIG&);
    bool WRadStdDataCutConfIceToNormal(WRADStdFormat::Data::Version10::CutConfiguration&, CUTCONFIG&);
    bool WRadStdDataRadialIceToNormal(WRADStdFormat::Data::Version10::Radial&, RADIAL&);
    bool WRadStdDataRadialIceToNWC(WRADStdFormat::Data::Version10::Radial_NWC&, RADIAL_NWC&);

    bool WRadStdDataHeaderNormalToIce(GENERICHEADER&, WRADStdFormat::Data::Version10::GenericHeader&);
    bool WRadStdDataSiteConfNormalToIce(SITECONFIG&, WRADStdFormat::Data::Version10::SiteConfiguration&);
    bool WRadStdDataTaskConfNormalToIce(TASKCONFIG&, WRADStdFormat::Data::Version10::TaskConfiguration&);
    bool WRadStdDataCutConfNormalToIce(CUTCONFIG&, WRADStdFormat::Data::Version10::CutConfiguration&);
    bool WRadStdDataRadialNormalToIce(RADIAL&, WRADStdFormat::Data::Version10::Radial&);
    bool WRadStdDataRadialNWCToIce(RADIAL_NWC&, WRADStdFormat::Data::Version10::Radial_NWC&);


    bool WRadStdDataSiteConfIceToPAR(WRADStdFormat::Data::Version10::SiteConfigurationPAR&, SITECONFIGPAR&);
    bool WRadStdDataTaskConfIceToPAR(WRADStdFormat::Data::Version10::TaskConfigurationPAR&, TASKCONFIGPAR&);
    bool WRadStdDataBeamConfIceToPAR(WRADStdFormat::Data::Version10::BeamConfigurationPAR&, BEAMCONFIGPAR&);
    bool WRadStdDataCutConfIceToPAR(WRADStdFormat::Data::Version10::CutConfigurationPAR&, CUTCONFIGPAR&);

    bool WRadStdDataSiteConfPARToIce(SITECONFIGPAR&, WRADStdFormat::Data::Version10::SiteConfigurationPAR&);
    bool WRadStdDataTaskConfPARToIce(TASKCONFIGPAR&, WRADStdFormat::Data::Version10::TaskConfigurationPAR&);
    bool WRadStdDataBeamConfPARToIce(BEAMCONFIGPAR&, WRADStdFormat::Data::Version10::BeamConfigurationPAR&);
    bool WRadStdDataCutConfPARToIce(CUTCONFIGPAR&, WRADStdFormat::Data::Version10::CutConfigurationPAR&);




    bool WRadStdDataCommonBlockIceToNormal(WRADStdFormat::Data::Version10::CommonBlock&, COMMONBLOCK&);
    bool WRadStdDataCommonBlockNormalToIce(COMMONBLOCK&, WRADStdFormat::Data::Version10::CommonBlock&);

    bool WRadStdDataCommonBlockIceToPAR(WRADStdFormat::Data::Version10::CommonBlockPAR&, COMMONBLOCKPAR&);
    bool WRadStdDataCommonBlockPARToIce(COMMONBLOCKPAR&, WRADStdFormat::Data::Version10::CommonBlockPAR&);

    bool WRadStdDataIceToNormal(WRADStdFormat::Data::Version10::RadarRawData&, WRADRAWDATA&);
    bool WRadStdDataNormalToIce(WRADRAWDATA&, WRADStdFormat::Data::Version10::RadarRawData&);



    // std product
    bool WRadStdProductIceToNormal(WRADStdFormat::Product::Standard&, WRADPRODATA&);
    bool WRadStdProductNormalToIce(WRADPRODATA&, WRADStdFormat::Product::Standard&);
};

