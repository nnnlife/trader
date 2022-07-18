import QtQuick 2.15
import QtQuick.Layouts 1.15
import QtQuick.Controls 2.12


Item {
    width: 200
    height: 100
    //border.width: 2
    //border.color: "#80d7d7d7" 

    GridLayout {
        anchors.fill: parent
        rows: 3
        columns: 6
        //rowSpacing: 0
        //columnSpacing: 0

        Rectangle {
            color: "lightgreen"
            Layout.row: 0
            Layout.column: 0
            width: 200 * 4 / 6
            height: 100 * 2 / 3
            Layout.rowSpan: 2
            Layout.columnSpan: 4
        }

        Text {
            Layout.row: 0
            Layout.column: 4
            Layout.columnSpan: 2
            Layout.fillWidth: true
            height: 100 * 1 / 3
            text: "111M"
        }

        Rectangle {
            Layout.row: 1
            Layout.column: 4
            Layout.columnSpan: 2
            //text: "10.9M"
            color: "blue"
        }
        Text {
            Layout.row: 2
            Layout.column: 0
            Layout.columnSpan: 2
            text: "2.3%"
        }
        Text {
            Layout.row: 2
            Layout.column: 2
            Layout.columnSpan: 2
            text: "-1.1%"
        }
    }
}
