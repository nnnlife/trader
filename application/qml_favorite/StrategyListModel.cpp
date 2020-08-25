#include "StrategyListModel.h"
#include "StockStat.h"


StrategyListModel::StrategyListModel(QObject *parent)
: AbstractListModel(parent) {
}


QStringList StrategyListModel::getServerList() {
    return StockStat::instance()->getStrategyList();
}


void StrategyListModel::menuClicked(int index) {
    Q_UNUSED(index);
}
