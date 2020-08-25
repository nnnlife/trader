import QtQuick 2.0
import QtQuick.Layouts 1.0
import QtQuick.Controls 2.12
import LensChartView 1.0
import "./"


ApplicationWindow {
    id: root
    width: 1000 
    height: 800 
    visible: true

    LensChartView {
        anchors.fill: parent
    }
}
