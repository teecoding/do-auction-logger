from time import sleep
import requests
import os
import json
from datetime import datetime
from dotenv import load_dotenv
from bs4 import BeautifulSoup

load_dotenv()

AUCTION_TYPES = ['hour', 'day', 'week']
ROOT_PATH = os.path.dirname(os.path.abspath(__file__))
SERVERS=["int5","int1","de2","de4","es1","fr1","int7","int11","int14","gbl1","int2","int6","mx1","us2","pl3","ru1","ru5","tr3","tr4","tr5"]
SERVER_SWAP_DELAY=5

def formattedLogMsg(content, status = 'INFO'):
    return f'[{str(datetime.now()).split(".")[0]}] - {status} - {content}' 

class Logger:
    
    def __init__(self):
        self.session = requests.Session()

        self.server_links = []
        self.server_after_login = None
        self.current_server = None
        self.auction = {
            "hour": {
                "start": None,
                "end": None,
                "items": []
            },
            "day":  {
                "start": None,
                "end": None,
                "items": []
            },
            "week":  {
                "start": None,
                "end": None,
                "items": []
            },
        }

        self._login()

    # Start logging auction data from servers
    def start(self):
        for type in AUCTION_TYPES:
            self._log(type)

        self._swapServer(SERVERS[0])
            
        for id, server in enumerate(SERVERS):
            self.current_server = SERVERS[id]

            self._load()

            for type in AUCTION_TYPES:
                self._log(type)

            try: 
                if SERVERS[id+1] != self.server_after_login:
                    self._swapServer(SERVERS[id+1])
                else:
                    self.current_server = SERVERS[id-1]
            except:
                break
        formattedLogMsg('Done.')

    # Create necessary folders if they don't exist
    def _prepareFolders(self):
        if os.path.exists(f"{ROOT_PATH}/data") == False:
            os.mkdir(f"{ROOT_PATH}/data")

        if os.path.exists(f"{ROOT_PATH}/data/{self.current_server}") == False:
            os.mkdir(f"{ROOT_PATH}/data/{self.current_server}")
        
        for type in AUCTION_TYPES:
            if os.path.exists(f"{ROOT_PATH}/data/{self.current_server}/{type}") == False:
                os.mkdir(f"{ROOT_PATH}/data/{self.current_server}/{type}")

    # Login to darkorbit and store current server
    def _login(self):
        print(formattedLogMsg('Logging in..'))
        r = self.session.get(f'https://www.darkorbit.com/');
        soup = BeautifulSoup(r.content, 'lxml')
        form = soup.find('form', {"class":"bgcdw_login_form"})
        r = self.session.post(form['action'], data={"username": os.getenv('USERNAME'), "password": os.getenv('PASSWORD')})
        self.server_after_login = self.current_server = r.url.split('//')[-1].split('.')[0]
        self._load()

    # Load auction and scrappe data from it
    def _load(self):
        self._clearData()
        print(formattedLogMsg('Loading auction..'))
        res = self.session.get(f"https://{self.current_server}.darkorbit.com/indexInternal.es?action=internalAuction")
        soup = BeautifulSoup(res.content, 'lxml')

        try:
            for type in AUCTION_TYPES:
                self._getStartEndDate(soup, type)
                self._getItems(soup, type)
            self._getServerLinks()
        except:
            print(formattedLogMsg('Unable to get auction data. Are you sure you have correct credentials?', 'ERROR'))
            exit()

    # Get latest auction items
    def _getItems(self, soup: BeautifulSoup, type):
        for items in soup.find(id=f"auction_content_{type}").find_all('div', {"class":"auction_list_history"}):
            for item in items.find('tbody', {"class":"auction_history_wrapper"}).find_all("tr", {"class": "auctionItemRow"}):
                self.auction[type]['items'] += [self._parseItem(item)]

    # Get latest auction end date
    def _getStartEndDate(self, soup: BeautifulSoup, type):
        end = datetime.strptime(soup.find(id=f"auction_history_selection_{type}").find_all('div', {"class": "filter_item"})[0].text.strip(), '%Y-%m-%d %H:%M:%S')
        hour = f"0{end.hour}" if end.hour <= 9 else end.hour
        second = f"0{end.second}" if end.second <= 9 else end.second
        self.auction[type]['end'] = f"{end.date()} {hour}:{end.minute}:{second}"
        hour = 23 if end.hour -1 == -1 else end.hour - 1
        self.auction[type]['start'] = f"{end.date()} {hour}:{end.minute}:{second}"

    # Get server links
    def _getServerLinks(self):
        self.server_links = []
        res = self.session.post(f"https://{self.current_server}.darkorbit.com/ajax/instances.php", data={'command':'getInstanceList'})
        soup = BeautifulSoup(json.loads(res.content)['code'], 'lxml')
        for server in soup.find_all('tr', {"class":"serverSelection_ini"}):
            server_name = server['target'].split('//')[-1].split('.')[0]
            self.server_links += [{ server_name: server['target'] }]

    # Log auction items into file
    def _log(self, type):
        self._prepareFolders()
        filename = self.auction[type]['end'].replace('-', '').replace(':', '').replace(' ', '');
        filepath = f"{ROOT_PATH}/data/{self.current_server}/{type}/{filename}.json"
        if os.path.exists(filepath) == False:
            with open(f"{filepath}", 'a+') as f:
                f.write(json.dumps(self.auction[type], indent=4, separators=(',',': '), ensure_ascii=False).encode('utf8').decode())
                f.close()
            print(formattedLogMsg(f'Auction was logged - {filepath}'))

    # Helper function for parsing auction items from html
    def _parseItem(self, item: BeautifulSoup):
        return {
            "name": item.find('td',{'class':'auction_history_name_col'}).text.strip(),
            "type": item.find('td',{'class':'auction_history_type'}).text.strip(),
            "winner": item.find('td',{'class':'auction_history_winner'}).text.strip(),
            "payed": item.find('td',{'class':'auction_history_current'}).text.strip(),
        }

    # Helper function for swapping servers
    def _swapServer(self, next_server):
        print(formattedLogMsg(f'Will swao from {self.current_server} to {next_server} after {SERVER_SWAP_DELAY} seconds'))
        sleep(SERVER_SWAP_DELAY)

        for server in self.server_links:
            if next_server in server.keys():
                self.session.get(server[next_server])
                return

        raise ValueError(formattedLogMsg(f'Server {next_server} not found in servers..','ERROR'))

    # Helper function for clearing server links and server auction data
    def _clearData(self):
        self.auction = {
            "hour": {
                "start": None,
                "end": None,
                "items": []
            },
            "day":  {
                "start": None,
                "end": None,
                "items": []
            },
            "week":  {
                "start": None,
                "end": None,
                "items": []
            },
        }