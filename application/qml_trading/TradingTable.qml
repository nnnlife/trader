import QtQuick 2.15
import QtQuick.Layouts 1.0
import QtQuick.Controls 2.12
import TradingModel 1.0
import Qt.labs.qmlmodels 1.0

TableView {
    id: tradingTable
    columnSpacing: -1
    rowSpacing: -1
    clip: true
    topMargin: columnsHeader.implicitHeight
    flickableDirection: Flickable.VerticalFlick
    boundsBehavior: Flickable.StopAtBounds
    property var columnWidths: [90, 50, 100, 100, 60, 60, 90, 110, 80, 110, 80, 100, 70, 80, 70]
    columnWidthProvider: function (column) { return columnWidths[column]; }
    contentHeight: rows * 35


    Row {
        id: columnsHeader
        y: tradingTable.contentY
        z: 2
        Repeater {
            model: tradingTable.columns > 0 ? tradingTable.columns : 1
            Label {
                width: tradingTable.columnWidthProvider(modelData)
                height: 30
                text: tradingTable.model.headerData(modelData, Qt.Horizontal)
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
            column: 4
            Rectangle {
                border.width: 1
                border.color: "#d7d7d7"
                implicitHeight: 35

                Text {
                    text: {
                        if (qty == 0)
                            return "-"
                        else 
                            return display.toFixed(2) + "%"
                    }
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
            }
        }
        DelegateChoice {
            column: 11 
            Rectangle {
                implicitHeight: 35
                border.width: 1
                border.color: "#d7d7d7"

                Row {
                    spacing: 5
                    height: parent.height
                    anchors.horizontalCenter: parent.horizontalCenter
                    Button {
                        visible: {
                            if (qty > 0 && status !=0 && traded_qty != qty)
                                return true
                            return false
                        }
                        implicitWidth: 30
                        implicitHeight: 30
                        anchors.verticalCenter: parent.verticalCenter
                        text: "I"
                        onClicked: tradingTable.model.changeToImmediate(model.row, order_num)
                    }
                    Button {
                        visible: {
                            if (qty > 0 && status != 0 && traded_qty != qty && status != 1)
                                return true
                            return false
                        }
                        implicitWidth: 30
                        implicitHeight: 30
                        anchors.verticalCenter: parent.verticalCenter
                        text: "C"
                        onClicked: tradingTable.model.cancelOrder(model.row, order_num)
                    }
                }
            }
        }

        DelegateChoice {
            Rectangle {
                implicitHeight: 35 
                border.width: 1
                border.color: "#d7d7d7"
                color: {
                    if (traded_qty != qty) {
                        return "#70ffff99"
                    }
                    return "white"
                }

                Text {
                    text: display
                    anchors.fill: parent
                    verticalAlignment: Text.AlignVCenter
                    horizontalAlignment: Text.AlignHCenter
                }
                MouseArea {
                    anchors.fill: parent
                    onClicked: {
                        tradingTable.model.selectionChanged(model.row)
                    }
                }
            }
        }
    }
    ScrollIndicator.vertical: ScrollIndicator { }
}

