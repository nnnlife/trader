/****************************************************************************
** Generated QML type registration code
**
** WARNING! All changes made in this file will be lost!
*****************************************************************************/

#include <QtQml/qqml.h>
#include <QtQml/qqmlmoduleregistration.h>

#include <FavoriteListModel.h>
#include <RecentListModel.h>
#include <StrategyListModel.h>
#include <TtopAmountListModel.h>
#include <UpperLimitListModel.h>
#include <ViListModel.h>
#include <YtopAmountListModel.h>

void qml_register_types_favorite_backend()
{
    qmlRegisterTypesAndRevisions<FavoriteListModel>("favorite.backend", 1);
    qmlRegisterTypesAndRevisions<RecentListModel>("favorite.backend", 1);
    qmlRegisterTypesAndRevisions<StrategyListModel>("favorite.backend", 1);
    qmlRegisterTypesAndRevisions<TtopAmountListModel>("favorite.backend", 1);
    qmlRegisterTypesAndRevisions<UpperLimitListModel>("favorite.backend", 1);
    qmlRegisterTypesAndRevisions<ViListModel>("favorite.backend", 1);
    qmlRegisterTypesAndRevisions<YtopAmountListModel>("favorite.backend", 1);
    qmlRegisterModule("favorite.backend", 1, 0);
}

static const QQmlModuleRegistration registration("favorite.backend", 1, qml_register_types_favorite_backend);
