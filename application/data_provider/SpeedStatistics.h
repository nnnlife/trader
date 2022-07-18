#ifndef SPEED_STATISTICS_H_
#define SPEED_STATISTICS_H_

#include <QObject>
#include <QMap>
#include "stock_provider.grpc.pb.h"

using stock_api::CybosBidAskTickData;
using stock_api::CybosTickData;


class SpeedData {
public:
    QList<int> speed;
};


class SpeedStatistics : public QObject {
Q_OBJECT
public:
    SpeedStatistics(int secs, QObject *parent);

private:
    int secs;
    QMap<QString, SpeedData *> statistics;

private slots:
    void bidAskTickArrived(CybosBidAskTickData *);
    void stockTickArrived(CybosTickData *);
};


#endif
