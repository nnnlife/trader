import QtQuick 2.15
import QtQuick.Layouts 1.0
import QtQuick.Controls 2.12
import Qt.labs.qmlmodels 1.0



Rectangle {
    id: myrec
    height: 35
    width: 100
    color: 'yellow'
    border.width: 1
    border.color: "#d7d7d7"

    Row {
        //spacing: 5
        id: rowLayout
        anchors.horizontalCenter: parent.horizontalCenter
        height: parent.height
        Button {
            implicitWidth: 30
            implicitHeight: 30
            anchors.verticalCenter: parent.verticalCenter
            text: "I"
        }
        Button {
            implicitWidth: 30
            implicitHeight: 30
            anchors.verticalCenter: parent.verticalCenter
            text: "C"
        }

        Component.onCompleted: {
            console.log('row w and h', rowLayout.width, rowLayout.height)
        }
    }

    onWidthChanged: {
        console.log('width, height', width, height)
    }
}

