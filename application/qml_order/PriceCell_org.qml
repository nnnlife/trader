import QtQuick 2.15
import QtQuick.Layouts 1.0
import QtQuick.Controls 2.12
import Qt.labs.qmlmodels 1.0


Item {
    id: root
    property int priceFrom: 0
    property int cellRow: -1
    property int priceTo: 10000000

    property var price: undefined
    property var editPrice: undefined

    property int stockMarketType: 0 

    function getStepSize(p) {
        if (stockMarketType == 0) { // KOSDAQ
            if (p < 1000)
                return 1
            else if (1000 <= p && p < 5000)
                return 5
            else if (5000 <= p && p < 10000)
                return 10
            else if (10000 <= p && p < 50000)
                return 50
            else
                return 100
        }
        else if (stockMarketType == 1) { // KOSPI
            if (p < 1000)
                return 1
            else if (1000 <= p && p < 5000)
                return 5
            else if (5000 <= p && p < 10000)
                return 10
            else if (10000 <= p && p < 50000)
                return 50
            else if (50000 <= p && p < 100000)
                return 100
            else if (100000 <= p && p < 500000)
                return 500
            else
                return 1000
        }
        return 0
    }

    Rectangle {
        anchors.fill: parent
        border.width: 1
        border.color: "#d7d7d7"

        SpinBox {
            id: priceAdjust
            anchors.fill: parent
            from: priceFrom
            to: priceTo
            stepSize: 0
            visible: price != editPrice
            value: 0
            up.indicator.width: 20
            down.indicator.width: 20
            up {
                onPressedChanged: {
                    if (up.pressed) {
                        var step = getStepSize(value)
                        value = value + step
                        editPrice = value
                    }
                }
            }
            down {
                onPressedChanged: {
                    if (down.pressed) {
                        var step = getStepSize(value - 1)
                        value = value - step
                        editPrice = value
                    }
                }
            }
        }

        Text {
            id: plainPrice
            verticalAlignment: Text.AlignVCenter
            horizontalAlignment: Text.AlignHCenter
            text: qsTr("%L1").arg(price)
            anchors.fill: parent
            visible: true

            MouseArea {
                anchors.fill: parent
                onClicked: {
                    if (price != undefined && price > 0) {
                        priceAdjust.visible = true
                        plainPrice.visible = false
                    }
                }
            }
        }
    }

    onPriceChanged: {
        console.log('price changed', price)
        priceAdjust.value = price
        /*
        if (price == 0 && priceAdjust.visible) {
            priceAdjust.visible = false
            plainPrice.visible = true
        }
        */
    }
}
