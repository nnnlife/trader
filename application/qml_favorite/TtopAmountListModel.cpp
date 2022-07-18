#include "TtopAmountListModel.h"
#include <QDebug>


TtopAmountListModel::TtopAmountListModel(QObject *parent)
: AbstractListModel(parent) {}


QStringList TtopAmountListModel::getServerList() {
    QStringList result = StockStat::instance()->getTtopAmountList(mSelection);
    return result;
}



void TtopAmountListModel::menuClicked(int index) {
    if (index == 0) {
        if (currentSelectIndex() >= itemList.count() || currentSelectIndex() == -1)
            return;

        const ListItem * li = itemList.at(currentSelectIndex());
        StockStat::instance()->addToFavorite(li->code());
    }
}


void TtopAmountListModel::checkStateChanged(int index, bool state) {
    qWarning() << "RadioButton : " << index << "\t" << state;
    if (index == 0 && mSelection != TodayTopSelection::TOP_BY_RATIO) {
        mSelection = TodayTopSelection::TOP_BY_RATIO;
        refreshList();
    }
    else if (index == 1 && mSelection != TodayTopSelection::TOP_BY_MOMENTUM) {
        mSelection = TodayTopSelection::TOP_BY_MOMENTUM;
        refreshList();
    }
    else if (index == 2 && mSelection != TodayTopSelection::TOP_BY_AMOUNT) {
        mSelection = TodayTopSelection::TOP_BY_AMOUNT;
        refreshList();
    }
}
