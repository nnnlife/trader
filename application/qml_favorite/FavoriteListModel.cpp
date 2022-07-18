#include "FavoriteListModel.h"
#include "StockStat.h"
#include <QDebug>


FavoriteListModel::FavoriteListModel(QObject *parent)
: AbstractListModel(parent) {
    qWarning() << "Constructor";    
}


QStringList FavoriteListModel::getServerList() {
    qWarning() << "FavoriteListModel::getServerList";
    return StockStat::instance()->getFavoriteList();
}


void FavoriteListModel::menuClicked(int index) {
    qWarning() << "FavoriteListModel menuClicked : " << index << "\tindex : " <<
                    currentSelectIndex() << "\titemList count: " << itemList.count();

    if (currentSelectIndex() >= itemList.count() || currentSelectIndex() == -1) {
        return;
    }

    const ListItem * li = itemList.at(currentSelectIndex());

    if (index == 0) {
        StockStat::instance()->removeFromFavorite(li->code());
    }
    else if (index == 1) {
        StockStat::instance()->removeFromFavorite(li->code());
        StockStat::instance()->addToFavorite(li->code());
    }
}
