#ifndef ABSTRACT_LIST_MODEL_H_
#define ABSTRACT_LIST_MODEL_H_


#include <qqml.h>
#include <QDateTime>
#include <QAbstractListModel>


class ListItem : public QObject{
Q_OBJECT
public:
    ListItem(const QString &code, const QDateTime &dt);

    const QString & code() const { return m_code; }
    const QString & name() const { return m_name; }
    qreal yesterdayProfit() const;
    uint64_t yesterdayAmount() const;
    qreal todayProfit() const;
    qreal todayOpenProfit() const;
    qreal yearHighProfit() const;
    uint64_t todayAmount() const;
    bool isFavorite() const;

private:
    QString m_code;
    QString m_name;
    QDateTime m_today;
};


class AbstractListModel : public QAbstractListModel {
    Q_OBJECT

public:
    AbstractListModel(QObject *parent=nullptr);
    int rowCount(const QModelIndex &parent=QModelIndex()) const override;

    QVariant data(const QModelIndex &index, int role = Qt::DisplayRole) const override;
    QHash<int, QByteArray> roleNames() const override
    {
        return { {Qt::DisplayRole, "display"},
                 {Qt::UserRole,    "code"},
                 {Qt::UserRole + 1, "yprofit"},
                 {Qt::UserRole + 2, "tprofit"},
                 {Qt::UserRole + 3, "yamount"},
                 {Qt::UserRole + 4, "tamount"},
                 {Qt::UserRole + 5, "is_favorite"},
                 {Qt::UserRole + 6, "topen_profit"},
                 {Qt::UserRole + 7, "yearprofit"}};
    }
    Q_INVOKABLE void currentSelectionChanged(int index);
    Q_INVOKABLE void setCurrentIndex(int index);
    Q_INVOKABLE virtual void menuClicked(int index) = 0;
    virtual QStringList getServerList();
    int currentSelectIndex();
    virtual QString sectionName() = 0;

private:
    QDateTime today;

    void clearList();
    QString uint64ToString(uint64_t amount) const;
    int m_currentSelectIndex;

protected:
    QList<ListItem *> itemList;
    void refreshList();

private slots:
    //void stockListTypeChanged(QString);
    void infoUpdated(QString);
    void dateChanged();
    void stockListTypeChanged(QString);
    void focusChanged(QString);

signals:
    void clearCurrentIndex();
};



#endif
