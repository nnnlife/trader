#include "VolumePriceChartView.h"
#include "MinuteData.h"
#include <QStringList>
#include <QDebug>



VolumePriceChartView::VolumePriceChartView(QQuickItem *parent)
: QQuickPaintedItem(parent) {
    startHour = 9;
    connect(DataProvider::getInstance(), &DataProvider::minuteTickUpdated,
            this, &VolumePriceChartView::minuteTickUpdated);
    connect(DataProvider::getInstance(), &DataProvider::stockCodeChanged,
            this, &VolumePriceChartView::setCurrentStock);

    DataProvider::getInstance()->collectMinuteData();
    DataProvider::getInstance()->startStockCodeListening();
    DataProvider::getInstance()->startStockTick();
    resetData();
}


void VolumePriceChartView::resetData() {
    buyCumVolumes.clear();
    sellCumVolumes.clear();
    yesterdayClose = 0;
    currentPriceStep = 0;
    currentPrices.clear();
    currentBuyCumVolume.clear();
    currentSellCumVolume.clear();
    currentMaxVolume = currentMinVolume = 0;
}


void VolumePriceChartView::checkPriceBoundary(int price) {
    if (yesterdayClose == 0)
        return;

    while (1) {
        qreal priceStep = yesterdayClose * (0.05 * currentPriceStep);
        qreal upperPrice = yesterdayClose + priceStep;
        qreal lowerPrice = yesterdayClose - priceStep;

        if ((qreal)price < lowerPrice || (qreal)price > upperPrice)
            currentPriceStep += 1;
        else
            break;
    }
}


QString VolumePriceChartView::numberToShortString(uint number) {
    QStringList unitString;
    unitString << "" << "K" << "M" << "B";    
    QList<uint> unit = {1, 1000, 1000000, 1000000000};
    for (int i = 0; i < unitString.count(); ++i) {
        if (number < unit.at(i) * 1000) {
            return QString::number((double)number / unit.at(i), 'f', 1) + unitString.at(i);
        }
    }
    return QString();
}


void VolumePriceChartView::setCurrentStock(QString code) {
    if (currentStockCode != code) {
        resetData();
        currentStockCode = code;
        qWarning() << "currentStock: " << currentStockCode;
    }
}


void VolumePriceChartView::checkYBoundary(bool isRefresh, uint buy, uint sell) {
    uint min = (buy > sell)? sell:buy;
    uint max = (buy > sell)? buy:sell;

    if (currentMinVolume == 0)
        currentMinVolume = min;

    if (isRefresh) {
        if (min < currentMinVolume)
            currentMinVolume = min;

        if (currentMaxVolume == 0) {
            if (max * 2 > currentMaxVolume)
                currentMaxVolume = max * 2;
        }
        else {
            if (max > currentMaxVolume)
                currentMaxVolume = max * 2;
        }
        //qWarning() << "min max " << currentMinVolume << ", " << currentMaxVolume << "(" << max << ")";
    }
    else {
        if (min < currentMinVolume)
            currentMinVolume = min;

        if (max > currentMaxVolume) {
            qWarning() << "current max : " << currentMaxVolume << ", current: " << max;
            currentMaxVolume = max * 2;
        }
    }
    //qWarning() << "Boundary : " << currentMinVolume << ", " << currentMaxVolume;
}


int VolumePriceChartView::getDateTimeToSec(uint date, uint time) {
    Q_UNUSED(date);
    QTime startTime = QTime(startHour, 0, 0);
    QTime dataTime = QTime(int(time / 100), int(time % 100), 0);
    int diff = dataTime.msecsSinceStartOfDay() - startTime.msecsSinceStartOfDay();
    return (diff / 1000);
}


qreal VolumePriceChartView::convertTimeToXPos(long sec, qreal cw) {
    qreal totalWidth = cw * (COLUMN_COUNT - 2);
    qreal totalSec = (COLUMN_COUNT - 2) * 60 * 60;
    return cw + totalWidth * sec / totalSec;
}


qreal VolumePriceChartView::convertValueToYPos(uint volume, qreal ch) {
    qreal totalHeight = ch * (VolumePriceChartView::ROW_COUNT - 2);
    qreal valueGap = currentMaxVolume - currentMinVolume;
    qreal volumeHeight = totalHeight * (volume - currentMinVolume) / valueGap;
    qreal result = totalHeight - volumeHeight;

    //qWarning() << "gap: " << (uint)valueGap << ", h: " << totalHeight << " volume : " << volume << " pos : " << volumeHeight << " currentMin: " << currentMinVolume << " currentMax: " << currentMaxVolume ;
    return result;
}


