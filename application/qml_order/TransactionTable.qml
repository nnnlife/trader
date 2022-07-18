import QtQuick 2.15
import QtQuick.Layouts 1.0
import QtQuick.Controls 2.13
import Qt.labs.qmlmodels 1.0
import order.backend 1.0


TableView {
    id: transactionTable
    clip: true
    topMargin: columnsHeader.implicitHeight
    property var columnWidths: [50, 80, 90, 70, 130, 120, 60, 80, 80]
    columnWidthProvider: function (column) { return columnWidths[column]; }
    flickableDirection: Flickable.VerticalFlick
    boundsBehavior: Flickable.StopAtBounds
    reuseItems: false
    contentHeight: rows * 40

    Row {
        id: columnsHeader
        y: transactionTable.contentY
        z: 2
        Repeater {
            model: transactionTable.columns > 0 ? transactionTable.columns : 1
            Label {
                width: transactionTable.columnWidthProvider(modelData)
                height: 30
                text: transactionTable.model.headerData(modelData, Qt.Horizontal)
                color: "white"
                font.pixelSize: 15
                padding: 10
                verticalAlignment: Text.AlignVCenter
                horizontalAlignment: Text.AlignHCenter

                background: Rectangle { 
                    color: "#003767"
                    border.color: "#aaaaaa"
                    border.width: 1
                }
            }
        }
    }

    delegate: DelegateChooser {
        DelegateChoice {
            column: 3
            BuySellComboBox {
                implicitHeight: 40
                border.width: 1
                border.color: "#d7d7d7"
                isBuy: display ? 1 : 0
                isReadOnly: row != 0

                onOrderTypeChanged: {
                    //console.log('order type changed', index)
                    editData = index
                }
            }
        }

        DelegateChoice {
            column: 4
            QtyCell {
                implicitHeight: 40
                qty: display
                editQty: editData
                isReadOnly: !isQtyEditable
                onQtyValueChanged: {
                    console.log('edit qty changed', display, value, row)
                    editData = value
                }
            }
        }
        DelegateChoice {
            column: 5
            PriceCell {
                implicitHeight: 40
                stockMarketType: marketType
                price: {
                    editPrice = editData
                    return display
                }

                onEditPriceChanged: {
                    //console.log('edit price changed', display, editPrice, row)
                    editData = editPrice
                }
            }
        }

        DelegateChoice {
            column: 7
            MethodCombo {
                implicitHeight: 40
                border.width: 1
                border.color: "#d7d7d7"
                orderMethod: editData
                onIndexChanged: {
                    editData = index
                }
            }
        }

        DelegateChoice {
            column: 8
            ActionButton {
                implicitHeight: 40
                border.width: 1
                border.color: "#d7d7d7"
                availableAction: 1
                onStartAction: {
                    editData = action
                }
            }
        }


        DelegateChoice {
            Rectangle {
                border.width: 1
                border.color: "#d7d7d7"
                implicitHeight: 40

                Text {
                    verticalAlignment: Text.AlignVCenter
                    horizontalAlignment: Text.AlignHCenter
                    text: display
                    anchors.fill: parent
                }
            }
        }
    }

    ScrollBar.vertical: ScrollBar {
        topPadding: 30
    }
}
