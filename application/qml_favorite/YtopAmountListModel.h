#ifndef YTOP_AMOUNT_LIST_MODEL_H_
#define YTOP_AMOUNT_LIST_MODEL_H_

#include "AbstractListModel.h"

class YtopAmountListModel : public AbstractListModel {
    Q_OBJECT
    QML_ELEMENT
    Q_PROPERTY(QString dateSymbol READ dateSymbol WRITE setDateSymbol NOTIFY dateSymbolChanged)
    Q_PROPERTY(uint listDate READ listDate WRITE setListDate NOTIFY listDateChanged)

public:
    YtopAmountListModel(QObject *parent=nullptr);
    QStringList getServerList() override;
    Q_INVOKABLE void menuClicked(int index) override;
    QString sectionName() { return "ytopamount"; }

    const QString &dateSymbol() { return m_dateSymbol;}
    uint listDate() { return m_listDate; }

    void setDateSymbol(const QString &sym);
    void setListDate(uint d);

private:
    QStringList currentDisplayList;
    QString m_dateSymbol;
    uint m_listDate;

signals:
    void dateSymbolChanged();
    void listDateChanged();
};


#endif
