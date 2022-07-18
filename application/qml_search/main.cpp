#include <QGuiApplication>
#include <QQmlEngine>
#include <QQuickView>
#include <QQmlApplicationEngine>
#include <QScopedPointer>
#include <QFont>


int main(int argc, char *argv[]) {
    QCoreApplication::setAttribute(Qt::AA_EnableHighDpiScaling);
    QGuiApplication app(argc, argv);
    QFont f = app.font();
    f.setPointSize(10);
    app.setFont(f);

    QQmlApplicationEngine engine("main.qml");
    return app.exec();
}
