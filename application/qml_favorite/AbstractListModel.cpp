#include "AbstractListModel.h"
#include "StockStat.h"


#define CODE_ROLE       Qt::UserRole
#define YPROFIT_ROLE    (Qt::UserRole + 1)
#define TPROFIT_ROLE    (Qt::UserRole + 2)
#define YAMOUNT_ROLE    (Qt::UserRole + 3)
#define TAMOUNT_ROLE    (Qt::UserRole + 4)
#define FAVORITE_ROLE   (Qt::UserRole + 5)
#define TOPEN_ROLE      (Qt::UserRole + 6)
#define YEARPROFIT_ROLE      (Qt::UserRole + 7)


AbstractListModel::AbstractListModel(QObject *parent)
: QAbstractListModel(parent) {
    m_currentSelectIndex = -1;
    connect(StockStat::instance(), &StockStat::infoCleared, this, &AbstractListModel::dateChanged);
    connect(StockStat::instance(), &StockStat::infoUpdated, this, &AbstractListModel::infoUpdated);
    connect(StockStat::instance(), &StockStat::stockListTypeChanged, this, &AbstractListModel::stockListTypeChanged);
    connect(StockStat::instance(), &StockStat::currentFocusChanged, this, &AbstractListModel::focusChanged);
}


void AbstractListModel::clearList() {
    qWarning() << "clear list start";
    if (itemList.count() == 0)
        return;

    clearCurrentIndex();
    beginResetModel();
    QMutableListIterator<ListItem *> i(itemList);
    while (i.hasNext()) {
        ListItem *rc = i.next();
        i.remove();
        delete rc;
    }
    endResetModel();
    qWarning() << "clear list list count : " << itemList.count();
}


int AbstractListModel::currentSelectIndex() {
    return m_currentSelectIndex;
}


void AbstractListModel::stockListTypeChanged(QString type) {
    if (type == sectionName()) {
        refreshList();
    }
}


void AbstractListModel::setCurrentIndex(int index) {
    qWarning() << sectionName() << " setCurrentIndex: " << index;
    m_currentSelectIndex = index;
}


void AbstractListModel::focusChanged(QString section) {
    qWarning() << "focusChanged" << section;
    if (section != sectionName()) {
        emit clearCurrentIndex();
    }
}


void AbstractListModel::dateChanged() {
    refreshList();
    emit dataChanged(createIndex(0, 0), createIndex(itemList.count() - 1, 0));
}


QStringList AbstractListModel::getServerList() {
    return StockStat::instance()->getRecentSearch();
}


void AbstractListModel::refreshList() {
    if (!StockStat::instance()->currentDateTime().isValid())
        return;
    QStringList rcl = getServerList();

    if ( (rcl.count() < itemList.count()) || rcl.count() == 0) {
        qWarning() << "clear";
        clearList();
    }

    int listEndIndex = itemList.count() - 1;
    int rclEndIndex = rcl.count() - 1;
    while (listEndIndex >= 0 && rclEndIndex >= 0) {
        if (rcl.at(rclEndIndex) != itemList.at(listEndIndex)->code()) {
            clearList();
            break;
        }
        listEndIndex--;
        rclEndIndex--;
    }

    //qWarning() << "rcl count : " << rcl.count() << "\titemList count : " << itemList.count();
    for (int i = rcl.count() - itemList.count() - 1; i >= 0; i--) {
        //qWarning() << "start from : " << rcl.count() - itemList.count() - 1 << "\ti : " << i;
        beginInsertRows(QModelIndex(), 0, 0);
        itemList.prepend(new ListItem(rcl.at(i),
                                StockStat::instance()->currentDateTime()));
        endInsertRows();
    }
}


int AbstractListModel::rowCount(const QModelIndex &parent) const {
    //qWarning() << parent << "rowCount : " << itemList.count();
    Q_UNUSED(parent);
    return itemList.count();
}


QString AbstractListModel::uint64ToString(uint64_t amount) const {
    if (amount >= 1000000000) {
        qreal f = amount / 1000000000.0;
        return QString::number(f, 'f', 1) + " B";
    }
    else if (amount >= 1000000) {
        qreal f = amount / 1000000.0;
        return QString::number(f, 'f', 1) + " M";
    }
    else if (amount >= 1000) {
        qreal f = amount / 1000.0;
        return QString::number(f, 'f', 1) + " K";
    }

    return QString::number((uint)amount);
}


