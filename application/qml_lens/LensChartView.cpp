#include "LensChartView.h"
#include <QDebug>

#include <google/protobuf/util/time_util.h>
using google::protobuf::util::TimeUtil;

#define TICK_SPACE_RATIO    (3.0/4.0)


LensChartView::LensChartView(QQuickItem *parent)
: QQuickPaintedItem(parent) {
    setAntialiasing(true);
    //setAcceptedMouseButtons(Qt::AllButtons);
    connect(DataProvider::getInstance(), &DataProvider::stockCodeChanged,
            this, &LensChartView::setCurrentStock);
    connect(DataProvider::getInstance(), &DataProvider::tickArrived, this, &LensChartView::tickArrived);
    connect(DataProvider::getInstance(), &DataProvider::timeInfoArrived, this, &LensChartView::timeInfoArrived);

    DataProvider::getInstance()->startStockCodeListening();
    DataProvider::getInstance()->startStockTick();
}


QDateTime LensChartView::timestampToQDateTime(const Timestamp &t) {
    long msec = TimeUtil::TimestampToMilliseconds(t);
    return QDateTime::fromMSecsSinceEpoch(msec);
}


void LensChartView::tickArrived(CybosTickData *data) {
    QDateTime dt = timestampToQDateTime(data->tick_date());
    bool isUpdate = false;

    if (!mTickBeginDateTime.isValid()) {
        mTickBeginDateTime = dt;
    }

    if ( mTickInterval > DISPLAY_MSEC) { // 10 min
        resetData();
        update();
        return;
    }
    else if (dt.toMSecsSinceEpoch() - mTickBeginDateTime.toMSecsSinceEpoch() > mTickInterval) {
        if (mCurrentCandle.isValid()) {
            mCandles.append(mCurrentCandle);
            mCurrentCandle.clear();
        }
        else {
            mCandles.append(Candle());
        }
        mTickInterval += INTERVAL_MSEC;
        isUpdate = true;
    }


    if (QString::fromStdString(data->code()) == mCurrentStockCode) {
        mOpen = data->start_price();
        mCurrentCandle.addTickData(data->current_price(),
                                   data->volume(), data->buy_or_sell(), dt);
        isUpdate = true;
        checkPriceRange(data->current_price());
        checkVolumeMax();
    }

    if (isUpdate)
        update();
}


void LensChartView::checkVolumeMax() {
    qint64 currentMax = 0;
    for (int i = 0; i < mCandles.count(); i++) {
        if (mCandles[i].isValid() && mCandles[i].volume() > currentMax)
            currentMax = mCandles[i].volume();
    }

    if (mCurrentCandle.isValid() && mCurrentCandle.volume() > currentMax)
        currentMax = mCurrentCandle.volume();

    if (currentMax > mMaxVolume)
        mMaxVolume = currentMax;
}


void LensChartView::checkPriceRange(int price) {
    qreal p = (qreal)price;

    if (price > mCurrentHighPrice)
        mCurrentHighPrice = price;

    if (mCurrentLowPrice == 0 || mCurrentLowPrice > price)
        mCurrentLowPrice = price;

    if (mPriceSteps.count() == 0 || (p < mPriceSteps.at(1) || p > mPriceSteps.at(2))) {
        mPriceSteps.clear();
        int minPrice = 0;
        int maxPrice = 0;

        for (int i = 0; i < mCandles.count(); i++) {
            if (mCandles[i].isValid()) {
                if (mCandles[i].high() > maxPrice)
                    maxPrice = mCandles[i].high();

                if (minPrice == 0 || mCandles[i].low() < minPrice)
                    minPrice = mCandles[i].low();
            }
        }

        if (mCurrentCandle.isValid()) {
            if (mCurrentCandle.high() > maxPrice)
                maxPrice = mCurrentCandle.high();

            if (minPrice == 0 || mCurrentCandle.low() < minPrice)
                minPrice = mCurrentCandle.low();
        }


        if (minPrice != 0 && maxPrice != 0) {
            mPriceSteps.append(minPrice * 0.97);
            mPriceSteps.append(minPrice * 0.98);
            mPriceSteps.append(maxPrice * 1.02);
            mPriceSteps.append(maxPrice * 1.03);

            qWarning() << "minPrice : " << minPrice * 0.97 << "\tmaxPrice : " << maxPrice * 1.03;
        }
    }
}

void LensChartView::setCurrentStock(QString code) {
    if (mCurrentStockCode != code) {
        qWarning() << "setCurrentStock : " << code;
        mCurrentStockCode = code;
        resetData();
    }
}


