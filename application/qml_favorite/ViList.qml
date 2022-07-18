import QtQuick 2.15
import QtQuick.Layouts 1.0
import QtQuick.Controls 2.12
import Qt.labs.qmlmodels 1.0
import favorite.backend 1.0


Item {
    ColumnLayout {
        anchors.fill: parent
        MenuButton {
            firstCheckText: '동적'
            firstCheck: codeListView.model.filterDynamic
            secondCheckText: '정적'
            secondCheck: codeListView.model.filterStatic
            thirdCheckText: '상승'
            thirdCheck: codeListView.model.catchPlus

            Layout.alignment: Qt.AlignTop | Qt.AlignHCenter
            Layout.preferredWidth: 200
            Layout.preferredHeight: 50
            onCheckStateChanged: codeListView.model.checkStateChanged(index, state)
            onSelected: codeListView.model.menuClicked(index)
        }

        CodeListView {
            id: codeListView
            Layout.fillHeight: true
            Layout.preferredWidth: 200
            model: ViListModel{}
        }

        Connections {
            target: codeListView.model
            function onClearCurrentIndex() {
                console.log('ViList:Receive clear current index')
                codeListView.currentIndex = -1
            }
        }
    }
}
