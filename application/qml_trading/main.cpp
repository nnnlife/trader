#include <QGuiApplication>
#include <QQmlEngine>
#include <QQuickView>
#include <QQmlApplicationEngine>
#include <QScopedPointer>
#include "DataProvider.h"



int main(int argc, char *argv[]) {
    QCoreApplication::setAttribute(Qt::AA_EnableHighDpiScaling);
    QGuiApplication app(argc, argv);

    DataProvider::getInstance();
    QQmlApplicationEngine engine("main.qml");

    return app.exec();
}
