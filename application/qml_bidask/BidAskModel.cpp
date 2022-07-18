#include "BidAskModel.h"
#include <google/protobuf/util/time_util.h>
#include <QDebug>

using google::protobuf::util::TimeUtil;
using stock_api::OrderMsg;
using stock_api::OrderMethod;

#define VOLUME_DIFF_ROLE    (Qt::UserRole + 1)
#define PROFIT_ROLE         (Qt::UserRole + 2)
#define VI_ROLE             (Qt::UserRole + 3)

BidAskModel::BidAskModel(QObject *parent)
: QAbstractTableModel(parent) {
    connect(DataProvider::getInstance(), &DataProvider::tickArrived,
            this, &BidAskModel::tickArrived);
    connect(DataProvider::getInstance(), &DataProvider::bidAskTickArrived,
            this, &BidAskModel::bidAskTickArrived);
    connect(DataProvider::getInstance(), &DataProvider::stockCodeChanged,
            this, &BidAskModel::setCurrentStock);
    connect(DataProvider::getInstance(), &DataProvider::timeInfoArrived, this, &BidAskModel::timeInfoArrived);

    DataProvider::getInstance()->startStockTick();
    DataProvider::getInstance()->startBidAskTick();
    DataProvider::getInstance()->startStockCodeListening();
    resetData();
}


BidAskModel::~BidAskModel() {}


void BidAskModel::timeInfoArrived(QDateTime dt) {
    if (!currentDateTime.isValid() || (!DataProvider::getInstance()->isSimulation() && currentDateTime != dt)) {
        currentDateTime = dt;
        resetData();
    }
}


void BidAskModel::resetData() {
    beginResetModel();
    mData.resetData();
    //mViType = 48; // not received
    mViPrices.clear();
    setTotalBidRemain(0);
    setTotalAskRemain(0);
    setYesterdayClose(0);
    setTodayOpen(0);
    setHighlight(-1);
    endResetModel();
}


void BidAskModel::setTotalBidRemain(uint br) {
    if (br != totalBidRemain) {
        totalBidRemain = br;
        emit totalBidRemainChanged();
    }
}


void BidAskModel::setTotalAskRemain(uint br) {
    if (br != totalAskRemain) {
        totalAskRemain = br;
        emit totalAskRemainChanged();
    }
}


int BidAskModel::getUpperViPrice() {
    if (mViPrices.count() != 2)
        return 0;
    
    return mViPrices[0];
}


int BidAskModel::getLowerViPrice() {
    if (mViPrices.count() != 2)
        return 0;
    
    return mViPrices[1];
}


void BidAskModel::setCurrentStock(QString code) {
    if (currentStockCode != code) {
        resetData();
        mIsKospi = DataProvider::getInstance()->isKospi(code);
        currentStockCode = code;
        if (currentDateTime.isValid()) {
            mViPrices = DataProvider::getInstance()->getViPrices(code);
            emit upperViPriceChanged();
            emit lowerViPriceChanged();
            qWarning() << "mViPrices : " << mViPrices;
        }
        qWarning() << "currentStock: " << currentStockCode;
    }
}


void BidAskModel::setTodayOpen(int tc) {
    if (mTodayOpen != tc) {
        mTodayOpen = tc;
        emit todayOpenChanged();
    }
}


void BidAskModel::setTodayHigh(int th) {
    if (mTodayHigh != th) {
        mTodayHigh = th;
        emit todayHighChanged();
    }
}


void BidAskModel::setYesterdayClose(int yc) {
    if (yesterdayClose != yc) {
        yesterdayClose = yc;
        emit yesterdayCloseChanged();
    }
}


void BidAskModel::sell_immediately(int percentage) {
    if (mData.getCurrentPrice() > 0) {
        DataProvider::getInstance()->sell(currentStockCode, mData.getCurrentPrice(), 0, percentage, OrderMethod::TRADE_IMMEDIATELY);
        qWarning() << "SELL IMMEDIATE ";
    }
}


void BidAskModel::buy_immediately(int percentage) {
    if (mData.getCurrentPrice() > 0) {
        DataProvider::getInstance()->buy(currentStockCode, mData.getCurrentPrice(), 0, percentage, OrderMethod::TRADE_IMMEDIATELY);
        qWarning() << "BUY IMMEDIATE";
    }
}


void BidAskModel::buy_on_price(int row, int percentage) {
    int buyPrice = mData.getPriceByRow(row - 1);
    qWarning() << "BUY ON PRICE : " << buyPrice;
    if (buyPrice > 0) {
        DataProvider::getInstance()->buy(currentStockCode, buyPrice, 0, percentage, OrderMethod::TRADE_ON_PRICE);
    }
}


void BidAskModel::sell_on_price(int row, int percentage) {
    int sellPrice = mData.getPriceByRow(row - 1);
    qWarning() << "SELL ON PRICE : " << sellPrice;
    if (sellPrice > 0) {
        DataProvider::getInstance()->sell(currentStockCode, sellPrice, 0, percentage, OrderMethod::TRADE_ON_PRICE);
    }
}