void VolumePriceChartView::minuteTickUpdated(QString code) {
    if (currentStockCode != code)
        return;

    bool isRefresh = (buyCumVolumes.count() == 0);

    currentBuyCumVolume.clear();
    currentSellCumVolume.clear();
    currentPrices.clear();

    MinuteTick *mt = DataProvider::getInstance()->getMinuteTick(currentStockCode);
    const CybosDayDatas &queue = mt->getQueue();
    yesterdayClose = mt->getYesterdayClose();

    for (int i = buyCumVolumes.count(); i < queue.day_data_size(); i++) {
        const CybosDayData &d = queue.day_data(i);
        buyCumVolumes.append(QPair<long,uint>(getDateTimeToSec(d.date(), d.time()), d.cum_buy_volume()));
        sellCumVolumes.append(QPair<long,uint>(getDateTimeToSec(d.date(), d.time()), d.cum_sell_volume()));
        checkYBoundary(isRefresh, d.cum_buy_volume(), d.cum_sell_volume());
    }

    for (int i = 0; i < queue.day_data_size(); i++) {
        const CybosDayData &d = queue.day_data(i);
        currentPrices.append(QPair<long,int>(getDateTimeToSec(d.date(), d.time()), d.close_price()));
        checkPriceBoundary(d.close_price());
    }

    if (mt->getCurrent().start_price() != 0) {
        const CybosDayData &d = mt->getCurrent();
        /*
        if (d.cum_buy_volume() < d.cum_sell_volume())
            qWarning() << "reverse : " << d.time();
        */

        currentBuyCumVolume.append(QPair<long,uint>(getDateTimeToSec(d.date(), d.time()), d.cum_buy_volume()));
        currentSellCumVolume.append(QPair<long,uint>(getDateTimeToSec(d.date(), d.time()), d.cum_sell_volume()));
        currentPrices.append(QPair<long,int>(getDateTimeToSec(d.date(), d.time()), d.close_price()));
        checkYBoundary(isRefresh, d.cum_buy_volume(), d.cum_sell_volume());
        checkPriceBoundary(d.close_price());
    }

    update();
}


void VolumePriceChartView::drawGridLine(QPainter *painter, qreal cw, qreal ch) {
    painter->save();
    QPen pen = painter->pen();
    pen.setWidth(1);
    pen.setColor(QColor("#d7d7d7"));
    painter->setPen(pen);
  
    for (int i = 0; i < (VolumePriceChartView::ROW_COUNT - 2) / 2; i++) {
        QLineF line(cw, ch * 2 * (i+1), (cw) * 8, ch * 2 * (i+1));
        painter->drawLine(line); 
    }

    for (int i = 0; i < (VolumePriceChartView::COLUMN_COUNT - 1); i++) {
        QLineF line(cw * (i+1), 0, cw *(i+1), ch * (VolumePriceChartView::ROW_COUNT -2 ));
        painter->drawLine(line);
    }
    painter->restore(); 
}


void VolumePriceChartView::drawTimeLabel(QPainter *painter, qreal cw, qreal ch) {
    painter->save();

    for (int i = 0; i < (VolumePriceChartView::COLUMN_COUNT - 1); i++) {
        QRectF textBox(cw * (i + 1) - cw / 2, ch * (VolumePriceChartView::ROW_COUNT -2 ) + ch / 5, cw, ch);
        painter->drawText(textBox, Qt::AlignCenter, QString::number(i+startHour));
    }

    painter->restore();
}


void VolumePriceChartView::drawVolumePolygon(QPainter *painter, bool buyStrong, QPolygonF & polygon) {
    painter->save();
    QColor color;
    color = buyStrong? "#50ff0000" : "#500000ff";
    painter->setPen(QPen(color));
    painter->setBrush(QBrush(color));

    QPolygonF p;
    for (int i = 0; i < polygon.count(); i += 2) 
        p << polygon.at(i);        

    for (int i = polygon.count() - 1; i >= 1; i -= 2)
        p << polygon.at(i);

    painter->drawPolygon(p);

    painter->restore();
}


void VolumePriceChartView::drawCurrentLine(QPainter *painter, uint volume, long sec, bool buyStrong, qreal cw, qreal ch, uint ovolume) {
    painter->save();
    QPen pen;
    if (buyStrong)
        pen.setColor("#ff0000");
    else
        pen.setColor("#0000ff");
    pen.setWidth(1);
    pen.setStyle(Qt::DashLine);
    painter->setPen(pen);

    qreal t = convertTimeToXPos(sec, cw);

    qreal yPos = convertValueToYPos(volume, ch);
    painter->drawLine(QLineF(0.0, yPos, cw * (COLUMN_COUNT - 1), yPos));
    if (volume > ovolume) {
        painter->drawText(QRectF(t + cw / 5, yPos - ch / 3, cw * 2, ch / 4), Qt::AlignLeft | Qt::AlignVCenter, numberToShortString(volume));
        pen.setColor(Qt::black);
        painter->setPen(pen);
        qreal ratio = (qreal)volume / (volume + ovolume) * 100.;
        qreal oratio = (qreal)ovolume / (volume + ovolume) * 100.;
        painter->drawText(QRectF(cw * (COLUMN_COUNT - 1), yPos - ch / 4, cw, ch / 2), Qt::AlignCenter,
            QString::number((int)ratio) + QString(":") + QString::number((int)oratio));
    }
    else {
        painter->drawText(QRectF(t + cw / 5, yPos + ch / 4, cw * 2, ch / 4), Qt::AlignLeft | Qt::AlignVCenter, numberToShortString(volume));
    }

    painter->restore();
}


