#ifndef _SIMULATION_EVENT_H_
#define _SIMULATION_EVENT_H_


#include <QThread>
#include <iostream>
#include "stock_provider.grpc.pb.h"

using stock_api::SimulationStatus;

class SimulationEvent : public QThread {
Q_OBJECT
public:
    SimulationEvent(std::shared_ptr<stock_api::Stock::Stub> stub);
    void stopSimulation();
    bool isSimulation();

protected:
    void run();

private:
    std::shared_ptr<stock_api::Stock::Stub> stub_;

signals:
    void simulationStatusChanged(SimulationStatus *);
};


#endif
