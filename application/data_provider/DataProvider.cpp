#include "DataProvider.h"
#include <grpc/grpc.h>
#include <grpcpp/channel.h>
#include <grpcpp/client_context.h>
#include <grpcpp/create_channel.h>
#include <grpcpp/security/credentials.h>
#include <google/protobuf/util/time_util.h>
#include <QDebug>
#include "TickThread.h"
#include "TimeThread.h"
#include "BidAskThread.h"
#include "AlarmThread.h"
#include "StockListThread.h"
#include "BrokerThread.h"
#include "BrokerMinuteThread.h"
#include "StockSelectionThread.h"
#include "MinuteData.h"
#include "DayDataProvider.h"
#include "SimulationEvent.h"
#include "TraderThread.h"


using grpc::Channel;
using grpc::ClientContext;
using grpc::ClientReader;
using grpc::ClientReaderWriter;
using grpc::ClientWriter;
using grpc::Status;
using google::protobuf::util::TimeUtil;
using google::protobuf::Timestamp;
using google::protobuf::Empty;

using stock_api::Stock;
using stock_api::StockCodeQuery;
using stock_api::StockQuery;
using stock_api::CybosDayData;
using stock_api::CodeList;
using stock_api::CompanyName;

using grpc::ClientContext;
using stock_api::StockQuery;

using stock_api::CybosTickData;
using stock_api::BrokerSummary;
using stock_api::CybosDayDatas;
using stock_api::CybosBidAskTickData;
using stock_api::CybosSubjectTickData;
using google::protobuf::Timestamp;
using stock_api::SimulationStatus;
using stock_api::OrderResult;
using stock_api::OrderMsg;
using stock_api::TradeMsg;
using stock_api::TradeMsgType;
using stock_api::OrderType;
using stock_api::Bool;
using stock_api::Prices;
using stock_api::SimulationOperation;
using stock_api::TodayTopOption;


DataProvider::DataProvider()
: QObject(0) {
    qRegisterMetaType<CybosTickData>("CybosTickData");
    qRegisterMetaType<CybosTickData>("CybosTickDatas");
    qRegisterMetaType<CybosDayDatas>("CybosDayDatas");
    qRegisterMetaType<CybosBidAskTickData>("CybosBidAskTickData");
    qRegisterMetaType<CybosSubjectTickData>("CybosSubjectTickData");
    qRegisterMetaType<SimulationStatus>("SimulationStatus");
    qRegisterMetaType<OrderResult>("OrderResult");
    qRegisterMetaType<Timestamp>("Timestamp");
    qRegisterMetaType<CybosStockAlarm>("CybosStockAlarm");
    qRegisterMetaType<CybosStockAlarm>("BrokerSummary");
    qRegisterMetaType<CybosStockAlarm>("BrokerMinuteTick");
    qRegisterMetaType<CybosStockAlarm>("BrokerMinuteTickList");

    stub_ = Stock::NewStub(grpc::CreateChannel("localhost:50052", grpc::InsecureChannelCredentials()));

    minuteData = NULL;
    timeThread = NULL;
    alarmThread = NULL;
    stockListThread = NULL;

    tickThread = new TickThread(stub_);
    bidAskThread = new BidAskThread(stub_);
    stockSelectionThread = new StockSelectionThread(stub_);
    dayDataProvider = new DayDataProvider(stub_);
    brokerThread = new BrokerThread(stub_);
    brokerMinuteThread = new BrokerMinuteThread(stub_);
    SimulationEvent *simulationEvent = new SimulationEvent(stub_);
    traderThread = new TraderThread(stub_);
    m_simulationStatus = _isSimulation() ? RUNNING: STOP;

    connect(tickThread, &TickThread::tickArrived, this, &DataProvider::tickArrived);
    connect(bidAskThread, &BidAskThread::tickArrived, this, &DataProvider::bidAskTickArrived);
    connect(brokerThread, &BrokerThread::summaryArrived, this, &DataProvider::brokerSummaryArrived);
    connect(brokerMinuteThread, &BrokerMinuteThread::brokerMinuteTickArrived, this, &DataProvider::brokerMinuteTickArrived);
    connect(stockSelectionThread, &StockSelectionThread::stockCodeChanged, this, &DataProvider::stockCodeReceived);
    connect(dayDataProvider, &DayDataProvider::dataReady, this, &DataProvider::dayDataReady);
    connect(dayDataProvider, &DayDataProvider::minuteDataReady, this, &DataProvider::minuteDataReady);
    connect(simulationEvent, &SimulationEvent::simulationStatusChanged, this, &DataProvider::setSimulationStatus);

    simulationEvent->start();
    startTimeListening();
}


