import requests
import os
import json

from time import sleep
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
        self.server_after_login = ""
        self.current_server = ""
        self.history_id = None
        self.start_at = ""
        self.end_at = ""
        self.soup = None

        self._login()

    # Start logging auction data from servers
    def start(self):
        for auction_type in AUCTION_TYPES:
            self._log(auction_type)

        self._swapServer(SERVERS[0])
            
        for id, server in enumerate(SERVERS):
            self.current_server = SERVERS[id]

            self._load()

            for auction_type in AUCTION_TYPES:
                self._log(auction_type)

            try: 
                if SERVERS[id+1] != self.server_after_login:
                    self._swapServer(SERVERS[id+1])
                else:
                    self.current_server = SERVERS[id-1]
            except:
                break
        print(formattedLogMsg('Done.'))

    # Create necessary folders if they don't exist
    def _createDataFolder(self):
        if os.path.exists(f"{ROOT_PATH}/data") == False:
            os.mkdir(f"{ROOT_PATH}/data")

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
        self.items = {
            "hour": [],
            "day": [],
            "week": [],
        }
        res = self.session.get(f"https://{self.current_server}.darkorbit.com/indexInternal.es?action=internalAuction&lang=en")
        self.soup = BeautifulSoup(res.content, 'lxml')
        
        print(formattedLogMsg(f'User: {os.getenv('USERNAME')} Password: {os.getenv('PASSWORD')}', 'DEBUG'))
        with open('./data/test.html', 'w+') as f:
            f.write(self.soup.prettify())
            f.close()

        for auction_type in AUCTION_TYPES:
            self._getStartEndDate(auction_type)
            self._getItems(auction_type)
        self._getServerLinks()
        

    # Get latest auction items
    def _getItems(self, auction_type):
        for items in self.soup.find(id=f"auction_content_{auction_type}").find_all('div', {"class":"auction_list_history"}):
            for item in items.find('tbody', {"class":"auction_history_wrapper"}).find_all("tr", {"class": "auctionItemRow"}):
                self.items[auction_type] += [self._parseItem(auction_type, item)]

    # Get latest auction end date
    def _getStartEndDate(self, auction_type):
        date_element = self.soup.find(id=f"auction_history_selection_{auction_type}").find_all('div', {"class": "filter_item"})[0]
        self.history_id = date_element['id'].replace('history_','')

        end = datetime.strptime(date_element.text.strip(), '%Y-%m-%d %H:%M:%S')

        hour = f"0{end.hour}" if end.hour <= 9 else end.hour
        second = f"0{end.second}" if end.second <= 9 else end.second
        self.end_at = f"{end.date()} {hour}:{end.minute}:{second}"
        
        hour = 23 if end.hour -1 == -1 else end.hour - 1
        self.start_at = f"{end.date()} {hour}:{end.minute}:{second}"

    # Get server links
    def _getServerLinks(self):
        self.server_links = []
        res = self.session.post(f"https://{self.current_server}.darkorbit.com/ajax/instances.php", data={'command':'getInstanceList'})
        soup = BeautifulSoup(json.loads(res.content)['code'], 'lxml')
        for server in soup.find_all('tr', {"class":"serverSelection_ini"}):
            server_name = server['target'].split('//')[-1].split('.')[0]
            self.server_links += [{ server_name: server['target'] }]

    # Log auction items into file
    def _log(self, auction_type):
        self._createDataFolder()
        filename = f"{self.current_server}-{auction_type}-{self.end_at.replace('-', '').replace(':', '').replace(' ', '')}.jsonl"
        filepath = f"{ROOT_PATH}/data/{filename}"

        if os.path.exists(filepath) == False:
            with open(f"{filepath}", 'a+') as f:
                for item in self.items[auction_type]:
                    f.write(json.dumps(item, ensure_ascii=False).encode('utf8').decode() + '\n')
                f.close()
            print(formattedLogMsg(f'Auction was logged - {self.current_server} - {auction_type} - {filename}'))

    # Helper function for parsing auction items from html
    def _parseItem(self, auction_type, item: BeautifulSoup):
        return {
            "history_id": self.history_id,
            "server": self.current_server,
            "auction_type": auction_type,
            "name": self._getItemLootId(auction_type, item.find('td', {'class': 'auction_history_name_col'}).text.strip()),
            "winner": item.find('td',{'class':'auction_history_winner'}).text.strip(),
            "payed": item.find('td',{'class':'auction_history_current'}).text.strip().replace('.',''),
            "start_at": self.start_at,
            "end_at": self.end_at 
        }

    def _getItemLootId(self, auction_type, item_name):
        for items in self.soup.find(id=f"auction_content_{auction_type}").find_all('div', {"class":"auction_list_current"}):
            for item in items.find('tbody', {"class":"auction_item_wrapper"}).find_all("tr", {"class": "auctionItemRow"}):
                if item.find('td', {"class": "auction_item_name_col"}).text.strip() == item_name:
                    return item.find('input', {'id': f"{item['itemkey']}_lootId"})['value']

        raise ValueError(formattedLogMsg(f'Item with name {item_name} was not found..','ERROR'))


    # Helper function for swapping servers
    def _swapServer(self, next_server):
        print(formattedLogMsg(f'Will swap from {self.current_server} to {next_server} after {SERVER_SWAP_DELAY} seconds'))
        sleep(SERVER_SWAP_DELAY)

        for server in self.server_links:
            if next_server in server.keys():
                self.session.get(server[next_server])
                return

        raise ValueError(formattedLogMsg(f'Server {next_server} not found in servers..','ERROR'))
