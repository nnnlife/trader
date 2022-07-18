import QtQuick 2.15
import QtQuick.Layouts 1.0
import QtQuick.Controls 2.12
import Qt.labs.qmlmodels 1.0


Rectangle {
    property var isBuy: 0
    property var isReadOnly: false
    signal orderTypeChanged(int index)

    Text {
        verticalAlignment: Text.AlignVCenter
        horizontalAlignment: Text.AlignHCenter
        text: isBuy == 0 ? "매도" : "매수"
        anchors.fill: parent
        visible: isReadOnly
    }

    ComboBox {
        id: combo
        visible: !isReadOnly
        anchors.fill: parent
        model: ["매도", "매수"]
        indicator.visible: false
        flat: true
        currentIndex: isBuy

        contentItem: Text {
            color: combo.currentIndex == 0 ? "blue" : "red"
            text: combo.displayText
            verticalAlignment: Text.AlignVCenter
            horizontalAlignment: Text.AlignHCenter
        }
        onCurrentIndexChanged: {
            orderTypeChanged(currentIndex)
        }
    }
}
