#ifndef _ORDER_HANDLER_H_
#define _ORDER_HANDLER_H_

#include <QObject>
#include "DataProvider.h"

class OrderHandler : public QObject{
Q_OBJECT
public:
    static OrderHandler *instance() {
        static OrderHandler *handler = nullptr;

        if (handler == nullptr)
            handler = new OrderHandler;

        return handler;
    }

    void setCurrentStock(const QString &code);
    void fillSellOrder(const QString &code, const QString &name, int price, int quantity);
    int getMarketType(const QString &code);

private:
    OrderHandler();

signals:
    void orderResultArrived(OrderResult *);
    void tickArrived(CybosTickData *);
    void currentPriceChanged(const QString &code, int price);
    void simulationStatusChanged(bool);

private slots:
    void sendBalanceRequest();
    void tickHandler(CybosTickData *);

signals:
    void fillSellOrderSelected(const QString &code, const QString &name, int price, int quantity);
};


#endif
