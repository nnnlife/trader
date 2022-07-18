#ifndef _BIDASK_THREAD_H_
#define _BIDASK_THREAD_H_


#include <QThread>
#include <iostream>
#include "stock_provider.grpc.pb.h"

using stock_api::CybosBidAskTickData;

class BidAskThread : public QThread {
Q_OBJECT
public:
    BidAskThread(std::shared_ptr<stock_api::Stock::Stub> stub);

protected:
    void run();

private:
    std::shared_ptr<stock_api::Stock::Stub> stub_;

signals:
    void tickArrived(CybosBidAskTickData *);
};


#endif
