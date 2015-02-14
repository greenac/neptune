from user_migration import UsersToJson

user_to_json = UsersToJson()
#user_to_json.save_to_file()
user_to_json.load_users_from_file_to_db()
#user_to_json.test_querey()
#user_to_json.users_from_servers()