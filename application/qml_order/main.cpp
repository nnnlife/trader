#include <QGuiApplication>
#include <QQmlEngine>
#include <QQuickView>
#include <QQmlApplicationEngine>
#include <QScopedPointer>
#include <QQuickStyle>
#include "DataProvider.h"



int main(int argc, char *argv[]) {
    QCoreApplication::setAttribute(Qt::AA_EnableHighDpiScaling);
    QGuiApplication app(argc, argv);
    QQuickStyle::setStyle("Material");
    DataProvider::getInstance();
    QQmlApplicationEngine engine("main.qml");

    return app.exec();
}
