#include "BidAskData.h"
#include <QDebug>
#include <google/protobuf/util/time_util.h>
using google::protobuf::util::TimeUtil;


//#define BIDASK_DEBUG

int getBidUnit(bool isKospi, int price) {
    if (price < 1000)
        return 1;
    else if (price < 5000)
        return 5;
    else if (price < 10000)
        return 10;
    else if (price < 50000)
        return 50;

    if (isKospi) {
        if (price < 100000)
            return 100;
        else if (price < 500000)
            return 500;
        return 1000;
    }
    return 100;
}


BidAskData::BidAskData() {
    mBidAskTickReceived = false;
}


void BidAskData::resetData() {
    mBidAskTickReceived = false;
    mLowerViPrices.clear();
    mUpperViPrices.clear();
    mBidSpread.clear();
    mAskSpread.clear();
    mTradeUnit.clear();
}


int BidAskData::getRowByPrice(int price) const {
    for (int i = 0; i < mBidSpread.count(); i++) {
        if (mBidSpread[i].price() == price)
            return 10 + i;
    }
    for (int i = 0; i < mAskSpread.count(); i++) {
        if (mAskSpread[i].price() == price)
            return 9 - i;
    }
    return -1;
}


const BidAskUnit * BidAskData::getUnitByRow(int row) const {
    if (row >= 0 && row <= 9) { // ASK
        int index = 9 - row;
        if ( index < mAskSpread.count())
            return &mAskSpread.at(index);
    }
    else if (row >= 10 && row <= 19) {
        int index = row - 10;
        if ( index < mBidSpread.count())
            return &mBidSpread.at(index);
    }

    return nullptr;
}

int BidAskData::getPriceByRow(int row) const {
    const BidAskUnit * bau = getUnitByRow(row);
    if (bau != nullptr)
        return bau->price();
    return 0;
}


int BidAskData::getRemainByRow(int row) const {
    const BidAskUnit * bau = getUnitByRow(row);
    if (bau != nullptr)
        return bau->remain();
    return 0;
}


int BidAskData::getDiffByRow(int row) const {
    const BidAskUnit * bau = getUnitByRow(row);
    if (bau != nullptr)
        return bau->diff();
    return 0;
}


void BidAskData::setViPrices(int openPrice) {
    mLowerViPrices.clear();
    mUpperViPrices.clear();
    mLowerViPrices.append(qreal(openPrice) * 0.7); 
    mLowerViPrices.append(qreal(openPrice) * 0.8); 
    mLowerViPrices.append(qreal(openPrice) * 0.9); 
    mUpperViPrices.append(qreal(openPrice) * 1.1);
    mUpperViPrices.append(qreal(openPrice) * 1.2);
    mUpperViPrices.append(qreal(openPrice) * 1.3);
}


bool BidAskData::speculateIsViPrice(int price, bool isKospi) const {
    if (mLowerViPrices.count() > 0) {
        int unit = getBidUnit(isKospi, price);
        for (int i = 0; i < mUpperViPrices.count(); i++) {
            if (mUpperViPrices.at(i) > price && mUpperViPrices.at(i) <= price + unit)
                return true;
        }

        for (int i = 0; i < mLowerViPrices.count(); i++) {
            if (mLowerViPrices.at(i) < price && mLowerViPrices.at(i) > price - unit)
                return true;
        }
    }
    return false;
}


void BidAskData::setTick(CybosTickData *d) {
#ifdef BIDASK_DEBUG
    qWarning() << "Tick Arrived";
    debugTick(d);
    debugCurrentBidAsk();
#endif
    long msec = TimeUtil::TimestampToMilliseconds(d->tick_date());
    mTradeUnit.setData(d->current_price(), d->volume(), d->buy_or_sell(), QDateTime::fromMSecsSinceEpoch(msec));

    if (!mBidAskTickReceived) {
        if (mBidSpread.count() == 0) 
            mBidSpread.append(BidAskUnit(d->bid_price()));
        else {
            mBidSpread.clear();
            mBidSpread.append(BidAskUnit(d->bid_price()));
        }

        if (mAskSpread.count() == 0)
            mAskSpread.append(BidAskUnit(d->ask_price()));
        else {
            mAskSpread.clear();
            mAskSpread.append(BidAskUnit(d->ask_price()));
        }
    }
    else {
        if (mBidSpread.count() > 0 && mAskSpread.count() > 0) {
            if (mBidSpread[0].price() != d->bid_price()) {
                int index = -1;
                for (int i = 0; i < mBidSpread.count(); i++) {
                    if (mBidSpread[i].price() == d->bid_price()) {
                        index = i;
                        break;
                    }
                }

                if (index == -1) {
                    BidAskUnit bau(d->bid_price());
                    mBidSpread.insert(0, bau);
                }
                else {
                    for (int i = 0; i < index; i++)
                        mBidSpread.removeFirst();
                }
            }

            if (mAskSpread[0].price() != d->ask_price()) {
                int index = -1;
                for (int i = 0; i < mAskSpread.count(); i++) {
                    if (mAskSpread[i].price() == d->ask_price()) {
                        index = i;
                        break;
                    }
                }

                if (index == -1) {
                    BidAskUnit bau(d->ask_price());
                    mAskSpread.insert(0, bau);
                }
                else {
                    for (int i = 0; i < index; i++)
                        mAskSpread.removeFirst();
                }
            }
        }
        else {
            qWarning() << "BidAskData: Spread count is zero";
        }
    }
#ifdef BIDASK_DEBUG
    debugCurrentBidAsk();
#endif
}