QVariant AbstractListModel::data(const QModelIndex &index, int role) const {
    //qWarning() << "data\t" << index << "\trole: " << role;
    const ListItem * rc = itemList.at(index.row());
    if (role == Qt::DisplayRole)
        return rc->name();
    else if (role == CODE_ROLE)
        return rc->code();
    else if (role == TPROFIT_ROLE)
        return QVariant(rc->todayProfit());
    else if (role == YPROFIT_ROLE)
        return QVariant(rc->yesterdayProfit());
    else if (role == YAMOUNT_ROLE)
        return uint64ToString(rc->yesterdayAmount());
    else if (role == TAMOUNT_ROLE)
        return uint64ToString(rc->todayAmount());
    else if (role == FAVORITE_ROLE)
        return QVariant(rc->isFavorite());
    else if (role == TOPEN_ROLE)
        return QVariant(rc->todayOpenProfit());
    else if (role == YEARPROFIT_ROLE)
        return QVariant(rc->yearHighProfit());

    return "";
}


void AbstractListModel::infoUpdated(QString code) {
    for (int i = 0; i < itemList.count(); i++) {
        ListItem * rc = itemList.at(i);
        if (rc->code() == code) {
            emit dataChanged(createIndex(i, 0), createIndex(i, 0));
            break;
        }
    }
}


void AbstractListModel::currentSelectionChanged(int index) {
    qWarning() << sectionName() << " currentSelectionChanged: " << index;
    if (index >= 0 && index < itemList.count()) {
        ListItem * rc = itemList.at(index);
        StockStat::instance()->setCurrentCode(sectionName(), rc->code());
    }
}


ListItem::ListItem(const QString &_code, const QDateTime &_dt)
: QObject(nullptr), m_code(_code), m_today(_dt){
    m_name = StockStat::instance()->getInfo(m_code)->getName();
}


qreal ListItem::yesterdayProfit() const {
    StockInfo * info = StockStat::instance()->getInfo(m_code);
    if (info->beforeYesterdayClosePrice() > 0) {
        qreal profit = ((qreal)info->getYesterdayData().close_price() - info->beforeYesterdayClosePrice()) / info->beforeYesterdayClosePrice() * 100.0;
        return profit;
    }
    return 0.0;
}


qreal ListItem::todayOpenProfit() const {
    StockInfo * info = StockStat::instance()->getInfo(m_code);
    if (info->todayOpenPrice() > 0 && info->todayCurrentPrice() > 0) {
        qreal profit = ((qreal)info->todayCurrentPrice() - info->todayOpenPrice()) / info->todayOpenPrice() * 100.0;
        return profit;
    }
    return 0.0;
}


qreal ListItem::yearHighProfit() const {
    StockInfo * info = StockStat::instance()->getInfo(m_code);
    if (info->todayCurrentPrice() > 0 && info->yearHighPrice() > 0) {
        qreal profit = ((qreal)info->todayCurrentPrice() - info->yearHighPrice()) / info->yearHighPrice() * 100.0;
        return profit;
    }
    return 0.0;
}


qreal ListItem::todayProfit() const {
    StockInfo * info = StockStat::instance()->getInfo(m_code);
    if (info->todayCurrentPrice() > 0 && info->getYesterdayData().close_price() > 0.0) {
        qreal profit = ((qreal)info->todayCurrentPrice() - info->getYesterdayData().close_price()) / info->getYesterdayData().close_price() * 100.0;
        return profit;
    }
    return 0.0;
}


uint64_t ListItem::yesterdayAmount() const {
    StockInfo * info = StockStat::instance()->getInfo(m_code);
    return info->getYesterdayData().amount();
}


uint64_t ListItem::todayAmount() const {
    StockInfo * info = StockStat::instance()->getInfo(m_code);
    return info->todayAmount();
}


bool ListItem::isFavorite() const {
    return StockStat::instance()->isInFavoriteList(m_code);
}
