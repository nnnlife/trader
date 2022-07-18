#ifndef RECENT_LIST_MODEL_H_
#define RECENT_LIST_MODEL_H_


#include <qqml.h>
#include <QDateTime>
#include "AbstractListModel.h"


class RecentListModel : public AbstractListModel {
    Q_OBJECT
    QML_ELEMENT

public:
    RecentListModel(QObject *parent=nullptr);
    Q_INVOKABLE void menuClicked(int index) override;
    QStringList getServerList() override;
    QString sectionName() { return "recent"; }
};


#endif
