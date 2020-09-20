#include "MinuteData.h"
#include <google/protobuf/util/time_util.h>
#include <grpcpp/client_context.h>
#include "DayDataProvider.h"
#include <QDebug>
#include "Util.h"

using google::protobuf::util::TimeUtil;


// TODO: need heartbeat because it is possible having no data for some period

MinuteTick::MinuteTick(const QString &_code, const QDateTime &dt, int intervalMin) {
    code = _code;
    createDateTime = dt;
    previousDataReceived = false;
    currentMSecs = 0;
    yesterdayClose = 0;
    highestVolume = 0;
    openPrice = 0;
    mAmount = 0;
    highestPrice = lowestPrice = 0;
    intervalMinute = intervalMin;
}


MinuteTick::~MinuteTick() {
}


void MinuteTick::skipReceivePreviousData() {
    previousDataReceived = true;
}


void MinuteTick::minuteDataReady(QString _code, CybosDayDatas * data) {
    if (code == _code) {
        previousDataReceived = true;
        QDateTime ct = createDateTime.addSecs(60);
        uint t = ct.time().hour() * 100 + ct.time().minute();
        int inTimeCount = 0;
        //qWarning() << "Ready Time : " << createDateTime;
        for (int i = 0; i < data->day_data_size(); i++) {
            const CybosDayData &d = data->day_data(i);
            uint time = d.time();
            mAmount += (long long)d.amount();
            //qWarning() << "data time : " << time;
            if (time > t) 
                break;
            else 
                inTimeCount++;
        }
        //qWarning() << "receive MinuteData size(" << data->day_data_size() << "), until : " << t << "\t inTime count " << inTimeCount;

        const int im = intervalMinute;
        // if count 6 then complete 1 candle and use last as current
        // if count is 5 then complete 1 -> (5-1)/3 = 1 and queueCount * im = 3, until < 5
        int queueCount = int((inTimeCount - 1) / im);

        for (int i = 0; i < queueCount; i++) {
            for (int j = im * i; j < im * i + im; j++) {
                if (j == im * i)
                    setCurrentData(data->day_data(j));
                else
                    updateCurrentData(data->day_data(j));
            }
            pushToQueue();
        }
        //qWarning() << "start from : " << queueCount * im << "\tuntil : " << inTimeCount;
        for (int i = queueCount * im; i < inTimeCount; i++) {
            if (i == queueCount * im)
                setCurrentData(data->day_data(i));
            else
                updateCurrentData(data->day_data(i));
        }
        //qWarning() << "send minuteTickUpdated";
        if (inTimeCount > 0)
            emit minuteTickUpdated(code);
    }
}


void MinuteTick::setCurrentData(CybosTickData *d, long msec) {
    QDateTime dt = QDateTime::fromMSecsSinceEpoch(msec);
    currentData.set_date(dt.toString("yyyyMMdd").toUInt());
    currentData.set_time(dt.toString("hhmm").toUInt());
    currentData.set_start_price(d->current_price());
    currentData.set_highest_price(d->current_price());
    currentData.set_lowest_price(d->current_price());
    currentData.set_close_price(d->current_price());
    currentData.set_volume(d->volume());
    currentData.set_is_synchronized_bidding(d->market_type() == 49);

    setVolumeBoundary(d->volume());

    if (d->market_type() == 50) {
        currentData.set_amount(d->volume() * d->current_price());
        currentData.set_cum_sell_volume(d->cum_sell_volume());
        currentData.set_cum_buy_volume(d->cum_buy_volume());
    }
    //qWarning() << "setCurrentData Tick : " << dt;
    currentMSecs = msec;
}


void MinuteTick::setCurrentData(const CybosDayData &d) {
    uint t = d.time();
    t = morning::Util::decreaseTime(t, 1);

    QDateTime dt = QDateTime(QDate(int(d.date() / 10000), int(d.date() % 10000 / 100), int(d.date() % 100)), QTime(int(t / 100), int(t % 100), 0));
    //qWarning() << "setCurrentData Day Data : " << dt;
    currentData.set_date(d.date());
    currentData.set_time(t);
    currentData.set_start_price(d.start_price());
    currentData.set_highest_price(d.highest_price());
    currentData.set_lowest_price(d.lowest_price());
    currentData.set_close_price(d.close_price());
    currentData.set_volume(d.volume());

    setPriceBoundary(d.highest_price(), d.lowest_price());
    setVolumeBoundary(d.volume());
    currentData.set_amount(d.amount());
    currentData.set_cum_sell_volume(d.cum_sell_volume());
    currentData.set_cum_buy_volume(d.cum_buy_volume());
    currentData.set_is_synchronized_bidding(false);
    currentMSecs = dt.toMSecsSinceEpoch();
}


bool MinuteTick::isTimeout(long current) {
    if (currentMSecs == 0)
        return false;
    else if (current - currentMSecs > intervalMinute * 60 * 1000)
        return true;

    return false;
}


bool MinuteTick::appendTick(CybosTickData *d) {
    if (!isPreviousDataReceived())
        return false;

    long msec = TimeUtil::TimestampToMilliseconds(d->tick_date());
    yesterdayClose = d->current_price() - d->yesterday_diff();

    // open price will be zero, when market is not opened
    openPrice = d->start_price();
    setPriceBoundary(d->current_price());

    if (currentMSecs == 0) {
        setCurrentData(d, msec);
    }
    else {
        if (isTimeout(msec) || (currentData.is_synchronized_bidding() ^ (d->market_type() == 49))) {
            pushToQueue();
            setCurrentData(d, msec);
        }
        else {
            updateCurrentData(d);
        }
    }

    return true;
}


