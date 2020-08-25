#ifndef LENS_CHARTVIEW_H_
#define LENS_CHARTVIEW_H_

#include <QQuickPaintedItem>
#include <QPainter>
#include <QTransform>
#include <QPair>
#include <QWheelEvent>
#include "DataProvider.h"
#include "Candle.h"


class LensChartView : public QQuickPaintedItem {
    Q_OBJECT
    QML_ELEMENT
public:
    enum {
        ROW_COUNT = 13,
        PRICE_ROW_COUNT = 10,
        COLUMN_COUNT = 10,
        VOLUME_ROW_COUNT = 2,
        TIME_LABEL_ROW_COUNT = 1,
    };
    MorningTickChartView(QQuickItem *parent = 0);
    void paint(QPainter *painter);

    qreal mapPriceToPos(int price, qreal startY, qreal endY);

private:
    QString mCurrentStockCode;
    QList<int> mPriceSteps;
    QList<Candle> mCandles;
    Candle mCurrentCandle;

    uint currentVolumeMax;
    uint currentVolumeMin;
    QDateTime currentDateTime;

    void resetData();
    void calculateMinMaxRange();
    void setPriceSteps(int h, int l);
    void updatePriceSteps(int h, int l);
    void setVolumeMinMax(uint h, uint l);
    void updateVolumeMax(uint h);

    qreal getCandleLineWidth(qreal w);
    //qreal getTimeToXPos(uint time, qreal tickWidth, uint dataStartHour);
    qreal getTimeToXPos(uint t, qreal tickWidth, uint startTime);
    qreal getVolumeHeight(uint v, qreal ch);

    void drawGridLine(QPainter *painter, qreal cw, qreal ch);
    void drawCandle(QPainter *painter, const CybosDayData &data, qreal startX, qreal horizontalGridStep, qreal priceChartEndY);
    void drawVolume(QPainter *painter, const CybosDayData &data, qreal startX, qreal tickWidth, qreal ch, qreal volumeEndY);
    void drawTimeLabels(QPainter *painter, qreal tickWidth, qreal cw, qreal ch, qreal startX, int cellCount, uint startTime);
    void drawPriceLabels(QPainter *painter, qreal startX, qreal ch);
    void drawCurrentLineRange(QPainter *painter, MinuteTick * mt, qreal startX, const CybosDayData &data, qreal cw, qreal priceChartEndY);


private slots:
    void setCurrentStock(QString);
    void timeInfoArrived(QDateTime);
    void tickArrived(CybosTickData *data);
};

#endif
