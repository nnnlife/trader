#ifndef BIDASK_DATA_H_
#define BIDASK_DATA_H_


#include <QList>
#include <iostream>
#include <QMap>
#include <QPair>
#include <QDateTime>
#include <QDebug>


#include "stock_provider.grpc.pb.h"
using stock_api::CybosBidAskTickData;
using stock_api::CybosTickData;


#define SUSTAIN_TIME_MSECS  30000

class BidAskUnit {
public:
    BidAskUnit(int price) {
        mPrice = price;
        mRemain = mDiff = 0;
    }

    int price() const { return mPrice; }
    int remain() const { return mRemain; }
    int diff() const { return mDiff; }
    void setCurrentRemain(int current) {
        if (remain() == 0)
            mRemain = current;
        else {
            mDiff = current - remain();
        }
    }

private:
    int mPrice;
    int mRemain;
    int mDiff;
};



class TradeUnit {
public:
    TradeUnit() {
        clear();
    }

    int volume() const { return mVolume; }
    int price() const { return mPrice; }
    bool isBuy() const { return mIsBuy; }

    void setData(int price, int vol, bool isBuy, const QDateTime &dt) {
        mPrice = price;
        mVolume = vol;
        mIsBuy = isBuy;

        if (isBuy) {
            QMapIterator<int, QPair<QDateTime, QList<int> > > it(mBuyMap);
            while (it.hasNext()) {
                it.next();
                if (dt.toMSecsSinceEpoch() - it.value().first.toMSecsSinceEpoch() > SUSTAIN_TIME_MSECS) {
                    mBuyMap.remove(it.key());
                }
            }

            if (!mBuyMap.contains(price)) {
                mBuyMap[price].first = dt;
                mBuyMap[price].second = QList({0, 0, 0});
            }
        
            mBuyMap[price].first = dt;
            if (price * vol >= 100000000)
                mBuyMap[price].second[2] += 1;
            else if (price * vol >= 50000000)
                mBuyMap[price].second[1] += 1;
            else if (price * vol >= 10000000)
                mBuyMap[price].second[0] += 1;

            mTotalBuy += (unsigned long long)vol;
        }
        else {
            QMapIterator<int, QPair<QDateTime, QList<int> > > it(mSellMap);
            while (it.hasNext()) {
                it.next();
                if (dt.toMSecsSinceEpoch() - it.value().first.toMSecsSinceEpoch() > SUSTAIN_TIME_MSECS) {
                    mSellMap.remove(it.key());
                }
            }
            if (!mSellMap.contains(price)) {
                mSellMap[price].first = dt;
                mSellMap[price].second = QList({0, 0, 0});
            }

            mSellMap[price].first = dt;
            if (price * vol >= 100000000)
                mSellMap[price].second[2] += 1;
            else if (price * vol >= 50000000)
                mSellMap[price].second[1] += 1;
            else if (price * vol >= 10000000)
                mSellMap[price].second[0] += 1;
            
            mTotalSell += (unsigned long long)vol;
        }
    }
    void setPrice(int p) { mPrice = p; }
    void setVolume(int v) { mVolume = v; }
    void setIsBuy(bool b) { mIsBuy = b; }
    qreal getBuyRate() const {
        return mTotalBuy / float(mTotalBuy + mTotalSell);
    }

    QList<int> getVolumeByPrice(bool isBuy, int price) const {
        if (isBuy) {
            if (mBuyMap.contains(price))
                return mBuyMap[price].second;
        }
        else {
            if (mSellMap.contains(price))
                return mSellMap[price].second;
        }
        return QList<int>();
    }

    QMap<int, QPair<QDateTime, QList<int> > > mBuyMap;
    QMap<int, QPair<QDateTime, QList<int> > > mSellMap;

    void clear() {
        mPrice = mVolume = 0;
        mTotalBuy = mTotalSell = 0;
        mIsBuy = false;
        mBuyMap.clear();
        mSellMap.clear();
    }

private:
    bool mIsBuy;
    int mPrice;
    int mVolume;
    unsigned long long mTotalBuy;
    unsigned long long mTotalSell;
};


class BidAskData {
public:
    BidAskData();

    void setTick(CybosTickData *d);
    void setBidAskTick(CybosBidAskTickData *d);
    void resetData();
    int getPriceByRow(int row) const;
    int getRemainByRow(int row) const;
    int getDiffByRow(int row) const;
    int getRowByPrice(int price) const;
    int getCurrentPrice() const { return mTradeUnit.price(); } 
    bool getIsCurrentBuy() const { return mTradeUnit.isBuy(); }
    int getCurrentVolume() const { return mTradeUnit.volume(); }
    QList<int> getVolumeByPrice(bool isBuy, int price) const { return mTradeUnit.getVolumeByPrice(isBuy, price); }
    qreal getBuyRate() const { return mTradeUnit.getBuyRate(); }
    bool speculateIsViPrice(int price, bool isKospi) const;

private:
    QList<BidAskUnit> mBidSpread;
    QList<BidAskUnit> mAskSpread;
    TradeUnit mTradeUnit;

    bool mBidAskTickReceived;
    QList<qreal> mLowerViPrices;
    QList<qreal> mUpperViPrices;

    const BidAskUnit *getUnitByRow(int row) const;
    void fillBidSpread(CybosBidAskTickData *);
    void fillAskSpread(CybosBidAskTickData *d);
    void updateAskSpread(CybosBidAskTickData *d);
    void updateBidSpread(CybosBidAskTickData *d);

    void setViPrices(int openPrice);
private:
    bool checkPriceOrder(bool bid, CybosBidAskTickData *);


    void debugBidAskTick(CybosBidAskTickData *d);
    void debugTick(CybosTickData *d);

    void debugCurrentBidAsk();
};



#endif