void MinuteTick::setVolumeBoundary(long long volume) {
    if (volume > highestVolume)
        highestVolume = volume;
}


void MinuteTick::setPriceBoundary(int high, int low) {
    setPriceBoundary(low);
    setPriceBoundary(high);
}


void MinuteTick::setPriceBoundary(int price) {
    if (lowestPrice == 0 || lowestPrice > price)
        lowestPrice = price;

    if (price > highestPrice)
        highestPrice = price;
}


QString MinuteTick::getDebugString() {
    QString debug = QString("current minute size : ");
    debug += QString::number(queue.day_data_size());
    debug += "\ncurrentData: \n";
    debug += QString::fromStdString(currentData.DebugString());
    debug += "\n";
    return debug;
}


void MinuteTick::pushToQueue() {
    CybosDayData *d = queue.add_day_data();
    *d = currentData;
    currentData.Clear();
}


void MinuteTick::updateCurrentData(CybosTickData *d) {
    if (d->current_price() > currentData.highest_price())
        currentData.set_highest_price(d->current_price());
    
    if (d->current_price() < currentData.lowest_price())
        currentData.set_lowest_price(d->current_price());

    currentData.set_close_price(d->current_price());
    currentData.set_volume(currentData.volume() + d->volume());

    setVolumeBoundary(currentData.volume());
    if (d->market_type() == 50) {
        currentData.set_amount(d->volume() * d->current_price() + currentData.amount());
        currentData.set_cum_sell_volume(d->cum_sell_volume());
        currentData.set_cum_buy_volume(d->cum_buy_volume());
    }
}


void MinuteTick::updateCurrentData(const CybosDayData &d) {
    if (d.highest_price() > currentData.highest_price())
        currentData.set_highest_price(d.highest_price());

    if (d.lowest_price() < currentData.lowest_price())
        currentData.set_lowest_price(d.lowest_price());

    currentData.set_close_price(d.close_price());
    currentData.set_volume(currentData.volume() + d.volume());

    setVolumeBoundary(currentData.volume());
    setPriceBoundary(d.highest_price(), d.lowest_price());

    currentData.set_amount(currentData.amount() + d.amount());
    currentData.set_cum_sell_volume(d.cum_sell_volume());
    currentData.set_cum_buy_volume(d.cum_buy_volume());
}


MinuteData::MinuteData(QObject *parent, std::shared_ptr<stock_api::Stock::Stub> stub, int min, const QString &code, bool isSimul)
: QObject(parent) {
    stub_ = stub;
    lastCheckTime = 0;
    intervalMinute = min;
    isSimulation = isSimul;
    currentStockCode = code;
    dayDataProvider = new DayDataProvider(stub_);
}


void MinuteData::setCurrentStockCode(const QString &code) {
    currentStockCode = code;
}


MinuteTick * MinuteData::getMinuteTick(const QString &code, const QDateTime &serverTime) {
    if (!codeMap.contains(code)) {
        codeMap[code] = new MinuteTick(code, serverTime, intervalMinute);
        requestPreviousData(codeMap[code]);
    }

    return codeMap[code]; 
}


void MinuteData::clearData() {
    // TODO: clear MinuteData when realtime data is started
    QMapIterator<QString, MinuteTick *> i(codeMap);
    while (i.hasNext()) {
        i.next();
        delete i.value();
    }
    codeMap.clear();
    currentDateTime = QDateTime();
}


void MinuteData::setSimulation(bool isSimul) {
    if (isSimulation ^ isSimul) {
        isSimulation = isSimul;
        clearData();
    }
}


void MinuteData::requestPreviousData(MinuteTick *tick) {
    connect(dayDataProvider, &DayDataProvider::minuteDataReady,
                tick, &MinuteTick::minuteDataReady);

    connect(tick, &MinuteTick::minuteTickUpdated,
                this, &MinuteData::minuteTickUpdated);
    const QDateTime &dt = tick->getCreateDateTime();

    QDateTime currentDateTime = QDateTime::currentDateTime();
    QDateTime todayLimit = QDateTime(currentDateTime.date(), QTime(18, 30, 0));
    if (dt.date() == currentDateTime.date() && currentDateTime < todayLimit) {
        qWarning() << "request Today Minute Data";
        dayDataProvider->requestTodayMinuteData(tick->getCode());
    }
    else {
        dayDataProvider->requestMinuteData(tick->getCode(), dt, dt); // does not matter since query is done with 1 day
        qWarning() << "request past minute data " << tick->getCode() << "\t" << dt;
    }
}


void MinuteData::timeInfoArrived(QDateTime dt) {
    if (!isSimulation) {
        qWarning() << "not simulation timeInfoArrived clear data";
        clearData();
    }

    currentDateTime = dt;
}


void MinuteData::stockTickArrived(CybosTickData *data) {
    // Clear codeMap when mode is changed between simulation and realtime
    QString code = QString::fromStdString(data->code());

    if (codeMap.contains(code)) {
        if (codeMap[code]->appendTick(data)) 
            emit minuteTickUpdated(code);
    }
    else if (currentStockCode == code && !codeMap.contains(code)) {
        long msec = TimeUtil::TimestampToMilliseconds(data->tick_date());
        QDateTime dt = QDateTime::fromMSecsSinceEpoch(msec);
        qWarning() << "MinuteData: " << code << " created at " << dt;
        codeMap[code] = new MinuteTick(code, dt, intervalMinute);
        requestPreviousData(codeMap[code]);
    }

    delete data;
}