QVariant BidAskModel::data(const QModelIndex &index, int role) const
{
    if (index.row() >= BidAskModel::START_ROW && index.row() <= BidAskModel::STEPS * 2) {

        if (index.column() == BidAskModel::PRICE_COLUMN) {
            int price = mData.getPriceByRow(index.row() - 1);
            if (role == Qt::DisplayRole) {
                if (price != 0)
                    return QVariant(price);
            }
            else if (role == PROFIT_ROLE) {
                if (price != 0 && getYesterdayClose() != 0) {
                    return QVariant((price - getYesterdayClose()) / qreal(getYesterdayClose()) * 100.0);
                }
            }
            else if (role == VI_ROLE) {
                if (price != 0) {
                    if (mViPrices.count() > 0) {
                        if (mViPrices.contains(price))
                            return QVariant(true);
                    }
                }
                return QVariant(false);
            }
        }
        else if ((index.column() == BidAskModel::ASK_REMAIN_COLUMN && index.row() >= START_ROW && index.row () <= START_ROW + 9) || 
                (index.column() == BidAskModel::BID_REMAIN_COLUMN && index.row() >= START_ROW + 10 && index.row() <= START_ROW + 19)) {
            if (role == Qt::DisplayRole) {
                int remain = mData.getRemainByRow(index.row() - 1);
                if (remain != 0)
                    return QVariant(remain);
            }
            else if (role == VOLUME_DIFF_ROLE) {
                int diff = mData.getDiffByRow(index.row() - 1);
                if (diff != 0)
                    return QVariant(diff);
            }
        }
        else if (index.row() == highlight && index.column() == BidAskModel::ASK_REMAIN_COLUMN && !mData.getIsCurrentBuy() && mData.getCurrentPrice() != 0) {
            return QVariant(mData.getCurrentVolume());
        }
        else if (index.row() == highlight && index.column() == BidAskModel::BID_REMAIN_COLUMN && mData.getIsCurrentBuy() && mData.getCurrentPrice() != 0) {
            return QVariant(mData.getCurrentVolume());
        }
        else if (index.column() == 0 || index.column() == COLUMN_COUNT - 1) {
            bool isBuyCol = index.column() != 0;
            int price = mData.getPriceByRow(index.row() - 1);
            QList<int> list = mData.getVolumeByPrice(isBuyCol, price);
            if (list.count() == 0)
                return QVariant(QString());
            else
                return QVariant(QString::number(list[2]) + " / " + 
                        QString::number(list[1]) + " / " + QString::number(list[0]));
        }
    }
    else if (index.row() == 0 && (index.column() == 0 || index.column() == 6)) {
        return QVariant(mData.getBuyRate());
    }
    return QVariant(QString());
}


void BidAskModel::tickArrived(CybosTickData *data) {
    if (currentStockCode != QString::fromStdString(data->code())) {
        delete data;
        return;
    }

    /* Maybe cannot get vi prices at right time since vi plugin is calculating when request prices in here
    if (mViType == 48 || (data->market_type() == 50 && mViType == 49)) {
        mViPrices = DataProvider::getInstance()->getViPrices(currentStockCode);
        mViType = 50;
    }*/
    //long msec = TimeUtil::TimestampToMilliseconds(data->tick_date());
    //qWarning() << QDateTime::fromMSecsSinceEpoch(msec) << "\tcurrent: " << data->current_price() << ", volume: " << data->volume() << "\tBUY:" << data->buy_or_sell() << "\task: " << data->ask_price() << ", bid: " << data->bid_price();
    setYesterdayClose(data->current_price() - data->yesterday_diff());
    setTodayOpen(data->start_price());
    setTodayHigh(data->highest_price());
    setHighlightPosition(data->current_price());
    mData.setTick(data);
    /*
    if (data->market_type() == 49)
        mViType = 49;
    */

    dataChanged(createIndex(0, 0), createIndex(20, 8));
    delete data;
}


void BidAskModel::setHighlightPosition(int price) {
    int index = mData.getRowByPrice(price);
    setHighlight(index >= 0?index+1:index);
}


void BidAskModel::bidAskTickArrived(CybosBidAskTickData *data) {
    if (currentStockCode != QString::fromStdString(data->code())) {
        delete data;
        return;
    }

    mData.setBidAskTick(data);
    setTotalAskRemain(data->total_ask_remain());
    setTotalBidRemain(data->total_bid_remain()); 
    //setHighlight(-1);
    dataChanged(createIndex(1, 2), createIndex(20, 4));
    //long msec = TimeUtil::TimestampToMilliseconds(data->tick_date());
    //qWarning() << QDateTime::fromMSecsSinceEpoch(msec) << "\tASK: " << data->ask_prices(0) << "(" << data->ask_remains(0) << ")\t" << "BID: " << data->bid_prices(0) << "(" << data->bid_remains(0) << ")";
    delete data;
}


void BidAskModel::setHighlight(int row) {
    //qWarning() << "setHighlight: " << highlight << " to " << row;
    if (highlight != row) {
        highlight = row;
        emit highlightChanged();
    }
}
