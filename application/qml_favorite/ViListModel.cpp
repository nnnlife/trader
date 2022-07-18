#include "ViListModel.h"
#include "StockStat.h"
#include <QDebug>

#define ALL 0
#define STATIC 1
#define DYNAMIC 2

ViListModel::ViListModel(QObject *parent)
: AbstractListModel(parent) {
    mFilterStatic = true;
    mFilterDynamic = false;
    mCatchPlus = true;
}


QStringList ViListModel::getServerList() {
    return StockStat::instance()->getViList();
}


void ViListModel::menuClicked(int index) {Q_UNUSED(index);}


void ViListModel::checkStateChanged(int index, bool state) {
    qWarning() << "checkStateChanged : " << index << "\t" << state;
    if (index == 0)
        setFilterDynamic(state);
    else if (index == 1)
        setFilterStatic(state);
    else if (index == 2)
        setCatchPlus(state);
}


void ViListModel::setFilterStatic(bool s) {
    qWarning() << "setFilterStatic : " << s << "\t" << mFilterStatic;
    if (s ^ mFilterStatic) {
        qWarning() << "refresh static";
        mFilterStatic = s;
        emit filterStaticChanged();
        refreshList();
    }
}


void ViListModel::setFilterDynamic(bool d) {
    if (mFilterDynamic ^ d) {
        qWarning() << "refresh dynamic";
        mFilterDynamic = d;
        emit filterDynamicChanged();
        refreshList();
    }
}


void ViListModel::setCatchPlus(bool c) {
    if (mCatchPlus ^ c) {
        mCatchPlus = c;
        emit catchPlusChanged();
        refreshList();
    }
}
