#include "StockData.h"
#include <QPainterPath>
#include <QLocale>
#include <google/protobuf/util/time_util.h>
using google::protobuf::util::TimeUtil;

#define TICK_SPACE_RATIO    (1.0/5.0)


StockData::StockData(const QString &code) {
    mCorpName = DataProvider::getInstance()->getCompanyName(code);
}


void StockData::addCandle() {
    mCandles.append(mCurrentCandle);
    mCurrentCandle.clear();

    if (mCandles.count() >= DISPLAY_MSEC / INTERVAL_MSEC)
        mCandles.removeFirst();
}


QDateTime StockData::timestampToQDateTime(const Timestamp &t) {
    long msec = TimeUtil::TimestampToMilliseconds(t);
    return QDateTime::fromMSecsSinceEpoch(msec);
}


void StockData::tickArrived(CybosTickData *data) {
    QDateTime dt = timestampToQDateTime(data->tick_date());

    if (!mCurrentCandle.isValid()) {
        mCurrentCandle.setStartDateTime(dt);
    }
    else {
        if (dt.toMSecsSinceEpoch() - mCurrentCandle.startDateTime().toMSecsSinceEpoch() > INTERVAL_MSEC) {
            addCandle();
        }
    }

    if (mOpen == 0)
        mOpen = data->start_price();
    else if (mOpen > 0 && mCurrentCandle.was_uni_price() && data->market_type() == 50)
        mOpen = data->current_price();

    mYesterdayClose = data->current_price() - data->yesterday_diff();
    mCurrentCandle.addTickData(data->current_price(),
                                data->volume(), data->buy_or_sell(),
                                data->amount_ratio(),
                                data->market_type() == 50);
    
    mCurrentRatio = QString::number(data->amount_ratio(), 'f', 3);
    mCurrentAmount = uint64ToString(data->cum_amount() * (data->is_kospi()? 10000 : 1000));

    if (mOpen > 0) {
        qreal profit = ((qreal)data->current_price() - mOpen) / mOpen * 100.0;
        mOpenProfit = QString::number(profit, 'f', 1);
    }
    
    checkPriceRange(data->current_price());
    checkVolumeMax();    
}


void StockData::checkPriceRange(int price) {
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

            //qWarning() << "minPrice : " << minPrice * 0.97 << "\tmaxPrice : " << maxPrice * 1.03;
        }
    }
}


