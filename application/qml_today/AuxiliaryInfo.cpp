#include "AuxiliaryInfo.h"
#include <QVector>
#include <QPainterPath>
#include <QPointF>
#include "MorningTickChartView.h"


static QVector<qreal> firstControlPoints(const QVector<qreal>& vector)
{
    QVector<qreal> result;

    int count = vector.count();
    result.resize(count);
    result[0] = vector[0] / 2.0;

    QVector<qreal> temp;
    temp.resize(count);
    temp[0] = 0;

    qreal b = 2.0;

    for (int i = 1; i < count; i++) {
        temp[i] = 1 / b;
        b = (i < count - 1 ? 4.0 : 3.5) - temp[i];
        result[i] = (vector[i] - result[i - 1]) / b;
    }

    for (int i = 1; i < count; i++)
        result[count - i - 1] -= temp[count - i] * result[count - i];

    return result;
}



/*!
  Calculates control points which are needed by QPainterPath.cubicTo function to draw the cubic Bezier cureve between two points.
*/
static QVector<QPointF> calculateControlPoints(const QVector<QPointF> &points)
{
    QVector<QPointF> controlPoints;
    controlPoints.resize(points.count() * 2 - 2);

    int n = points.count() - 1;

    if (n == 1) {
        //for n==1
        controlPoints[0].setX((2 * points[0].x() + points[1].x()) / 3);
        controlPoints[0].setY((2 * points[0].y() + points[1].y()) / 3);
        controlPoints[1].setX(2 * controlPoints[0].x() - points[0].x());
        controlPoints[1].setY(2 * controlPoints[0].y() - points[0].y());
        return controlPoints;
    }

    // Calculate first Bezier control points
    // Set of equations for P0 to Pn points.
    //
    //  |   2   1   0   0   ... 0   0   0   ... 0   0   0   |   |   P1_1    |   |   P0 + 2 * P1             |
    //  |   1   4   1   0   ... 0   0   0   ... 0   0   0   |   |   P1_2    |   |   4 * P1 + 2 * P2         |
    //  |   0   1   4   1   ... 0   0   0   ... 0   0   0   |   |   P1_3    |   |   4 * P2 + 2 * P3         |
    //  |   .   .   .   .   .   .   .   .   .   .   .   .   |   |   ...     |   |   ...                     |
    //  |   0   0   0   0   ... 1   4   1   ... 0   0   0   | * |   P1_i    | = |   4 * P(i-1) + 2 * Pi     |
    //  |   .   .   .   .   .   .   .   .   .   .   .   .   |   |   ...     |   |   ...                     |
    //  |   0   0   0   0   0   0   0   0   ... 1   4   1   |   |   P1_(n-1)|   |   4 * P(n-2) + 2 * P(n-1) |
    //  |   0   0   0   0   0   0   0   0   ... 0   2   7   |   |   P1_n    |   |   8 * P(n-1) + Pn         |
    //
    QVector<qreal> vector;
    vector.resize(n);

    vector[0] = points[0].x() + 2 * points[1].x();


    for (int i = 1; i < n - 1; ++i)
        vector[i] = 4 * points[i].x() + 2 * points[i + 1].x();

    vector[n - 1] = (8 * points[n - 1].x() + points[n].x()) / 2.0;

    QVector<qreal> xControl = firstControlPoints(vector);

    vector[0] = points[0].y() + 2 * points[1].y();

    for (int i = 1; i < n - 1; ++i)
        vector[i] = 4 * points[i].y() + 2 * points[i + 1].y();

    vector[n - 1] = (8 * points[n - 1].y() + points[n].y()) / 2.0;

    QVector<qreal> yControl = firstControlPoints(vector);

    for (int i = 0, j = 0; i < n; ++i, ++j) {

        controlPoints[j].setX(xControl[i]);
        controlPoints[j].setY(yControl[i]);

        j++;

        if (i < n - 1) {
            controlPoints[j].setX(2 * points[i + 1].x() - xControl[i + 1]);
            controlPoints[j].setY(2 * points[i + 1].y() - yControl[i + 1]);
        } else {
            controlPoints[j].setX((points[n].x() + xControl[n - 1]) / 2);
            controlPoints[j].setY((points[n].y() + yControl[n - 1]) / 2);
        }
    }
    return controlPoints;
}



