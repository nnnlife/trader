#ifndef TRANSACTION_MODEL_H_
#define TRANSACTION_MODEL_H_

#include <qqml.h>
#include <QAbstractTableModel>
#include "TransactionData.h"
#include <QDebug>
#include "OrderHandler.h"


class TransactionModel : public QAbstractTableModel {
    Q_OBJECT
    QML_ELEMENT

public:
    enum {
        COLUMN_COUNT = 9
    };

    TransactionModel(QObject *parent=nullptr);

    int columnCount(const QModelIndex &parent = QModelIndex()) const override
    {
        Q_UNUSED(parent);
        return COLUMN_COUNT;
    }

    int rowCount(const QModelIndex &parent = QModelIndex()) const override
    {
        Q_UNUSED(parent);
        return mTransactionData.count();
    }

    Qt::ItemFlags flags(const QModelIndex &index) const override;

    QVariant headerData(int secion, Qt::Orientation orientation, int role=Qt::DisplayRole) const override;
    QVariant data(const QModelIndex &index, int role) const override;
    bool setData(const QModelIndex &index, const QVariant &value, int role = Qt::EditRole) override;

    Q_INVOKABLE void selectionChanged(int row);
    Q_INVOKABLE void refresh();

    QHash<int, QByteArray> roleNames() const override
    {
        return { {Qt::DisplayRole, "display"},
                 {Qt::EditRole, "editData"},
                 {Qt::UserRole, "isQtyEditable"},
                 {Qt::UserRole + 1, "actionType"},
                 {Qt::UserRole + 2, "marketType"},
                 {Qt::UserRole + 3, "code"}};
    }

private:
    QList<TransactionData *> mTransactionData;

    void clearTransactionData();

private slots:
    void simulationStatusChanged();
    void orderResultArrived(OrderResult *r);
    void setCurrentPrice(const QString &code, int price);
    void fillSellOrder(const QString &code, const QString &name, int price, int quantity);
    void formCleared();
};


#endif
