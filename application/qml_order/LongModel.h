#ifndef LONG_MODEL_H_
#define LONG_MODEL_H_

#include <qqml.h>
#include <QAbstractTableModel>
#include "LongData.h"
#include <QDebug>
#include "OrderHandler.h"


class LongModel : public QAbstractTableModel {
    Q_OBJECT
    QML_ELEMENT
    Q_PROPERTY(int balance READ getBalance NOTIFY balanceChanged)

public:
    enum {
        COLUMN_COUNT = 6
    };

    LongModel(QObject *parent=nullptr);

    int columnCount(const QModelIndex &parent = QModelIndex()) const override
    {
        Q_UNUSED(parent);
        return COLUMN_COUNT;
    }

    int rowCount(const QModelIndex &parent = QModelIndex()) const override
    {
        Q_UNUSED(parent);
        return mLongData.count();
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

    Q_INVOKABLE void selectionChanged(int row);
    Q_INVOKABLE void refresh();
    Q_INVOKABLE void setCurrentStock(int row);

private:
    QList<LongData> mLongData;
    int mCurrentBalance = 0;

signals:
    void balanceChanged();

private slots:
    void simulationStatusChanged();
    void orderResultArrived(OrderResult *r);
    void setCurrentPrice(const QString &code, int price);
};


#endif
