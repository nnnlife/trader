#ifndef _BROKER_MINUTE_THREAD_H_
#define _BROKER_MiNUTE_THREAD_H_


#include <QThread>
#include <iostream>
#include "stock_provider.grpc.pb.h"

using stock_api::BrokerMinuteTick;

class BrokerMinuteThread : public QThread {
Q_OBJECT
public:
    BrokerMinuteThread(std::shared_ptr<stock_api::Stock::Stub> stub);

protected:
    void run();

private:
    std::shared_ptr<stock_api::Stock::Stub> stub_;

signals:
    void brokerMinuteTickArrived(BrokerMinuteTick *);
};


#endif
