import QtQuick 2.0
import QtQuick.Layouts 1.0
import QtQuick.Controls 2.12
import MorningChartView 1.0


ApplicationWindow {
    id: root
    width: 1000; height: 830
    visible: true

    RowLayout {
        id: menuArea
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.right: parent.right
        height: 30
        CheckBox {
            Layout.fillHeight: true
            Layout.fillWidth: true
            checked: dayView.pinnedCode
            text: 'Set to pin Code'
            onCheckStateChanged: dayView.pinnedCode = checkState == Qt.Checked?true:false
        }

        Text {
            id: codeField
            Layout.fillHeight: true
            Layout.fillWidth: true
            font.pointSize: 14
            verticalAlignment: Text.AlignVCenter
            text: dayView.corporateName
        }
        
        TextField {
            Layout.fillHeight: true
            Layout.fillWidth: true
            text: dayView.pcode
            onAccepted: {
                dayView.pcode = text
            }
        }
    }

    DayView {
        id: dayView
        anchors.top: menuArea.bottom
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: parent.bottom

        onCorporateNameChanged: codeField.text = dayView.corporateName
    }
}
