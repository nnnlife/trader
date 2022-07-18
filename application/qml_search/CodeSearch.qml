import QtQuick 2.0
import QtQuick.Layouts 1.0
import QtQuick.Controls 2.12
import search.backend 1.0


Item {
    id: root
    property alias code: codeField.text
    signal codeEntered()

    RowLayout {
        TextField {
            id: codeField
            Layout.preferredWidth: 100
            text: SearchBackend.currentCode
            onAccepted: root.codeEntered()
        }
    }
}
