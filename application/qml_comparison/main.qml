import QtQuick 2.0
import QtQuick.Layouts 1.0
import QtQuick.Controls 2.12
import VolumePriceChartView 1.0
import "./"


ApplicationWindow {
    id: root
    width: 450 // 9 * 60
    height: 480 // 12 * 40
    visible: true

    VolumePriceChartView {
        anchors.fill: parent
    }
}