void DataProvider::stockCodeReceived(QString code) {
    //qWarning() << "receive stock code received : " << code;
    currentStockCode = code;

    if (minuteData != NULL)
        minuteData->setCurrentStockCode(code);

    emit stockCodeChanged(code);
}


void DataProvider::forceChangeStockCode(const QString &code) {
    stockCodeReceived(code);
}


void DataProvider::setCurrentDateTime(const QDateTime &dt) {
    _setCurrentDateTime(dt); 
}


void DataProvider::buy(const QString &code, int price, int qty, int per, OrderMethod m) {
    traderThread->order(code, price, qty, per, m, true);
}


void DataProvider::sell(const QString &code, int price, int qty, int per, OrderMethod m) {
    traderThread->order(code, price, qty, per, m, false);
}


void DataProvider::convertTimeInfo(Timestamp *t) {
    long msec = TimeUtil::TimestampToMilliseconds(*t);
    //qWarning() << "time arrived : " << QDateTime::fromMSecsSinceEpoch(msec);
    m_currentDateTime = QDateTime::fromMSecsSinceEpoch(msec);
    delete t;
    emit timeInfoArrived(m_currentDateTime);
}


void DataProvider::startTimeListening() {
    if (timeThread == NULL) {
        timeThread = new TimeThread(stub_);
        connect(timeThread, &TimeThread::timeInfoArrived, this, &DataProvider::convertTimeInfo);
        timeThread->start();
    }
}


void DataProvider::startAlarmListening() {
    if (alarmThread == NULL) {
        alarmThread = new AlarmThread(stub_);
        connect(alarmThread, &AlarmThread::alarmArrived, this, &DataProvider::alarmArrived);
        alarmThread->start();
    }
}


void DataProvider::startListTypeListening() {
    if (stockListThread == NULL) {
        stockListThread = new StockListThread(stub_);
        connect(stockListThread, &StockListThread::stockListChanged, this, &DataProvider::stockListTypeChanged);
        stockListThread->start();
    }
}


void DataProvider::startOrderListening() {
    if (!traderThread->isRunning()) {
        disconnect(traderThread, nullptr, nullptr, nullptr);
        connect(traderThread, &TraderThread::orderResultArrived, this, &DataProvider::orderResultArrived);
        traderThread->start();
    }
}


void DataProvider::requestDayData(const QString &code, int countOfDays, const QDateTime &_untilTime) {
    // TODO: Cache
    dayDataProvider->requestDayData(code, countOfDays, _untilTime);
}


void DataProvider::requestMinuteData(const QString &code, const QDateTime &fromTime, const QDateTime &untilTime) {
    qWarning() << "request minute data: " << code << " from:" << fromTime << " until:" << untilTime;
    dayDataProvider->requestMinuteData(code, fromTime, untilTime);
}


void DataProvider::collectMinuteData(int min) {
    if (minuteData == NULL) {
        minuteData = new MinuteData(this, stub_, min, currentStockCode, isSimulation());
        connect(tickThread, &TickThread::tickArrived, minuteData, &MinuteData::stockTickArrived);
        connect(minuteData, &MinuteData::minuteTickUpdated, this, &DataProvider::minuteTickUpdated);
        connect(this, &DataProvider::timeInfoArrived, minuteData, &MinuteData::timeInfoArrived);
    }
}


void DataProvider::startStockTick() {
    if (!tickThread->isRunning())
        tickThread->start();
}


void DataProvider::startBidAskTick() {
    if (!bidAskThread->isRunning())
        bidAskThread->start();
}


void DataProvider::startStockCodeListening() {
    if (!stockSelectionThread->isRunning())
        stockSelectionThread->start();
}


