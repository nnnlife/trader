import QtQuick 2.5
import QtQuick.Layouts 1.2
import QtQuick.Controls 1.4

Item {
    width: 640
    height: 480

    GridLayout {
        anchors.fill: parent

        columns: 5
        rows: 2

        Rectangle {
            Layout.row: 0
            Layout.column: 0
            Layout.columnSpan: 4
            Layout.rowSpan: 2
            width: 400 
            height: 240

            color: "red"
        }

        Rectangle {
            Layout.row: 0
            Layout.column: 4
            Layout.columnSpan: 1
            Layout.rowSpan: 2
            width: 320
            height: 240

            color: "green"
        }

        Rectangle {
            Layout.row: 2
            Layout.column: 0
            Layout.columnSpan: 5
            Layout.rowSpan: 3

            width: 320
            height: 240

            color: "blue"
        }
    }
}
