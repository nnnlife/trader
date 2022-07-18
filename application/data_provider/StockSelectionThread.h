#ifndef STOCK_SELECTION_THREAD_H_
#define STOCK_SELECTION_THREAD_H_

#include <QThread>
#include <iostream>
#include <QDateTime>
#include "stock_provider.grpc.pb.h"

class StockSelectionThread : public QThread {
Q_OBJECT
public:
    StockSelectionThread(std::shared_ptr<stock_api::Stock::Stub> stub);

protected:
    void run();

private:
    std::shared_ptr<stock_api::Stock::Stub> stub_;

signals:
    void stockCodeChanged(QString code);
};

#endif
