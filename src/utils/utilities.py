from _datetime import datetime
from bson import ObjectId

from src.app import logger, message_logger
from src.utils.constants import join_event_model, role_model, event_model, MAX_NUMBER_RANGE_DEFAULT as MAX_NUM, \
    user_model

import os
import random
import traceback

# Get user role id
role = role_model.get_one({'role': 'auth_user'})
role_auth_id = str(role['_id']) if role else role_model.get_one(
    {'role': 'auth_user'})

# Get admin role id
role_admin = role_model.get_one({'role': 'admin'})
role_admin_id = str(role_admin['_id']) if role_admin else role_model.get_one(
    {'role': 'admin'})


# Create new folder and get path
def create_folder(folder_name):
    year = datetime.utcnow().year
    uploads_event_folder = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'static', 'uploads')
    year_path = os.path.join(uploads_event_folder, str(year))
    folder_path = os.path.join(year_path, folder_name)
    logger.info(f"Make folder {folder_path}")
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    return folder_path


# Function creating number list for user choose
def create_number_list(max_range: int, limit: int, event_id: str, user_id: str):
    list_selected, all_number_selected, user_selected = [], [], []
    unavailable_number = {}
    # user_rolled check which number chosen by user
    user_rolled = join_event_model.get_one({'event_id': event_id, 'user_id': user_id})
    if 'selected_number' in user_rolled and 'number_choices' in user_rolled:
        number_selected = user_rolled['selected_number'].split(', ')
        for number in number_selected:
            try:
                user_selected.append(int(number))
            except ValueError:
                continue
    # rolled get all number was chosen
    rolled = join_event_model.get_all()
    if rolled:
        for roll in rolled:
            if 'selected_number' in roll and 'number_choices' in roll and roll['event_id'] == event_id:
                if roll['selected_number'] != '':
                    list_selected.append(roll['selected_number'])
    # Add number was selected to list selected
    for number in list_selected:
        arr = number.split(', ')
        for i in arr:
            all_number_selected.append(int(i))
    # Dict for number selected
    for num in all_number_selected:
        if num not in unavailable_number:
            unavailable_number[num] = 1
        else:
            # Counting up for number selected
            unavailable_number[num] += 1
        # When number selected own by user, remove 1 count from unavailable dict
        if num in user_selected:
            unavailable_number[num] -= 1
    list_number = {}
    for i in range(1, max_range + 1):
        if i > 0:
            if i in unavailable_number:
                if limit - unavailable_number[i] > 0 and unavailable_number[i] > 0:
                    list_number[i] = limit - unavailable_number[i]
            else:
                list_number[i] = limit
    # logger.info(f"List avaiable number: {list_number}")
    return list_number.keys()


def update_user_join(_id):
    # Log info
    message_logger.info(f"Update user join with new number list.")
    # Get main event
    main_event = event_model.get_one({'_id': ObjectId(_id)})
    # Copy dict and remove unused field
    for i in ['_id', 'date_start', 'date_created']:
        main_event.pop(i)
    # Get event range number, if not get the default range
    if 'range_number' not in main_event:
        main_event['range_number'] = MAX_NUM
    # Get users id of users chosen
    event_join = join_event_model.get_many({
        "event_id": _id, "number_choices": {"$exists": True}, "selected_number": {"$exists": True}
    })
    # Loop through event_join get each user data
    for user in event_join:
        turn_roll = user['user_point'] // main_event['point_exchange']
        logger.info(f"User id: {user['user_id']} | {user['turn_roll']}")
        try:
            # Get list number selected
            selected_number = list(map(int, user['selected_number'].split(', ')))
        except ValueError:
            selected_number = None
            message_logger.info(f"User have selected_number is '' (None string).")
            # Handle user:
            message_logger.info(f"Before update user: {user['selected_number']}")
            # Remove number > event range number
            while selected_number is not None and  len(selected_number) > 0 and selected_number[len(selected_number) - 1] > main_event['range_number']:
                message_logger.info(f"Removed number: [{selected_number[len(selected_number) - 1]}]")
                selected_number.pop()
            # Combine new list to string
            selected_number_str = ', '.join(map(str, selected_number)) if selected_number is not None else None
            # Try update new data
            try:
                join_event_model.update(user['_id'], {
                    'turn_roll': turn_roll,
                    'number_choices': len(selected_number),
                    'selected_number': selected_number_str
                })
                message_logger.info(f"After update user: {selected_number_str}")
            # When get error => export message
            except Exception as e:
                error_msg = traceback.format_exc()
                logger.error(f"Error when update user join automatic.\nError: '{e}'\n{error_msg}")
    event_join2 = join_event_model.get_many({
        "event_id": _id, "number_choices": {"$exists": False}, "selected_number": {"$exists": False}
    })
    for user in event_join2:
        turn_roll = user['user_point'] // main_event['point_exchange']
        try:
            join_event_model.update(user['_id'], {
                'turn_roll': turn_roll
            })
        except Exception as e:
            error_msg = traceback.format_exc()
            logger.error(f"Error when update user join automatic.\nError: '{e}'\n{error_msg}")


