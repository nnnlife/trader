#ifndef STOCK_STAT_H_
#define STOCK_STAT_H_

#include <QObject>
#include <QMap>
#include <QStringList>
#include <QDateTime>
#include "DataProvider.h"


class StockInfo : public QObject {
Q_OBJECT
public:
    StockInfo(const QString &code, const QDateTime &dt);
    ~StockInfo();
    const QString &getName() { return m_name; }
    void setTodayData(int openPrice, int currentPrice, uint64_t amount);
    bool isYesterdayDataReceived();
    bool isTodayDataReceived();
    const CybosDayData &getYesterdayData() { return yesterdayData; }
    int beforeYesterdayClosePrice();
    int todayOpenPrice() { return m_todayOpen; }
    int todayCurrentPrice() { return m_currentPrice; }
    int yearHighPrice() { return m_yearHigh; }
    uint64_t todayAmount() { return m_todayAmount; }

private:
    QString m_code;
    QString m_name;
    int m_todayOpen;
    int m_currentPrice;
    int m_yearHigh;
    bool m_isKospi;
    uint64_t m_todayAmount;
    CybosDayData yesterdayData;
    CybosDayData beforeYesterdayData;

private slots:
    void dayDataReceived(QString code, CybosDayDatas *data);

signals:
    void infoUpdated(QString);
};


class StockStat : public QObject {
Q_OBJECT
public:
    static StockStat * instance() {
        static StockStat *stat = NULL;
        if (stat == NULL)
            stat = new StockStat;

        return stat;
    }

    QStringList getRecentSearch();
    QStringList getFavoriteList();
    QStringList getViList();
    TopList * getYtopAmountList();
    QStringList getTtopAmountList(TodayTopSelection s);
    QStringList getStrategyList();
    QStringList getUpperLimitList();
    void addToFavorite(const QString &code);
    void removeFromFavorite(const QString &code);

    bool isInFavoriteList(const QString &code) const;
    StockInfo * getInfo(const QString &code);
    void setCurrentCode(const QString &section, const QString &code);
    const QDateTime &currentDateTime() { return m_currentDateTime; }
    void clearRecentList();

private:
    StockStat();

    QMap<QString, StockInfo *> infoMap;
    QDateTime m_currentDateTime;
    void clearStat();
    QStringList mCurrentFavoriteList;

private slots:
    void tickArrived(CybosTickData *);
    void timeInfoArrived(QDateTime dt);
    void alarmArrived(CybosStockAlarm *);

signals:
    void stockListTypeChanged(QString);
    void infoUpdated(QString);
    void infoCleared();
    void currentFocusChanged(QString);
};


#endif
