#include <QGuiApplication>
#include <QQmlEngine>
#include <QQuickView>
#include <QQmlApplicationEngine>
#include <QScopedPointer>
//#include "stock_provider.pb.h"
#include "DataProvider.h"

/*
using stock_api::CybosTickData;
using stock_api::CybosDayDatas;
using stock_api::CybosBidAskTickData;
using stock_api::CybosSubjectTickData;
using google::protobuf::Timestamp;
*/


int main(int argc, char *argv[]) {
    /*
    setenv("TZ", "UTC", 1);
    qRegisterMetaType<CybosTickData>("CybosTickData");
    qRegisterMetaType<CybosDayDatas>("CybosDayDatas");
    qRegisterMetaType<CybosBidAskTickData>("CybosBidAskTickData");
    qRegisterMetaType<CybosSubjectTickData>("CybosSubjectTickData");
    qRegisterMetaType<Timestamp>("Timestamp");
    */
    QCoreApplication::setAttribute(Qt::AA_EnableHighDpiScaling);
    QGuiApplication app(argc, argv);

    DataProvider::getInstance();
    QQmlApplicationEngine engine("main.qml");

    return app.exec();
}
