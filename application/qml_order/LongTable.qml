import QtQuick 2.15
import QtQuick.Layouts 1.0
import QtQuick.Controls 2.12
import Qt.labs.qmlmodels 1.0

TableView {
    id: longTable
    //columnSpacing: -1
    //rowSpacing: -1
    clip: true
    topMargin: columnsHeader.implicitHeight
    flickableDirection: Flickable.VerticalFlick
    boundsBehavior: Flickable.StopAtBounds
    property var columnWidths: [100, 70, 70, 70, 60, 100]
    columnWidthProvider: function (column) { return columnWidths[column]; }
    contentHeight: rows * 40

    Row {
        id: columnsHeader
        y: longTable.contentY
        z: 2
        Repeater {
            model: longTable.columns > 0 ? longTable.columns : 1
            Label {
                width: longTable.columnWidthProvider(modelData)
                height: 30
                text: longTable.model.headerData(modelData, Qt.Horizontal)
                color: '#aaaaaa'
                font.pixelSize: 15
                padding: 10
                verticalAlignment: Text.AlignVCenter
                horizontalAlignment: Text.AlignHCenter

                background: Rectangle { 
                    color: "#333333"
                    border.color: "#aaaaaa"
                    border.width: 1
                }
            }
        }
    }

    delegate: DelegateChooser {
        DelegateChoice {
            column: 2
            Rectangle {
                border.width: 1
                border.color: "#d7d7d7"
                implicitHeight: 40

                Text {
                    text: display.toFixed(2) + "%"
                    anchors.fill: parent
                    verticalAlignment: Text.AlignVCenter
                    horizontalAlignment: Text.AlignHCenter
                    color: {
                        if (display > 0.0)
                            return "red"
                        else if (display < 0.0)
                            return "blue"
                        return "black"
                    }
                }
                MouseArea {
                    anchors.fill: parent
                    onClicked: {
                        longTable.model.selectionChanged(model.row)
                    }
                }
            }
        }

        DelegateChoice {
            Rectangle {
                implicitHeight: 40 
                border.width: 1
                border.color: "#d7d7d7"

                Text {
                    text: {
                        if (typeof(display) == "number")
                            return qsTr("%L1").arg(display)
                        return display
                    }

                    anchors.fill: parent
                    verticalAlignment: Text.AlignVCenter
                    horizontalAlignment: Text.AlignHCenter
                }
                MouseArea {
                    anchors.fill: parent
                    onClicked: {
                        if (model.column == 0) {
                            longTable.model.setCurrentStock(model.row)
                        }
                        else {
                            longTable.model.selectionChanged(model.row)
                        }
                    }
                }
            }
        }
    }

    ScrollBar.vertical: ScrollBar {
        topPadding: 30
    }
}
