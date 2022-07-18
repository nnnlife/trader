#include "RecentListModel.h"
#include "StockStat.h"


#define CODE_ROLE       Qt::UserRole
#define YPROFIT_ROLE    (Qt::UserRole + 1)
#define TPROFIT_ROLE    (Qt::UserRole + 2)
#define YAMOUNT_ROLE    (Qt::UserRole + 3)
#define TAMOUNT_ROLE    (Qt::UserRole + 4)


RecentListModel::RecentListModel(QObject *parent)
: AbstractListModel(parent) {}


QStringList RecentListModel::getServerList() {
    return StockStat::instance()->getRecentSearch();
}


void RecentListModel::menuClicked(int index) {
    qWarning() << "RecentListModel menuClicked: " << index << "\tindex : " << currentSelectIndex();
    if (index == 0) {
        if (currentSelectIndex() >= itemList.count() || currentSelectIndex() == -1)
            return;

        const ListItem * li = itemList.at(currentSelectIndex());
        StockStat::instance()->addToFavorite(li->code());
    }
    else if (index == 1) {
        emit clearCurrentIndex();
        StockStat::instance()->clearRecentList();
    }
}
