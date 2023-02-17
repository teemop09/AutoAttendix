from getpass import getpass

def validate_choice(text, choices, upper=False, lower=False):
    user_choice = input(text)
    if upper:
        user_choice = user_choice.upper()
    elif lower:
        user_choice = user_choice.lower()

    while user_choice not in choices:
        user_choice = input(text)
        if upper:
            user_choice = user_choice.upper()
        elif lower:
            user_choice = user_choice.lower()
     
    return user_choice

def prompt_credentials():
    username = input("Username (eg. TP012345)\t: ").lower()
    password = getpass("Password\t\t: ")
    return (username, password)