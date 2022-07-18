#include "UpperLimitListModel.h"
#include "StockStat.h"


UpperLimitListModel::UpperLimitListModel(QObject *parent)
: AbstractListModel(parent) {
}


QStringList UpperLimitListModel::getServerList() {
    return StockStat::instance()->getUpperLimitList();
}


void UpperLimitListModel::menuClicked(int index) {
    if (index == 0) {
        if (currentSelectIndex() >= itemList.count() || currentSelectIndex() == -1)
            return;

        const ListItem * li = itemList.at(currentSelectIndex());
        StockStat::instance()->addToFavorite(li->code());
    }
    else if (index == 1) {
	qWarning() << "refreshList UpperLimitListModel";
        refreshList();
    }
}
