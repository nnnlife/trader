#ifndef CANDLE_H_
#define CANDLE_H_


class Candle {
public:
    Candle() {
    }

    void addTickData(int currentPrice, long long volume, const QDateTime &dt) {
        if (!isValid()) {
        }
        else {
        }
    }

    bool isValid() { return valid; }

private:
    int currentPrice = 0;
    int high = 0;
    int low = 0;
    int open = 0;
    int close = 0;
    bool valid = false;
};


#endif
