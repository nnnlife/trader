#ifndef DAY_DATA_PROVIDER_H_
#define DAY_DATA_PROVIDER_H_


#include <QObject>
#include <QMap>
#include <QDateTime>
#include <qqml.h>
#include "stock_provider.grpc.pb.h"
#include <google/protobuf/util/time_util.h>


using google::protobuf::Timestamp;
using google::protobuf::util::TimeUtil;
using stock_api::CybosDayData;
using grpc::ClientContext;
using stock_api::CybosDayDatas;


class DayDataQuery;

class DayDataProvider : public QObject {
    Q_OBJECT
public:
    enum DATA_TYPE{
        DAY_DATA = 0,
        MINUTE_DATA = 1,
        TODAY_MINUTE_DATA = 2
    };
    DayDataProvider(std::shared_ptr<stock_api::Stock::Stub> stub);

    Q_INVOKABLE void requestDayData(const QString &code,
                                    int countOfDays,
                                    const QDateTime &untilTime);

    Q_INVOKABLE void requestMinuteData(const QString &code,
                                    const QDateTime &fromTime,
                                    const QDateTime &untilTime);
    Q_INVOKABLE void requestTodayMinuteData(const QString &code);


private:
    std::shared_ptr<stock_api::Stock::Stub> stub_;
    QList<DayDataQuery> waitingQueue;
    QList<DayDataQuery> cachedQueue;
    bool isProcessing = false;

private:
    void checkWaitingList();

private slots:
    void dataReceived(QString, CybosDayDatas*);
    void minuteDataReceived(QString, CybosDayDatas*);
    void todayMinuteDataReceived(QString, CybosDayDatas*);

signals:
    void dataReady(QString, CybosDayDatas*);
    void minuteDataReady(QString, CybosDayDatas*);
};


class DayDataQuery {
public:
    explicit DayDataQuery(const QString &code, const QDateTime &fromTime, const QDateTime &untilTime, DayDataProvider::DATA_TYPE type) {
        mCode = code;
        mFromTime = fromTime;
        mUntilTime = untilTime;
        mDataType = type;
        cachedData = nullptr;
    }

public:
    const QString &getCode() { return mCode; }
    const QDateTime &getFromTime() { return mFromTime; }
    const QDateTime &getUntilTime() { return mUntilTime; }
    DayDataProvider::DATA_TYPE getDataType() { return mDataType; }
    bool isCached() { return cachedData != nullptr; }
    void setResultData(CybosDayDatas *d) { cachedData = new CybosDayDatas(*d); }
    CybosDayDatas *getCachedData() { return cachedData; }

private:
    QString mCode;
    QDateTime mFromTime;
    QDateTime mUntilTime;
    DayDataProvider::DATA_TYPE mDataType;
    CybosDayDatas *cachedData;
};



class DayDataCollector : public QObject {
Q_OBJECT
public:
    DayDataCollector(std::shared_ptr<stock_api::Stock::Stub> stub,
                        const QString &_code,
                        const QDateTime &_fromTime,
                        const QDateTime &_untilTime,
                        DayDataProvider::DATA_TYPE type);

private:
    std::shared_ptr<stock_api::Stock::Stub> stub_;
    QString code;
    Timestamp * fromTime;
    Timestamp * untilTime;
    DayDataProvider::DATA_TYPE dataType;

public slots:
    void process();

signals:
    void finished(QString, CybosDayDatas *);
    void minuteDataReady(QString, CybosDayDatas *);
    void todayMinuteDataReady(QString, CybosDayDatas *);
};


#endif
