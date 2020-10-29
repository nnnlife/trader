#include "StockStat.h"
#include <QDebug>


StockStat::StockStat()
: QObject(nullptr) {
    connect(DataProvider::getInstance(), &DataProvider::timeInfoArrived, this, &StockStat::timeInfoArrived);
    connect(DataProvider::getInstance(), &DataProvider::stockListTypeChanged, this, &StockStat::stockListTypeChanged);
    connect(DataProvider::getInstance(), &DataProvider::tickArrived, this, &StockStat::tickArrived);

    DataProvider::getInstance()->startStockCodeListening();
    DataProvider::getInstance()->startListTypeListening();
    DataProvider::getInstance()->startStockTick();
}


QStringList StockStat::getRecentSearch() {
    return DataProvider::getInstance()->getRecentSearch();
}


QStringList StockStat::getUpperLimitList() {
    qWarning() << "getUpperLimistList : " << DataProvider::getInstance()->getYesterdayUpperLimitList().count();
    return DataProvider::getInstance()->getYesterdayUpperLimitList();
}


QStringList StockStat::getFavoriteList() {
    mCurrentFavoriteList = DataProvider::getInstance()->getFavoriteList();
    return mCurrentFavoriteList;
}


bool StockStat::isInFavoriteList(const QString &code) const {
    return mCurrentFavoriteList.contains(code);
}


QStringList StockStat::getViList() {
    return DataProvider::getInstance()->getViList();
}


QStringList StockStat::getStrategyList() {
    return DataProvider::getInstance()->getStrategyList();
}


QStringList StockStat::getTtopAmountList(TodayTopSelection s) {
    return DataProvider::getInstance()->getTtopAmountList(s);
}


TopList * StockStat::getYtopAmountList() {
    return DataProvider::getInstance()->getYtopAmountList();
}


void StockStat::addToFavorite(const QString &code) {
    DataProvider::getInstance()->addToFavorite(code);
}


void StockStat::removeFromFavorite(const QString &code) {
    DataProvider::getInstance()->removeFromFavorite(code);
}


void StockStat::timeInfoArrived(QDateTime dt) {
    //qWarning() << "timeInfo arrived"  << dt << "\tisSimul: " << DataProvider::getInstance()->isSimulation();
    if (!m_currentDateTime.isValid() || !DataProvider::getInstance()->isSimulation()) {
        m_currentDateTime = dt;
        clearStat();
        qWarning() << "clearStat";
        emit infoCleared();
    }
}


void StockStat::setCurrentCode(const QString &section, const QString &code) {
    emit currentFocusChanged(section);
    DataProvider::getInstance()->setCurrentStock(code);
}


StockInfo * StockStat::getInfo(const QString &code) {
    if (infoMap.contains(code))
        return infoMap[code];
    else if (currentDateTime().isValid() && !infoMap.contains(code)) {
        infoMap[code] = new StockInfo(code, currentDateTime());
        connect(infoMap[code], &StockInfo::infoUpdated, this, &StockStat::infoUpdated);
        return infoMap[code];
    }
    return nullptr;
}


void StockStat::clearStat() {
    QMapIterator<QString, StockInfo *> i(infoMap);
    while (i.hasNext()) {
        i.next();
        delete i.value();
    }
    infoMap.clear();
}


void StockStat::tickArrived(CybosTickData *data) {
    QString code = QString::fromStdString(data->code());
    if (infoMap.contains(code)) {
        StockInfo *info = getInfo(code);
        info->setTodayData(data->start_price(), data->current_price(),
                            data->cum_amount());
        emit infoUpdated(code);
    }
    delete data;
}


void StockStat::alarmArrived(CybosStockAlarm *alarm) {
    qWarning() << "alarm arrived : " << QString::fromStdString(alarm->code()) << "\t" <<
                    alarm->alarm_category() << "\t" << QString::fromStdString(alarm->title());
}


void StockStat::clearRecentList() {
    DataProvider::getInstance()->clearRecentList();
}


StockInfo::StockInfo(const QString &code, const QDateTime &dt)
: QObject(nullptr) {
    m_code = code;
    m_todayOpen = m_currentPrice = m_yearHigh = 0;
    m_todayAmount = 0;
    m_isKospi = DataProvider::getInstance()->isKospi(code);
    m_name = DataProvider::getInstance()->getCompanyName(code);
    m_yearHigh = DataProvider::getInstance()->getYearHighInfo(code)->price();
    connect(DataProvider::getInstance(), &DataProvider::dayDataReady, this, &StockInfo::dayDataReceived);
    DataProvider::getInstance()->requestDayData(m_code, 10, dt.addDays(-1));
}


StockInfo::~StockInfo() {}


void StockInfo::dayDataReceived(QString code, CybosDayDatas *data) {
    if (m_code != code) 
        return;
    int count = data->day_data_size();
    // TODO: conside new stocked
    if (count > 1) {
        const CybosDayData &d = data->day_data(count - 1);
        const CybosDayData &d2 = data->day_data(count - 2);
        yesterdayData = d;
        beforeYesterdayData = d2;
        //qWarning() << code << "\tdate: " << d.date() << "\tamount: " << d.amount();
        emit infoUpdated(m_code);
    }
    else {
        qWarning() << code << " data size is under 2, actual: " << count;
    }
}



void StockInfo::setTodayData(int openPrice, int currentPrice, uint64_t amount) {
    m_todayOpen = openPrice;
    m_currentPrice = currentPrice;
    if (m_isKospi)
        m_todayAmount = amount * 10000;
    else
        m_todayAmount = amount * 1000;
}


int StockInfo::beforeYesterdayClosePrice() {
    return beforeYesterdayData.close_price();
}


bool StockInfo::isYesterdayDataReceived() {
    return yesterdayData.close_price() == 0;
}


bool StockInfo::isTodayDataReceived() {
    return m_todayOpen == 0;
}