void VolumePriceChartView::drawVolume(QPainter *painter, qreal cellWidth, qreal cellHeight) {
    bool buyStrong = false;
    QPolygonF polygon;
    QList<QPair<long,uint> > buyC = buyCumVolumes + currentBuyCumVolume;
    QList<QPair<long,uint> > sellC = sellCumVolumes + currentSellCumVolume;
    for (int i = 0; i < buyC.count(); i++) {
        if (i == 0) {
            if (buyC.at(i).second >= sellC.at(i).second)
                buyStrong = true;
            else
                buyStrong = false;
        }
        if ((buyStrong && buyC.at(i).second < sellC.at(i).second ) ||
                (!buyStrong && buyC.at(i).second >= sellC.at(i).second)) {
            drawVolumePolygon(painter, buyStrong, polygon);
            buyStrong = !buyStrong;
            polygon.clear();
        }

        QPointF buyP = QPointF(convertTimeToXPos(buyC.at(i).first, cellWidth), convertValueToYPos(buyC.at(i).second, cellHeight));
        QPointF sellP = QPointF(convertTimeToXPos(sellC.at(i).first, cellWidth), convertValueToYPos(sellC.at(i).second, cellHeight));

        polygon << buyP << sellP;

        if (i == buyC.count() - 1) {
            drawVolumePolygon(painter, buyStrong, polygon);
            drawCurrentLine(painter, buyC.at(i).second, buyC.at(i).first, true, cellWidth, cellHeight, sellC.at(i).second);
            drawCurrentLine(painter, sellC.at(i).second, sellC.at(i).first, false, cellWidth, cellHeight, buyC.at(i).second);
        }
    }
}


qreal VolumePriceChartView::convertPriceToYPos(int price, qreal ch) {
    qreal minPrice = yesterdayClose - yesterdayClose * 0.05 * currentPriceStep;
    qreal maxPrice = yesterdayClose + yesterdayClose * 0.05 * currentPriceStep;
    qreal priceGap = maxPrice - minPrice;
    qreal height = ch * (ROW_COUNT - 2);
    return height - (price - minPrice) / priceGap * height;
}


void VolumePriceChartView::drawPrice(QPainter *painter, qreal cw, qreal ch) {
    painter->save();
    QPolygonF p;
    QPen pen;
    pen.setWidth(2);
    for (int i = 0; i < currentPrices.count(); i++) {
        qreal xPos = convertTimeToXPos(currentPrices.at(i).first, cw);
        qreal yPos = convertPriceToYPos(currentPrices.at(i).second, ch);
        //qWarning() << "x: " << xPos << "y: " << yPos << ", height: " << height << ", ratioHeight: " << (currentPrices.at(i).second - minPrice) / priceGap * height << ", yesterday: " << yesterdayClose;
        //qWarning() << "(" << i << ") " << "x : " << xPos << ", y: " << yPos;
        p << QPointF(xPos, yPos);  

        if (i == currentPrices.count() - 1) {
            if (currentPrices.at(i).second >= yesterdayClose)
                pen.setColor(Qt::red);
            else
                pen.setColor(Qt::blue);
        }
    }
    painter->setPen(pen);
    painter->drawPolyline(p);
    painter->restore();
}


void VolumePriceChartView::drawPercentageLine(QPainter *painter, qreal cw, qreal ch) {
    painter->save();

    QPen pen;
    pen.setWidth(1);
    pen.setColor(QColor("#80000000"));
    painter->setPen(pen);
    painter->drawLine(QLineF(cw, ch * (ROW_COUNT - 2) / 2, cw * (COLUMN_COUNT - 1), ch * (ROW_COUNT - 2) / 2));

    if (currentPriceStep > 1) {
        qreal fivePer = yesterdayClose * 0.05;
        for (int i = 0; i < currentPriceStep - 1; i++) {
            qreal bottomY = convertPriceToYPos(yesterdayClose - (i+1) * fivePer, ch);
            qreal upperY = convertPriceToYPos(yesterdayClose + (i+1) * fivePer, ch);
            pen.setColor(QColor("#80ff0000"));
            painter->setPen(pen);
            painter->drawLine(QLineF(cw, upperY, cw * (COLUMN_COUNT - 1), upperY));
            pen.setColor(QColor("#800000ff"));
            painter->setPen(pen);
            painter->drawLine(QLineF(cw, bottomY, cw * (COLUMN_COUNT - 1), bottomY));
        }
    }
    painter->restore(); 
}


void VolumePriceChartView::paint(QPainter *painter) {
    painter->setRenderHint(QPainter::Antialiasing);
    QSizeF canvasSize = size();
    qreal cellHeight = canvasSize.height() / ROW_COUNT;
    qreal cellWidth = canvasSize.width() / COLUMN_COUNT;
    drawGridLine(painter, cellWidth, cellHeight);
    drawTimeLabel(painter, cellWidth, cellHeight);
    if (yesterdayClose != 0) {
        drawPercentageLine(painter, cellWidth, cellHeight);
        drawPrice(painter, cellWidth, cellHeight);
    }
    drawVolume(painter, cellWidth, cellHeight);
}
