import QtQuick 2.15
import QtQuick.Layouts 1.0
import QtQuick.Controls 2.12
import Qt.labs.qmlmodels 1.0



Item {
    id: root

    property var qty: 0
    property var editQty: 0
    property var isReadOnly: true
    property bool usePercentage: false
    property int qtyFrom: 0
    property int qtyTo: (usePercentage ? 100: 10000000)

    signal qtyValueChanged(int value)

    Rectangle {
        anchors.fill: parent
        border.width: 1
        border.color: "#d7d7d7"

        Row {
            id: qtyAdjust
            visible: (!isReadOnly && qty != editQty)
            anchors.fill: parent
            SpinBox {
                implicitHeight: parent.height
                implicitWidth: 90
                from: qtyFrom
                to: qtyTo
                editable: true
                value: editQty
                stepSize: (usePercentage ? 25 : 1)
                up.indicator.width: 20
                down.indicator.width: 20
                onValueChanged: {
                    qtyValueChanged(value)
                }
            }
            ButtonGroup {
                buttons: unitButton.children
            }

            Item {
                implicitWidth: 40
                height: parent.height
                Row {
                    id: unitButton
                    anchors.fill: parent
                    ToolButton {
                        text: 'P'
                        width: 20
                        height: parent.height
                        checkable: true
                        checked: usePercentage
                        onClicked: {
                            if (checked)
                                usePercentage = true;
                            else
                                usePercentage = false;
                        }
                    }
                    ToolButton {
                        text: 'Q'
                        checked: !usePercentage
                        height: parent.height
                        checkable: true
                        width: 20
                        onClicked: {
                            if (checked)
                                usePercentage = false;
                            else
                                usePercentage = true;
                        }
                    }
                }
            }
           
        }
        Text {
            id: plainQty
            verticalAlignment: Text.AlignVCenter
            horizontalAlignment: Text.AlignHCenter
            text: qsTr("%L1").arg(qty)
            anchors.fill: parent
            visible: qty == editQty

            MouseArea {
                anchors.fill: parent
                onClicked: {
                    if (!isReadOnly && !qtyAdjust.visible) {
                        qtyAdjust.visible = true
                        plainQty.visible = false
                    }
                }
            }
        }
    }
}
