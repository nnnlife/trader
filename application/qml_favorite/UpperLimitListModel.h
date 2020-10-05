#ifndef ULIMIT_LIST_MODEL_H_
#define ULIMIT_LIST_MODEL_H_

#include "AbstractListModel.h"

class UpperLimitListModel : public AbstractListModel {
    Q_OBJECT
    QML_ELEMENT

public:
    UpperLimitListModel(QObject *parent=nullptr);
    QStringList getServerList() override;
    Q_INVOKABLE void menuClicked(int index) override;
    QString sectionName() { return "strategy"; }
};


#endif
