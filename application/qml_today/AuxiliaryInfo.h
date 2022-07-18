#ifndef AUXILIARY_INFO_H_
#define AUXILIARY_INFO_H_

#include <QObject>
#include <QList>
#include <QPainter>


class MorningTickChartView;

class AuxiliaryInfo {
public:
    AuxiliaryInfo(MorningTickChartView *v);

    void addPriceWithXAxis(qreal x, int c, int h);
    void drawAverageLine(QPainter *painter, qreal endY, int count=20);
    void drawCandleSelection(QPainter *painter, qreal startX, qreal endX, qreal endY);

private:
    class TimePrice {
    public:
        TimePrice(qreal x, int c, int h) {
            xPos = x;
            close = c;
            highest = h;
        }

        qreal xPos;
        int close;
        int highest;
    };

    QList<TimePrice> timePriceList;
    MorningTickChartView *mtcv;
};

#endif
