#ifndef CANDLE_H_
#define CANDLE_H_

#include <QObject>
#include <QDateTime>


class Candle {
public:
    Candle() {
    }

    void addTickData(int currentPrice, long long volume, bool isBuy, double amountRatio, bool isNormalPrice) {
        if (mOpen == 0)
            mOpen = currentPrice;

        mClose = currentPrice;
        mAmountRatio = amountRatio;
        if (mLow == 0 || currentPrice < mLow)
            mLow = currentPrice;

        if (currentPrice > mHigh)
            mHigh = currentPrice;

        if (isBuy)
            mBuyVolume += volume;
        else
            mSellVolume += volume;

        if (!isNormalPrice)
            mIsUniPrice = true;
        else if (mIsUniPrice && isNormalPrice) {
            mIsUniPrice = false;
        }

        mWasUniPrice = !isNormalPrice;
    }

    bool isValid() const { return mStartDateTime.isValid() && mOpen > 0; }

    void clear() {
        mHigh = mLow = mOpen = mClose = 0;
        mBuyVolume = mSellVolume = 0;
        mAmountRatio = 0.0;
        mStartDateTime = QDateTime();
        mIsUniPrice = false;
        // do not clear mWasUniPrice for finding new open after VI
    }

    int high() const { return mHigh; }
    int open() const { return mOpen; }
    int close() const { return mClose; }
    int low() const { return mLow; }
    bool buy_upper_hand() const { return mBuyVolume > mSellVolume; }
    bool is_uni_price() const { return mIsUniPrice; }
    bool was_uni_price() const { return mWasUniPrice; }
    double amount_ratio() const { return mAmountRatio; }
    long long volume() const { return mBuyVolume + mSellVolume; }
    const QDateTime & startDateTime() { return mStartDateTime; }

    void setStartDateTime(const QDateTime &dt) {
        mStartDateTime = dt;
    }

private:
    int mClose = 0;
    int mHigh = 0;
    int mLow = 0;
    int mOpen = 0;
    double mAmountRatio = 0.0;
    long long mBuyVolume = 0;
    long long mSellVolume = 0;
    bool mIsUniPrice = false;
    bool mWasUniPrice = false;
    QDateTime mStartDateTime;
};


#endif
