#ifndef _TRADER_THREAD_H_
#define _TRADER_THREAD_H_


#include <QThread>
#include <iostream>
#include "stock_provider.grpc.pb.h"


using stock_api::OrderMethod;
using stock_api::OrderMsg;
using stock_api::OrderResult;


class TraderThread : public QThread {
Q_OBJECT
public:
    TraderThread(std::shared_ptr<stock_api::Stock::Stub> stub);

    void order(const QString &code, int price, int quantity, int percentage, OrderMethod m, bool isBuy);

protected:
    void run();

private:
    std::shared_ptr<stock_api::Stock::Stub> stub_;

signals:
    void orderResultArrived(OrderResult *);
};


#endif
