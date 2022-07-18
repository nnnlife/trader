import QtQuick 2.0
import QtQuick.Layouts 1.0
import QtQuick.Controls 2.12
import search.backend 1.0


Item {
    property date currentDate: new Date()

    property alias year: yearField.text
    property alias month: monthField.text
    property alias day: dayField.text
    property alias hour: hourField.text
    property alias minute: minuteField.text

    RowLayout {
        spacing: 10
        TextField {
            id: yearField
            Layout.preferredWidth: 80
            inputMethodHints: Qt.ImhDigitsOnly
            maximumLength: 4
            text: currentDate.getFullYear()
        }

        Text {
            text: "년"
        }

        TextField {
            id: monthField
            Layout.preferredWidth: 40
            inputMethodHints: Qt.ImhDigitsOnly
            maximumLength: 2
            text: currentDate.getMonth() + 1
        }

        Text {
            text: "월"
        }

        TextField {
            id: dayField
            Layout.preferredWidth: 40
            inputMethodHints: Qt.ImhDigitsOnly
            maximumLength: 2
            text: currentDate.getDate()
        }

        Text {
            text: "일"
        }

        TextField {
            id: hourField
            Layout.preferredWidth: 40
            inputMethodHints: Qt.ImhDigitsOnly
            maximumLength: 2
            text: currentDate.getHours()
        }

        Text {
            text: ":"
        }

        TextField {
            id: minuteField
            Layout.preferredWidth: 40
            inputMethodHints: Qt.ImhDigitsOnly
            maximumLength: 2
            text: currentDate.getMinutes()
        }
    }
}
