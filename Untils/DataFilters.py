from DBSingleton import DBSingleton

db = DBSingleton.getInstance().get_db()


def is_private_chat(data):
    if "message" in data and "chat" in data["message"] and 'type' in data["message"]['chat']:
        if data["message"]["chat"]["type"] == "private":
            return True
    return False


def check_if_text_message(current_update, text,username=None):
    if 'message' in current_update and 'text' in current_update['message'] and (current_update['message'][
        'text'] == text or current_update['message'][
        'text'] == text+"@"+str(username)):
        return True
    return False


def check_if_text_in_message(current_update, text,username=None):
    if 'message' in current_update and 'text' in current_update['message'] and text in current_update['message'][
        'text']:
        return True
    return False

def check_if_in_callback_data(current_update, text):
    if 'callback_query' in current_update and 'data' in current_update['callback_query'] and text in \
            current_update['callback_query']['data']:
        return True
    return False


def get_variables(current_update):
    user_id = current_update['callback_query']['from']['id']
    msg_id = current_update['callback_query']['message']['message_id']
    call_back = current_update['callback_query']['data']
    if "$" in call_back:
        variables = str(call_back.split("$")[-1])
        data = variables.split("_")
    else:
        data = None
    return user_id, msg_id, data


def is_reply_to_message(current_update, text):
    if 'message' in current_update and 'reply_to_message' in current_update['message'] and 'text' in \
            current_update['message']['reply_to_message'] and current_update['message']['reply_to_message'][
        'text'] == text:
        return True
    return False


def is_reply_to_message_text_list_in(current_update, lst):
    if 'message' in current_update and 'reply_to_message' in current_update['message'] and 'text' in \
            current_update['message']['reply_to_message']:
        for text in lst:
            if text not in current_update['message']['reply_to_message']['text']:
                return False
        return True
    return False


def get_value_from_dataframe(dataframe, col_title, index):
    # Check if dataframe is empty or None
    if dataframe.empty or dataframe is None:
        return None

    # Check if col_title exists in the dataframe
    if col_title not in dataframe.columns:
        return None

    # Check if index exists in the dataframe
    if index not in dataframe.index:
        return None

    # Return the value in the specified cell
    value = dataframe.loc[index, col_title]
    return value

def set_value_in_dataframe(dataframe, col_title, index, new_value):
    # Check if dataframe is empty or None
    if dataframe.empty or dataframe is None:
        return None

    # Check if col_title exists in the dataframe
    if col_title not in dataframe.columns:
        return None

    # Check if index exists in the dataframe
    if index not in dataframe.index:
        return None

    # Update the value in the specified cell
    dataframe.loc[index, col_title] = new_value
    return dataframe

def get_all_indexes_from_dataframe(dataframe):
    if dataframe.empty or dataframe is None:
        return []

    return dataframe.index.tolist()