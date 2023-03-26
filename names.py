import requests
from urllib3 import disable_warnings
from urllib.parse import quote
import psutil
import base64
import os
import logging
import re


logger = logging.getLogger(__name__)
disable_warnings()
RIOTCLIENT_API = "https://127.0.0.1:{}"
LCU_NAME = 'LeagueClientUx'


class LCU:
    def __init__(self):
        self.process_args = {}
        self.get_lcu_args()

    def is_lcu_available(self):
        for p in psutil.process_iter():
            if LCU_NAME in p.name():
                return True
        return False

    def get_lcu_args(self):
        if not self.is_lcu_available():
            logger.warn(f"No {LCU_NAME} found. Login to an account and try again.")
            return

        matcher = re.compile(r'^--([^=]+)=(.+)$')
        for p in psutil.process_iter():
            if LCU_NAME in p.name():
                args = p.cmdline()
                for a in args:
                    if match := matcher.match(a):
                        name, value = match.groups()
                        self.process_args[name] = value
                break

        self.lcu_session_token = base64.b64encode(
            ("riot:" + self.process_args['remoting-auth-token']).encode("ascii")
        ).decode("ascii")
        self.riotclient_session_token = base64.b64encode(
            ("riot:" + self.process_args['riotclient-auth-token']).encode("ascii")
        ).decode("ascii")

        self.lcu_headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": "Basic " + self.lcu_session_token,
        }

        self.riotclient_headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "LeagueOfLegendsClient",
            "Authorization": "Basic " + self.riotclient_session_token,
        }

    def get_participants(self):
        logger.info("Getting Participants")
        url = RIOTCLIENT_API.format(self.process_args['riotclient-app-port']) + "/chat/v5/participants/champ-select"
        r = requests.get(url, headers=self.riotclient_headers, verify=False)
        participants = r.json()["participants"]
        return participants

    def get_participant_names(self):
        participants = self.get_participants() or []
        return [x["name"] for x in participants]

    def get_porofessor_link(self):
        base = f"https://porofessor.gg/pregame/{self.process_args['region']}/"
        names = self.get_participant_names()
        if names:
            param = ",".join(quote(name) for name in names)
            return base + param
        return None


if __name__ == "__main__":
    client = LCU()
    link = client.get_porofessor_link()
    if link:
        logger.info(link)
        os.popen(f'start "" "{link}"')
    else:
        logger.warn("no link")
