#include "TransactionModel.h"
#include "TrColumn.h"
#include <QMutableListIterator>

#define QTY_EDIT_ROLE           (Qt::UserRole)
#define ACTION_ROLE             (Qt::UserRole + 1) 
#define MARKET_TYPE_ROLE        (Qt::UserRole + 2) 
#define CODE_ROLE               (Qt::UserRole + 3) 



TransactionModel::TransactionModel(QObject *parent)
: QAbstractTableModel(parent) {
    connect(OrderHandler::instance(), &OrderHandler::currentPriceChanged, this, &TransactionModel::setCurrentPrice);
    connect(OrderHandler::instance(), &OrderHandler::simulationStatusChanged, this, &TransactionModel::simulationStatusChanged);
    connect(OrderHandler::instance(), &OrderHandler::orderResultArrived, this, &TransactionModel::orderResultArrived);

    connect(OrderHandler::instance(), &OrderHandler::fillSellOrderSelected, this, &TransactionModel::fillSellOrder);
    TransactionData * t = new TransactionData;
    mTransactionData.append(t);
    connect(t, &TransactionData::formCleared, this, &TransactionModel::formCleared);
}


void TransactionModel::clearTransactionData() {
    QMutableListIterator<TransactionData *> i(mTransactionData);
    while (i.hasNext()) {
        i.next();
        delete i.value();
    }
    mTransactionData.clear();
}


void TransactionModel::simulationStatusChanged() {
    beginResetModel();
    clearTransactionData();
    TransactionData *t = new TransactionData;
    mTransactionData.append(t);
    connect(t, &TransactionData::formCleared, this, &TransactionModel::formCleared);
    endResetModel();
}


void TransactionModel::formCleared() {
    dataChanged(createIndex(0, 0), createIndex(0, COLUMN_COUNT));
}


Qt::ItemFlags TransactionModel::flags(const QModelIndex &index) const {
    qWarning() << "flags : " << index.row() << ", " << index.column();
    if (index.row() < mTransactionData.count()) {
        return mTransactionData.at(index.row())->isEditable(index.column()) ? Qt::ItemIsEditable : Qt::NoItemFlags;
    }

    return Qt::NoItemFlags;
}


bool TransactionModel::setData(const QModelIndex &index, const QVariant &value, int role) {
    qWarning() << "setData : " << index.row() << ", " << index.column() << " role : " << role;
    if (index.row() < mTransactionData.count() && role == Qt::EditRole) {
        int row = index.row();
        return mTransactionData[row]->setEditData(index.column(), value);
    }
    return false;
}


QVariant TransactionModel::headerData(int section, Qt::Orientation orientation, int role) const {
    Q_UNUSED(role);
    if (orientation == Qt::Horizontal) {
        switch(section) {
        case COLUMN::Status:        return "상태";
        case COLUMN::OrderNum:      return "번호";
        case COLUMN::Name:          return "종목";
        case COLUMN::OrderType:     return "구분";
        case COLUMN::Quantity:      return "수량";
        case COLUMN::Price:         return "단가";
        case COLUMN::CurrentPrice:  return "현재가";
        case COLUMN::OrderStrategy: return "주문방식";
        case COLUMN::Execution:     return "실행";
        default: break;
        }
    }
    return QVariant();
}


QVariant TransactionModel::data(const QModelIndex &index, int role) const {
    if (index.row() < mTransactionData.count()) {
        if (role == Qt::DisplayRole) {
            return mTransactionData.at(index.row())->getDisplayData(index.column());
        }
        else if (role == Qt::EditRole) {
            return mTransactionData.at(index.row())->getEditData(index.column());
            qWarning() << "EditRole : ";
        }
        else if (role == ACTION_ROLE) {
            return QVariant(mTransactionData.at(index.row())->availableAction());
        }
        else if (role == MARKET_TYPE_ROLE) {
            return QVariant(mTransactionData.at(index.row())->marketType());
        }
        else if (role == CODE_ROLE) {
            return QVariant(mTransactionData.at(index.row())->code());
        }
        else if (role == QTY_EDIT_ROLE) {
            return QVariant(mTransactionData.at(index.row())->isEditable(index.column()));
        }
    }

    return QVariant(QString(""));
}


void TransactionModel::selectionChanged(int row) {
    if (row < mTransactionData.count()) {
    }
}


void TransactionModel::refresh() {
    static int priceStart = 51000;
    static int type = 0;
    beginInsertRows(QModelIndex(), mTransactionData.count(), mTransactionData.count());
    Report r;
    r.set_company_name("삼성전자");
    r.set_code("A005930");
    r.set_hold_price(priceStart);
    r.set_price(priceStart);
    r.set_quantity(10);
    r.set_flag(OrderStatusFlag::STATUS_REGISTERED);
    r.set_method((type % 2== 0?OrderMethod::TRADE_ON_PRICE:OrderMethod::TRADE_ON_BID_ASK_MEET));
    r.set_internal_order_num("I1212");
    TransactionData *transactionData = new TransactionData(r);
    qWarning() << "create transaction data";
    mTransactionData.append(transactionData);
    priceStart += 10000;
    type += 1;
    endInsertRows();
}



void TransactionModel::orderResultArrived(OrderResult *r) {
    for (int i = 0; i < r->report_size(); i++) {
        int index = -1;
        bool isRemove = false;
        const Report &report = r->report(i);

        if (!report.is_buy() && report.flag() == OrderStatusFlag::STATUS_REGISTERED && report.method() == OrderMethod::TRADE_UNKNOWN)
            continue;

        for (int j = 1; j < mTransactionData.count(); j++) {
            if (mTransactionData[j]->isMatched(QString::fromStdString(report.internal_order_num()), QString::fromStdString(report.order_num()))) {
                if (report.flag()  == OrderStatusFlag::STATUS_TRADED ||
                        (report.flag() == OrderStatusFlag::STATUS_CONFIRM && report.quantity() == 0))
                    isRemove = true;
                else 
                    mTransactionData[j]->updateData(report);

                index = j;
                break;
            }
        }

        if (isRemove) {
            beginRemoveRows(QModelIndex(), index, index);
            delete mTransactionData[index];
            mTransactionData.removeAt(index);
            endRemoveRows();
        }
        else {
            if (index == -1) {
                beginInsertRows(QModelIndex(), mTransactionData.count(), mTransactionData.count());
                TransactionData * transactionData = new TransactionData(report);
                qWarning() << "create transaction data";
                mTransactionData.append(transactionData);
                endInsertRows();
            }
            else {
                dataChanged(createIndex(index, 0), createIndex(index, COLUMN_COUNT));
            }
        }
    }
}


void TransactionModel::setCurrentPrice(const QString &code, int price) {
    for (int i = 0; i < mTransactionData.count(); i++) {
        if (mTransactionData[i]->code() == code) {
            if (mTransactionData[i]->setCurrentPrice(price))
                dataChanged(createIndex(i, 6), createIndex(i, 6));
        }
    }
}


void TransactionModel::fillSellOrder(const QString &code, const QString &name, int price, int quantity) {
    mTransactionData[0]->resetData();
    mTransactionData[0]->fillOrder(code, name, price, quantity);
    dataChanged(createIndex(0, 0), createIndex(0, COLUMN_COUNT));
}