void LensChartView::resetData() {
    qWarning() << "resetData";
    mPriceSteps.clear();
    mTickBeginDateTime = QDateTime();
    mTickInterval = INTERVAL_MSEC;
    mCurrentCandle.clear();
    mMaxVolume = 0;
    mOpen = 0;
    mCurrentHighPrice = mCurrentLowPrice = 0;
    mCandles.clear();
    mPriceSteps.clear();
}


void LensChartView::timeInfoArrived(QDateTime dt) {
    if (!mCurrentDateTime.isValid() || (!DataProvider::getInstance()->isSimulation() && mCurrentDateTime != dt)) {
        mCurrentDateTime = dt;
        resetData();
        update();
    }
}



qreal LensChartView::mapPriceToPos(int price, qreal endY, qreal startY) {
    qreal priceGap = mPriceSteps.at(mPriceSteps.size() - 1) - mPriceSteps.at(0); 
    qreal positionGap = endY - startY; // device coordinate zero is started from upper
    qreal pricePosition = price - mPriceSteps.at(0);
    qreal result = endY - pricePosition * positionGap / priceGap;
    return result;
}


void LensChartView::drawGridLine(QPainter *painter, qreal cw, qreal ch) {
    painter->save();
    QPen pen = painter->pen();
    pen.setWidth(1);
    pen.setColor(QColor("#d7d7d7"));
    painter->setPen(pen);
  
    for (int i = 0; i < PRICE_ROW_COUNT / 2 + 1; i++) {
        QLineF line(0, ch * 2 * (i+1), (cw) * COLUMN_COUNT, ch * 2 * (i+1));
        painter->drawLine(line); 
    }
    painter->restore(); 
}


qreal LensChartView::getCandleLineWidth(qreal w) {
    if (w * 0.2 < 1.0)
        return 1.0;
    return (int)w * 0.2;
}


void LensChartView::drawCurrentPriceLine(QPainter *painter, int price, qreal fromX, qreal untilX, qreal startY, qreal endY, qreal cellWidth) {
    painter->save();
    QPen pen = painter->pen();
    pen.setColor("#ff0000");
    pen.setWidth(1);
    pen.setStyle(Qt::DashLine);
    painter->setPen(pen);
    qreal current_y = mapPriceToPos(price, endY, startY);
    painter->drawLine(QLineF(fromX, current_y, untilX, current_y));
    /*
    pen.setColor(Qt::black);
    painter->setPen(pen);
    QFont f = painter->font();
    f.setPixelSize(13);
    painter->setFont(f);
    QLocale locale;
    painter->drawText(QRectF(0, current_y - 8, cellWidth, 16),
                    Qt::AlignCenter, locale.toCurrencyString(price, " "));
    */
    painter->restore();
}


void LensChartView::drawCandle(QPainter *painter, const Candle &candle, qreal x, qreal candleWidth, qreal startY, qreal endY) {
    QColor color;
    painter->save();
    if (candle.close() >= candle.open())
        color.setRgb(255, 0, 0);
    else 
        color.setRgb(0, 0, 255);

    QPen pen = painter->pen();
    painter->setBrush(QBrush(color));
    pen.setColor(color);

    qreal penWidth = getCandleLineWidth(candleWidth);
    pen.setWidthF(penWidth);
    painter->setPen(pen);
    qreal candle_y_low = mapPriceToPos(candle.low(), endY, startY);
    qreal candle_y_high = mapPriceToPos(candle.high(), endY, startY);
    qreal candle_y_open = mapPriceToPos(candle.open(), endY, startY);
    qreal candle_y_close = mapPriceToPos(candle.close(), endY, startY);

    qreal line_x = x + (candleWidth / 2);
    painter->drawLine(QLineF(line_x, candle_y_high, line_x, candle_y_low));
    painter->setPen(Qt::NoPen);
    painter->drawRect(QRectF(x, candle_y_open, candleWidth, candle_y_close - candle_y_open));
    
    qreal profit = (qreal(candle.high()) - candle.low()) / candle.low() * 100.0;
    if (qAbs(profit) >= 0.5)
        painter->drawText(QRectF(x - 5, candle_y_low + 10, candleWidth + 10, 15), Qt::AlignCenter, QString::number(profit, 'f', 1));

    painter->restore();
}


qreal LensChartView::getVolumeHeight(qint64 volume, qreal volumeHeight) {
    return volumeHeight * volume / mMaxVolume;
}


