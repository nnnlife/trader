#include "LongModel.h"
#include <QDebug>


LongModel::LongModel(QObject *parent)
: QAbstractTableModel(parent) {
    connect(OrderHandler::instance(), &OrderHandler::currentPriceChanged, this, &LongModel::setCurrentPrice);
    connect(OrderHandler::instance(), &OrderHandler::simulationStatusChanged, this, &LongModel::simulationStatusChanged);
    connect(OrderHandler::instance(), &OrderHandler::orderResultArrived, this, &LongModel::orderResultArrived);
}


void LongModel::simulationStatusChanged() {
    mCurrentBalance = 0;
    beginResetModel();
    mLongData.clear();
    endResetModel();
}


QVariant LongModel::headerData(int section, Qt::Orientation orientation, int role) const {
    Q_UNUSED(role);
    if (orientation == Qt::Horizontal) {
        switch(section) {
        case 0: return "종목";
        case 1: return "현재가";
        case 2: return "수익률";
        case 3: return "장부가";
        case 4: return "수량";
        case 5: return "금액";
        default: break;
        }
    }
    return QVariant();
}


QVariant LongModel::data(const QModelIndex &index, int role) const {
    //qWarning() << "data : " << index.row() << ", " << index.column();
    if (index.row() < mLongData.count()) {
        if (role == Qt::DisplayRole) 
            return mLongData.at(index.row()).getDisplayData(index.column());
    }

    return QVariant();
}


void LongModel::selectionChanged(int row) {
    if (row < mLongData.count()) {
        LongData data = mLongData[row];
        int sendPrice = (data.currentPrice() == 0 ? data.bookPrice() : data.currentPrice());
        OrderHandler::instance()->fillSellOrder(data.code(), data.name(), sendPrice, data.quantity());
    }
}


void LongModel::setCurrentStock(int row) {
    if (row < mLongData.count()) {
        OrderHandler::instance()->setCurrentStock(mLongData[row].code());
    }
}


void LongModel::refresh() {
    static int priceStart = 51000;
    beginResetModel(); // use reset because begininsert does not work with scrollbar
    Report r;
    r.set_company_name("삼성전자");
    r.set_code("A005930");
    r.set_hold_price(priceStart);
    r.set_quantity(10);
    r.set_internal_order_num("I1212");

    priceStart += 1000;
    LongData longData(r);
    mLongData.insert(0, longData);
    endResetModel();
}


void LongModel::orderResultArrived(OrderResult *r) {
    if (r->current_balance() != 0)
        setBalance(r->current_balance());

    for (int i = 0; i < r->report_size(); i++) {
        int index = -1;
        bool isRemove = false;
        const Report &report = r->report(i);
        if (report.is_buy() || (report.flag() != OrderStatusFlag::STATUS_REGISTERED || report.method() != OrderMethod::TRADE_UNKNOWN))
            continue;

        for (int j = 0; j < mLongData.count(); j++) {
            if (mLongData[j].isMatched(QString::fromStdString(report.internal_order_num()))) {
                if (report.quantity() == 0) 
                    isRemove = true;
                else 
                    mLongData[j].updateData(report);

                index = j;
                break;
            }
        }


        if (isRemove) {
            beginRemoveRows(QModelIndex(), index, index);
            mLongData.removeAt(index);
            endRemoveRows();
        }
        else {
            if (index == -1) {
                beginInsertRows(QModelIndex(), 0, 0); // use reset because begininsert does not work with scrollbar
                LongData longData(report);
                mLongData.insert(0, longData);
                endInsertRows();
            }
            else {
                dataChanged(createIndex(index, 0), createIndex(index, COLUMN_COUNT));
            }
        }
    }
}


void LongModel::setCurrentPrice(const QString &code, int price) {
    for (int i = 0; i < mLongData.count(); i++) {
        if (mLongData[i].code() == code) {
            if (mLongData[i].setCurrentPrice(price))
                dataChanged(createIndex(i, 1), createIndex(i, 2));
            break;
        }
    }
}
