#include "LensChartView.h"
#include <QPainterPath>
#include <QMapIterator>
#include <QDebug>

#include <google/protobuf/util/time_util.h>
using google::protobuf::util::TimeUtil;




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


void LensChartView::sendCurrentCode() {
    DataProvider::getInstance()->setCurrentStock(mCurrentStockCode);
}


void LensChartView::setCurrentRatio(const QString &ratio) {
    if (mCurrentRatio != ratio) {
        mCurrentRatio = ratio;
        currentRatioChanged();
    }
}


void LensChartView::setCurrentAmount(const QString &amount) {
    if (mCurrentAmount != amount) {
        mCurrentAmount = amount;
        currentAmountChanged();
    }
}

void LensChartView::setOpenProfit(const QString &p) {
    if (mOpenProfit != p) {
        mOpenProfit = p;
        openProfitChanged();
    }
}


void LensChartView::setCorpName(const QString &name) {
    if (mCorpName != name) {
        mCorpName = name;
        corpNameChanged();
    }
}


void LensChartView::tickArrived(CybosTickData *data) {
    QString code = QString::fromStdString(data->code());

    if (!mStockMap.contains(code))
        mStockMap.insert(code, new StockData(code));
    
    mStockMap[code]->tickArrived(data);

    if (QString::fromStdString(data->code()) == mCurrentStockCode) {
        StockData *stockData = mStockMap[code];
        setCurrentRatio(stockData->currentRatio());
        setCurrentAmount(stockData->currentAmount());
        setOpenProfit(stockData->openProfit());
        update();
    }
    delete data;
}


void LensChartView::setPinCode(bool p) {
    if (p ^ mPinCode) {
        qWarning() << "setPinCode " << p;
        mPinCode = p;
        emit pinCodeChanged();
    }
}


void LensChartView::setCurrentStock(QString code) {
    if (mCurrentStockCode != code && !mPinCode) {
        qWarning() << "setCurrentStock : " << code;
        mCurrentStockCode = code;
        resetData();

        if (!mStockMap.contains(code))
            mStockMap.insert(code, new StockData(code));
        
        setCorpName(mStockMap[code]->corpName());
        update();
    }
}


void LensChartView::resetData() {
    qWarning() << "resetData";
    setCurrentRatio("");
    setCurrentAmount("");
    setOpenProfit("");
}


void LensChartView::timeInfoArrived(QDateTime dt) {
    if (!mCurrentDateTime.isValid() || !DataProvider::getInstance()->isSimulation()) {
        mCurrentDateTime = dt;
        resetData();
        QMapIterator<QString, StockData *> i(mStockMap);
        while (i.hasNext()) {
            i.next();
            delete i.value();
        }
        mStockMap.clear();
        update();
    }
}


void LensChartView::drawVolumeCenterLine(QPainter *painter, qreal x, qreal endX, qreal startY, qreal endY) {
    painter->save();
    QPen pen;
    pen.setStyle(Qt::DashLine);
    pen.setWidth(1);
    pen.setColor("#000000");
    painter->setPen(pen);
    qreal yPos = (startY + endY) / 2;
    painter->drawLine(QLineF(x, yPos, endX, yPos));
    painter->restore();
}


void LensChartView::drawGridLine(QPainter *painter, qreal cw, qreal ch) {
    painter->save();
    QPen pen = painter->pen();
    pen.setWidth(1);
    pen.setColor(QColor("#d7d7d7"));
    painter->setPen(pen);
  
    for (int i = 0; i < StockData::PRICE_ROW_COUNT / 2; i++) {
        QLineF line(0, ch * 2 * (i+1), (cw) * StockData::COLUMN_COUNT, ch * 2 * (i+1));
        painter->drawLine(line); 
    }
    painter->restore(); 
}


void LensChartView::drawAmountRatioGridLine(QPainter *painter, qreal x, qreal endX, qreal startY, qreal endY) {
    int lineCount = int(0.2 / 0.05);
    double lineStartY = (endY + startY) * 0.5;
    double halfHeight = (endY - startY) * 0.5;
    double lineHeight = halfHeight / lineCount;
    painter->save();
    QPen pen = painter->pen();
    pen.setWidth(1);
    pen.setColor(QColor("#d7d7d7"));
    painter->setPen(pen);

    for (int i = 0; i < lineCount; i++) {
        painter->drawLine(QLineF(x, lineStartY + lineHeight * (i + 1), endX, lineStartY + lineHeight * (i + 1)));
        painter->drawLine(QLineF(x, lineStartY - lineHeight * (i + 1), endX, lineStartY - lineHeight * (i + 1)));
    }
    painter->restore();
}


void LensChartView::paint(QPainter *painter) {
    QSizeF canvasSize = size();
    qreal cellHeight = canvasSize.height() / StockData::ROW_COUNT;
    qreal cellWidth = canvasSize.width() / StockData::COLUMN_COUNT;

    drawGridLine(painter, cellWidth, cellHeight);
    
    drawVolumeCenterLine(painter, 0, canvasSize.width(), cellHeight * StockData::PRICE_ROW_COUNT, canvasSize.height());
    drawAmountRatioGridLine(painter, 0, canvasSize.width(), cellHeight * StockData::PRICE_ROW_COUNT, canvasSize.height());
    if (mCurrentStockCode.isEmpty() || !mStockMap.contains(mCurrentStockCode))
        return;

    mStockMap[mCurrentStockCode]->paint(painter, canvasSize);
}
