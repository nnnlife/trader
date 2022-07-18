#include "SpeedStatistics.h"

SpeedStatistics::SpeedStatistics(int _secs, QObject *parent)
: QObject(parent) {
    secs = _secs;
}


void SpeedStatistics::bidAskTickArrived(CybosBidAskTickData *data) {

}


void SpeedStatistics::stockTickArrived(CybosTickData *data) {

}
