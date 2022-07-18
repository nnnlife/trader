#ifndef MIN_INFO_H_
#define MIN_INFO_H_

#include "stock_provider.grpc.pb.h"

using stock_api::CybosDayDatas;
using stock_api::CybosDayData;


class MinInfo {
public:
    MinInfo(int minInterval);
    ~MinInfo();

    int count();
    void clear();

    const CybosDayData &get(int i);
    void setData(CybosDayDatas *cd);
    void setCurrentDateTime(uint cd, uint ct);

    int getHighestPrice() { return highestPrice; }
    int getLowestPrice() { return lowestPrice; }
    uint getHighestVolume() { return highestVolume; }
    uint getLowestVolume() { return lowestVolume; }
    int getLatestClosePrice();

    bool isCloserToMaximum();
    bool isEmpty();

private:
    int minuteInterval;
    int highestPrice;
    int lowestPrice;
    uint highestVolume;
    uint lowestVolume;
    uint currentDate;
    uint currentTime;

    CybosDayDatas data;
};


#endif

