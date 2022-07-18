import QtQuick 2.15
import QtQuick.Layouts 1.0
import QtQuick.Controls 2.15
import BidAskModel 1.0
import Qt.labs.qmlmodels 1.0
import "../data_provider"


ApplicationWindow {
    id: root
    width: 1000; height: 800
    visible: true

    TableView {
        id: bidAskTable
        anchors.fill: parent
        columnSpacing: 0
        rowSpacing: 0
        clip: true
        property int activeBuyRow: -1
        property int activeSellRow: -1

        model: BidAskModel{
            id: bidaskModel
        }

        delegate: DelegateChooser {
            DelegateChoice {
                column: 3
                Rectangle {
                    id: priceColumn
                    implicitWidth: (root.width) / 7
                    implicitHeight: (root.height) / 22

                    color: {
                        if (model.row <= 20 && model.row > 10) return "#10ff0000"
                        else if (model.row > 0 && model.row <= 10) return "#100000ff"
                        else return "#ffffff"
                    }
                    border.color: bidaskModel.highlight == model.row ?"black":"#d7d7d7"
                    border.width: bidaskModel.highlight == model.row ? 2:1

                    Text {
                        text: {
                            if (model.row == 0)
                                return qsTr("%L1").arg(bidaskModel.upperViPrice)
                            else if (model.row == 21)
                                return qsTr("%L1").arg(bidaskModel.lowerViPrice)
                            return qsTr("%L1").arg(display)
                        }
                        horizontalAlignment: Text.AlignRight
                        verticalAlignment: Text.AlignVCenter
                        anchors.fill: parent
                        font.pointSize: 12
                        rightPadding: 5
                        font.bold: {
                            if (typeof(display) == "number" && (bidaskModel.todayHigh == display || bidaskModel.todayOpen == display))
                                return true;
                            return false;
                        }
                        color: {
                            var fcolor = "black"

                            if (typeof(display) == "number"){
                                if (display == bidaskModel.todayOpen) {
                                    fcolor = 'green'
                                }
                                else if (display > bidaskModel.yesterdayClose) {
                                    fcolor = "red"
                                }
                                else if (display < bidaskModel.yesterdayClose) {
                                    fcolor = "blue"
                                }
                            }
                            // console.log("display", typeof(display), parseInt(display), bidaskModel.yesterdayClose, typeof(bidaskModel.yesterdayClose), fcolor)
                            return fcolor;
                        }
                    }
                    Text {
                        text: {
                            if (typeof(profit) == "number") {
                                return profit.toFixed(2)
                            }
                            return ""
                        }
                        anchors.left: parent.left
                        anchors.bottom: parent.bottom
                        font.pointSize: 7
                        color: {
                            if (typeof(display) == "number") {
                                if (profit > 0) 
                                    return "red"
                                else if (profit < 0) 
                                    return "blue"
                            }
                            return "black"
                        }
                    }
                    Rectangle {
                        anchors.left: parent.left
                        anchors.top: parent.top
                        width: parent.width / 10
                        height: parent.height / 4
                        color: "green"
                        visible: is_vi
                    }
                    MouseArea {
                        anchors.fill: parent
                        onClicked: {
                            console.log("row : ", model.row)
                        }
                    }
                }
            }

            DelegateChoice {
                column: 2
                Rectangle {
                    id: askRemainColumn
                    implicitWidth: (root.width) / 7
                    implicitHeight: (root.height) / 22
                    color: "#ffffff"
                    border.color: "#d7d7d7"
                    border.width: 1

                    Rectangle {
                        id: askRemainBar
                        height: parent.height
                        color: "#100000ff"
                        anchors.right: askRemainColumn.right
                        width: {
                            if (model.row <= 10 && typeof(display) == "number" && bidaskModel.totalAskRemain > 0) {
                                //console.log('BID BAR', model.row, display, bidaskModel.totalAskRemain, parent.width * 3.0 * display / bidaskModel.totalAskRemain)
                                return parent.width * 3.0 * display / (bidaskModel.totalAskRemain + bidaskModel.totalBidRemain)
                            }
                            return 0
                        }
                    }

                    Rectangle {
                        height: parent.height
                        color: vdiff > 0 ? "#40ff0000":"#400000ff"
                        anchors.right: vdiff > 0 ? askRemainBar.left : undefined
                        anchors.left: vdiff < 0 ? askRemainBar.left : undefined
                        width: {
                            if (model.row <= 10 && typeof(vdiff) == "number" && bidaskModel.totalAskRemain > 0) {
                                return parent.width * 3.0 * Math.abs(vdiff) / (bidaskModel.totalAskRemain + bidaskModel.totalBidRemain)
                            }
                            return 0
                        }
                    }

                    Text {
                        text: {
                            if (model.row == 21)
                                return bidaskModel.totalAskRemain
                            else if (model.row >= 1 && model.row <= 10)
                                return display + vdiff
                            else
                                return display
                        }
                        anchors.fill: parent
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                        font.pointSize: 11
                        color: model.row > 10 && model.row <= 20 ? "blue":"black"
                    }

                }
            }

            DelegateChoice {
                column: 4
                Rectangle {
                    id: bidRemainColumn
                    implicitWidth: (root.width) / 7
                    implicitHeight: (root.height) / 22
                    color: "#ffffff"
                    border.color: "#d7d7d7"
                    border.width: 1
                    Rectangle {
                        id: bidRemainBar
                        height: parent.height
                        color: "#10ff0000"
                        anchors.left: bidRemainColumn.left
                        width: {
                            if (model.row >= 11 && typeof(display) == "number" && bidaskModel.totalBidRemain > 0) {
                                //console.log('ASK BAR', model.row, display, bidaskModel.totalBidRemain, parent.width * 3.0 * display / bidaskModel.totalBidRemain)
                                return parent.width * 3.0 * display / (bidaskModel.totalBidRemain + bidaskModel.totalAskRemain)
                            }
                            return 0
                        }
                    }

                    Rectangle {
                        height: parent.height
                        color: vdiff > 0 ? "#40ff0000":"#400000ff"
                        anchors.left: vdiff > 0? bidRemainBar.right : undefined
                        anchors.right: vdiff < 0? bidRemainBar.right : undefined
                        width: {
                            if (model.row >= 11 && typeof(vdiff) == "number" && bidaskModel.totalBidRemain > 0) {
                                return parent.width * 3.0 * Math.abs(vdiff) / (bidaskModel.totalBidRemain + bidaskModel.totalAskRemain)
                            }
                            return 0
                        }
                    }

                    Text {
                        text: {
                            if (model.row == 21)
                                return bidaskModel.totalBidRemain
                            else if (model.row >= 11 && model.row <= 20)
                                return display + vdiff
                            else
                                return display
                        }
                        anchors.fill: parent
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                        font.pointSize: 11
                        color: model.row <= 10 && model.row >= 1? "red":"black"
                    }

                }
            }
            DelegateChoice {
                row: 0
                column: 0
                Rectangle {
                    implicitWidth: (root.width - 6) / 7
                    implicitHeight: (root.height - 20) / 22
                    Rectangle {
                        color: "blue"
                        height: parent.height
                        width: {
                            if (typeof(display) == "number") {
                                return parent.width * (1.0 - display)
                            }
                            return 0
                        }
                    }
                }
            }

            DelegateChoice {
                row: 0
                column: 6
                Rectangle {
                    id: buyVolumeBar
                    implicitWidth: (root.width - 6) / 7
                    implicitHeight: (root.height - 20) / 22
                    Rectangle {
                        color: "red"
                        height: parent.height
                        anchors.right: buyVolumeBar.right
                        width: {
                            if (typeof(display) == "number") {
                                return parent.width * display
                            }
                            return 0
                        }
                    }
                }
            }

            DelegateChoice {
                column: 1
                Rectangle {
                    implicitWidth: (root.width - 6) / 7
                    implicitHeight: (root.height - 20) / 22
                    color: "#ffffff"
                    border.color: "#d7d7d7"
                    border.width: 1
                    Text {
                        visible: model.row == 21
                        anchors.fill: parent
                        text: "1/2 SELL"
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                        color: 'blue'
                        font.pointSize: 10
                        z: parent.z + 1
                        MouseArea {
                            anchors.fill: parent
                            onClicked: bidaskModel.sell_immediately(50)
                        }
                    }
                    Rectangle {
                        id: orderBox
                        anchors.fill: parent
                        visible: bidAskTable.activeSellRow == model.row
                        z: bidAskTable.activeSellRow == model.row ? parent.z + 1 : 0
                        Row {
                            spacing: 1
                            anchors.fill: parent
                            SpinBox {
                                id: sellSpinBox
                                implicitWidth: parent.width * 2 / 3
                                implicitHeight: parent.height
                                to: 100
                                from: 25
                                stepSize: 25
                                value: 100
                                up.indicator.width: 25
                                down.indicator.width: 25 
                                onVisibleChanged: {
                                    value = 100
                                }
                            }
                            Button {
                                implicitWidth: parent.width / 3
                                implicitHeight: parent.height
                                text: '매도'
                                onClicked: {
                                    bidaskModel.sell_on_price(model.row, sellSpinBox.value)
                                    bidAskTable.activeSellRow = -1
                                }
                            }
                        }
                    }

                    MouseArea {
                        anchors.fill: parent
                        onClicked: {
                            if (model.row >= 1 && model.row <= 20) {
                                bidAskTable.activeSellRow = model.row
                            }
                        }
                    }
                }
            }

            DelegateChoice {
                column: 5
                Rectangle {
                    implicitWidth: (root.width - 6) / 7
                    implicitHeight: (root.height - 20) / 22
                    color: "#ffffff"
                    border.color: "#d7d7d7"
                    border.width: 1
                    Text {
                        visible: model.row == 21
                        anchors.fill: parent
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                        color: 'red'
                        font.pointSize: 10
                        text: "1/2 BUY"
                        z: parent.z + 1
                        MouseArea {
                            anchors.fill: parent
                            onClicked: bidaskModel.buy_immediately(50)
                        }

                    }

                    Rectangle {
                        id: orderBox
                        anchors.fill: parent
                        visible: bidAskTable.activeBuyRow == model.row
                        z: bidAskTable.activeBuyRow == model.row ? parent.z + 1 : 0
                        Row {
                            spacing: 1
                            anchors.fill: parent
                            SpinBox {
                                id: buySpinBox
                                implicitWidth: parent.width * 2 / 3
                                implicitHeight: parent.height
                                to: 100
                                from: 25
                                stepSize: 25
                                value: 100
                                up.indicator.width: 25
                                down.indicator.width: 25 
                                onVisibleChanged: {
                                    value = 100
                                }
                            }
                            Button {
                                implicitWidth: parent.width / 3
                                implicitHeight: parent.height
                                text: '매수'
                                onClicked: {
                                    // order is important
                                    console.log('BUY ', buySpinBox.value)
                                    bidaskModel.buy_on_price(model.row, buySpinBox.value)
                                    bidAskTable.activeBuyRow = -1
                                }
                            }
                        }
                    }

                    MouseArea {
                        anchors.fill: parent
                        onClicked: {
                            if (model.row >= 1 && model.row <= 20) {
                                console.log('Clicked')
                                bidAskTable.activeBuyRow = model.row
                                //orderBox.z = z + 1
                            }
                        }
                    }
                }
            }

            DelegateChoice {
                Rectangle {
                    implicitWidth: (root.width - 6) / 7
                    implicitHeight: (root.height - 20) / 22
                    color: "#ffffff"
                    border.color: "#d7d7d7"
                    border.width: 1

                    Text {
                        text: {
                            if (model.row == 21 && model.column == 0)
                                return "SELL"
                            else if (model.row == 21 && model.column == 6)
                                return "BUY"
                            else if (model.row == 21 && model.column == 1)
                                return "1/2 SELL"
                            else if (model.row == 21 && model.column == 5)
                                return "1/2 BUY"
                            else if (model.column == 0 || model.column == 6) {
                                return display
                            }
                            return ""
                        }
                        anchors.fill: parent
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                        font.pointSize: 10
                        color: {
                            if (model.row == 21 && (model.column == 0 || model.column == 1))
                                return "blue"
                            else if (model.row == 21 && (model.column == 6 || model.column == 5))
                                return "red"
                            return "black"
                        }
                    }
                    MouseArea {
                        anchors.fill: parent
                        onClicked: {
                            if (model.row == 21 && model.column == 0)
                                bidaskModel.sell_immediately(100)
                            else if (model.row == 21 && model.column ==6)
                                bidaskModel.buy_immediately(100)
                            else if (model.column == 6) 
                                bidAskTable.activeBuyRow = -1
                            else if (model.column == 0)
                                bidAskTable.activeSellRow = -1
                        }
                    }
                }
            }
        }
    }
}
