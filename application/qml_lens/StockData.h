#ifndef STOCK_DATA_H_
#define STOCK_DATA_H_

#include "Candle.h"
#include "DataProvider.h"
#include <QPainter>

#include <google/protobuf/timestamp.pb.h>
using google::protobuf::Timestamp;

#define INTERVAL_MSEC   10000 // 10 sec
#define DISPLAY_MSEC    1800000 // 30 min, total 180 candle


class StockData {
public:
    enum {
        ROW_COUNT = 13,
        PRICE_ROW_COUNT = 10,
        COLUMN_COUNT = 31,
        VOLUME_ROW_COUNT = 2,
        PRICE_COLUMN_COUNT = 30,
    };

    StockData(const QString &code);

    void tickArrived(CybosTickData *data);

    const QString &currentRatio() {
        return mCurrentRatio;
    }
    const QString &currentAmount() {
        return mCurrentAmount;
    }

    const QString &openProfit() {
        return mOpenProfit;
    }

    const QString &corpName() {
        return mCorpName;
    }
    void paint(QPainter *painter, const QSizeF &canvasSize);


private:
    QList<Candle> mCandles;
    QList<qreal> mPriceSteps;

    Candle mCurrentCandle;
    qint64 mMaxVolume = 0;
    int mCurrentHighPrice = 0;
    int mCurrentLowPrice = 0;
    int mOpen = 0;
    int mYesterdayClose = 0;

    QString mCorpName;
    QString mCurrentAmount;
    QString mCurrentRatio;
    QString mOpenProfit;


private:
    void addCandle();
    void checkPriceRange(int price);
    void checkVolumeMax();
    QString uint64ToString(uint64_t amount) const;
    QDateTime timestampToQDateTime(const Timestamp &t);
    qreal getCandleLineWidth(qreal w);
    qreal mapPriceToPos(int price, qreal endY, qreal startY);
    qreal getVolumeHeight(qint64 volume, qreal volumeHeight);


    void drawCurrentPriceLine(QPainter *painter, int price, qreal fromX, qreal untilX, qreal startY, qreal endY, qreal cellWidth, qreal currentX);
    void drawCandle(QPainter *painter, const Candle &candle, qreal x, qreal candleWidth, qreal candleSpace, qreal startY, qreal endY);
    void drawVolume(QPainter *painter, const Candle &candle, qreal x, qreal volumeWidth, qreal startY, qreal endY);
    void displayLowHighText(QPainter *painter, qreal x, qreal cellWidth, qreal cellHeight, qreal startY, qreal endY);
    void displayOpenPriceLine(QPainter *painter, qreal x, qreal endX, qreal startY, qreal endY, qreal cellWidth);

    void drawAmountRatio(QPainter *painter, qreal startY, qreal endY, QList<QPair<qreal, qreal> > &list);
    void drawCurrentTime(QPainter *painter, const QDateTime & dt, qreal startX, qreal startY, qreal w, qreal h);
};

#endif