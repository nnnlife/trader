#ifndef CANDLE_H_
#define CANDLE_H_

#include <QObject>
#include <QDateTime>


class Candle {
public:
    Candle() {
    }

    void addTickData(int currentPrice, long long volume, const QDateTime &dt) {
        if (!mStartDateTime.isValid()) {
            mOpen = currentPrice;
            mStartDateTime = dt;
        }

        mClose = currentPrice;

        if (mLow == 0 || currentPrice < mLow)
            mLow = currentPrice;

        if (currentPrice > mHigh)
            mHigh = currentPrice;

        mVolume += volume;
    }

    bool isValid() const { return mStartDateTime.isValid(); }

    void clear() {
        mHigh = 0;
        mLow = 0;
        mOpen = 0;
        mVolume = 0;
        mClose = 0;
        mStartDateTime = QDateTime();
    }

    int high() const { return mHigh; }
    int open() const { return mOpen; }
    int close() const { return mClose; }
    int low() const { return mLow; }
    long long volume() const { return mVolume; }

private:
    int mClose = 0;
    int mHigh = 0;
    int mLow = 0;
    int mOpen = 0;
    long long mVolume = 0;
    QDateTime mStartDateTime;
};


#endif