void LensChartView::drawVolume(QPainter *painter, const Candle &candle, qreal x, qreal volumeWidth, qreal startY, qreal endY) {
    if (mMaxVolume == 0)
        return;

    painter->save();
    painter->setBrush(QBrush(Qt::green));
    painter->setPen(Qt::NoPen);
    
    qreal h = getVolumeHeight(candle.volume(), endY - startY);
    if (candle.buy_upper_hand())
        painter->fillRect(QRectF(x, endY - h, volumeWidth, endY), QBrush(Qt::red));
    else
        painter->fillRect(QRectF(x, endY - h, volumeWidth, endY), QBrush(Qt::blue));

    painter->restore();
}


void LensChartView::displayLowHighText(QPainter *painter, qreal x, qreal cellWidth, qreal startY, qreal endY) {
    painter->save();
    QFont f = painter->font();
    f.setPixelSize(13);
    painter->setFont(f);

    QLocale locale;
    qreal low_y = mapPriceToPos(mCurrentLowPrice, endY, startY);
    qreal high_y = mapPriceToPos(mCurrentHighPrice, endY, startY);
    qreal gap = (qreal(mCurrentHighPrice) - mCurrentLowPrice) / mCurrentLowPrice * 100.0;

    painter->setPen(QPen(Qt::black));
    painter->drawText(QRectF(x, low_y + 20, cellWidth, 15),
                    Qt::AlignCenter, locale.toCurrencyString(mCurrentLowPrice, " "));

    painter->drawText(QRectF(x, high_y - 35, cellWidth, 15),
                    Qt::AlignCenter, locale.toCurrencyString(mCurrentHighPrice, " "));
    
    painter->drawText(QRectF(x, (low_y + high_y) / 2, cellWidth, 15),
                    Qt::AlignCenter, QString::number(gap, 'f', 1));
    painter->restore();
}


void LensChartView::displayOpenPriceLine(QPainter *painter, qreal x, qreal endX, qreal startY, qreal endY) {
    painter->save();
    QPen pen;
    pen.setStyle(Qt::DashLine);
    pen.setWidth(1);
    pen.setColor("#00ff00");
    painter->setPen(pen);
    qreal yPos = mapPriceToPos(mOpen, endY, startY);
    painter->drawLine(QLineF(x, yPos, endX, yPos));
    painter->restore();
}


void LensChartView::paint(QPainter *painter) {
    QSizeF canvasSize = size();
    qreal cellHeight = canvasSize.height() / ROW_COUNT;
    qreal cellWidth = canvasSize.width() / COLUMN_COUNT;

    drawGridLine(painter, cellWidth, cellHeight);
    if (mPriceSteps.count() == 0) 
        return;

    qreal candleCount = DISPLAY_MSEC / INTERVAL_MSEC;
    qreal spaceCount = candleCount * 2 - 1;
    qreal candleWidth = cellWidth * PRICE_COLUMN_COUNT / (candleCount + spaceCount * TICK_SPACE_RATIO);
    qreal spaceWidth = candleWidth * TICK_SPACE_RATIO; 
    qreal currentStartX = cellWidth;

    for (int i = 0; i < mCandles.count(); i++) {
        drawCandle(painter, mCandles.at(i), currentStartX, candleWidth, 0.0, cellHeight * PRICE_ROW_COUNT);
        drawVolume(painter, mCandles.at(i), currentStartX, candleWidth, cellHeight * PRICE_ROW_COUNT, cellHeight * (PRICE_ROW_COUNT + VOLUME_ROW_COUNT));
        currentStartX += candleWidth + spaceWidth;
    }

    if (mCurrentCandle.isValid()) {
        drawCandle(painter, mCurrentCandle, currentStartX, candleWidth, 0.0, cellHeight * PRICE_ROW_COUNT);
        drawVolume(painter, mCurrentCandle, currentStartX, candleWidth, cellHeight * PRICE_ROW_COUNT, cellHeight * (PRICE_ROW_COUNT + VOLUME_ROW_COUNT));
        drawCurrentPriceLine(painter, mCurrentCandle.close(), cellWidth, cellWidth * COLUMN_COUNT, 0.0, cellHeight * PRICE_ROW_COUNT, cellWidth);
    }

    if (mCurrentLowPrice != 0 && mCurrentHighPrice != 0)
        displayLowHighText(painter, 0, cellWidth, 0.0, cellHeight * PRICE_ROW_COUNT);

    if (mOpen != 0)
        displayOpenPriceLine(painter, 0, canvasSize.width(), 0.0, cellHeight * PRICE_ROW_COUNT);
}
