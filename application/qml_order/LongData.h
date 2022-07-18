#ifndef LONG_DATA_H_
#define LONG_DATA_H_


#include <QObject>
#include <QVariant>
#include "stock_provider.grpc.pb.h"
using stock_api::Report;
using stock_api::OrderResult;
using stock_api::OrderStatusFlag;
using stock_api::OrderMethod;
using stock_api::OrderMsg;


class LongData {
public:
    LongData(const Report& r);

    QVariant getDisplayData(int column) const;
    bool isMatched(const QString &iOrderNum) {
        if (mInternalOrderNum == iOrderNum)
            return true;
        return false;    
    }
    bool setCurrentPrice(int price) {
        if (mCurrentPrice == price)
            return false;
        mCurrentPrice = price;
        return true;
    }

    void setData(const Report &r);
    void updateData(const Report &r);

    const QString &code() { return mCode; }
    int quantity() { return mQuantity; }
    int bookPrice() { return mBookPrice; }
    const QString &name() { return mName; }
    int currentPrice() { return mCurrentPrice; }

private:
    QString mInternalOrderNum;
    QString mName;
    QString mCode;
    int mCurrentPrice;    
    int mBookPrice;
    int mQuantity;
    long long mAmount;
};

#endif
