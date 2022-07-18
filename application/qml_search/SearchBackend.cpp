#include "SearchBackend.h"
#include <QDebug>
#include <QProcess>
#include <QStringList>


SearchBackend::SearchBackend(QObject *parent)
: QObject(parent) {
    mTimer = new QTimer(this);
    mTimer->setInterval(1000);
    connect(mTimer, &QTimer::timeout, this, &SearchBackend::setCurrentTime);
    m_currentCode = "";
    m_currentDateTime = QDateTime::currentDateTime();
    m_serverDateTime = QDateTime::currentDateTime();
    m_simulationSpeed = 1.0;

    connect(DataProvider::getInstance(), &DataProvider::stockCodeChanged,
            this, &SearchBackend::stockCodeChanged);
    connect(DataProvider::getInstance(), &DataProvider::timeInfoArrived, this, &SearchBackend::timeInfoArrived);
    connect(DataProvider::getInstance(), &DataProvider::simulationStatusChanged, this, &SearchBackend::setSimulationStatus);
    DataProvider::getInstance()->startStockCodeListening();
    m_simulationRunning = DataProvider::getInstance()->isSimulation();
    //qWarning() << "SearchBackend";
    mTimer->start();
}


void SearchBackend::timeInfoArrived(QDateTime dt) {
    //qWarning() << "SearchBackend>\t" << "timeInfoArrived : " << dt;
    setServerDateTime(dt);
}


void SearchBackend::setCurrentTime() {
    setCurrentDateTime(QDateTime::currentDateTime());
}


QString SearchBackend::currentCode() {
    return m_currentCode;
}


QDateTime SearchBackend::currentDateTime() {
    if (!mIsManualTime)
        return m_currentDateTime; 
    
    return m_serverDateTime;
}


qreal SearchBackend::simulationSpeed() {
    return m_simulationSpeed;
}


bool SearchBackend::simulationRunning() {
    return m_simulationRunning;
}


QDateTime SearchBackend::serverDateTime() {
    return m_serverDateTime;
}


void SearchBackend::stockCodeChanged(QString code) {
    setCurrentCode(code);
}


void SearchBackend::setSimulationRunning(bool r) {
    qWarning() << "setSimulationRunning: org " << m_simulationRunning << "\t value : " << r;
    if (m_simulationRunning ^ r) {
        m_simulationRunning = r;
        emit simulationRunningChanged();
    }
}


void SearchBackend::setSimulationStatus(bool status) {
    qWarning() << "setSimulationStatus : " << status;
    setSimulationRunning(status);
}


void SearchBackend::startSimulation() {
    qWarning() << "startSimulation";
    DataProvider::getInstance()->startSimulation(m_serverDateTime, m_simulationSpeed);
}


void SearchBackend::stopSimulation() {
    qWarning() << "stopSimulation";
    DataProvider::getInstance()->stopSimulation();
}


void SearchBackend::setServerDateTime(const QDateTime &dt) {
    if (m_serverDateTime.toMSecsSinceEpoch() != dt.toMSecsSinceEpoch()) {
        m_serverDateTime = dt;
        emit serverDateTimeChanged();
    }
}


void SearchBackend::setSimulationSpeed(qreal s) {
    if (m_simulationSpeed != s) {
        qWarning() << "Spped SET : "<< s;
        m_simulationSpeed = s;
        emit simulationSpeedChanged();
    }
}


void SearchBackend::setCurrentCode(const QString &code) {
    qWarning() << "setCurrentCode : " << code;
    if (m_currentCode != code) {
        m_currentCode = code;
        emit currentCodeChanged();
    }
}


void SearchBackend::setCurrentDateTime(const QDateTime &dt) {
    if (m_currentDateTime.toMSecsSinceEpoch() != dt.toMSecsSinceEpoch()) {
        //qWarning() << "setCurrentDateTime : " << dt;
        m_currentDateTime = dt;
        emit currentDateTimeChanged();
    }
}


void SearchBackend::sendCurrentStock(const QString &code) {
    DataProvider::getInstance()->setCurrentStock(code);
}


void SearchBackend::sendCurrentDateTime(const QDateTime &dt) {
    mIsManualTime = true;
    qWarning() << "sendCurrentDateTime : " << dt;
    DataProvider::getInstance()->setCurrentDateTime(dt);
}


bool SearchBackend::launchApp(const QString &path, const QString &name) {
    QProcess *process = new QProcess;
    connect(process, &QProcess::started, process, &QProcess::deleteLater);
    //QString dir = qgetenv("MORNING_PATH") + path;
    QString dir = "/devel/trader_rev" + path;
    bool ret = process->startDetached(dir + "/" + name, QStringList(), dir);
    return ret;
}


void SearchBackend::launchTick() {
    launchApp("/application/qml_today", "qml_today");
}


void SearchBackend::launchTrader() {
    launchApp("/application/qml_trading", "qml_trading");
}


void SearchBackend::launchBidAsk() {
    launchApp("/application/qml_bidask", "morning_bidask");
}


void SearchBackend::launchDayChart() {
    launchApp("/application/qml_dayquery", "morning_dayview");
}


void SearchBackend::launchFavorite() {
    launchApp("/application/qml_favorite", "qml_favorite");
}


void SearchBackend::launchLens() {
    launchApp("/application/qml_lens", "qml_lens");
}


void SearchBackend::startSubscribeCodes() {
    QStringList subscribeCodes = DataProvider::getInstance()->getSubscribeCodes();
    qWarning() << "Subscrbie Code count : " << subscribeCodes.size();
    for (int i = 0; i < subscribeCodes.size(); i++) {
        if (!subscribeCodes.at(i).endsWith("_II") && !subscribeCodes.at(i).endsWith("_I"))
            DataProvider::getInstance()->requestTickSubscribe(subscribeCodes.at(i));

        if (subscribeCodes.at(i).startsWith("A")) {
            qWarning() << "START REQUEST TICK" << subscribeCodes.at(i);
            DataProvider::getInstance()->requestBidAskSubscribe(subscribeCodes.at(i));
            DataProvider::getInstance()->requestSubjectSubscribe(subscribeCodes.at(i));
        }
    }
    DataProvider::getInstance()->requestAlarmSubscribe();
}
