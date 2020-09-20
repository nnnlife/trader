import QtQuick 2.15
import QtQuick.Layouts 1.0
import QtQuick.Controls 2.12
import Qt.labs.qmlmodels 1.0
import favorite.backend 1.0

    
ListView {
    id: codeListView
    clip: true
    Layout.alignment: Qt.AlignTop | Qt.AlignHCenter
    spacing: -1.0

    Component {
        id: profitText
        Text {
            leftPadding: 5
            horizontalAlignment: Text.AlignCenter
            verticalAlignment: Text.AlignVCenter
            color: {
                if (profit < 0.0)
                    return "blue"
                else if (profit > 0.0)
                    return "red"

                return "black"
            }
            text: profit.toFixed(2) + "%"
        }
    }

    Component {
        id: smallProfitText
        Text {
            leftPadding: 5
            font.pixelSize: 8
            horizontalAlignment: Text.AlignCenter
            verticalAlignment: Text.AlignVCenter
            color: {
                if (profit < 0.0)
                    return "blue"
                else if (profit > 0.0)
                    return "red"

                return "black"
            }
            text: profit.toFixed(2) + "%"
        }
    }

    Component {
        id: yearProfitText
        Text {
            leftPadding: 0
            verticalAlignment: Text.AlignVCenter
            color: {
                if (profit > -15.0 && profit != 0.0)
                    return "magenta"

                return "black"
            }
            text: profit.toFixed(2) + "%"
        }
    }

    Component {
        id: amountText

        Text {
            rightPadding: 3

            verticalAlignment: Text.AlignVCenter
            horizontalAlignment: Text.AlignRight
            text: amount
        }
    }


    delegate: Rectangle {
        width: 200
        height: 50 
        border.width: 1
        border.color: "#80d7d7d7" 
        
        GridLayout {
            anchors.fill: parent
            rows: 3
            columns: 8
            rowSpacing: 0
            columnSpacing: 0
            Rectangle {
                Layout.row: 0
                Layout.column: 0
                Layout.minimumWidth: parent.width * 6 / 8
                Layout.maximumWidth: parent.width * 6 / 8
                Layout.minimumHeight: parent.height * 2 / 3
                width: parent.width * 6 / 8
                height: parent.height * 2 / 3
                Layout.rowSpan: 2
                Layout.columnSpan: 6
                color: is_favorite?"#50FFFF00":"#FFFFFF"
                Text {
                    text: display
                    anchors.fill: parent
                    verticalAlignment: Text.AlignVCenter
                    leftPadding: 3
                    elide: Text.ElideRight
                    font.pointSize: 13
                }
            }

            Loader {
                sourceComponent: amountText
                Layout.row: 0
                Layout.column: 6
                Layout.columnSpan: 2
                Layout.fillWidth: true
                height: parent.height / 3
                property var amount: tamount
            }
            Loader {
                sourceComponent: amountText
                Layout.row: 1
                Layout.column: 6
                Layout.columnSpan: 2
                Layout.fillWidth: true
                height: parent.height / 3

                property var amount: yamount
            }

            Loader {
                Layout.row: 2
                Layout.column: 0
                Layout.columnSpan: 2
                width: parent.width * 1 / 4
                height: parent.height / 3
                sourceComponent: profitText
                property double profit: tprofit
            }
            Loader {
                Layout.row: 2
                Layout.column: 2
                Layout.columnSpan: 2
                width: parent.width * 1 / 4
                height: parent.height / 3
                sourceComponent: profitText
                property double profit: topen_profit
            }
            Loader {
                Layout.row: 2
                Layout.column: 4
                Layout.columnSpan: 2
                width: parent.width * 1 / 4
                height: parent.height / 3
                sourceComponent: smallProfitText
                property double profit: yprofit
            }
            Loader {
                Layout.row: 2
                Layout.column: 6
                Layout.columnSpan: 2
                width: parent.width * 1 / 4
                height: parent.height / 3
                sourceComponent: yearProfitText
                property double profit: yearprofit
            }

        }
        
        MouseArea {
            anchors.fill: parent
            onClicked: codeListView.currentIndex = index
        }
    }
    highlight: Rectangle {
        width: 200
        height: 100
        color: 'red'
    }
    
    onCurrentItemChanged: {
        codeListView.model.currentSelectionChanged(codeListView.currentIndex)
    }

    onCurrentIndexChanged: {
        codeListView.model.setCurrentIndex(currentIndex)
    }

    currentIndex: -1
}

