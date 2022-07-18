import QtQuick 2.15
import QtQuick.Layouts 1.0
import QtQuick.Controls 2.12
import TradingModel 1.0
import Qt.labs.qmlmodels 1.0


ApplicationWindow {
    id: root
    width: 1240; height: 400
    visible: true

    RowLayout {
        id: editArea
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.right: parent.right
        height: 30
        CheckBox {
            Layout.fillHeight: true
            Layout.fillWidth: true
            checked: false
            text: 'Set to pin Code'
        }

        Button {
            Layout.fillHeight: true
            Layout.fillWidth: true
            font.pixelSize: 12
            text: 'Reset'
        }

        Label {
            Layout.fillHeight: true
            Layout.fillWidth: true
            font.pixelSize: 12
            text: tradingModel.balance
            verticalAlignment: Text.AlignVCenter
        }
    }

    TradingTable {
        anchors.top: editArea.bottom
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        model: TradingModel{
            id: tradingModel
        }
    }
}
