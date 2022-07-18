import QtQuick 2.15
import QtQuick.Layouts 1.0
import QtQuick.Controls 2.12
import Qt.labs.qmlmodels 1.0


Rectangle {
    property int availableAction: 0

    signal startAction(int action)

    ButtonGroup {
        buttons: {
            if (availableAction == 1)
                return editColumn
            return noColumn
        }
    }

    Row {
        anchors.fill: parent
        id: noColumn
    }

    Row {
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.verticalCenter: parent.verticalCenter
        spacing: 10.0
        id: editColumn
        RoundButton {
            width: 30
            height: 30
            text: "\u2713"
            onClicked: startAction(1)
        }

        RoundButton {
            width: 30
            height: 30
            text: "\u2715"
            onClicked: startAction(0)
        }
    }
}
