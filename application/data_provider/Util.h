#include <QDate>

namespace morning {
    class Util {
        public:
        static QDate convertToDate(unsigned int d) {
            unsigned int year = d / 10000;
            unsigned int month = d % 10000 / 100;
            unsigned int day = d % 100;
            return QDate(year, month, day);
        }

        static unsigned int decreaseTime(unsigned int time, int minutes) {
            if ((time - minutes) % 100 > 59) {
                int t = (int(time / 100) - 1) * 100 + (60 - minutes);
                return (unsigned int)t;
            }
            return (unsigned int)time - minutes;
        }
    };
};
