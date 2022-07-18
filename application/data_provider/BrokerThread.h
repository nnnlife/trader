#ifndef _BROKER_THREAD_H_
#define _BROKER_THREAD_H_


#include <QThread>
#include <iostream>
#include "stock_provider.grpc.pb.h"

using stock_api::BrokerSummary;

class BrokerThread : public QThread {
Q_OBJECT
public:
    BrokerThread(std::shared_ptr<stock_api::Stock::Stub> stub);

protected:
    void run();

private:
    std::shared_ptr<stock_api::Stock::Stub> stub_;

signals:
    void summaryArrived(BrokerSummary *);
};


#endif