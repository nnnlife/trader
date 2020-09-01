#ifndef SEARCH_BACKEND_H_
#define SEARCH_BACKEND_H_


#include <QObject>
#include <qqml.h>
#include <QTimer>
#include "DataProvider.h"


class SearchBackend : public QObject
{
    Q_OBJECT
    Q_PROPERTY(QString currentCode READ currentCode WRITE setCurrentCode NOTIFY currentCodeChanged)
    Q_PROPERTY(QDateTime currentDateTime READ currentDateTime WRITE setCurrentDateTime NOTIFY currentDateTimeChanged)
    Q_PROPERTY(QDateTime serverDateTime READ serverDateTime WRITE setServerDateTime NOTIFY serverDateTimeChanged)
    Q_PROPERTY(bool simulationRunning READ simulationRunning WRITE setSimulationRunning NOTIFY simulationRunningChanged)
    Q_PROPERTY(qreal simulationSpeed READ simulationSpeed WRITE setSimulationSpeed NOTIFY simulationSpeedChanged)
    QML_ELEMENT
    QML_SINGLETON

public:
    explicit SearchBackend(QObject *parent = nullptr);

    QString currentCode();
    QDateTime currentDateTime();
    QDateTime serverDateTime();
    bool simulationRunning();
    qreal simulationSpeed();

    void setCurrentCode(const QString &code);
    void setCurrentDateTime(const QDateTime &dt);
    void setSimulationRunning(bool r);
    void setServerDateTime(const QDateTime &dt);
    void setSimulationSpeed(qreal s);

    Q_INVOKABLE void sendCurrentStock(const QString &code);
    Q_INVOKABLE void sendCurrentDateTime(const QDateTime &dt);
    Q_INVOKABLE void launchTick();
    Q_INVOKABLE void launchTrader();
    Q_INVOKABLE void launchBidAsk();
    Q_INVOKABLE void launchDayChart();
    Q_INVOKABLE void launchFavorite();
    Q_INVOKABLE void launchLens();

    Q_INVOKABLE void startSimulation();
    Q_INVOKABLE void stopSimulation();
    Q_INVOKABLE void startSubscribeCodes();

private:
    QString m_currentCode;
    QDateTime m_currentDateTime;
    QDateTime m_serverDateTime;
    bool m_simulationRunning;
    qreal m_simulationSpeed;
    bool mIsManualTime = false;
    QTimer * mTimer;

    bool launchApp(const QString &path, const QString &name);

private slots:
    void stockCodeChanged(QString code);
    void timeInfoArrived(QDateTime dt);
    void setSimulationStatus(bool status);
    void setCurrentTime();

signals:
    void currentCodeChanged();
    void currentDateTimeChanged();
    void simulationRunningChanged();
    void simulationSpeedChanged();
    void serverDateTimeChanged();
};


#endif
