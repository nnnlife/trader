import QtQuick 2.5
import QtQuick.Layouts 1.2
import QtQuick.Controls 1.4


Item {
    width: 640
    height: 480

    GridLayout {
        anchors.fill: parent
        rows: 2
        columns: 2

        Rectangle {
            Layout.minimumWidth: 320
            Layout.minimumHeight: 240
            color: "yellow"
            Layout.row: 0
            Layout.column: 0
        }

        Rectangle {
            color: "lightgreen"
            Layout.row: 0
            Layout.column: 1
            Layout.minimumWidth: 320
            Layout.minimumHeight: 240
        }


        Rectangle {
            color: "lightgreen"
            Layout.row: 1
            Layout.column: 0
            Layout.minimumWidth: 320
            Layout.minimumHeight: 240
        }

        Rectangle {
            color: "lightgreen"
            Layout.row: 1
            Layout.column: 1
            Layout.minimumWidth: 320
            Layout.minimumHeight: 240
        }
    }
}
