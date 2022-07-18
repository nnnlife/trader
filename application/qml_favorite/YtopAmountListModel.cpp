#include "YtopAmountListModel.h"
#include "StockStat.h"


YtopAmountListModel::YtopAmountListModel(QObject *parent)
: AbstractListModel(parent) {
    m_dateSymbol = "-";    
    m_listDate = 0;
}


QStringList YtopAmountListModel::getServerList() {
    TopList *tlist = StockStat::instance()->getYtopAmountList();
    currentDisplayList.clear();
    qWarning() << "top list count : " << tlist->codelist_size() << "\t" << tlist->date();
    for (int i = 0; i < 30; i++) {
        if (i > tlist->codelist_size() - 1)
            break;
        currentDisplayList.append(QString::fromStdString(tlist->codelist(i)));
    }
    if (tlist->is_today_data())
        setDateSymbol("T");
    else
        setDateSymbol("Y");

    setListDate(tlist->date());

    return currentDisplayList;
}


void YtopAmountListModel::menuClicked(int index) {
    if (index == 0) {
        if (currentSelectIndex() >= itemList.count() || currentSelectIndex() == -1)
            return;
        StockStat::instance()->addToFavorite(currentDisplayList.at(currentSelectIndex()));
    }
}


void YtopAmountListModel::setDateSymbol(const QString &sym) {
    if (m_dateSymbol != sym) {
        m_dateSymbol = sym;
        emit dateSymbolChanged();
    }
}


void YtopAmountListModel::setListDate(uint d) {
    if (m_listDate != d) {
        m_listDate = d;
        emit listDateChanged();
    }
}
