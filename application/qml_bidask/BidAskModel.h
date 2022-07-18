#ifndef BIDASK_MODEL_H_
#define BIDASK_MODEL_H_

#include <qqml.h>
#include <QAbstractTableModel>
#include "DataProvider.h"
#include "BidAskData.h"



class BidAskModel : public QAbstractTableModel {
    Q_OBJECT
    Q_PROPERTY(int highlight READ getHighlight WRITE setHighlight NOTIFY highlightChanged)
    Q_PROPERTY(int yesterdayClose READ getYesterdayClose WRITE setYesterdayClose NOTIFY yesterdayCloseChanged)
    Q_PROPERTY(int totalBidRemain READ getTotalBidRemain WRITE setTotalBidRemain NOTIFY totalBidRemainChanged)
    Q_PROPERTY(int totalAskRemain READ getTotalAskRemain WRITE setTotalAskRemain NOTIFY totalAskRemainChanged)
    Q_PROPERTY(int todayHigh READ getTodayHigh WRITE setTodayHigh NOTIFY todayHighChanged)
    Q_PROPERTY(int todayOpen READ getTodayOpen WRITE setTodayOpen NOTIFY todayOpenChanged)
    Q_PROPERTY(int upperViPrice READ getUpperViPrice NOTIFY upperViPriceChanged)
    Q_PROPERTY(int lowerViPrice READ getLowerViPrice NOTIFY lowerViPriceChanged)
    
    QML_ELEMENT

public:
    enum {
        START_ROW = 1,
        ASK_DIFF_COLUMN = 1,
        ASK_REMAIN_COLUMN = 2,
        BID_REMAIN_COLUMN = 4,
        BID_DIFF_COLUMN = 5,
        PRICE_COLUMN = 3,
        COLUMN_COUNT = 7,
        ROW_COUNT = 22,
        STEPS = 10
    };
    
    BidAskModel(QObject *parent=nullptr);
    ~BidAskModel();

    int columnCount(const QModelIndex &parent = QModelIndex()) const override
    {
        Q_UNUSED(parent);
        return BidAskModel::COLUMN_COUNT;
    }

    int rowCount(const QModelIndex &parent = QModelIndex()) const override
    {
        Q_UNUSED(parent);
        return BidAskModel::ROW_COUNT;
    }

    QVariant data(const QModelIndex &index, int role) const override;

    QHash<int, QByteArray> roleNames() const override
    {
        return { {Qt::DisplayRole, "display"},
                 {Qt::UserRole + 1, "vdiff" },
                 {Qt::UserRole + 2, "profit"},
                 {Qt::UserRole + 3, "is_vi"}};
    }

    void setHighlight(int row);
    int getHighlight() { return highlight; }

    void setYesterdayClose(int yc);
    int getYesterdayClose() const { return yesterdayClose; }

    void setTodayOpen(int to);
    int getTodayOpen() const { return mTodayOpen; }

    void setTodayHigh(int th);
    int getTodayHigh() const { return mTodayHigh; }

    void setTotalBidRemain(uint br);
    void setTotalAskRemain(uint br);
    uint getTotalBidRemain() { return totalBidRemain; }
    uint getTotalAskRemain() { return totalAskRemain; }

    int getUpperViPrice();
    int getLowerViPrice();

    Q_INVOKABLE void sell_immediately(int percentage);
    Q_INVOKABLE void buy_immediately(int percentage);
    Q_INVOKABLE void buy_on_price(int row, int percentage);
    Q_INVOKABLE void sell_on_price(int row, int percentage);

private:
    int highlight;
    int yesterdayClose;
    int mTodayOpen;
    int mTodayHigh;
    bool mIsKospi;
    //int mViType;
    QList<int> mViPrices;
    uint totalBidRemain;
    uint totalAskRemain;

    QString currentStockCode;
    BidAskData mData;
    QDateTime currentDateTime;

private:
    int getPriceByRow(int row) const ;
    uint getRemain(int row, int column) const;
    int getRemainDiff(int row, int column) const;
    void resetData();
    void setHighlightPosition(int price);

private slots:
    void tickArrived(CybosTickData *);
    void bidAskTickArrived(CybosBidAskTickData *);
    void setCurrentStock(QString);
    void timeInfoArrived(QDateTime dt);

signals:
    void highlightChanged();
    void yesterdayCloseChanged();
    void totalAskRemainChanged();
    void totalBidRemainChanged();
    void todayHighChanged();
    void upperViPriceChanged();
    void lowerViPriceChanged();
    void todayOpenChanged();
};


#endif