QPainterPath splineFromPoints(const QVector<QPointF> &points, int penWidth)
{
    QPainterPath splinePath;
    QVector<QPointF> controlPoints;
    if (points.count() >= 2)
        controlPoints = calculateControlPoints(points);

    if ((points.size() < 2) || (controlPoints.size() < 2)) {
        return splinePath;
    }

    Q_ASSERT(points.count() * 2 - 2 == controlPoints.count());

    // Use worst case scenario to determine required margin.
    qreal margin = penWidth * 1.42;

    splinePath.moveTo(points.at(0));
    for (int i = 0; i < points.size() - 1; i++) {
        const QPointF &point = points.at(i + 1);
        splinePath.cubicTo(controlPoints[2 * i], controlPoints[2 * i + 1], point);
    }
    return splinePath;
}




AuxiliaryInfo::AuxiliaryInfo(MorningTickChartView *v) {
   mtcv = v; 
}


void AuxiliaryInfo::addPriceWithXAxis(qreal x, int c, int h) {
    timePriceList.append(TimePrice(x, c, h));
}


void AuxiliaryInfo::drawCandleSelection(QPainter *painter, qreal startX, qreal endX, qreal endY) {
    int startPointIndex = -1;
    int endPointIndex = -1;
    qreal startDiff = 100.0;
    qreal endDiff = 100.0;

    for (int i = 0; i < timePriceList.count(); i++) {
        if (qAbs(timePriceList.at(i).xPos - startX) < startDiff) {
            startPointIndex = i;
            startDiff = qAbs(timePriceList.at(i).xPos - startX);
        }

        if (qAbs(timePriceList.at(i).xPos - endX) < endDiff) {
            endPointIndex = i;
            endDiff = qAbs(timePriceList.at(i).xPos - endX);
        }
    }
    //qWarning() << "startIndex : " << startPointIndex << "\tendIndex : " << endPointIndex;

    if (startPointIndex != -1 && endPointIndex != -1 && startPointIndex != endPointIndex) {
        QColor color;
        if (timePriceList.at(startPointIndex).highest < timePriceList.at(endPointIndex).highest)
            color.setRgb(255, 0, 0, 60);
        else 
            color.setRgb(0, 0, 255, 60);

        qreal rStartX = timePriceList.at(startPointIndex).xPos;
        qreal rEndX = timePriceList.at(endPointIndex).xPos;
        qreal rStartY = mtcv->mapPriceToPos(timePriceList.at(startPointIndex).highest, endY, 0);
        qreal rEndY = mtcv->mapPriceToPos(timePriceList.at(endPointIndex).highest, endY, 0);

        painter->fillRect(QRectF(rStartX, rStartY, rEndX - rStartX, rEndY - rStartY), color);

        QFont font = painter->font();
        font.setPointSize(5);
        painter->setFont(font);
        QPen pen = painter->pen();
        pen.setColor(Qt::black);
        painter->setPen(pen);
        qreal smallY = rStartY < rEndY ? rStartY : rEndY;
        qreal profit = (qreal(timePriceList.at(endPointIndex).highest) - timePriceList.at(startPointIndex).highest) / timePriceList.at(startPointIndex).highest * 100.0;
        painter->drawText(QPointF(rStartX, rStartY - 10), QString::number(timePriceList.at(startPointIndex).highest));
        painter->drawText(QPointF(rEndX, rEndY - 10), QString::number(timePriceList.at(endPointIndex).highest));
        if (timePriceList.at(endPointIndex).highest >= timePriceList.at(startPointIndex).highest)
            pen.setColor(Qt::red);
        else
            pen.setColor(Qt::blue);
        painter->setPen(pen);
        painter->drawText(QPointF(rEndX, smallY - 20), QString::number(profit, 'f', 1));
    }
}


void AuxiliaryInfo::drawAverageLine(QPainter *painter, qreal endY, int count) {
    painter->save();
    QVector<QPointF> points;
    if (timePriceList.count() < count) {
        painter->restore();
        return;
    }

    for (int i = count - 1; i < timePriceList.count(); i++) {
        long long priceSum = 0;
        for (int j = i - count + 1; j <= i; j++) {
            priceSum += (long long) timePriceList.at(j).close;
        }
        points.append(QPointF(timePriceList.at(i).xPos, 
                        mtcv->mapPriceToPos(priceSum / 20.0, endY, 0)));
    }

    if (points.size() > 0) {
        QPen pen;
        pen.setColor(Qt::green);
        painter->setPen(pen);
        QPainterPath path = splineFromPoints(points, 2);
        painter->drawPath(path);
    }
    painter->restore();
}
