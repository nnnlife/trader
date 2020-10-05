import QtQuick 2.15
import QtQuick.Layouts 1.0
import QtQuick.Controls 2.12


ApplicationWindow {
    id: root
    width: 1440; height: 800
    visible: true

    RowLayout { 
        anchors.fill: parent
        spacing: 0.0

        FavoriteList {
            Layout.fillWidth: true
            Layout.fillHeight: true
        }

        StrategyList {
            Layout.fillWidth: true
            Layout.fillHeight: true
        }
        TtopAmountList {
            Layout.fillWidth: true
            Layout.fillHeight: true
        }
        /*
        ViList {
            Layout.fillWidth: true
            Layout.fillHeight: true
        }*/
        
        UpperLimitList {
            Layout.fillWidth: true
            Layout.fillHeight: true
        }

        YtopAmountList {
            Layout.fillWidth: true
            Layout.fillHeight: true
        }

        RecentList {
            Layout.fillWidth: true
            Layout.fillHeight: true
        }
    }
}
