#ifndef VOLUME_PRICE_CHARTVIEW_H_
#define VOLUME_PRICE_CHARTVIEW_H_

#include <QQuickPaintedItem>
#include <QPainter>
#include "DataProvider.h"


class VolumePriceChartView : public QQuickPaintedItem {
    Q_OBJECT
    QML_ELEMENT
public:
    enum {
        ROW_COUNT = 12,
        COLUMN_COUNT = 9
    };
    VolumePriceChartView(QQuickItem *parent = 0);
    void paint(QPainter *painter);
    void drawGridLine(QPainter * painter, qreal cw, qreal ch);
    void drawTimeLabel(QPainter *painter, qreal cw, qreal ch);

private:
    int startHour;
    QString currentStockCode;
    int yesterdayClose;
    int currentPriceStep;
    uint currentMinVolume;
    uint currentMaxVolume;

    void resetData();
    bool isTimeout(long secs);
    QList<QPair<long,uint> > buyCumVolumes;
    QList<QPair<long,uint> > sellCumVolumes;
    QList<QPair<long,uint> > currentBuyCumVolume;
    QList<QPair<long,uint> > currentSellCumVolume;
    QList<QPair<long,int> > currentPrices;
    QString numberToShortString(uint number);

    void checkYBoundary(bool isRefresh, uint buy, uint sell);
    void checkPriceBoundary(int price);

    int getDateTimeToSec(uint date, uint time);
    qreal convertTimeToXPos(long sec, qreal cw);
    qreal convertValueToYPos(uint volume, qreal ch);
    qreal convertPriceToYPos(int price, qreal ch);

private:
    void drawPercentageLine(QPainter *painter, qreal cw, qreal ch);
    void drawPrice(QPainter *painter, qreal cw, qreal ch);

    void drawVolume(QPainter *painter, qreal cellWidth, qreal cellHeight);
    void drawVolumePolygon(QPainter * painter, bool buyStrong, QPolygonF & polygon);

    void drawCurrentLine(QPainter *painter, uint volume, long sec, bool buyStrong, qreal cw, qreal ch, uint ovolume);

private slots:
    void minuteTickUpdated(QString);
    void setCurrentStock(QString);
};

#endif
