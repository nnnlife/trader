#ifndef MINUTE_DATA_H_
#define MINUTE_DATA_H_

#include <QObject>
#include <QMap>
#include <QDateTime>
#include "stock_provider.grpc.pb.h"


class DayDataProvider;

using stock_api::CybosBidAskTickData;
using stock_api::CybosTickData;
using stock_api::CybosDayDatas;
using stock_api::CybosDayData;


class MinuteTick : public QObject{
Q_OBJECT
public:
    MinuteTick(const QString &code, const QDateTime &dt, int intervaMin);
    ~MinuteTick();
    
    bool appendTick(CybosTickData *d);
    const CybosDayData &getCurrent() { return currentData; }
    const CybosDayDatas &getQueue() { return queue; }
    bool isTimeout(long current);
    int getYesterdayClose() { return yesterdayClose; }

    int     getHighestPrice() { return highestPrice; }
    int     getLowestPrice() { return lowestPrice; }
    int     getOpenPrice() { return openPrice; }
    uint    getHighestVolume() { return highestVolume; }
    long long getAmount() { return mAmount; }
    const QDateTime &getCreateDateTime() { return createDateTime; }
    const QString &getCode() { return code; }
    bool isPreviousDataReceived() { return previousDataReceived; }
    void skipReceivePreviousData();

private:
    CybosDayData currentData;
    CybosDayDatas queue;
    QString code;
    QDateTime createDateTime;

    long currentMSecs;
    int yesterdayClose;
    int intervalMinute;
    int highestPrice;
    int lowestPrice;
    int openPrice;
    uint highestVolume;
    long long mAmount;

    bool previousDataReceived;
    bool isSimulation;

    void setCurrentData(CybosTickData *d, long msec);
    void setCurrentData(const CybosDayData &d);
    void updateCurrentData(CybosTickData *d);
    void updateCurrentData(const CybosDayData &d);
    void pushToQueue();
    void setPriceBoundary(int price);
    void setPriceBoundary(int high, int low);
    void setVolumeBoundary(long long volume);

public:
    QString getDebugString();


public slots:
    void minuteDataReady(QString, CybosDayDatas *);

signals:
    void minuteTickUpdated(QString);
};


class MinuteData : public QObject {
Q_OBJECT
public:
    MinuteData(QObject *parent, std::shared_ptr<stock_api::Stock::Stub> stub, int min, const QString &code, bool isSimul);
    MinuteTick * getMinuteTick(const QString &code, const QDateTime &serverTime);
    void setSimulation(bool isSimul);
    void setCurrentStockCode(const QString &code);

private:
    std::shared_ptr<stock_api::Stock::Stub> stub_;
    QMap<QString, MinuteTick *> codeMap;
    long lastCheckTime;
    bool isSimulation;
    int intervalMinute;
    void clearData();
    DayDataProvider *dayDataProvider;
    QString currentStockCode;
    QDateTime currentDateTime;

    void requestPreviousData(MinuteTick *tick);

public slots:
    void stockTickArrived(CybosTickData *);
    void timeInfoArrived(QDateTime);

signals:
    void minuteTickUpdated(QString);
};


#endif
