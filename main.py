import json  # loads, dump
import msvcrt  # getch
import re  # search
import sys  # exc_info
import traceback  # print_exception
from getpass import getpass
import os  # path, getcwd
import requests  # post, get, delete
from typing import Tuple, Union
from balloontip import balloon_tip
from detectqr import detect_otp_from_qr
from helper import prompt_credentials, validate_choice


def login_user(
    username, password, url, login_headers
) -> Tuple[bool, requests.Response]:
    payload = f"username={username}&password={password}"
    response = requests.post(url, headers=login_headers, data=payload)
    return (response.ok, response)


def extract_ticket_from_text(text: str) -> str:
    pattern = '<form\saction="(.+)"\smethod="\w+">'
    re_result = re.search(pattern, text)
    ticket_link = ""

    if re_result is not None:
        ticket_link = re_result.group(1)
    # The following code extract "TGT-{strings}" from the link
    ticket = ticket_link.split("/")[-1]
    return ticket


def send_otp(otp: Union[int, str], service_ticket: str) -> requests.Response:
    # """ Send OTP to GraphQL. """
    # """ Basically taking attendance """
    headers = {
        "Origin": "https://apspace.apu.edu.my",
        "x-amz-user-agent": "aws-amplify/2.0.7",
        "x-api-key": "da2-dv5bqitepbd2pmbmwt7keykfg4",
        "ticket": f"{service_ticket}",
        "Content-Type": "application/json",
    }
    operation_name = "updateAttendance"
    query = """mutation updateAttendance($otp: String!) {
    updateAttendance(otp: $otp) {
        id
        attendance
        classcode
        date
        startTime
        endTime
        classType
        __typename
    }
    }
    """

    variables = {"otp": otp}
    attendix_graphql_url = "https://attendix.apu.edu.my/graphql"
    response = requests.post(
        attendix_graphql_url,
        headers=headers,
        json={"operationName": operation_name, "query": query, "variables": variables},
    )
    return response


def parse_attendix_status(response: requests.Response) -> str:
    """Return attendance update status based on error message."""
    response_dict = json.loads(response.text)
    attendix_error = response_dict.get("errors")
    attendix_data = response_dict.get("data")
    status = ""

    if attendix_error is None:
        if attendix_data.get("updateAttendance").get("attendance") == "Y":
            status = "SUCCESS"
        else:
            status = "NOT GOOD"
    else:
        # if there're errors
        status = attendix_error[0].get("message")
    return status


def update_attendance_service(url, payload) -> None:
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    # """ Pending and wait for OTP"""
    if len(sys.argv) > 1 and sys.argv[1].strip().isdigit():
        otp = sys.argv[1].strip()
    else:
        print("[#] Waiting for QR Code...")
        otp = detect_otp_from_qr()

    # """ Get service ticket for Attendix """
    response = requests.post(url, headers=headers, data=payload)
    service_ticket = response.text
    print(service_ticket)
    print("=" * 10)

    attendix_r = send_otp(otp, service_ticket)
    attendance_update_status = parse_attendix_status(attendix_r)

    print("[#] Now wait for few seconds...")
    balloon_tip("Sent OTP!", f"Status: {attendance_update_status}")


def main():
    login_headers = {
        "Origin": "https://apspace.apu.edu.my",
        "Content-Type": "application/x-www-form-urlencoded",
    }
    attendance_and_logout_payload = "service=https://api.apiit.edu.my/attendix"

    cwd = os.path.abspath(os.path.dirname(__file__))  # current working directory
    secret_path = os.path.join(cwd, "secrets.json")
    base_url = "https://cas.apiit.edu.my/cas"
    url = f"{base_url}/v1/tickets"

    with open(secret_path, "r") as sf:
        sec = json.loads(sf.read())
    has_credentials = False
    # check for empty string in secret file
    # if not empty means HAVE records of credentials
    for v in sec.values():
        if v:
            has_credentials = True

    # """LOGIN PROCESS """
    # Special flag for when saved credentials is wrong
    wrong_credentials_record = False
    # Flag for whether logged in or not
    login = False
    while not login:
        # Ask for login details
        # if no correct credentials record
        if wrong_credentials_record or not has_credentials:
            username, password = prompt_credentials()
        else:
            username = sec.get("uname")
            password = sec.get("pw")

        login_success, response = login_user(username, password, url, login_headers)
        if not login_success:
            print("[!] Login failed!\n")
            if has_credentials:
                print("[!] Saved credentials are possibly wrong!\n")
                wrong_credentials_record = True
            continue
        login = True
        print("[/] Login successful!\n")

        # """ Extract ticket from response body """
        login_ticket = extract_ticket_from_text(response.text)
        url_ticket = f"{base_url}/v1/tickets/{login_ticket}"
        print(login_ticket)
        print("=" * 10)

        if has_credentials and not wrong_credentials_record:
            continue

        # if no credentials record
        save_confirm = validate_choice(
            "Do you want to save your credentials? [y/n]: ", ["y", "n"], lower=True
        )

        # Save credentials in secret file
        # if user wants to
        if save_confirm == "y":
            with open(secret_path, "w") as sf:
                d = {"uname": username, "pw": password}
                json.dump(d, sf, indent="")
                print("[/] Credentials saved.")
    try:
        update_attendance_service(url_ticket, attendance_and_logout_payload)
    except:
        traceback.print_exception(*sys.exc_info())
        # Get error name
        balloon_tip("Error!", sys.exc_info()[0].__name__)
    finally:
        try:
            """log out"""
            if requests.delete(
                url_ticket, headers=login_headers, data=attendance_and_logout_payload
            ).ok:
                print("[/] Logged out successfully.")
            else:
                print(f"[!] Fail to log out...\nSend this to author:{login_ticket}")
        except UnboundLocalError:
            # if user haven't log in yet
            # ignore and exit program
            traceback.print_exception(*sys.exc_info())
        print("Press any key to exit...", end="", flush=True)
        msvcrt.getch()


if __name__ == "__main__":
    print("Starting...")
    main()
