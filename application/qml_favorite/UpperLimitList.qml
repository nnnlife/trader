import QtQuick 2.15
import QtQuick.Layouts 1.0
import QtQuick.Controls 2.12
import Qt.labs.qmlmodels 1.0
import favorite.backend 1.0


Item {
    ColumnLayout {
        anchors.fill: parent
        MenuButton {
            buttonColor: 'yellow'
            firstText: 'ADD'
            secondText: 'REFRESH'
            Layout.alignment: Qt.AlignTop | Qt.AlignHCenter
            Layout.preferredWidth: 200
            Layout.preferredHeight: 50
            onSelected: codeListView.model.menuClicked(index)
        }

        CodeListView {
            id: codeListView
            Layout.fillHeight: true
            Layout.preferredWidth: 200
            model: UpperLimitListModel{}
        }

        Connections {
            target: codeListView.model
            function onClearCurrentIndex() {
                console.log('UpperLimitList:Receive clear current index')
                codeListView.currentIndex = -1
            }
        }

    }
}