#ifndef FAVORITE_LIST_MODEL_H_
#define FAVORITE_LIST_MODEL_H_

#include "AbstractListModel.h"

class FavoriteListModel : public AbstractListModel {
    Q_OBJECT
    QML_ELEMENT

public:
    FavoriteListModel(QObject *parent=nullptr);
    QStringList getServerList() override;
    Q_INVOKABLE void menuClicked(int index) override;
    QString sectionName() { return "favorite"; }
};

#endif
