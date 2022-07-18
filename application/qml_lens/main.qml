import QtQuick 2.0
import QtQuick.Layouts 1.0
import QtQuick.Controls 2.12
import LensChartView 1.0
import "./"


ApplicationWindow {
    id: root
    width: 600
    height: 675
    visible: true

    Rectangle {
        id: codeInfo
        width: parent.width
        anchors.top: parent.top
        height: 50
        color: '#F5F5DC'

        Row {
            anchors.fill: parent
            spacing: 0

            Text {
                width: 140
                height: parent.height    
                text: lensChart.corpName
                font.pointSize: 11
                verticalAlignment: Text.AlignVCenter
                MouseArea {
                    anchors.fill: parent
                    onClicked: {
                        lensChart.sendCurrentCode()
                    }
                }
            }

            Column {
                height: parent.height
                width: 70
                Text {
                    width: parent.width
                    height: parent.height / 2
                    text: lensChart.currentRatio
                    font.pointSize: 11
                    verticalAlignment: Text.AlignVCenter
                    color: {
                        if (parseFloat(lensChart.currentRatio) >= 0.5)
                            return 'red'
                        else
                            return 'blue'
                    }
                }
                Text {
                    width: parent.width
                    height: parent.height / 2
                    text: lensChart.openProfit + '%'
                    font.pointSize: 11
                    verticalAlignment: Text.AlignVCenter
                    color: {
                        if (parseFloat(lensChart.openProfit) > 0.0)
                            return 'red'
                        else
                            return 'blue'
                    }
                }
            }

            Text {
                width: 70
                height: parent.height
                text: lensChart.currentAmount
                font.pointSize: 12
                verticalAlignment: Text.AlignVCenter
            }

            CheckBox {
                width: 70
                height: parent.height
                text: 'pin'
                checked: lensChart.pinCode
                onCheckStateChanged: lensChart.pinCode = checkState == Qt.Checked?true:false
            }
        }

    }

    Flickable {
        id: codeView
        width: parent.width
        anchors.top: codeInfo.bottom        
        anchors.bottom: parent.bottom

        contentWidth: lensChart.width
        boundsBehavior: Flickable.StopAtBounds
        LensChartView {
            id: lensChart
            width: 2048
            height: parent.height
        }
        ScrollBar.horizontal: ScrollBar{
            id: hscrollbar
	    }

        onContentWidthChanged: {
            console.log('content width changed to ', contentWidth)
            hscrollbar.position = 1.0
        }
    }
}
