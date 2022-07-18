import QtQuick 2.15
import QtQuick.Layouts 1.0
import QtQuick.Controls 2.12
import Qt.labs.qmlmodels 1.0
import order.backend 1.0


ApplicationWindow {
    id: root
    width: 1250; height: 300
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
            onClicked: {
                longTable.model.refresh()
                transactionTable.model.refresh()
            }
        }
    }

    RowLayout {
        anchors.top: editArea.bottom
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        spacing: 1.0

        LongTable {
            id: longTable
            Layout.fillHeight: true
            Layout.minimumWidth: 470
            model: LongModel {}
        }

        TransactionTable {
            id: transactionTable
            Layout.fillHeight: true
            Layout.fillWidth: true
            model: TransactionModel {}
        }
    }
}
