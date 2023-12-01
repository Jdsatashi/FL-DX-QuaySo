from src.mongodb import ROLE_TABLE

role = ROLE_TABLE.find_one({'role': 'auth_user'})
role_auth_id = str(role['_id']) if role else ROLE_TABLE.find_one(
    {'role': 'auth_user'})

role_admin = ROLE_TABLE.find_one({'role': 'admin'})
role_admin_id = str(role_admin['_id']) if role_admin else ROLE_TABLE.find_one(
    {'role': 'admin'})
