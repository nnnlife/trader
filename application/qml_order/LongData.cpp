#include "LongData.h"
#include <QDebug>


LongData::LongData(const Report& r) {
    mInternalOrderNum = QString::fromStdString(r.internal_order_num());
    mName = QString::fromStdString(r.company_name());
    mCode = QString::fromStdString(r.code());
    mBookPrice = int(r.hold_price());
    mQuantity = r.quantity();
    mAmount = mBookPrice * mQuantity;
    mCurrentPrice = 0;
}


void LongData::updateData(const Report &r) {
    mBookPrice = int(r.hold_price());
    mQuantity = r.quantity();
    mAmount = mBookPrice * mQuantity;
}


QVariant LongData::getDisplayData(int column) const{
    switch(column) {
    case 0:
        return mName;
    case 1:
        return QVariant(mCurrentPrice);
    case 2:
        if (mCurrentPrice > 0 && mBookPrice > 0) 
            return (qreal(mCurrentPrice) - mBookPrice) / mBookPrice * 100.0 - 0.28;
        return QVariant(0.0);
    case 3:
        return QVariant(mBookPrice);
    case 4:
        return QVariant(mQuantity);
    case 5:
        return QVariant((uint)mAmount);
    }

    return QVariant();
}
