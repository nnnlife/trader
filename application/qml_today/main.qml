import QtQuick 2.15
import QtQuick.Layouts 1.0
import QtQuick.Controls 2.12
import MorningTickChartView 1.0
import "./"


ApplicationWindow {
    id: root
    width: 1400 
    height: 800 
    visible: true

    Row {
        id: option
        height: 30
        CheckBox {
            id: broker
            text: '거래원'
            checked: morningTickChart.subjectVisible
            onClicked: morningTickChart.subjectVisible = checked
        }

        Text {
            text: morningTickChart.corporationName
            verticalAlignment: Text.AlignVCenter
            leftPadding: 20
            font.bold: true
            height: parent.height
        }

        Text {
            text: '외국계: '
            verticalAlignment: Text.AlignVCenter
            leftPadding: 20
            height: parent.height
        }

        Text {
            text: qsTr("%L1").arg(morningTickChart.foreignerVolume)
            verticalAlignment: Text.AlignVCenter
            leftPadding: 5 
            color: morningTickChart.foreignerVolume > 0? 'red': 'blue'
            height: parent.height
        }

        Text {
            text: '전일'
            verticalAlignment: Text.AlignVCenter
            leftPadding: 50 
            height: parent.height
        }

        Text {
            text: morningTickChart.yesterdayAmount
            verticalAlignment: Text.AlignVCenter
            leftPadding: 5
            height: parent.height
        }

        Text {
            text: '금일'
            verticalAlignment: Text.AlignVCenter
            leftPadding: 50 
            height: parent.height
        }

        Text {
            text: morningTickChart.todayAmount
            verticalAlignment: Text.AlignVCenter
            leftPadding: 5
            height: parent.height
        }
    }

    MorningTickChartView {
        id: morningTickChart
        anchors.top: option.bottom
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: parent.bottom
    }
}
