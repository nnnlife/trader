#ifndef TRADE_DATA_H_
#define TRADE_DATA_H_

#include <QObject>
#include <QDateTime>
#include <QVariant>

#include "stock_provider.grpc.pb.h"
using stock_api::Report;
using stock_api::OrderResult;
using stock_api::OrderStatusFlag;
using stock_api::OrderMethod;
using stock_api::OrderMsg;


class TradeData {
public:
    TradeData();

    bool isMatched(const QString &orderNum, const QString &internalOrderNum);
    void setData(const Report &r);
    bool updateData(const Report &r);
    bool setCurrentPrice(int price) {
        if (mCurrentPrice == price)
            return false;
        mCurrentPrice = price;
        return true;
    }

    QVariant getDisplayData(int column) const;

    const QString &getCode() const { return mCode; }
    int getQuantity() const { return mQuantity; }
    int getFlag() const { return int(mFlag); }
    int getMethod() const { return int(mMethod); }
    bool getIsBuy() const { return mIsBuy; }
    int getTradedQuantity() const { return mTradedQuantity; }
    const QString &getOrderNum() const {
        if (mOrderNum.length() > 0)
            return mOrderNum;
        return mInternalOrderNum;
    }

private:
    QString mInternalOrderNum;
    QString mOrderNum;
    QString mCompanyName;
    QString mCode;
    QDateTime mLastUpdateTime;
    bool mIsBuy;
    OrderStatusFlag mFlag;
    OrderMethod mMethod;
    int mHoldPrice;
    int mPrice;
    int mQuantity;
    int mCurrentPrice;
    int mTradedPrice;
    int mTradedQuantity;

private:
    QString flagToString(OrderStatusFlag flag, int quantity) const;
    QString methodToString(OrderMethod method) const;
    QVariant getCurrentProfit() const;
};


#endif
