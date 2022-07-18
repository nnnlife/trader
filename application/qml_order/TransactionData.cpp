#include "TransactionData.h"
#include <QDebug>
#include "OrderHandler.h"
#include "TrColumn.h"


TransactionData::TransactionData(const Report& r) :
QObject(nullptr) {
    mFormData = false;
    updateData(r);
}


TransactionData::TransactionData() :
QObject(nullptr){
    mFormData = true;
    resetData();
}


bool TransactionData::isEditable(int column) const {
    if (mFormData) {
        if (column >= (int)COLUMN::OrderType && column <= (int)COLUMN::OrderStrategy)
            return true;
    }
    else {
        if (column == COLUMN::Quantity) {
            if (mFlag == OrderStatusFlag::STATUS_REGISTERED && content.orderStrategy() == OrderMethod::TRADE_ON_BID_ASK_MEET)
                return true;
        }
        else if (column == COLUMN::Price || column == COLUMN::OrderStrategy) {
            if (mFlag != OrderStatusFlag::STATUS_UNKNOWN &&
                mFlag != OrderStatusFlag::STATUS_TRADED &&
                mFlag != OrderStatusFlag::STATUS_DENIED)
                return true;
        }
    }
    return false;
}


int TransactionData::marketType() const {
    return mMarketType;
}


int TransactionData::availableAction() const {
    if (mFormData) {
        return OK_CANCEL;
    }
    return NO_ACTION;
}


void TransactionData::setCode(const QString &code) {
    mMarketType = OrderHandler::instance()->getMarketType(code);
    mCode = code;
}


void TransactionData::resetData() {
    content.reset();
    editContent.reset();
    mFlag = OrderStatusFlag::STATUS_UNKNOWN;
    mMarketType = 1; // KOSPI
    mCurrentPrice = 0;
    mName = "";
    mCode = "";
    mInternalOrderNum = "";
    mOrderNum = "";
    mIsBuy = true;
}


bool TransactionData::setEditData(int column, const QVariant &value) {
    if (column == COLUMN::OrderType) {
        if (mFormData) {
            mIsBuy = value.toInt() == 1;
            qWarning() << "mIsBuy : " << mIsBuy;
            return true;
        }
    }
    else if (column == COLUMN::Price) {
        qWarning() << "setEditPrice : " << value.toInt();
        editContent.setPrice(value.toInt());
        return true;
    }
    else if (column == COLUMN::Quantity) {
        editContent.setQuantity(value.toInt());
        return true;
    }
    else if (column == COLUMN::OrderStrategy) {
        editContent.setOrderStrategy((OrderMethod)value.toInt());
        return true;
    }
    else if (column == COLUMN::Execution) {
        if (!mFormData) {
            if (value.toInt() == NO_ACTION) {
                if (mFlag == OrderStatusFlag::STATUS_TRADING || mFlag == OrderStatusFlag::STATUS_SUBMITTED) {
                    DataProvider::getInstance()->cancelOrder(mCode, mOrderNum);
                    return true;
                }
            }
        }
        else {
            if (value.toInt() == NO_ACTION) {
                resetData();
                emit formCleared();
                return true;
            }
        }
    }
    return false;
}


void TransactionData::updateData(const Report &r) {
    mInternalOrderNum = QString::fromStdString(r.internal_order_num());
    mOrderNum = QString::fromStdString(r.order_num());
    mName = QString::fromStdString(r.company_name());
    setCode(QString::fromStdString(r.code()));

    content.setPrice(int(r.price()));
    content.setQuantity(r.quantity());
    content.setOrderStrategy(r.method());
    editContent = content;

    mFlag = r.flag();
    mIsBuy = r.is_buy();
    mCurrentPrice = 0;
}


QVariant TransactionData::getDisplayData(int column) const{
    switch(column) {
    case COLUMN::Status:
        return flagToString(mFlag, content.quantity());
    case COLUMN::OrderNum:
        if (mOrderNum.isEmpty())
            return mInternalOrderNum;
        return mOrderNum;
    case COLUMN::Name:
        return mName;
    case COLUMN::OrderType:
        return QVariant(mIsBuy);
    case COLUMN::Quantity:
        return QVariant(content.quantity());
    case COLUMN::Price:
        return QVariant(content.price());
    case COLUMN::CurrentPrice:
        return QVariant(mCurrentPrice);
    case COLUMN::OrderStrategy:
        return QVariant((int)content.orderStrategy());
    default: break;
    }

    return QVariant(QString(""));
}


QVariant TransactionData::getEditData(int column) const {
    switch(column) {
    case COLUMN::Name:
        return mName;
    case COLUMN::OrderType:
        return QVariant(mIsBuy);
    case COLUMN::Quantity:
        return QVariant(editContent.quantity());
    case COLUMN::Price:
        return QVariant(editContent.price());
    case COLUMN::CurrentPrice:
        return QVariant(mCurrentPrice);
    case COLUMN::OrderStrategy:
        qWarning() << "getEditData OrderStrategy : " << (int)editContent.orderStrategy();
        return QVariant((int)editContent.orderStrategy());
    default: break;
    }

    return QVariant(QString(""));
}


bool TransactionData::isMatched(const QString &iOrderNum, const QString &orderNum) {
    if (mInternalOrderNum == iOrderNum || mOrderNum == orderNum)
        return true;
    return false;    
}


bool TransactionData::setCurrentPrice(int price) {
    if (mCurrentPrice == price)
        return false;
    mCurrentPrice = price;
    return true;
}


void TransactionData::fillOrder(const QString &code, const QString &name, int price, int quantity) {
    setCode(code);
    mName = name;
    mIsBuy = false;
    content.setPrice(price);
    content.setQuantity(quantity);
    content.setOrderStrategy(OrderMethod::TRADE_IMMEDIATELY);
    editContent = content;
}


QString TransactionData::flagToString(OrderStatusFlag flag, int quantity) const {
    switch(flag) {
    case OrderStatusFlag::STATUS_UNKNOWN:
        return QString("*");
    case OrderStatusFlag::STATUS_REGISTERED:
        return QString("등록");
    case OrderStatusFlag::STATUS_TRADING:
        if (mIsBuy)
            return QString("일부매수");
        else
            return QString("일부매도");
    case OrderStatusFlag::STATUS_SUBMITTED:
        return QString("접수");
    case OrderStatusFlag::STATUS_TRADED:
        return QString("체결");
    case OrderStatusFlag::STATUS_DENIED:
        return QString("거절");
    case OrderStatusFlag::STATUS_CONFIRM:
        if (quantity == 0) 
            return QString("취소");
        else
            return QString("확인");
    default: break;
    }
    return QString("-");
}


/*
QString TransactionData::methodToString(OrderMethod m) const {
    switch(m) {
    case OrderMethod::TRADE_UNKNOWN:
        return QString("*");
    case OrderMethod::TRADE_IMMEDIATELY:
        return QString("IMM");
    case OrderMethod::TRADE_ON_BID_ASK_MEET:
        return QString("BA_M");
    case OrderMethod::TRADE_ON_PRICE:
        return QString("ON_P");
    default: break;
    }
    return "-";
}
*/
