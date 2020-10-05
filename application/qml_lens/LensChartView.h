#ifndef LENS_CHARTVIEW_H_
#define LENS_CHARTVIEW_H_

#include <QQuickPaintedItem>
#include <QPainter>
#include <QTransform>
#include <QPair>
#include <QMap>
#include <QWheelEvent>
#include "Candle.h"
#include "StockData.h"



class LensChartView : public QQuickPaintedItem {
    Q_OBJECT
    QML_ELEMENT
    Q_PROPERTY(bool pinCode READ pinCode WRITE setPinCode NOTIFY pinCodeChanged)
    Q_PROPERTY(QString corpName READ corpName NOTIFY corpNameChanged)
    Q_PROPERTY(QString currentAmount READ currentAmount NOTIFY currentAmountChanged)
    Q_PROPERTY(QString currentRatio READ currentRatio NOTIFY currentRatioChanged)
    Q_PROPERTY(QString openProfit READ openProfit NOTIFY openProfitChanged)

public:
    LensChartView(QQuickItem *parent = 0);

    bool pinCode() { return mPinCode; }
    void setPinCode(bool p);

    void paint(QPainter *painter);

    const QString &corpName() { return mCorpName; }
    const QString &currentAmount() { return mCurrentAmount; }
    const QString &currentRatio() { return mCurrentRatio; }
    const QString &openProfit() { return mOpenProfit; }

    Q_INVOKABLE void sendCurrentCode();

private:
    QString mCurrentStockCode;
    QDateTime mCurrentDateTime;

    QString mCorpName;
    QString mCurrentAmount;
    QString mCurrentRatio;
    QString mOpenProfit;
    bool mPinCode = false;

    QMap<QString, StockData *> mStockMap;

    void resetData();

    void setCurrentRatio(const QString &ratio);
    void setCurrentAmount(const QString &amount);
    void setOpenProfit(const QString &p);
    void setCorpName(const QString &name);

    void drawGridLine(QPainter *painter, qreal cw, qreal ch);
    void drawVolumeCenterLine(QPainter *painter, qreal x, qreal endX, qreal startY, qreal endY);
    void drawAmountRatioGridLine(QPainter *painter, qreal x, qreal endX, qreal startY, qreal endY);

private slots:
    void setCurrentStock(QString);
    void timeInfoArrived(QDateTime);
    void tickArrived(CybosTickData *data);

signals:
    void pinCodeChanged();
    void corpNameChanged();
    void currentRatioChanged();
    void currentAmountChanged();
    void openProfitChanged();
};

#endif
