#ifndef TTOP_AMOUNT_LIST_MODEL_H_
#define TTOP_AMOUNT_LIST_MODEL_H_

#include "AbstractListModel.h"
#include "StockStat.h"

class TtopAmountListModel : public AbstractListModel {
    Q_OBJECT
    QML_ELEMENT

public:
    TtopAmountListModel(QObject *parent=nullptr);
    QStringList getServerList() override;
    Q_INVOKABLE void menuClicked(int index) override;
    Q_INVOKABLE void checkStateChanged(int index, bool state);
    QString sectionName() { return "ttopamount"; }

private:
    TodayTopSelection mSelection = TodayTopSelection::TOP_BY_RATIO;
};


#endif
