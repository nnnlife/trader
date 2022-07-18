#include "DayDataProvider.h"
#include <QThread>
#include <iostream>
#include <grpc/grpc.h>
#include <grpcpp/channel.h>
#include <grpcpp/client_context.h>
#include <grpcpp/create_channel.h>
#include <grpcpp/security/credentials.h>
//#include "stock_provider.grpc.pb.h"
#include <google/protobuf/util/time_util.h>
#include <QDebug>

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

using grpc::ClientContext;
using stock_api::StockQuery;


DayDataCollector::DayDataCollector(std::shared_ptr<stock_api::Stock::Stub> stub,
                        const QString &_code,
                        const QDateTime &_fromTime,
                        const QDateTime &_untilTime,
                        DayDataProvider::DATA_TYPE type)
: QObject(0), stub_(stub), code(_code), dataType(type){
    fromTime = new Timestamp(TimeUtil::TimeTToTimestamp(_fromTime.toTime_t()));
    untilTime = new Timestamp(TimeUtil::TimeTToTimestamp(_untilTime.toTime_t()));
}

void DayDataCollector::process() {
    ClientContext context;
    CybosDayDatas * data = new CybosDayDatas;
    StockQuery stock_query;
    stock_query.set_code(code.toStdString());
    stock_query.set_allocated_from_datetime(fromTime);
    stock_query.set_allocated_until_datetime(untilTime);

    if (dataType == DayDataProvider::MINUTE_DATA) {
        stub_->GetMinuteData(&context, stock_query, data);
        emit minuteDataReady(code, data);
    }
    else if (dataType == DayDataProvider::DAY_DATA){
        stub_->GetDayData(&context, stock_query, data);
        emit finished(code, data);
    }
    else if (dataType == DayDataProvider::TODAY_MINUTE_DATA) {
        StockCodeQuery stockCodeQuery;
        stockCodeQuery.set_code(code.toStdString());
        stub_->GetTodayMinuteData(&context, stockCodeQuery, data);
        emit todayMinuteDataReady(code, data);
    }
}


DayDataProvider::DayDataProvider(std::shared_ptr<stock_api::Stock::Stub> stub)
: QObject(0) {
    stub_ = stub;
}


void DayDataProvider::requestDayData(const QString &code,
                                    int countOfDays,
                                    const QDateTime &untilTime) {
    QDateTime fromTime = untilTime.addDays(-countOfDays);

    for (int i = 0; i < cachedQueue.count(); i++) {
        if (cachedQueue[i].getCode() == code && cachedQueue[i].isCached() &&
            cachedQueue[i].getDataType() == DAY_DATA && cachedQueue[i].getFromTime().date() == fromTime.date() &&
            cachedQueue[i].getUntilTime().date() == untilTime.date()) {
            //qWarning() << "return cached day data : " << code;
            emit dataReady(code, cachedQueue[i].getCachedData());
            return;
        }
    }

    waitingQueue.append(DayDataQuery(code, fromTime, untilTime, DAY_DATA));
    checkWaitingList();
}


void DayDataProvider::requestMinuteData(const QString &code,
                                     const QDateTime &fromTime,
                                     const QDateTime &untilTime) {
    for (int i = 0; i < cachedQueue.count(); i++) {
        if (cachedQueue[i].getCode() == code && cachedQueue[i].isCached() &&
            cachedQueue[i].getDataType() == MINUTE_DATA && cachedQueue[i].getFromTime().date() == fromTime.date() &&
            cachedQueue[i].getUntilTime().date() == untilTime.date()) {
            //qWarning() << "return cached minute data : " << code;
            emit minuteDataReady(code, cachedQueue[i].getCachedData());
            return;
        }
    }

    waitingQueue.append(DayDataQuery(code, fromTime, untilTime, MINUTE_DATA));
    checkWaitingList();
}


void DayDataProvider::requestTodayMinuteData(const QString &code) {
    waitingQueue.append(DayDataQuery(code, QDateTime::currentDateTime(),
                                            QDateTime::currentDateTime(), TODAY_MINUTE_DATA));
    checkWaitingList();
}


void DayDataProvider::dataReceived(QString code, CybosDayDatas *data) {
    isProcessing = false;
    //qWarning() << "provider day data received : " << data->day_data_size();
    for (int i = 0; i < cachedQueue.count(); i++) {
        if (cachedQueue[i].getCode() == code && !cachedQueue[i].isCached() &&
            cachedQueue[i].getDataType() == DAY_DATA) {
            cachedQueue[i].setResultData(data);
            break;
        }
    }

    emit dataReady(code, data);
    checkWaitingList();
}


void DayDataProvider::minuteDataReceived(QString code, CybosDayDatas *data) {
    isProcessing = false;
    //qWarning() << "provider minute data received(minute) : " << data->day_data_size();
    for (int i = 0; i < cachedQueue.count(); i++) {
        if (cachedQueue[i].getCode() == code && !cachedQueue[i].isCached() &&
            cachedQueue[i].getDataType() == MINUTE_DATA) {
            cachedQueue[i].setResultData(data);
            break;
        }
    }

    emit minuteDataReady(code, data);
    checkWaitingList();
}


void DayDataProvider::todayMinuteDataReceived(QString code, CybosDayDatas *data) {
    isProcessing = false;
    //qWarning() << "provider today minute data received(minute) : " << data->day_data_size();
    emit minuteDataReady(code, data);
    checkWaitingList();
}


void DayDataProvider::checkWaitingList() {
    if (isProcessing)
        return;

    if (waitingQueue.count() > 0) {
        isProcessing = true;
        DayDataQuery query = waitingQueue.first();
        if (query.getDataType() != TODAY_MINUTE_DATA)
            cachedQueue.append(query);

        waitingQueue.removeFirst();
        QThread * thread = new QThread;
        DayDataCollector * worker = new DayDataCollector(stub_ ,query.getCode(), query.getFromTime(), query.getUntilTime(), query.getDataType());
        worker->moveToThread(thread);
        connect(thread, SIGNAL(started()), worker, SLOT(process()));
        connect(worker, SIGNAL(finished(QString, CybosDayDatas*)), this, SLOT(dataReceived(QString, CybosDayDatas*)));
        connect(worker, &DayDataCollector::minuteDataReady, this,  &DayDataProvider::minuteDataReceived);
        connect(worker, &DayDataCollector::todayMinuteDataReady, this,  &DayDataProvider::todayMinuteDataReceived);
        connect(worker, SIGNAL(finished(QString, CybosDayDatas*)), thread, SLOT(quit()));
        connect(worker, SIGNAL(finished(QString, CybosDayDatas*)), worker, SLOT(deleteLater()));
        connect(thread, SIGNAL(finished()), thread, SLOT(deleteLater()));
        thread->start();
    }
}