void BidAskData::fillBidSpread(CybosBidAskTickData *d) {
    for (int i = 0; i < d->bid_prices_size(); i++)
        mBidSpread[i].setCurrentRemain(d->bid_remains(i));
}


void BidAskData::fillAskSpread(CybosBidAskTickData *d) {
    for (int i = 0; i < d->ask_prices_size(); i++)
        mAskSpread[i].setCurrentRemain(d->ask_remains(i));
}


void BidAskData::setBidAskTick(CybosBidAskTickData *d) {
#ifdef BIDASK_DEBUG
    qWarning() << "BidAskTick Arrived";
    debugBidAskTick(d);
    debugCurrentBidAsk();
#endif
    mBidAskTickReceived = true;
    if (checkPriceOrder(true, d)) //BID
        fillBidSpread(d);
    else {
        //qWarning() << "updateBidSpread";
        updateBidSpread(d);
    }

    if (checkPriceOrder(false, d))
        fillAskSpread(d);
    else {
        //qWarning() << "updateAskSpread";
        updateAskSpread(d);
    }
#ifdef BIDASK_DEBUG
    debugCurrentBidAsk();
#endif
}


bool BidAskData::checkPriceOrder(bool bid, CybosBidAskTickData *d) {
    if (bid) {
        if (d->bid_prices_size() != mBidSpread.count())
            return false;

        for (int i = 0; i < d->bid_prices_size(); i++) {
            if (d->bid_prices(i) != mBidSpread[i].price())
                return false;
        }
        return true;
    }

    if (d->ask_prices_size() != mAskSpread.count())
        return false;

    for (int i = 0; i < d->ask_prices_size(); i++) {
        if (d->ask_prices(i) != mAskSpread[i].price())
            return false;
    }
    return true;
}


void BidAskData::updateBidSpread(CybosBidAskTickData *d) {
    for (int i = 0; i < d->bid_prices_size(); i++) {
        int price = d->bid_prices(i);
        if (price == 0)
            continue;

        int remain = d->bid_remains(i);
        bool found = false;
        int index = mBidSpread.count();
        for (int j = 0; j < mBidSpread.count(); j++) {
            if (price > mBidSpread[j].price() && index == mBidSpread.count())
                index = j;

            if (mBidSpread[j].price() == price) {
                found = true;
                mBidSpread[j].setCurrentRemain(remain);
            }
        }

        if (!found) {
            BidAskUnit bau(price);
            bau.setCurrentRemain(remain);
            mBidSpread.insert(index, bau);
        }
    }

    QMutableListIterator<BidAskUnit> it(mBidSpread);
    while (it.hasNext()) {
        int price = it.next().price();
        bool found = false;
        for (int i = 0; i < d->bid_prices_size(); i++) {
            if (price == d->bid_prices(i)) {
                found = true;
                break;
            }
        }

        if (!found)
            it.remove();
    }
}


void BidAskData::updateAskSpread(CybosBidAskTickData *d) {
    for (int i = 0; i < d->ask_prices_size(); i++) {
        int price = d->ask_prices(i);
        if (price == 0)
            continue;

        int remain = d->ask_remains(i);
        bool found = false;
        int index = mAskSpread.count();
        for (int j = 0; j < mAskSpread.count(); j++) {
            if (price < mAskSpread[j].price() && index == mAskSpread.count())
                index = j;

            if (mAskSpread[j].price() == price) {
                found = true;
                mAskSpread[j].setCurrentRemain(remain);
            }
        }

        if (!found) {
            BidAskUnit bau(price);
            bau.setCurrentRemain(remain);
            mAskSpread.insert(index, bau);
        }
    }

    QMutableListIterator<BidAskUnit> it(mAskSpread);
    while (it.hasNext()) {
        int price = it.next().price();
        //qWarning() << "price: " << price;
        bool found = false;
        for (int i = 0; i < d->ask_prices_size(); i++) {
            if (price == d->ask_prices(i)) {
                found = true;
                break;
            }
        }

        if (!found)
            it.remove();
    }
}


void BidAskData::debugBidAskTick(CybosBidAskTickData *d) {
    std::cout << "DEBUG) BidAskTick ask ";
    for (int i = 0; i < d->ask_prices_size(); i++) {
        std::cout << d->ask_prices(i) << "(" << d->ask_remains(i) << ") ";
    }
    std::cout << std::endl;
    std::cout << "bid ";
    for (int i = 0; i < d->bid_prices_size(); i++) {
        std::cout << d->bid_prices(i) << "(" << d->bid_remains(i) << ") ";
    }
    std::cout << std::endl;
}


void BidAskData::debugTick(CybosTickData *d) {
    std::cout << "DEBUG) tick price " << d->current_price() << " ask(" << d->ask_price() << ") bid(" << d->bid_price() << ")" << std::endl;
}


void BidAskData::debugCurrentBidAsk() {
    std::cout << "DEBUG) current spread ask ";
    for (int i = 0; i < mAskSpread.count(); i++) {
        std::cout << mAskSpread.at(i).price() << "(" << mAskSpread.at(i).remain() << ", " << mAskSpread.at(i).diff() << ") ";
    }
    std::cout << std::endl;
    std::cout << "bid ";
    for (int i = 0; i < mBidSpread.count(); i++) {
        std::cout << mBidSpread.at(i).price() << "(" << mBidSpread.at(i).remain() << ", " << mBidSpread.at(i).diff() << ") ";
    }
    std::cout << std::endl;
}