void DataProvider::startBrokerSummaryListening() {
    if (!brokerThread->isRunning())
        brokerThread->start();
}


void DataProvider::startBrokerMinuteTickListening() {
    if (!brokerMinuteThread->isRunning())
        brokerMinuteThread->start();
}


void DataProvider::startSimulation(const QDateTime &dt, qreal speed) {
    qWarning() << "startSimulation : " << m_simulationStatus;
    if (m_simulationStatus == STOP) {
        ClientContext context;
        SimulationOperation op;
        Timestamp *t = new Timestamp(TimeUtil::TimeTToTimestamp(dt.toTime_t()));
        op.set_is_on(true);
        op.set_allocated_start_datetime(t);
        op.set_speed(speed);
        Bool ret;
        stub_->StartSimulation(&context, op, &ret);
    }
}


void DataProvider::stopSimulation() {
    if (m_simulationStatus == RUNNING) {
        _stopSimulation();
    }
}


void DataProvider::setSimulationStatus(SimulationStatus *status) {
    if ( (m_simulationStatus == RUNNING && status->simulation_on()) ||
        (m_simulationStatus == STOP && !status->simulation_on()))
        return;

    if (status->simulation_on())
        m_simulationStatus = RUNNING;
    else
        m_simulationStatus = STOP;

    if (minuteData != NULL) 
        minuteData->setSimulation(status->simulation_on());

    emit simulationStatusChanged(status->simulation_on());
}


bool DataProvider::isSimulation() {
    if (m_simulationStatus == STOP || m_simulationStatus == RUNNING_TO_STOP)
        return false;
    return true;
}


void DataProvider::setCurrentStock(const QString &code) {
    _setCurrentStock(code);
}


QString DataProvider::getCompanyName(const QString &code) {
    ClientContext context;
    CompanyName* cn = new CompanyName;
    StockCodeQuery scq;
    scq.set_code(code.toStdString());
    stub_->GetCompanyName(&context, scq, cn);
    QString name = QString::fromStdString(cn->company_name());
    delete cn;
    return name;
}


YearHighInfo * DataProvider::getYearHighInfo(const QString &code) {
    ClientContext context;
    YearHighInfo *yearHighInfo = new YearHighInfo;
    StockCodeQuery scq;
    scq.set_code(code.toStdString());
    stub_->GetYearHigh(&context, scq, yearHighInfo);
    return yearHighInfo;
}


BrokerSummary * DataProvider::getBrokerSummary(const QString &code) {
    ClientContext context;
    BrokerSummary *summary = new BrokerSummary;
    StockCodeQuery scq;
    scq.set_code(code.toStdString());
    stub_->GetBrokerSummary(&context, scq, summary);
    return summary;
}


BrokerMinuteTickList *DataProvider::getBrokerMinuteTick(const QString &code) {
    ClientContext context;
    BrokerMinuteTickList *list = new BrokerMinuteTickList;
    StockCodeQuery scq;
    scq.set_code(code.toStdString());
    stub_->GetBrokerMinuteTick(&context, scq, list);
    return list;
}


MinuteTick * DataProvider::getMinuteTick(const QString &code) {
    if (minuteData && !code.isEmpty()) {
        if (isSimulation())
            return minuteData->getMinuteTick(code, currentDateTime());
        else {
            QDateTime dt = QDateTime::currentDateTime();
            QDateTime todayLimit = QDateTime(dt.date(), QTime(18, 30, 0));
            if (currentDateTime().date() == dt.date() && dt < todayLimit)
                return minuteData->getMinuteTick(code, QDateTime::currentDateTime());
            else
                return minuteData->getMinuteTick(code, currentDateTime());
        }
    }
    return nullptr;
}


QStringList DataProvider::getSubscribeCodes() {
    ClientContext context;
    CodeList * codeList = new CodeList;
    Empty empty;
    qWarning() << "Request Subscribe codes";
    stub_->GetSubscribeCodes(&context, empty, codeList);
    qWarning() << "Request Subscribe codes OK " << codeList->codelist_size();
    QStringList list;
    for (int i = 0; i < codeList->codelist_size(); i++)
        list.append(QString::fromStdString(codeList->codelist(i)));
    delete codeList;
    return list;
}


