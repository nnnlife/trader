#ifndef _ALARM_THREAD_H_
#define _ALARM_THREAD_H_


#include <QThread>
#include <iostream>
#include "stock_provider.grpc.pb.h"

using stock_api::CybosStockAlarm;

class AlarmThread : public QThread {
Q_OBJECT
public:
    AlarmThread(std::shared_ptr<stock_api::Stock::Stub> stub);

protected:
    void run();

private:
    std::shared_ptr<stock_api::Stock::Stub> stub_;

signals:
    void alarmArrived(CybosStockAlarm *);
};


#endif
