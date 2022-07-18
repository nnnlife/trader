#ifndef VI_LIST_MODEL_H_
#define VI_LIST_MODEL_H_

#include "AbstractListModel.h"

class ViListModel : public AbstractListModel {
    Q_OBJECT
    QML_ELEMENT

    Q_PROPERTY(bool filterDynamic READ filterDynamic WRITE setFilterDynamic NOTIFY filterDynamicChanged)
    Q_PROPERTY(bool filterStatic READ filterStatic WRITE setFilterStatic NOTIFY filterStaticChanged)
    Q_PROPERTY(bool catchPlus READ catchPlus WRITE setCatchPlus NOTIFY catchPlusChanged)

public:
    ViListModel(QObject *parent=nullptr);
    QStringList getServerList() override;
    Q_INVOKABLE void menuClicked(int index) override;
    Q_INVOKABLE void checkStateChanged(int index, bool state);
    QString sectionName() { return "vi"; }

    bool catchPlus() { return mCatchPlus; }
    bool filterDynamic() { return mFilterDynamic; }
    bool filterStatic() { return mFilterStatic; }

    void setFilterDynamic(bool d);
    void setFilterStatic(bool s);
    void setCatchPlus(bool c);

private:
    bool mFilterDynamic;
    bool mFilterStatic;
    bool mCatchPlus;

signals:
    void filterDynamicChanged();
    void filterStaticChanged();
    void catchPlusChanged();
};


#endif
