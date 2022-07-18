#include "OrderHandler.h"


OrderHandler::OrderHandler() {
    connect(DataProvider::getInstance(), &DataProvider::tickArrived,
            this, &OrderHandler::tickHandler);
    connect(DataProvider::getInstance(), &DataProvider::orderResultArrived,
            this, &OrderHandler::orderResultArrived);
    connect(DataProvider::getInstance(), &DataProvider::simulationStatusChanged, this, &OrderHandler::sendBalanceRequest);
    connect(DataProvider::getInstance(), &DataProvider::simulationStatusChanged, this, &OrderHandler::simulationStatusChanged);

    DataProvider::getInstance()->startStockTick();

    DataProvider::getInstance()->startOrderListening();
    DataProvider::getInstance()->sendBalanceRequest();
}


void OrderHandler::sendBalanceRequest() {
    DataProvider::getInstance()->sendBalanceRequest();
    //DataProvider::getInstance()->getLongStock();
}


void OrderHandler::tickHandler(CybosTickData *d) {
    QString code = QString::fromStdString(d->code());
    emit currentPriceChanged(code, d->current_price());
    delete d;
}


void OrderHandler::setCurrentStock(const QString &code) {
    DataProvider::getInstance()->setCurrentStock(code);
}


void OrderHandler::fillSellOrder(const QString &code, const QString &name, int price, int quantity) {
    emit fillSellOrderSelected(code, name, price, quantity);
}


int OrderHandler::getMarketType(const QString &code) {
    return (DataProvider::getInstance()->isKospi(code) ? 1 : 0);
}
