#include "LensChartView.h"
#include <QDebug>

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
    if (data->code() != mCurrentStockCode)
        return;

    QDateTime dt = timestampToQDateTime(data->tick_date());

    if (mCurrentCandle.isValid()) {
        if (mCurrentCandle.isTimeIn(
    }
    else {
        mCurrentCandle.addTickData(data->current_price(),
                                   data->volume(),
                                   dt);
    }
}


void LensChartView::resetData() {
    currentVolumeMin = currentVolumeMax = 0;
    mPriceSteps.clear();
}


void LensChartView::timeInfoArrived(QDateTime dt) {
    if (!currentDateTime.isValid() || (!DataProvider::getInstance()->isSimulation() && currentDateTime != dt)) 
        resetData();
}


void LensChartView::setCurrentStock(QString code) {
    if (mCurrentStockCode != code) {
        mCurrentStockCode = code;
        resetData();
    }
}


qreal LensChartView::mapPriceToPos(int price, qreal startY, qreal endY) {
    qreal priceGap = mPriceSteps.at(mPriceSteps.size() - 1) - mPriceSteps.at(0); 
    qreal positionGap = startY - endY; // device coordinate zero is started from upper
    qreal pricePosition = price - mPriceSteps.at(0);
    qreal result = startY - pricePosition * positionGap / priceGap;
    return result;
}


void LensChartView::calculateMinMaxRange() {
    MinuteTick *mt = DataProvider::getInstance()->getMinuteTick(mCurrentStockCode);
    int highest = yesterdayMinInfo.getHighestPrice();
    int lowest = yesterdayMinInfo.getLowestPrice();
    uint highestVolume = yesterdayMinInfo.getHighestVolume();
    qWarning() << "(yesterday) " << highest << ", " << lowest;
    setPriceSteps(highest, lowest);

    if (mt != NULL) {
        qWarning() << "(mt) " << mt->getHighestPrice() << ", " << mt->getLowestPrice();
        if (mt->getHighestPrice() > highest)
            highest = mt->getHighestPrice();

        // Start Simulation -> Launch Tick App -> Tick is arrived first but not lowest price is calculated yet
        if (mt->getLowestPrice() != 0 && mt->getLowestPrice() < lowest)
            lowest = mt->getLowestPrice();

        if (mt->getHighestVolume() > highestVolume)
            highestVolume = mt->getHighestVolume();

        updatePriceSteps(highest, lowest);
    }


    setVolumeMinMax(highestVolume, yesterdayMinInfo.getLowestVolume());
}


void LensChartView::setVolumeMinMax(uint h, uint l) {
    if (currentVolumeMax == 0) {
        currentVolumeMax = h;
        currentVolumeMin = l;
    }
    else {
        if (currentVolumeMin == 0 || l < currentVolumeMin)
            currentVolumeMin = l;

        if (h > currentVolumeMax)
            currentVolumeMax = h;
    }
    //qWarning() << "volume max : " << currentVolumeMax << "\tvolume min : " << currentVolumeMin;
}


void LensChartView::updateVolumeMax(uint h) {
    if (h > currentVolumeMax) {
        //qWarning() << "CurrentVolumeMax : " << h;
        currentVolumeMax = h;
    }
}


void LensChartView::drawGridLine(QPainter *painter, qreal cw, qreal ch) {
    painter->save();
    QPen pen = painter->pen();
    pen.setWidth(1);
    pen.setColor(QColor("#d7d7d7"));
    painter->setPen(pen);
  
    for (int i = 0; i < ROW_COUNT / 2 + 1; i++) {
        QLineF line(0, ch * 2 * (i+1), (cw) * COLUMN_COUNT, ch * 2 * (i+1));
        painter->drawLine(line); 
    }
    painter->restore(); 
}


void LensChartView::setPriceSteps(int h, int l) {
    qWarning() << "setPriceSteps : " << h << " " << l;
    int high = 0, low = 0;
    if (mPriceSteps.count() == 0) {
        high = int(h * 1.05);
        low = int(l * 0.95);
    }
    else {
        if (h == 0) {
            high = mPriceSteps.at(mPriceSteps.count() - 1);
            low = int(l * 0.95);
        }
        
        if (l == 0) {
            high = int(h * 1.05);
            low = mPriceSteps.at(0);
        }

        if (h != 0 && l != 0) {
            high = int(h * 1.05);
            low = int(l * 0.95);
        }
    }
    mPriceSteps.clear();


    int priceGap = (high - low) / PRICE_ROW_COUNT;
    qWarning() << "priceGap : " << high << " " << low << " gap: " << priceGap;
    if (priceGap < 100)
        priceGap = 10;
    else
        priceGap = 100;

    int minimumUnit = low - (low % priceGap);
    int step = (high - minimumUnit) / PRICE_ROW_COUNT;
    step = step - (step % priceGap);
    qWarning() << "minimumUnit : " << minimumUnit << " STEP : " << step << " HIGH : " << high << " SUM : " << step * PRICE_ROW_COUNT + minimumUnit;
    while (step * PRICE_ROW_COUNT + minimumUnit < high) 
        step += priceGap;
    qWarning() << "STEP 2 : " << step;

    for (int i = 0; i < PRICE_ROW_COUNT + 1; i++) 
        mPriceSteps.append(minimumUnit + step * i);
    qWarning() << "steps : " << mPriceSteps;
}


void LensChartView::updatePriceSteps(int h, int l) {
    //qWarning() << "updatePriceSteps : " << h << " " << l;
    if (mPriceSteps.count() == 0) {
        setPriceSteps(h, l);
    }
    else {
        if (l * 0.97 < mPriceSteps.at(0))
            setPriceSteps(0, l);

        if (h * 1.03 > mPriceSteps.at(mPriceSteps.count() - 1)) 
            setPriceSteps(h, 0);
    }
}


qreal LensChartView::getCandleLineWidth(qreal w) {
    if (w * 0.2 < 1.0)
        return 1.0;
    return (int)w * 0.2;
}


qreal LensChartView::getVolumeHeight(uint v, qreal ch) {
    if (v < currentVolumeMin)
        return 0.0;

    qreal vRange = qreal(currentVolumeMax - currentVolumeMin);
    //qWarning() << "vol diff : " << (v - currentVolumeMin) << "\tvRange : " << vRange << "\t ch : " << ch;
    return ch * VOLUME_ROW_COUNT * (v - currentVolumeMin) / vRange;
}


void LensChartView::drawVolume(QPainter *painter, const CybosDayData &data, qreal startX, qreal tickWidth, qreal ch, qreal volumeEndY) {
    QColor color;
    painter->save();
    if (data.cum_sell_volume() > data.cum_buy_volume())
        color.setRgb(0, 0, 255);
    else
        color.setRgb(255, 0, 0);
    painter->setBrush(QBrush(color));
    painter->setPen(Qt::NoPen);
    if (data.volume() > 0) {
        qreal volumeHeight = getVolumeHeight(data.volume(), ch);
        painter->drawRect(QRectF(startX, volumeEndY - volumeHeight, tickWidth, volumeHeight));
    }
    painter->restore();
}


void LensChartView::drawCandle(QPainter *painter, const CybosDayData &data, qreal startX, qreal horizontalGridStep, qreal priceChartEndY) {
    QColor color;
    painter->save();
    if (data.close_price() >= data.start_price()) {
        if (data.is_synchronized_bidding())
            color.setRgb(255, 165, 0);
        else
            color.setRgb(255, 0, 0);
    }
    else {
        if (data.is_synchronized_bidding())
            color.setRgb(173, 216, 230);
        else
            color.setRgb(0, 0, 255);
    }

    QPen pen = painter->pen();
    painter->setBrush(QBrush(color));
    pen.setColor(color);

    qreal penWidth = getCandleLineWidth(horizontalGridStep);
    pen.setWidthF(penWidth);
    painter->setPen(pen);
    qreal candle_y_low = mapPriceToPos(data.lowest_price(), priceChartEndY, 0);
    qreal candle_y_high = mapPriceToPos(data.highest_price(), priceChartEndY, 0);
    qreal candle_y_open = mapPriceToPos(data.start_price(), priceChartEndY, 0);
    qreal candle_y_close = mapPriceToPos(data.close_price(), priceChartEndY, 0);

    qreal line_x = startX + (horizontalGridStep / 2);
    painter->drawLine(QLineF(line_x, candle_y_high, line_x, candle_y_low));
    painter->setPen(Qt::NoPen);
    painter->drawRect(QRectF(startX, candle_y_open, horizontalGridStep, candle_y_close - candle_y_open));

    painter->restore();
}


qreal LensChartView::getTimeToXPos(uint dataTime, qreal tickWidth, uint startTime) {
    QTime st(int(startTime / 100), int(startTime % 100), 0);
    QTime dt(int(dataTime / 100), int(dataTime % 100), 0);
    qreal diff = (dt.msecsSinceStartOfDay() - st.msecsSinceStartOfDay()) / 1000.0 / 180.0; // 3 min
    //qWarning() << time << "\t" << tickWidth * 2 * diff << "\t" << diff << "\t" ;//<< tickWidth * PRICE_COLUMN_COUNT / 2;
    return (tickWidth + (tickWidth * TICK_SPACE_RATIO)) * diff;
}


void LensChartView::drawPriceLabels(QPainter *painter, qreal startX, qreal ch) {
    painter->save();
    QPen pen = painter->pen();
    pen.setColor(QColor("#000000"));
    painter->setPen(pen);

    for (int i = 0; i < mPriceSteps.count() - 1; i++) {
        painter->drawText((int)startX, (int)(ch * PRICE_ROW_COUNT  - ch * i),
                            QString::number(mPriceSteps.at(i)));
    }
    painter->restore();
}


void LensChartView::drawTimeLabels(QPainter *painter,
                                            qreal tickWidth,
                                            qreal cw, qreal ch,
                                            qreal startX,
                                            int cellCount,
                                            uint startTime) {
    painter->save();
    QPen pen;
    pen.setWidth(1);
    painter->setPen(pen);

    QTime t = QTime(startTime / 100, startTime % 100, 0);
    qreal yPos = ch * (PRICE_ROW_COUNT + TIME_LABEL_ROW_COUNT + SUBJECT_ROW_COUNT);
    for (int i = 0; i < cellCount * 2; i++) { 
        t = t.addSecs(60 * 30); // 30 min
        QString label;
        qreal xPos = getTimeToXPos(t.hour() * 100 + t.minute(), tickWidth, startTime);
        qreal lineHeight = ch / 6;
        if (t.minute() == 0) {
            label = QString::number(t.hour());
            lineHeight = ch / 5;
            QLineF line(startX + xPos, 0, startX + xPos, yPos + lineHeight);
            pen.setColor(QColor("#d7d7d7"));
            painter->setPen(pen);
            painter->drawLine(line); 
            pen.setColor(Qt::black);
            painter->setPen(pen);
            painter->drawText(QRectF(startX + xPos - cw / 6,
                                    yPos + lineHeight, cw / 3, ch / 3),
                                Qt::AlignCenter, label);

        }
        else {
            QLineF line(startX + xPos, 0, startX + xPos, yPos + lineHeight);
            pen.setColor(QColor("#50d7d7d7"));
            painter->setPen(pen);
            painter->drawLine(line); 
        }
    }
    painter->restore();
}


void LensChartView::drawCurrentLineRange(QPainter *painter, MinuteTick *mt, qreal startX, const CybosDayData &data, qreal cw, qreal priceChartEndY) {
    painter->save();
    QPen pen;
    pen.setStyle(Qt::DashLine);
    pen.setWidth(1);
    if (data.is_synchronized_bidding())
        pen.setColor("#ff00ff");
    else
        pen.setColor("#ff0000");
    painter->setPen(pen);

    qreal current_y = mapPriceToPos(data.close_price(), priceChartEndY, 0);
    qreal upper_y = mapPriceToPos(data.close_price() * 1.03, priceChartEndY, 0);;
    qreal lower_y = mapPriceToPos(data.close_price() * 0.97, priceChartEndY, 0);;
    painter->drawLine(QLineF(0, current_y, cw * PRICE_COLUMN_COUNT, current_y));
    painter->drawText(int(cw * PRICE_COLUMN_COUNT + cw), int(current_y), QString::number(data.close_price()));
    pen.setColor("#90000000");
    painter->setPen(pen);
    painter->drawLine(QLineF(0, upper_y, cw * PRICE_COLUMN_COUNT, upper_y));
    painter->drawLine(QLineF(0, lower_y, cw * PRICE_COLUMN_COUNT, lower_y));

    if (mt->getYesterdayClose() != 0) {
        qreal yesterdayDiff = (int(data.close_price()) - mt->getYesterdayClose()) / (qreal)mt->getYesterdayClose() * 100.0;
        if (yesterdayDiff < 0)
            pen.setColor("#0000ff");
        else
            pen.setColor("#ff0000");
        painter->setPen(pen);
        painter->drawText(/*int(cw * PRICE_COLUMN_COUNT + cw)*/ startX + 10, int(current_y + 20), QString::number(yesterdayDiff, 'f', 1));
    }

    if (mt->getOpenPrice() != 0) {
        qreal openDiff = (int(data.close_price()) - mt->getOpenPrice()) / (qreal)mt->getOpenPrice() * 100.0;

        if (openDiff < 0) 
            pen.setColor("#0000ff");
        else
            pen.setColor("#ff0000");
        painter->setPen(pen);
        painter->drawText(/*int(cw * PRICE_COLUMN_COUNT + cw)*/ startX + 10, int(current_y - 20), QString::number(openDiff, 'f', 1));
    }

    painter->restore();
}


void LensChartView::paint(QPainter *painter) {
    QSizeF canvasSize = size();
    qreal cellHeight = canvasSize.height() / ROW_COUNT;
    qreal cellWidth = canvasSize.width() / COLUMN_COUNT;

    drawGridLine(painter, cellWidth, cellHeight);
    if (mPriceSteps.count() == 0)
        return;

    drawPriceLabels(painter, canvasSize.width() - cellWidth * 2 + 10, cellHeight);
    qreal startX = 0;
    // normally 8:30 ~ 15:30 : 420 min / 3 : 140 ticks (0 ~ 10: count = 11)
    qreal todayTickCount = 141;
    qreal todaySpaceCount = todayTickCount - 1;
    // normally 9:00 ~ 15:30 : 390 min / 3 : 130 ticks
    qreal yesterdayTickCount = 131;
    qreal yesterdaySpaceCount = yesterdayTickCount - 1;

    AuxiliaryInfo aInfo(this);
    // Space width between tick is 2/3 tick width, area_width = (count + (count - 1) * 2/3) * tickWidth
    qreal todayTickWidth = cellWidth * TODAY_COLUMN_COUNT / (todayTickCount + todaySpaceCount * TICK_SPACE_RATIO);
    qreal yesterdayTickWidth = cellWidth * YESTERDAY_COLUMN_COUNT / (yesterdayTickCount + yesterdaySpaceCount * TICK_SPACE_RATIO);

    if (!yesterdayMinInfo.isEmpty()) {
        uint st = yesterdayMinInfo.get(0).time();
        drawTimeLabels(painter, yesterdayTickWidth, cellWidth, cellHeight, startX, YESTERDAY_COLUMN_COUNT, st);
        for (int i = 0; i < yesterdayMinInfo.count(); i++) {
            const CybosDayData &d = yesterdayMinInfo.get(i);
            qreal xPos = getTimeToXPos(d.time(), yesterdayTickWidth, st);
            aInfo.addPriceWithXAxis(startX + xPos, d.close_price(), d.highest_price());
            drawCandle(painter, d, startX + xPos, yesterdayTickWidth, cellHeight * PRICE_ROW_COUNT);
            drawVolume(painter, d, startX + xPos, yesterdayTickWidth, cellHeight, cellHeight * (PRICE_ROW_COUNT + VOLUME_ROW_COUNT));
        }
    }

    if (!mCurrentStockCode.isEmpty()) {
        startX = cellWidth * YESTERDAY_COLUMN_COUNT + 1;
        MinuteTick *mt = DataProvider::getInstance()->getMinuteTick(mCurrentStockCode);
        if (mt == NULL)
            return;

        const CybosDayDatas &queue = mt->getQueue();
        drawTimeLabels(painter, todayTickWidth, cellWidth, cellHeight, startX,
                        TODAY_COLUMN_COUNT, todayStartTime.hour() * 100 + todayStartTime.minute());
        
        for (int i = 0; i < queue.day_data_size(); i++) {
            const CybosDayData &d = queue.day_data(i);
            qreal xPos = getTimeToXPos(d.time(), todayTickWidth, todayStartTime.hour() * 100 + todayStartTime.minute());
            aInfo.addPriceWithXAxis(startX + xPos, d.close_price(), d.highest_price());
            drawCandle(painter, d, startX + xPos, todayTickWidth, cellHeight * PRICE_ROW_COUNT);
            drawVolume(painter, d, startX + xPos, todayTickWidth, cellHeight, cellHeight * (PRICE_ROW_COUNT + VOLUME_ROW_COUNT));
        }
        
        if (mt->getCurrent().start_price() != 0) {
            const CybosDayData &d = mt->getCurrent();
            qreal xPos = getTimeToXPos(d.time(), todayTickWidth, todayStartTime.hour() * 100 + todayStartTime.minute());
            drawCandle(painter, d, startX + xPos, todayTickWidth, cellHeight * PRICE_ROW_COUNT);
            drawVolume(painter, d, startX + xPos, todayTickWidth, cellHeight, cellHeight * (PRICE_ROW_COUNT + VOLUME_ROW_COUNT));
            aInfo.addPriceWithXAxis(startX + xPos, d.close_price(), d.highest_price());
            drawCurrentLineRange(painter, mt, startX + xPos, d, cellWidth, cellHeight * PRICE_ROW_COUNT);
        }
    }

    aInfo.drawAverageLine(painter, cellHeight * PRICE_ROW_COUNT);
}
