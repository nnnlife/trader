#ifndef LENS_CHARTVIEW_H_
#define LENS_CHARTVIEW_H_

#include <QQuickPaintedItem>
#include <QPainter>
#include <QTransform>
#include <QPair>
#include <QWheelEvent>
#include "DataProvider.h"
#include "Candle.h"

#include <google/protobuf/timestamp.pb.h>
using google::protobuf::Timestamp;

#define INTERVAL_MSEC   5000 // 5 sec
#define DISPLAY_MSEC    600000 // 10 min


class LensChartView : public QQuickPaintedItem {
    Q_OBJECT
    QML_ELEMENT
public:
    enum {
        ROW_COUNT = 13,
        PRICE_ROW_COUNT = 10,
        COLUMN_COUNT = 11,
        VOLUME_ROW_COUNT = 2,
        PRICE_COLUMN_COUNT = 1,
        TIME_LABEL_ROW_COUNT = 1,
    };
    LensChartView(QQuickItem *parent = 0);
    void paint(QPainter *painter);

    qreal mapPriceToPos(int price, qreal endY, qreal startY);
    qreal getVolumeHeight(qint64 volume, qreal volumeHeight);

private:
    QString mCurrentStockCode;
    QList<qreal> mPriceSteps;
    QList<Candle> mCandles;
    Candle mCurrentCandle;
    QDateTime mCurrentDateTime;
    QDateTime mTickBeginDateTime;
    qint64 mTickInterval = INTERVAL_MSEC;
    qint64 mMaxVolume = 0;

    void resetData();

    QDateTime timestampToQDateTime(const Timestamp &t);
    qreal getCandleLineWidth(qreal w);
    void checkVolumeMax();

    void checkPriceRange(int price);
    void drawGridLine(QPainter *painter, qreal cw, qreal ch);
    void drawCurrentPriceLine(QPainter *painter, int price, qreal fromX, qreal untilX, qreal startY, qreal endY);
    void drawCandle(QPainter *painter, const Candle &candle, qreal x, qreal candleWidth, qreal startY, qreal endY);
    void drawVolume(QPainter *painter, const Candle &candle, qreal x, qreal volumeWidth, qreal startY, qreal endY);

private slots:
    void setCurrentStock(QString);
    void timeInfoArrived(QDateTime);
    void tickArrived(CybosTickData *data);
};

#endif
