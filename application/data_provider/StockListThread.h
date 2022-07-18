#ifndef STOCK_LIST_THREAD_H_
#define STOCK_LIST_THREAD_H_

#include <QThread>
#include <iostream>
#include <QDateTime>
#include "stock_provider.grpc.pb.h"

class StockListThread : public QThread {
Q_OBJECT
public:
    StockListThread(std::shared_ptr<stock_api::Stock::Stub> stub);

protected:
    void run();

private:
    std::shared_ptr<stock_api::Stock::Stub> stub_;

signals:
    void stockListChanged(QString type);
};

#endif
