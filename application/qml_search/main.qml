import QtQuick 2.0
import QtQuick.Layouts 1.0
import QtQuick.Controls 2.12
import search.backend 1.0


ApplicationWindow {
    id: root
    width: 1000
    height: 100
    visible: true

    ColumnLayout {
        id: col
        RowLayout {
            DateTime {
                id: dateTime
                Layout.minimumWidth: 350 
                Layout.preferredWidth: 250 
                Layout.preferredHeight: 40
                Layout.rightMargin: 30 
            }


            Button {
                Layout.preferredWidth: 50
                Layout.preferredHeight: 40
                Layout.rightMargin: 100 
                text: "SET"

                onClicked: {
                    SearchBackend.sendCurrentDateTime(
                                            new Date(dateTime.year, dateTime.month - 1, dateTime.day,
                                                        dateTime.hour, dateTime.minute, 0))
                }
            }

            CodeSearch {
                id: codeSearch
                Layout.preferredWidth: 80
                Layout.preferredHeight: 40
                Layout.rightMargin: 20
                Connections {
                    target: codeSearch
                    function onCodeEntered() {
                        SearchBackend.sendCurrentStock(codeSearch.code)
                    }
                }
            }

            Button {
                id: subscribeButton
                Layout.leftMargin: 50
                Layout.preferredWidth: 80
                Layout.preferredHeight: 40
                text: "Subscribe"
                onClicked: SearchBackend.startSubscribeCodes()
            }
            
            Button {
                id: startButton
                Layout.leftMargin: 50
                Layout.preferredWidth: 80
                Layout.preferredHeight: 40
                text: "START"
                background: Rectangle {
                    color: {
                        if (startButton.down) {
                            return "#d0d0d0"
                        }
                        else {
                            if (SearchBackend.simulationRunning)
                                return "#ff0000"
                            else
                                return "#e0e0e0"
                        }
                    }
                }
                onClicked: SearchBackend.startSimulation()
            }

            Button {
                id: stopButton
                Layout.preferredWidth: 80
                Layout.preferredHeight: 40
                text: "STOP"
                background: Rectangle {
                    color: {
                        if (stopButton.down) {
                            return "#d0d0d0"
                        }
                        else {
                            if (!SearchBackend.simulationRunning)
                                return "#ff0000"
                            else
                                return "#e0e0e0"
                        }
                    }
                }
                onClicked: {
                    SearchBackend.stopSimulation()
                }
            }
            Layout.bottomMargin: 10
        }

        RowLayout {
            spacing: 20
            Button {
                text: "TICK"
                Layout.leftMargin: 10 
                Layout.preferredWidth: 50 
                Layout.preferredHeight: 30 
                onClicked: {
                    SearchBackend.launchTick()
                }
            }

            Button {
                text: 'LENS'
                Layout.preferredWidth: 50 
                Layout.preferredHeight: 30 
                onClicked: {
                    SearchBackend.launchLens()
                }
            }


            Button {
                text: "DAY"
                Layout.preferredWidth: 50 
                Layout.preferredHeight: 30 
                onClicked: {
                    SearchBackend.launchDayChart()
                }
            }

            Button {
                text: "BA"
                Layout.preferredWidth: 50 
                Layout.preferredHeight: 30 
                onClicked: {
                    SearchBackend.launchBidAsk()
                }
            }

            Button {
                text: "Trader"
                Layout.preferredWidth: 60
                Layout.preferredHeight: 30 
                onClicked: {
                    SearchBackend.launchTrader()
                }
            }

            Button {
                text: "Favorite"
                Layout.preferredWidth: 75 
                Layout.preferredHeight: 30 
                onClicked: {
                    SearchBackend.launchFavorite()
                }
            }


            Text {
                id: timeText
                text: SearchBackend.currentDateTime.toLocaleDateString(Qt.locale("ko_KR"), "yyyy-MM-dd") + "  " + "<b>" + SearchBackend.currentDateTime.toLocaleTimeString(Qt.locale("ko_KR"), "hh:mm:ss") + "</b>"
                verticalAlignment: Text.AlignVCenter
                horizontalAlignment: Text.AlignHCenter
                Layout.preferredWidth: 300 
                Layout.preferredHeight: 30 
                Layout.rightMargin: 50
                font.pointSize: 16
                Connections {
                    target: SearchBackend
                    function onCurrentDateTimeChanged() {
                        timeText.text = SearchBackend.currentDateTime.toLocaleDateString(Qt.locale("ko_KR"), "yyyy-MM-dd") + "  " + "<b>" + SearchBackend.currentDateTime.toLocaleTimeString(Qt.locale("ko_KR"), "hh:mm:ss") + "</b>"
                    }
                }
            }
            
            Text {
                text: "Simulation Speed"
                verticalAlignment: Text.AlignVCenter
                Layout.preferredWidth: 100 
                Layout.preferredHeight: 30 
            }

            TextField {
                id: speedField
                Layout.preferredWidth: 50 
                Layout.preferredHeight: 30 
                text: SearchBackend.simulationSpeed
                onAccepted: {
                    SearchBackend.simulationSpeed = parseFloat(speedField.text)
                }
            }
        }
    }
}
