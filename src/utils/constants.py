from typing import Final

from src.models import Models
from src.mongodb import EVENT_TABLE, ACCOUNT_TABLE, USER_JOIN_EVENT, ROLE_TABLE

MAX_NUMBER_RANGE_DEFAULT: Final[int] = 266
DATE_RANDOM: Final[int] = 1
event_model = Models(table=EVENT_TABLE)
join_event_model = Models(table=USER_JOIN_EVENT)
user_model = Models(table=ACCOUNT_TABLE)
role_model = Models(table=ROLE_TABLE)
