#ifndef _TICK_THREAD_H_
#define _TICK_THREAD_H_


#include <QThread>
#include <iostream>
#include "stock_provider.grpc.pb.h"

using stock_api::CybosTickData;

class TickThread : public QThread {
Q_OBJECT
public:
    TickThread(std::shared_ptr<stock_api::Stock::Stub> stub);

protected:
    void run();

private:
    std::shared_ptr<stock_api::Stock::Stub> stub_;

signals:
    void tickArrived(CybosTickData *);
};


#endif
