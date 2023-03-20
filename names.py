import requests
from urllib3 import disable_warnings
from urllib.parse import quote
import json
import platform
import psutil
import base64
import os
from functools import cached_property
import logging



logger = logging.getLogger(__name__)
disable_warnings()
LCU_API = "https://127.0.0.1:{}"
RIOTCLIENT_API = 'https://127.0.0.1:{}'


class LCU:
    def __init__(self):
        self.getLCUArguments()

    @cached_property
    def lcu_name(self):
        lcu_name = ''
        system = platform.system()
        if system in ('Darwin', 'Linux'):
            lcu_name = 'LeagueClientUx'
        else:
            lcu_name = 'LeagueClientUx.exe'
        return lcu_name

    def is_lcu_available(self):
        return self.lcu_name in (p.name() for p in psutil.process_iter())

    def getLCUArguments(self):
        if not self.is_lcu_available():
            logger.warn(f'No {self.lcu_name} found. Login to an account and try again.')
            return

        for p in psutil.process_iter():
            if p.name() == self.lcu_name:
                args = p.cmdline()
                for a in args:
                    if '--region=' in a:
                        self.region = a.split('--region=', 1)[1].lower()
                    if '--remoting-auth-token=' in a:
                        self.auth_token = a.split('--remoting-auth-token=', 1)[1]
                        self.lcu_session_token = base64.b64encode(
                            ('riot:' + self.auth_token).encode('ascii')
                        ).decode('ascii')
                    if '--app-port' in a:
                        self.app_port = a.split('--app-port=', 1)[1]
                    if '--riotclient-auth-token=' in a:
                        self.riotclient_auth_token = a.split('--riotclient-auth-token=', 1)[1]
                        self.riotclient_session_token = base64.b64encode(
                            ('riot:' + self.riotclient_auth_token).encode('ascii')
                        ).decode('ascii')
                    if '--riotclient-app-port=' in a:
                        self.riotclient_app_port = a.split('--riotclient-app-port=', 1)[1]

        self.lcu_headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': 'Basic ' + self.lcu_session_token
        }

        self.riotclient_headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'User-Agent': 'LeagueOfLegendsClient',
            'Authorization': 'Basic ' + self.riotclient_session_token
        }


    def get_participants(self):
        participants = []    

        get_current_summoner = LCU_API.format(self.app_port) + '/lol-summoner/v1/current-summoner'
        r = requests.get(get_current_summoner, headers=self.lcu_headers, verify=False)
        r = json.loads(r.text)

        get_champ_select = LCU_API.format(self.app_port) + '/lol-champ-select/v1/session'
        r = requests.get(get_champ_select, headers=self.lcu_headers, verify=False)
        r = json.loads(r.text)
        if 'errorCode' in r:
            logger.warn('Not in champ select.')
        else:
            logger.info("* Getting Participants *")
            get_lobby = RIOTCLIENT_API.format(self.riotclient_app_port) + '/chat/v5/participants/champ-select'
            r = requests.get(get_lobby, headers=self.riotclient_headers, verify=False)
            r = json.loads(r.text)
            participants = r['participants']
        return participants

    def get_participant_names(self):
        participants = self.get_participants()
        if participants:
            return [x['name'] for x in participants]
        return []

    def get_porofessor_link(self):
        base = f'https://porofessor.gg/pregame/{self.region}/'
        names = self.get_participant_names()
        if names:
            param = ','.join(quote(name) for name in names)
            return base + param
        return None


if __name__ == '__main__':
    client = LCU()
    link = client.get_porofessor_link()
    if link:
        logger.info(link)
        os.popen(f'start "" "{link}"')
    else:
        logger.warn('no link')
