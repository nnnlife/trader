#ifndef DAY_VIEW_H_
#define DAY_VIEW_H_

#include <QQuickPaintedItem>
#include <QDateTime>
#include <QPainter>
#include <QHoverEvent>
#include "DataProvider.h"
#include "stock_provider.grpc.pb.h"


class TickStat {
public:
    TickStat() {
        mHighestPrice = mLowestPrice = 0;
        mMaxVolume = 0;
    }

    void setStat(int l, int h, unsigned long maxV) {
        mHighestPrice = h;
        mLowestPrice = l;
        mMaxVolume = maxV;
    }

    int getHighestPrice() const { return mHighestPrice; }
    int getLowestPrice() const { return mLowestPrice; }
    unsigned long getMaxVolume() const { return mMaxVolume; }
private:
    int mHighestPrice;
    int mLowestPrice;
    unsigned long mMaxVolume;

};


class DayData {
public:
    static const int PRICE_STEPS = 12;

    DayData();
    ~DayData();

    int countOfData();
    void setData(QString, CybosDayDatas *, const QMap<QString, TickStat> &tickStatMap);
    bool hasData();
    void resetData();
    int getHighestPrice() const { return mHighestPrice;}

    void setTodayData(const QString &code, int o, int h, int l, int c, unsigned long v, bool is_synchronized_bidding);

    const CybosDayData &getDayData(int i);
    const QList<int> &getPriceSteps();

    qreal mapPriceToPos(int price, qreal startY, qreal endY);
    int   mapPosToPrice(int yPos, qreal startY, qreal endY);
    qreal mapVolumeToPos(unsigned long volume, qreal startY, qreal endY);

    QDate convertToDate(unsigned int d);

    qreal getSellVolumeHeight(const CybosDayData & data, qreal h);
    qreal getForeignerBuyHeight(const CybosDayData & data, const CybosDayData &prev, qreal h);
    qreal getInstitutionBuyHeight(const CybosDayData & data, qreal h);

    qreal getVolumeStepWidth(int i, qreal w);
    qreal getForeignerStepWidth(int i, qreal w);
    qreal getInstitutionStepWidth(int i, qreal w);

    CybosDayData *getTodayData();

    long long getForeignerAmount(int i) {
        if (i < foreignerAmount.size())
            return foreignerAmount.at(i);
        return 0;
    }

    long long getInstitutionAmount(int i) {
        if (i < institutionAmount.size())
            return institutionAmount.at(i);
        return 0;
    }

private:
    CybosDayDatas *data;
    CybosDayData *todayData;
    QString code;
    int mLowestPrice;
    int mHighestPrice;
    unsigned long lowestVolume;
    unsigned long highestVolume;

    QList<int> priceSteps;
    QList<unsigned long> volumePPS; // per price steps
    QList<long> foreignerPPS;
    QList<long> institutionPPS;
    QList<long long> foreignerAmount;
    QList<long long> institutionAmount;

    void setPriceSteps(int l, int h);
    void setPPS();
    int getIndexOfPriceSteps(int price);
};

class DayView : public QQuickPaintedItem {
    Q_OBJECT
    QML_ELEMENT
    Q_PROPERTY(bool pinnedCode READ pinnedCode WRITE setPinnedCode NOTIFY pinnedCodeChanged)
    Q_PROPERTY(QString pcode READ pcode WRITE setPcode NOTIFY pcodeChanged)
    Q_PROPERTY(QString corporateName READ corporateName NOTIFY corporateNameChanged)

public:
    DayView(QQuickItem *parent = 0);
    void paint(QPainter *painter);

    void search();
    void setPinnedCode(bool isOn);
    bool pinnedCode() { return mPinnedCode; }
    QString pcode() { return mPcode; }
    void setPcode(const QString &code);
    QString corporateName() { return mCorporateName; }
    QMap<QString, TickStat> mTickMap;

private:
    void fillBackground(QPainter *painter, const QSizeF &itemSize);
    void drawGridLine(QPainter *painter, qreal lineVerticalSpace, qreal endX, int spaceCount);
    void drawPriceDistribution(QPainter *painter, qreal startX, qreal dWidth, qreal priceChartEndY, qreal priceHeightSpace);
    void drawForeignerPriceDistribution(QPainter *painter, qreal startX, qreal dWidth, qreal priceChartEndY, qreal priceHeightSpace);
    void drawInstitutionPriceDistribution(QPainter *painter, qreal startX, qreal dWidth, qreal priceChartEndY, qreal priceHeightSpace);
    void drawPriceLabels(QPainter *painter, qreal startX, qreal priceChartEndY, qreal priceHeightSpace);
    void drawCandle(QPainter *painter, const CybosDayData *data, qreal startX, qreal horizontalGridStep, qreal priceChartEndY);
    qreal drawVolume(QPainter *painter, const CybosDayData *data, qreal startX, qreal horizontalGridStep, qreal volumeEndY, qreal priceChartEndY, bool divideBuySell, int index);
    QString int64ToString(long long amount) const;

protected:
    void mouseReleaseEvent(QMouseEvent *e);
    void hoverMoveEvent(QHoverEvent *e);
    void mouseMoveEvent(QMouseEvent *e);
    void mousePressEvent(QMouseEvent *e);

private:
    QString stockCode;
    int countDays;
    QDateTime currentDateTime;
    DayData *dayData;
    qreal priceEndY;
    bool mPinnedCode;

    QString mPcode;
    QString mCorporateName;

    int mHighPriceInYear;
    int mDistanceFromYearHigh;

    qreal drawHorizontalY;
    qreal mouseTrackX;
    qreal mouseTrackY;

    qreal getCandleLineWidth(qreal gap);

signals:
    void corporateNameChanged();
    void pinnedCodeChanged();
    void pcodeChanged();

private slots:
    void dataReceived(QString, CybosDayDatas *);
    void searchReceived(QString);
    void tickDataArrived(CybosTickData *);
    void timeInfoArrived(QDateTime dt);
    void simulationStatusChanged(bool);
};


#endif
