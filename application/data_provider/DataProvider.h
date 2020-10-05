#ifndef DATA_PROVIDER_H_
#define DATA_PROVIDER_H_

#include <QObject>
#include <QDateTime>
#include <QStringList>
#include "stock_provider.grpc.pb.h"
#include <google/protobuf/timestamp.pb.h>

class BidAskThread;
class StockSelectionThread;
class TickThread;
class MinuteData;
class TimeThread;
class MinuteTick;
class DayDataProvider;
class SimulationEvent;
class StockListThread;
class AlarmThread;
class TraderThread;
class BrokerThread;
class BrokerMinuteThread;

using stock_api::CybosBidAskTickData;
using stock_api::CybosTickData;
using stock_api::CybosDayDatas;
using stock_api::CybosDayData;
using stock_api::CybosStockAlarm;
using stock_api::OrderMsg;
using stock_api::SimulationStatus;
using stock_api::TopList;
using stock_api::OrderMethod;
using stock_api::OrderResult;
using stock_api::TodayTopSelection;
using stock_api::YearHighInfo;
using stock_api::BrokerSummary;
using stock_api::BrokerMinuteTick;
using stock_api::BrokerMinuteTickList;
using google::protobuf::Timestamp;


class DataProvider : public QObject {
Q_OBJECT
public:
    enum SIMULATION {
        STOP = 0,
        RUNNING = 1,
        STOP_TO_RUNNING = 2,
        RUNNING_TO_STOP = 3,
    };

    static DataProvider *getInstance() {
        static DataProvider *provider = NULL;
        if (provider == NULL)
            provider = new DataProvider;
        return provider;
    }

    void startStockTick();
    void startBidAskTick();
    void startStockCodeListening();
    void startTimeListening();
    void startListTypeListening();
    void startAlarmListening();
    void startOrderListening();
    void startBrokerSummaryListening();
    void startBrokerMinuteTickListening();

    MinuteTick *getMinuteTick(const QString &code);

    QString getCompanyName(const QString &code);

    bool isSimulation();
    void collectMinuteData(int min=1);
    void requestDayData(const QString &code, int countOfDays, const QDateTime &_untilTime);
    void requestMinuteData(const QString &code, const QDateTime &fromTime, const QDateTime &untilTime);
    void setCurrentStock(const QString &code);
    void setCurrentDateTime(const QDateTime &dt);
    void startSimulation(const QDateTime &dt, qreal speed);
    void stopSimulation();
    YearHighInfo * getYearHighInfo(const QString &code);
    BrokerSummary * getBrokerSummary(const QString &code);
    BrokerMinuteTickList *getBrokerMinuteTick(const QString &code);

    QStringList getSubscribeCodes();
    QStringList getRecentSearch();
    QStringList getFavoriteList();
    QStringList getViList();
    QStringList getTtopAmountList(TodayTopSelection s);
    QStringList getStrategyList();
    QStringList getYesterdayUpperLimitList();

    TopList* getYtopAmountList();
    void clearRecentList();
    void addToFavorite(const QString &code);
    void removeFromFavorite(const QString &code);
    const QDateTime & currentDateTime() { return m_currentDateTime; }

    void forceChangeStockCode(const QString &code);

    void buy(const QString &code, int price, int qty, int per, OrderMethod m);
    void sell(const QString &code, int price, int qty, int per, OrderMethod m);
    void changeToImmediate(const QString &code, const QString &orderNum, int percentage);
    void cancelOrder(const QString &code, const QString &orderNum);
    void sendBalanceRequest();

    void requestTickSubscribe(const QString &code);
    void requestBidAskSubscribe(const QString &code);
    void requestSubjectSubscribe(const QString &code);
    void requestAlarmSubscribe();

    QList<int> getViPrices(const QString &code);
    bool isKospi(const QString &code);
    int getBidUnit(bool isKospi, int price);

private:
    DataProvider();

    std::shared_ptr<stock_api::Stock::Stub> stub_;

    TickThread *            tickThread;
    BidAskThread *          bidAskThread;
    AlarmThread *           alarmThread;
    StockSelectionThread *  stockSelectionThread;
    MinuteData *            minuteData;
    TimeThread *            timeThread;
    DayDataProvider *       dayDataProvider;
    SimulationEvent *       simulationEvent;
    StockListThread *       stockListThread;
    TraderThread *          traderThread;
    BrokerThread *          brokerThread;
    BrokerMinuteThread *    brokerMinuteThread;


    QString currentStockCode;
    QDateTime m_currentDateTime;

    SIMULATION m_simulationStatus;

    void _stopSimulation();
    bool _isSimulation();
    void _setCurrentStock(const QString &code);
    void _setCurrentDateTime(const QDateTime &dt);

private slots:
    void convertTimeInfo(Timestamp *);
    void setSimulationStatus(SimulationStatus *status);
    void stockCodeReceived(QString code);

signals:
    void stockCodeChanged(QString code);
    void tickArrived(CybosTickData *);
    void bidAskTickArrived(CybosBidAskTickData *);
    void alarmArrived(CybosStockAlarm *);
    void minuteTickUpdated(QString);
    void dayDataReady(QString, CybosDayDatas *);
    void minuteDataReady(QString, CybosDayDatas *);
    void timeInfoArrived(QDateTime dt);
    void simulationStatusChanged(bool);
    void stockListTypeChanged(QString);
    void orderResultArrived(OrderResult *);
    void brokerSummaryArrived(BrokerSummary *);
    void brokerMinuteTickArrived(BrokerMinuteTick *);
};


#endif
