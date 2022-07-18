#include "MinInfo.h"
#include "Util.h"


MinInfo::MinInfo(int minInterval) {
    minuteInterval = minInterval;
    clear();
}


MinInfo::~MinInfo() {
}


bool MinInfo::isEmpty() {
    return data.day_data_size() == 0;
}


int MinInfo::count() {
    return data.day_data_size();
}


const CybosDayData &MinInfo::get(int i) {
    return data.day_data(i);
}


bool MinInfo::isCloserToMaximum() {
    if (count() > 0) {
        int latest_close = data.day_data(count() - 1).close_price();
        return (getHighestPrice() - latest_close) < (latest_close - getLowestPrice());
    }
    return true;
}


void MinInfo::clear() {
    data.clear_day_data();
    lowestPrice = highestPrice = 0;
    highestVolume = lowestVolume = 0;
    currentDate = currentTime = 0;
}


int MinInfo::getLatestClosePrice() {
    if (count() == 0)
        return 0;

    return data.day_data(count() - 1).close_price();
}


void MinInfo::setCurrentDateTime(uint cd, uint ct) {
    currentDate = cd;
    currentTime = ct;
}


void MinInfo::setData(CybosDayDatas *cd) {
    clear();

    for (int i = 0; i < cd->day_data_size(); i++) {
        const CybosDayData &d = cd->day_data(i);
        if (d.date() == currentDate && d.time() > currentTime)
            break;

        CybosDayData * nd = data.add_day_data();
        *nd = d;
        uint time = d.time();

        uint volume = d.volume();
        uint amount = d.amount();

        for (int j = i + 1; j < cd->day_data_size(); j++) {
            const CybosDayData &p = cd->day_data(j);
            uint ctime = p.time();
            i++;
            if (currentDate == d.date() && ctime > currentTime) {
                i--;
                break;
            }
            else if (time + minuteInterval - 1 >= ctime) {
                if (p.highest_price() > nd->highest_price())
                    nd->set_highest_price(p.highest_price());

                if (p.lowest_price() < nd->lowest_price())
                    nd->set_lowest_price(p.lowest_price());
                
                nd->set_close_price(p.close_price());
                volume += p.volume();
                amount += p.amount();
            }
            else {
                i--;
                break;
            }
        }
        nd->set_volume(volume);
        nd->set_amount(amount);
        nd->set_time(morning::Util::decreaseTime(nd->time(), 1));

        if (nd->highest_price() > highestPrice)
            highestPrice = nd->highest_price();

        if (lowestPrice == 0 || nd->lowest_price() < lowestPrice)
            lowestPrice = nd->lowest_price();

        if (nd->volume() > highestVolume)
            highestVolume = nd->volume();

        if (lowestVolume == 0 || nd->volume() < lowestVolume)
            lowestVolume = nd->volume();

//        qWarning() << i << "\t" << d.time() << "\t" << nd->time() << nd->start_price() << "\t" << nd->close_price() << "\t" << nd->highest_price() << "\t" << nd->lowest_price();
    }
    /*
    qWarning() << "Highest : " << getHighestPrice();
    qWarning() << "Lowest : " << getLowestPrice();
    qWarning() << "Highest Volume : " << getHighestVolume();
    qWarning() << "Lowest Volume : " << getLowestVolume();
    qWarning() << "last : " << cd->day_data(cd->day_data_size() - 1).time();
    */
}
