#ifndef STRATEGY_LIST_MODEL_H_
#define STRATEGY_LIST_MODEL_H_

#include "AbstractListModel.h"

class StrategyListModel : public AbstractListModel {
    Q_OBJECT
    QML_ELEMENT

public:
    StrategyListModel(QObject *parent=nullptr);
    QStringList getServerList() override;
    Q_INVOKABLE void menuClicked(int index) override;
    QString sectionName() { return "strategy"; }
};


#endif
