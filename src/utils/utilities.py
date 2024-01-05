from _datetime import datetime

from src import logs
from src.logs import logger
from src.utils.constants import join_event_model, role_model

import os


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
    logs.logger.info(f"Make folder {folder_path}")
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
            user_selected.append(int(number))
    # rolled get all number was chosen
    rolled = join_event_model.get_all()
    if rolled:
        for roll in rolled:
            if 'selected_number' in roll and 'number_choices' in roll and roll['event_id'] == event_id:
                list_selected.append(roll['selected_number'])
    # Add number was selected to list selected
    for number in list_selected:
        arr = number.split(', ')
        for i in arr:
            if type(i) in [int, float]:
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
    return list_number.keys()