QStringList DataProvider::getRecentSearch() {
    ClientContext context;
    CodeList * codeList = new CodeList;
    Empty empty;
    stub_->GetRecentSearch(&context, empty, codeList);
    QStringList list;
    for (int i = 0; i < codeList->codelist_size(); i++)
        list.append(QString::fromStdString(codeList->codelist(i)));
    delete codeList;
    return list;
}


QStringList DataProvider::getFavoriteList() {
    ClientContext context;
    CodeList * codeList = new CodeList;
    Empty empty;
    stub_->GetFavoriteList(&context, empty, codeList);
    QStringList list;
    for (int i = 0; i < codeList->codelist_size(); i++)
        list.append(QString::fromStdString(codeList->codelist(i)));
    delete codeList;
    return list;
}


QStringList DataProvider::getViList() {
    ClientContext context;
    CodeList * codeList = new CodeList;
    Empty empty;
    stub_->GetViList(&context, empty, codeList);
    QStringList list;
    for (int i = 0; i < codeList->codelist_size(); i++)
        list.append(QString::fromStdString(codeList->codelist(i)));
    delete codeList;
    return list;
}


void DataProvider::changeToImmediate(const QString &code, const QString &orderNum, int percentage) {
    ClientContext context;
    Empty empty;
    TradeMsg tradeMsg;
    tradeMsg.set_msg_type(TradeMsgType::ORDER_MSG);
    OrderMsg *msg = new OrderMsg;
    msg->set_code(code.toStdString());
    msg->set_order_num(orderNum.toStdString());
    msg->set_percentage(percentage);
    msg->set_method(OrderMethod::TRADE_IMMEDIATELY);
    msg->set_order_type(OrderType::MODIFY);
    tradeMsg.set_allocated_order_msg(msg);
    stub_->RequestToTrader(&context, tradeMsg, &empty);
}


void DataProvider::cancelOrder(const QString &code, const QString &orderNum) {
    ClientContext context;
    Empty empty;
    TradeMsg tradeMsg;
    tradeMsg.set_msg_type(TradeMsgType::ORDER_MSG);
    OrderMsg *msg = new OrderMsg;
    msg->set_code(code.toStdString());
    msg->set_order_num(orderNum.toStdString());
    msg->set_order_type(OrderType::CANCEL);
    tradeMsg.set_allocated_order_msg(msg);
    stub_->RequestToTrader(&context, tradeMsg, &empty);
}


void DataProvider::sendBalanceRequest() {
    ClientContext context;
    Empty empty;
    TradeMsg tradeMsg;
    tradeMsg.set_msg_type(TradeMsgType::GET_BALANCE);
    stub_->RequestToTrader(&context, tradeMsg, &empty);
}


QStringList DataProvider::getTtopAmountList(TodayTopSelection s) {
    ClientContext context;
    CodeList * codeList = new CodeList;
    TodayTopOption opt;
    opt.set_selection(s);
    stub_->GetTodayTopAmountList(&context, opt, codeList);
    QStringList list;
    for (int i = 0; i < codeList->codelist_size(); i++)
        list.append(QString::fromStdString(codeList->codelist(i)));
    delete codeList;
    return list;
}


QStringList DataProvider::getYesterdayUpperLimitList() {
    ClientContext context;
    CodeList * codeList = new CodeList;
    Empty empty;
    stub_->GetYesterdayUpperLimitList(&context, empty, codeList);
    QStringList list;
    qWarning() << "getYesterdayUpperLimitList: " << codeList->codelist_size();
    for (int i = 0; i < codeList->codelist_size(); i++)
        list.append(QString::fromStdString(codeList->codelist(i)));
    delete codeList;
    return list;
}


QStringList DataProvider::getStrategyList() {
    ClientContext context;
    CodeList * codeList = new CodeList;
    Empty empty;
    stub_->GetStrategyList(&context, empty, codeList);
    QStringList list;
    for (int i = 0; i < codeList->codelist_size(); i++)
        list.append(QString::fromStdString(codeList->codelist(i)));
    delete codeList;
    return list;
}


