import QtQuick 2.15
import QtQuick.Layouts 1.0
import QtQuick.Controls 2.12
import Qt.labs.qmlmodels 1.0


Rectangle {
    property var orderMethod: 0
    property var methods: ["", "IMM", "ON_M", "ON_P"]
    signal indexChanged(int index)

    ComboBox {
        id: combo
        anchors.fill: parent
        model: methods
        indicator.visible: false
        flat: true
        currentIndex: orderMethod

        contentItem: Text {
            text: combo.displayText
            verticalAlignment: Text.AlignVCenter
            horizontalAlignment: Text.AlignHCenter
        }
        onCurrentIndexChanged: {
            indexChanged(currentIndex)
        }
    }
}
