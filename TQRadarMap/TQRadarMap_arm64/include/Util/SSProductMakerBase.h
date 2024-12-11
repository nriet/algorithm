#pragma once

#include "ProductMakerBase.h"
#include "WRADStdData.h"
#include "WRadDataAggregator.h"
#include "struct_WeatherRadar.h"

using namespace WRADStdFormat::Data;

class CSSProductMakerBase : public CProductMakerBase
{
public:
    using WRadStdDataInternalPtr = std::shared_ptr<WRADRAWDATA>;
    virtual void onReceiveWRadStdData() = 0;
    virtual int doAggregateWRadStdDataCut(Version10::RadarRawData&) = 0;
    virtual int doDispatchWRadStdData(WRadStdDataInternalPtr&) = 0;

    using TaskWRadDataEntry = std::tuple<
    Version10::RadarRawData,
    std::function<void ()>,
    std::function<void (std::exception_ptr)>>;

    using TaskWRadDataEntryPtr = std::shared_ptr<TaskWRadDataEntry>;

    std::list<TaskWRadDataEntryPtr>m_lTaskWRadData;

    using TaskSACRDataEntry = std::tuple<
    ::std::shared_ptr<::Product::Grid::GridProduct>,
    std::function<void ()>,
    std::function<void (std::exception_ptr)>>;

    using TaskSACREntryPtr = std::shared_ptr<TaskSACRDataEntry>;

    std::list<TaskSACREntryPtr>m_lTaskSACRData;
    // weather radar data cache
    CWRadDataAggregatorPtr m_iWRadDataAggregator;
    CWRadDataAggregatorPtr m_iWRadPostQCDataAggregator;
    CWRadDataAggregatorPtr m_iWRadNonQCDataAggregator;
    CWRadDataAggregatorPtr m_iWRadHisPostQCDataAggregator;
    CWRadDataAggregatorPtr m_iWRadHisNonQCDataAggregator;
};
