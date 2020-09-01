#include "TradingModel.h"


#define QTY_ROLE            (Qt::UserRole + 1)
#define STATUS_ROLE         (Qt::UserRole + 2)
#define BUY_ROLE            (Qt::UserRole + 3)
#define ORDER_NUM_ROLE      (Qt::UserRole + 4)
#define TRADED_QTY_ROLE     (Qt::UserRole + 5)
#define TRADE_METHOD_ROLE   (Qt::UserRole + 6)


TradingModel::TradingModel(QObject *parent)
: QAbstractTableModel(parent) {
    // TODO: get all data at startup
    mCurrentBalance = 0;
    connect(DataProvider::getInstance(), &DataProvider::tickArrived,
            this, &TradingModel::tickArrived);
    connect(DataProvider::getInstance(), &DataProvider::orderResultArrived,
            this, &TradingModel::orderResultArrived);
    connect(DataProvider::getInstance(), &DataProvider::simulationStatusChanged, this, &TradingModel::simulationStatusChanged);

    DataProvider::getInstance()->startStockTick();

    DataProvider::getInstance()->startOrderListening();
    qWarning() << "before send balance";
    DataProvider::getInstance()->sendBalanceRequest();
    qWarning() << "after send balance";
}


void TradingModel::simulationStatusChanged(bool isOn) {
    Q_UNUSED(isOn);
    beginResetModel();
    mTradeData.clear();
    endResetModel();
    DataProvider::getInstance()->sendBalanceRequest();
}


void TradingModel::tickArrived(CybosTickData *data) {
    QString code = QString::fromStdString(data->code());
    for (int i = 0; i < mTradeData.count(); i++) {
        if (mTradeData[i].getQuantity() - mTradeData[i].getTradedQuantity() > 0 && mTradeData[i].getCode() == code) {
            if (mTradeData[i].setCurrentPrice(data->current_price()))
                dataChanged(createIndex(i, 2), createIndex(i, 4));
        }
    }
    delete data;
}


void TradingModel::changeToImmediate(int row, const QString &orderNum) {
    qWarning() << "changeToImmediate : " << row << " " << orderNum;
    if (mTradeData.at(row).getOrderNum() == orderNum) {
        DataProvider::getInstance()->changeToImmediate(mTradeData.at(row).getCode(), orderNum, 100);
    }
}


void TradingModel::cancelOrder(int row, const QString &orderNum) {
    qWarning() << "cancelOrder : " << row << " " << orderNum;
    if (mTradeData.at(row).getOrderNum() == orderNum) {
        DataProvider::getInstance()->cancelOrder(mTradeData.at(row).getCode(), orderNum);
    }
}


QVariant TradingModel::headerData(int section, Qt::Orientation orientation, int role) const {
    Q_UNUSED(role);
    if (orientation == Qt::Horizontal) {
        switch(section) {
        case 0: return "회사명";
        case 1: return "구분";
        case 2: return "현재가";
        case 3: return "매수평균";
        case 4: return "수익";
        case 5: return "상태";
        case 6: return "매매방식";
        case 7: return "가격";
        case 8: return "수량";
        case 9: return "체결가격";
        case 10: return "체결수량";
        case 11: return "Action";
        case 12: return "CODE";
        case 13: return "주문번호";
        case 14: return "시간";
        default: break;
        }
    }
    return QVariant();
}


QVariant TradingModel::data(const QModelIndex &index, int role) const {
    //qWarning() << "data : " << index.row() << ", " << index.column();
    if (index.row() < mTradeData.count()) {
        if (role == Qt::DisplayRole) 
            return mTradeData.at(index.row()).getDisplayData(index.column());
        else if (role == QTY_ROLE) 
            return QVariant(mTradeData.at(index.row()).getQuantity());
        else if (role == STATUS_ROLE) 
            return QVariant(mTradeData.at(index.row()).getFlag());
        else if (role == TRADED_QTY_ROLE)
            return QVariant(mTradeData.at(index.row()).getTradedQuantity());
        else if (role == BUY_ROLE) 
            return QVariant(mTradeData.at(index.row()).getIsBuy());
        else if (role == ORDER_NUM_ROLE)
            return QVariant(mTradeData.at(index.row()).getOrderNum());
        else if (role == TRADE_METHOD_ROLE)
            return QVariant(mTradeData.at(index.row()).getMethod());
    }

    return QVariant();
}


void TradingModel::orderResultArrived(OrderResult *r) {
    qWarning() << "Order Received: count:(" << r->report_size() << ")";
    if (r->current_balance() != 0) {
        qWarning() << "BALANCE : " << r->current_balance();
        setBalance(r->current_balance());
    }

    for (int i = 0; i < r->report_size(); i++) {
        bool found = false;
        const Report &report = r->report(i);
        for (int j = 0; j < mTradeData.count(); j++) {
            if (mTradeData[j].isMatched(QString::fromStdString(report.order_num()),
                                       QString::fromStdString(report.internal_order_num()))) {
                found = true;
                mTradeData[j].updateData(report);
            }
        }
        if (!found) {
            beginInsertRows(QModelIndex(), 0, 0);
            TradeData tradeData;
            tradeData.setData(report);
            mTradeData.insert(0, tradeData);
            endInsertRows();
        }
    }
    //qWarning() << "count : " << mTradeData.count();
    dataChanged(createIndex(0, 0), createIndex(mTradeData.count() - 1, COLUMN_COUNT));
}


void TradingModel::selectionChanged(int row) {
    if (row < mTradeData.count()) {
        DataProvider::getInstance()->setCurrentStock(mTradeData.at(row).getCode());
    }
}
