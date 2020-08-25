#include <QGuiApplication>
#include <QQmlEngine>
#include <QQuickView>
#include <QQmlApplicationEngine>
#include <QScopedPointer>


int main(int argc, char *argv[]) {
    QCoreApplication::setAttribute(Qt::AA_EnableHighDpiScaling);
    QGuiApplication app(argc, argv);

    QQmlApplicationEngine engine("main.qml");
    return app.exec();
}