TopList * DataProvider::getYtopAmountList() {
    ClientContext context;
    Timestamp ts = Timestamp(TimeUtil::TimeTToTimestamp(m_currentDateTime.toTime_t()));
    TopList * topList = new TopList;
    stub_->GetYesterdayTopAmountList(&context, ts, topList);
    //qWarning() << "topList count : " << topList->codelist_size() << "\tdate" << topList->date() << "\tis_today_data" << topList->is_today_data();
    return topList;
}


void DataProvider::addToFavorite(const QString &code) {
    //qWarning() << "DataProvider addToFavorite : " << code;
    ClientContext context;
    StockCodeQuery data; 
    data.set_code(code.toStdString());
    Empty empty;
    stub_->AddFavorite(&context, data, &empty);
}


bool DataProvider::isKospi(const QString &code) {
    ClientContext context;
    StockCodeQuery data; 
    data.set_code(code.toStdString());
    Bool ret;
    stub_->IsKospi(&context, data, &ret);
    return ret.ret();
}


void DataProvider::removeFromFavorite(const QString &code) {
    ClientContext context;
    StockCodeQuery data; 
    data.set_code(code.toStdString());
    Empty empty;
    stub_->RemoveFavorite(&context, data, &empty);
}


void DataProvider::_stopSimulation() {
    ClientContext context;
    Empty * emptyReturn = new Empty;
    Empty empty;
    stub_->StopSimulation(&context, empty, emptyReturn);
    delete emptyReturn;
    m_simulationStatus = RUNNING_TO_STOP;
}


bool DataProvider::_isSimulation() {
    ClientContext context;
    SimulationStatus * status = new SimulationStatus;
    Empty empty;
    stub_->GetSimulationStatus(&context, empty, status);
    bool isOn = status->simulation_on();
    delete status;
    return isOn;
}


void DataProvider::_setCurrentStock(const QString &code) {
    ClientContext context;
    StockCodeQuery data;
    Empty empty;
    data.set_code(code.toStdString());
    stub_->SetCurrentStock(&context, data, &empty);
}


void DataProvider::_setCurrentDateTime(const QDateTime &dt) {
    ClientContext context;
    Timestamp data = Timestamp(TimeUtil::TimeTToTimestamp(dt.toTime_t()));
    Empty empty;
    stub_->SetCurrentDateTime(&context, data, &empty);
}


QList<int> DataProvider::getViPrices(const QString &code) {
    ClientContext context;
    StockCodeQuery data;
    Prices prices;
    data.set_code(code.toStdString());
    stub_->GetViPrice(&context, data, &prices);
    QList<int> priceList;
    for (int i = 0; i < prices.price_size(); i++)
        priceList.append(prices.price(i));
    return priceList;
}


void DataProvider::requestTickSubscribe(const QString &code) {
    ClientContext context;
    StockCodeQuery data;
    Empty empty;
    data.set_code(code.toStdString());
    stub_->RequestCybosTickData(&context, data, &empty);
}


void DataProvider::requestBidAskSubscribe(const QString &code) {
    ClientContext context;
    StockCodeQuery data;
    Empty empty;
    data.set_code(code.toStdString());
    stub_->RequestCybosBidAsk(&context, data, &empty);
}


void DataProvider::requestSubjectSubscribe(const QString &code) {
    ClientContext context;
    StockCodeQuery data;
    Empty empty;
    data.set_code(code.toStdString());
    stub_->RequestCybosSubject(&context, data, &empty);
}


void DataProvider::requestAlarmSubscribe() {
    ClientContext context;
    Empty * emptyReturn = new Empty;
    Empty empty;
    stub_->RequestCybosAlarm(&context, empty, emptyReturn);
    delete emptyReturn;
}


void DataProvider::clearRecentList() {
    ClientContext context;
    Empty empty;
    Empty emptyRet;
    stub_->ClearRecentList(&context, empty, &emptyRet);
}


int DataProvider::getBidUnit(bool isKospi, int price) {
    if (price < 1000)
        return 1;
    else if (price < 5000)
        return 5;
    else if (price < 10000)
        return 10;
    else if (price < 50000)
        return 50;

    if (isKospi) {
        if (price < 100000)
            return 100;
        else if (price < 500000)
            return 500;
        return 1000;
    }
    return 100;
}
