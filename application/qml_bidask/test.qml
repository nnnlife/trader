import QtQuick 2.15
import QtQuick.Layouts 1.0
import QtQuick.Controls 2.12
import Qt.labs.qmlmodels 1.0



Rectangle {
    width: 500
    height: 400

    Rectangle {
        anchors.left: parent.left
        width: 250
        height: 400
    }

    Rectangle {
        anchors.right: parent.right
        width: 250
        height: 400
    }

    SpinBox {
        width: 100
        height: 50
        id: spinBox
        visible: false
    }

    MouseArea {
        anchors.fill: parent
        onClicked: {
            console.log('clicked')
            spinBox.visible = true
            spinBox.z = z + 1
        }
    }
}

