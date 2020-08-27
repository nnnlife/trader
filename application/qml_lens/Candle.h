#ifndef CANDLE_H_
#define CANDLE_H_

#include <QObject>
#include <QDateTime>


class Candle {
public:
    Candle() {
    }

    void addTickData(int currentPrice, long long volume, bool isBuy, const QDateTime &dt) {
        if (!mStartDateTime.isValid()) {
            mOpen = currentPrice;
            mStartDateTime = dt;
        }

        mClose = currentPrice;

        if (mLow == 0 || currentPrice < mLow)
            mLow = currentPrice;

        if (currentPrice > mHigh)
            mHigh = currentPrice;

        if (isBuy)
            mBuyVolume += volume;
        else
            mSellVolume += volume;
    }

    bool isValid() const { return mStartDateTime.isValid(); }

    void clear() {
        mHigh = mLow = mOpen = mClose = 0;
        mBuyVolume = mSellVolume = 0;
        mStartDateTime = QDateTime();
    }

    int high() const { return mHigh; }
    int open() const { return mOpen; }
    int close() const { return mClose; }
    int low() const { return mLow; }
    bool buy_upper_hand() const { return mBuyVolume > mSellVolume; }
    long long volume() const { return mBuyVolume + mSellVolume; }

private:
    int mClose = 0;
    int mHigh = 0;
    int mLow = 0;
    int mOpen = 0;
    long long mBuyVolume = 0;
    long long mSellVolume = 0;
    QDateTime mStartDateTime;
};


#endif