# Auto random number function
def auto_random(event_id):
    # Log info
    message_logger.info(f"Auto random number for user.")
    # Get main event
    event = event_model.get_one({'_id': ObjectId(event_id)})
    event.pop('_id')
    # Get event range number
    event['range_number'] = MAX_NUM if 'range_number' not in event else int(event['range_number'])
    # Get user not joined and have turned choose number > 1
    event_join = join_event_model.get_many({
        "event_id": event_id,
        "turn_roll": {"$gt": 0},
        "number_choices": {"$exists": False},
        "selected_number": {"$exists": False}
    })
    # Get user was chosen but not choice all their turn
    wasted_choice = join_event_model.get_many({
        "event_id": event_id,
        "$expr": {"$gt": ["$turn_roll", "$number_choices"]},
        "turn_roll": {"$gt": 0},
        "$and": [
            {"number_choices": {"$exists": True}},
            {"selected_number": {"$exists": True}}
        ]
    })
    # Change object to list
    event_join = list(event_join)
    wasted_choice = list(wasted_choice)
    # Check if event_join have any value
    if any(event_join):
        logger.info("Event join ok")
        now = datetime.now()
        # Start loop through and random
        for user in event_join:
            loop = handle_random_for_each_user(user, event, now)
            if not loop:
                continue
    # Change object to list
    if any(wasted_choice):
        logger.info("Wasted join ok")
        now = datetime.now()
        # Start loop through and random
        for user in wasted_choice:
            loop = handle_random_for_each_user(user, event, now)
            if not loop:
                continue


def handle_random_for_each_user(user, event, now, set_turn=None):
    # Print user id
    number_choices = user.get('number_choices', 0)
    message_logger.info(f"User id: {user['user_id']} | Lượt chọn ban đầu: {user['turn_roll']} | Lượt đã chọn: {number_choices}.")
    message_logger.info(f"Số đã chọn ban đầu: [{user.get('selected_number', 0)}]")
    # Create available number dict
    number_list = create_number_list(event['range_number'], event['limit_repeat'], user.get('event_id'), user['user_id'])
    number_list = list(number_list)
    # Get number of turn roll or the roll was not selected
    logger.debug(f"Lỗi here")
    turn_roll = user['user_point'] // event['point_exchange'] \
        if number_choices == 0 else user['turn_roll'] - user['number_choices']
    message_logger.info(f"Lượt chọn khả thi: {turn_roll} lượt.")
    if set_turn is not None:
        if turn_roll > set_turn:
            turn_roll = int(set_turn)
        message = f"Số tem random phải nhỏ hơn tổng tem của user."
        return False, message
    logger.debug(f"Turn roll: {turn_roll}")
    # Random number ticket
    list_selected = number_list if turn_roll > len(number_list) else random.sample(number_list, turn_roll)
    if any(list_selected):
        list_selected = list(list_selected)
        # Get finally list after random | can be all random number list or old number list + random list
        try:
            number_selected = list_selected \
                if 'number_choices' not in user else list_selected + list(map(int, user['selected_number'].split(', ')))
        except ValueError:
            # Handle error when user['selected_number'] is '' or None
            user['selected_number'] = []
            number_selected = list_selected \
                if 'number_choices' not in user else list_selected + user['selected_number']
        message_logger.info(f"Random {len(list_selected)} số: {list_selected}.")
        message_logger.info(f"Tổng số đã chọn + số random: {len(number_selected)}.")
        # Change data array to string for saving to database
        list_selected_str = ', '.join(list(map(str, sorted(number_selected))))
        # Process updated
        try:
            join_event_model.update(user['_id'], {
                'number_choices': len(number_selected),
                'selected_number': list_selected_str,
                'date_updated': now
            })
            message_logger.info(f"Hệ thống tự động chọn số cho user '{user['user_id']}': [{list_selected_str}]")
        # Except error
        except Exception as e:
            error_msg = traceback.format_exc()
            logger.error(f"Error while randomly number for user.\n Error: {e}\n{error_msg}")
        return True
    else:
        message_logger.info(f"Số lượng tem đã hết.")
        return False


def update_user_role(_id):
    user = user_model.get_one({'_id': ObjectId(_id)})
    if 'role_id' not in user:
        user_model.update(ObjectId(_id), {
            'role_id': role_auth_id,
        })
