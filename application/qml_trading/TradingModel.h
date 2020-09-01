#ifndef TRADING_MODEL_H_
#define TRADING_MODEL_H_

#include <qqml.h>
#include <QAbstractTableModel>
#include "DataProvider.h"
#include "TradeData.h"
#include <QDebug>


class TradingModel : public QAbstractTableModel {
    Q_OBJECT
    QML_ELEMENT
    Q_PROPERTY(int balance READ getBalance WRITE setBalance NOTIFY balanceChanged)

public:
    enum {
        COLUMN_COUNT = 15
    };

    TradingModel(QObject *parent=nullptr);

    int columnCount(const QModelIndex &parent = QModelIndex()) const override
    {
        Q_UNUSED(parent);
        return COLUMN_COUNT;
    }

    int rowCount(const QModelIndex &parent = QModelIndex()) const override
    {
        Q_UNUSED(parent);
        return mTradeData.count();
    }

    int getBalance() { return mCurrentBalance; }

    void setBalance(int b) {
        if (b != mCurrentBalance) {
            mCurrentBalance = b;
            emit balanceChanged();
        }
    }

    QVariant headerData(int secion, Qt::Orientation orientation, int role=Qt::DisplayRole) const override;
    QVariant data(const QModelIndex &index, int role) const override;

    QHash<int, QByteArray> roleNames() const override
    {
        return { {Qt::DisplayRole, "display"},
                 {Qt::UserRole + 1, "qty" },
                 {Qt::UserRole + 2, "status"},
                 {Qt::UserRole + 3, "is_buy" },
                 {Qt::UserRole + 4, "order_num"},
                 {Qt::UserRole + 5, "traded_qty"},
                 {Qt::UserRole + 6, "trade_method"}};
    }

    Q_INVOKABLE void changeToImmediate(int row, const QString &orderNum);
    Q_INVOKABLE void cancelOrder(int row, const QString &orderNum);
    Q_INVOKABLE void selectionChanged(int row);

private:
    QList<TradeData> mTradeData;
    int mCurrentBalance;

private slots:
    void orderResultArrived(OrderResult *);
    void tickArrived(CybosTickData *);
    void simulationStatusChanged(bool);

signals:
    void balanceChanged();
};


#endif
