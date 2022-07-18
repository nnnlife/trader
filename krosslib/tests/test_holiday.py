from datetime import datetime
from krosslib import holiday

print('2022-05-05', holiday.is_holidays(datetime(2022, 5, 5)))
