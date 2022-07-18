#ifndef TRANSACTION_DATA_H_
#define TRANSACTION_DATA_H_


#include <QObject>
#include <QVariant>
#include "stock_provider.grpc.pb.h"
using stock_api::Report;
using stock_api::OrderResult;
using stock_api::OrderStatusFlag;
using stock_api::OrderMethod;
using stock_api::OrderMsg;


class TransactionData : public QObject {
Q_OBJECT

public:
    enum ActionType{
        NO_ACTION = 0,
        OK_CANCEL = 1,
    };

    TransactionData();
    TransactionData(const Report& r);

    QVariant getDisplayData(int column) const;
    QVariant getEditData(int column) const;
    bool setEditData(int column, const QVariant &value);

    bool isMatched(const QString &iOrderNum, const QString &orderNum);
    bool setCurrentPrice(int price);

    void setData(const Report &r);
    void updateData(const Report &r);

    void setCode(const QString &code);
    const QString &code() const { return mCode; }

    void fillOrder(const QString &code, const QString &name, int price, int quantity);
    bool isEditable(int column) const;
    void resetData();
    int availableAction() const;
    int marketType() const;

private:
    class DataContent {
    public:
        DataContent() {}
        DataContent(int price, int quantity, OrderMethod orderMethod) {
            mPrice = price;
            mQuantity = quantity;
            mOrderStrategy = orderMethod;
        }

        bool operator==(const DataContent &rhs) const {
            if (price() == rhs.price() &&
                quantity() == rhs.quantity() &&
                orderStrategy() == rhs.orderStrategy())
                return true;
            return false;
        }

        int price() const { return mPrice; }
        int quantity() const { return mQuantity; }
        OrderMethod orderStrategy() const { return mOrderStrategy; }
        void setPrice(int price) {
            mPrice = price;
        }

        void setQuantity(int quantity) {
            mQuantity = quantity;
        }

        void setOrderStrategy(OrderMethod m) {
            mOrderStrategy = m;
        }

        void reset() {
            mPrice = 0;
            mQuantity = 0;
            mOrderStrategy = OrderMethod::TRADE_UNKNOWN;
        }
    private:
        int mPrice = 0;
        int mQuantity = 0;
        OrderMethod mOrderStrategy = OrderMethod::TRADE_UNKNOWN;
    };

    QString mInternalOrderNum;
    QString mOrderNum;
    QString mName;
    QString mCode;
    OrderStatusFlag mFlag;
    int mCurrentPrice;    
    int mMarketType;
    bool mIsBuy;

    bool mFormData;

    DataContent content;
    DataContent editContent;

private:
    QString flagToString(OrderStatusFlag flag, int quantity) const;
    //QString methodToString(OrderMethod m) const;

signals:
    void formCleared();
};

#endif