void StockData::checkVolumeMax() {
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


qreal StockData::mapPriceToPos(int price, qreal endY, qreal startY) {
    qreal priceGap = mPriceSteps.at(mPriceSteps.size() - 1) - mPriceSteps.at(0); 
    qreal positionGap = endY - startY; // device coordinate zero is started from upper
    qreal pricePosition = price - mPriceSteps.at(0);
    qreal result = endY - pricePosition * positionGap / priceGap;
    return result;
}


qreal StockData::getCandleLineWidth(qreal w) {
    if (w * 0.2 < 1.0)
        return 1.0;
    return (int)w * 0.2;
}


void StockData::drawCurrentPriceLine(QPainter *painter, int price, qreal fromX, qreal untilX, qreal startY, qreal endY, qreal cellWidth, qreal currentX) {
    painter->save();
    QPen pen = painter->pen();
    pen.setColor("#ff0000");
    pen.setWidth(1);
    pen.setStyle(Qt::DashLine);
    painter->setPen(pen);
    qreal current_y = mapPriceToPos(price, endY, startY);
    painter->drawLine(QLineF(fromX, current_y, untilX, current_y));

    if (mOpen != 0) {
        qreal openDiff = (qreal(price) - mOpen) / mOpen * 100.0;
        if (openDiff < 0)
            pen.setColor("#0000ff");
        else
            pen.setColor("#ff0000");

        painter->setPen(pen);
        painter->drawText(currentX + 5, current_y - 15, QString::number(openDiff, 'f', 1));
    }

    if (mYesterdayClose != 0) {
        qreal yesterdayDiff = (qreal(price) - mYesterdayClose) / mYesterdayClose * 100.0;
        if (yesterdayDiff < 0)
            pen.setColor("#0000ff");
        else
            pen.setColor("#ff0000");

        painter->setPen(pen);
        painter->drawText(currentX + 5, current_y + 20, QString::number(yesterdayDiff, 'f', 1));
    }
    painter->restore();
}


void StockData::drawCandle(QPainter *painter, const Candle &candle, qreal x, qreal candleWidth, qreal candleSpace, qreal startY, qreal endY) {
    QColor color;
    painter->save();

    if (candle.is_uni_price()) {
        painter->fillRect(QRectF(x - candleSpace, startY, candleWidth + candleSpace, endY - startY), QBrush(QColor("#6099ccff")));
    }

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

    if (candle_y_close == candle_y_open)
        painter->drawRect(QRectF(x, candle_y_open, candleWidth, penWidth));
    else
        painter->drawRect(QRectF(x, candle_y_open, candleWidth, candle_y_close - candle_y_open));
    
    qreal profit = (qreal(candle.high()) - candle.low()) / candle.low() * 100.0;
    if (qAbs(profit) >= 0.5)
        painter->drawText(QRectF(x - 5, candle_y_low + 10, candleWidth + 10, 15), Qt::AlignCenter, QString::number(profit, 'f', 1));

    painter->restore();
}


qreal StockData::getVolumeHeight(qint64 volume, qreal volumeHeight) {
    return volumeHeight * volume / mMaxVolume;
}


void StockData::drawVolume(QPainter *painter, const Candle &candle, qreal x, qreal volumeWidth, qreal startY, qreal endY) {
    if (mMaxVolume == 0)
        return;

    painter->save();
    painter->setBrush(QBrush(Qt::green));
    painter->setPen(Qt::NoPen);
    
    qreal h = getVolumeHeight(candle.volume(), endY - startY);
    if (candle.buy_upper_hand())
        painter->fillRect(QRectF(x, endY - h, volumeWidth, endY), QBrush(QColor(255, 0, 0, 60)));
    else
        painter->fillRect(QRectF(x, endY - h, volumeWidth, endY), QBrush(QColor(0, 0, 255, 60)));

    painter->restore();
}


void StockData::displayLowHighText(QPainter *painter, qreal x, qreal cellWidth, qreal cellHeight, qreal startY, qreal endY) {
    painter->save();
    QFont f = painter->font();
    f.setPixelSize(13);
    painter->setFont(f);

    QLocale locale;
    painter->setPen(QPen(Qt::black));
    painter->drawText(QRectF(x, startY, cellWidth, cellHeight),
                    Qt::AlignCenter, locale.toCurrencyString(mCurrentHighPrice, " "));

    painter->drawText(QRectF(x, endY - cellHeight, cellWidth, cellHeight),
                    Qt::AlignCenter, locale.toCurrencyString(mCurrentLowPrice, " "));
    
    //painter->drawText(QRectF(x, (low_y + high_y) / 2, cellWidth, 15),
    //                Qt::AlignCenter, QString::number(gap, 'f', 1));
    painter->restore();
}


void StockData::displayOpenPriceLine(QPainter *painter, qreal x, qreal endX, qreal startY, qreal endY, qreal cellWidth) {
    painter->save();
    QPen pen;
    pen.setStyle(Qt::DashLine);
    pen.setWidth(2);
    pen.setColor("#00ff00");
    painter->setPen(pen);
    QLocale locale;

    qreal yPos = mapPriceToPos(mOpen, endY, startY);
    if (yPos > endY)
        yPos = endY - 10;
    else if (yPos < 0)
        yPos = startY + 3;
    painter->drawLine(QLineF(x, yPos, endX, yPos));
    pen.setColor("#000000");
    painter->setPen(pen);
    painter->drawText(QRectF(endX - cellWidth * 3, yPos, cellWidth, 15),
                    Qt::AlignCenter | Qt::AlignBottom, locale.toCurrencyString(mOpen, " "));
    painter->restore();
}


void StockData::drawAmountRatio(QPainter *painter, qreal startY, qreal endY, QList<QPair<qreal, qreal> > &list) {
    painter->save();
    QPen pen = painter->pen();
    pen.setWidth(2);
    pen.setColor(QColor("#ff00ff"));
    painter->setPen(pen);

    if (list.size() > 1) {
        QPainterPath path;
        qreal firstY = endY - ((list[0].second - 0.4) / 0.2 * (endY - startY));
        path.moveTo(list[0].first, firstY);

        for (int i = 1; i < list.size(); i++) {
            path.lineTo(list[i].first, endY - ((list[i].second - 0.4) / 0.2 * (endY - startY)));
            path.moveTo(list[i].first, endY - ((list[i].second - 0.4) / 0.2 * (endY - startY)));
        }
        painter->drawPath(path);
    }
    painter->restore();
}


void StockData::drawCurrentTime(QPainter *painter, const QDateTime & dt, qreal startX, qreal startY, qreal w, qreal h) {
    painter->save();
    painter->drawText(QRectF(startX, startY, w, h * (ROW_COUNT - PRICE_ROW_COUNT)),
                    Qt::AlignRight | Qt::AlignBottom, dt.toString("hh:mm"));
    painter->restore();
}


void StockData::paint(QPainter *painter, const QSizeF &canvasSize) {
    qreal cellHeight = canvasSize.height() / ROW_COUNT;
    qreal cellWidth = canvasSize.width() / COLUMN_COUNT;


    qreal candleCount = DISPLAY_MSEC / INTERVAL_MSEC;
    qreal spaceCount = candleCount * 2 - 1;
    qreal candleWidth = cellWidth * PRICE_COLUMN_COUNT / (candleCount + spaceCount * TICK_SPACE_RATIO);
    qreal spaceWidth = candleWidth * TICK_SPACE_RATIO; 
    qreal currentStartX = canvasSize.width() - cellWidth - candleWidth;

    QList<QPair<qreal, qreal> > amountRatio;

    if (mCurrentCandle.isValid()) {
        drawCandle(painter, mCurrentCandle, currentStartX, candleWidth, spaceWidth, 0.0, cellHeight * PRICE_ROW_COUNT);
        drawVolume(painter, mCurrentCandle, currentStartX, candleWidth, cellHeight * PRICE_ROW_COUNT, cellHeight * (PRICE_ROW_COUNT + VOLUME_ROW_COUNT));

        if (mCurrentCandle.amount_ratio() != 0.0)
            amountRatio.append(QPair<qreal, qreal>(currentStartX + (candleWidth / 2), mCurrentCandle.amount_ratio()));
        drawCurrentPriceLine(painter, mCurrentCandle.close(), 0, canvasSize.width() - cellWidth, 0.0, cellHeight * PRICE_ROW_COUNT, cellWidth, currentStartX + candleWidth);
        drawCurrentTime(painter, mCurrentCandle.startDateTime(), canvasSize.width() - cellWidth, cellHeight * PRICE_ROW_COUNT, cellWidth, cellHeight);
        currentStartX -= candleWidth + spaceWidth;
    }


    for (int i = mCandles.count() - 1; i >= 0; i--) {
        drawCandle(painter, mCandles.at(i), currentStartX, candleWidth, spaceWidth, 0.0, cellHeight * PRICE_ROW_COUNT);
        drawVolume(painter, mCandles.at(i), currentStartX, candleWidth, cellHeight * PRICE_ROW_COUNT, cellHeight * (PRICE_ROW_COUNT + VOLUME_ROW_COUNT));

        if (mCandles.at(i).amount_ratio() != 0.0)
            amountRatio.append(QPair<qreal, qreal>(currentStartX + (candleWidth / 2), mCandles.at(i).amount_ratio()));
        currentStartX -= candleWidth + spaceWidth;
    }



    drawAmountRatio(painter, cellHeight * PRICE_ROW_COUNT, canvasSize.height(), amountRatio);

    if (mCurrentLowPrice != 0 && mCurrentHighPrice != 0)
        displayLowHighText(painter, canvasSize.width() - cellWidth, cellWidth, cellHeight, 0.0, cellHeight * PRICE_ROW_COUNT);

    if (mOpen != 0)
        displayOpenPriceLine(painter, 0, canvasSize.width(), 0.0, cellHeight * PRICE_ROW_COUNT, cellWidth);
}




QString StockData::uint64ToString(uint64_t amount) const {
    if (amount >= 1000000000) {
        qreal f = amount / 1000000000.0;
        return QString::number(f, 'f', 1) + " B";
    }
    else if (amount >= 1000000) {
        qreal f = amount / 1000000.0;
        return QString::number(f, 'f', 1) + " M";
    }
    else if (amount >= 1000) {
        qreal f = amount / 1000.0;
        return QString::number(f, 'f', 1) + " K";
    }

    return QString::number((uint)amount);
}