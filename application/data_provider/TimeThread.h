#ifndef _TIME_THREAD_H_
#define _TIME_THREAD_H_


#include <QThread>
#include <iostream>
#include "stock_provider.grpc.pb.h"

using google::protobuf::Timestamp;

class TimeThread : public QThread {
Q_OBJECT
public:
    TimeThread(std::shared_ptr<stock_api::Stock::Stub> stub);

protected:
    void run();

private:
    std::string code;
    std::shared_ptr<stock_api::Stock::Stub> stub_;

signals:
    void timeInfoArrived(Timestamp *);
};


#endif
