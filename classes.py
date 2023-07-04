import uuid
from urllib import parse
from config import YOUTUBE_API_KEY
import aiohttp
from requests.exceptions import HTTPError
import asyncio

class Video:
    def __init__(self):
        self.link = None
        self.session = None
        self.id = uuid.uuid4().hex
        self.code = None
        self.thumbnail = None
        self.data = None
        self.duration = None
        self.name = None
        self.embed = None
    
    async def create(self, link: str, httpSession: aiohttp.ClientSession):
        self.link = link
        self.session = httpSession
        print(f'Creating {self.id}')
        self.code = self.parse_id()
        self.thumbnail = self.get_thumbnail_link()
        self.embed = self.get_embed_link()
        self.data = None
        await self.parse_data()
    
    def parse_id(self):
        
        FIND_ERROR = -1
        
        parsed = parse.urlparse(self.link)
        if parsed.path.find('/watch') != FIND_ERROR:
            return parsed.query.split('v=')[1].split('&')[0]
        if parsed.path.find('/user') != FIND_ERROR:
            return parsed.fragment.split('/')[-1]
        if parsed.path.find('/v/') != FIND_ERROR:
            return parsed.path.split('/v/')[1]
        if parsed.path.find('/embed/') != FIND_ERROR:
            return parsed.path.split('/embed/')[1]
        return parsed.path[1:]
    
    async def parse_data(self):
            params = {'id': self.code, 'key': YOUTUBE_API_KEY,
                'fields': 'items(snippet(title),contentDetails(duration))',
                'part': 'snippet,contentDetails'}
            print(f'Parsing for {self.code}')
            async with self.session.get(f'https://www.googleapis.com/youtube/v3/videos?{ parse.urlencode(params) }') as response:
                try:
                    print(f'Parse finished for {self.code}')
                    response.raise_for_status()
                except HTTPError as http_error:
                    print(f'HTTP error occurred: {http_error}')
                    self.data = -1
                except Exception as error:
                    print(f'Other error occurred: {error}')
                    self.data = -1
                else:
                    self.data = await response.json()
                    self.duration = self.parse_duration()
                    self.name = self.data['items'][0]['snippet']['title']
    
    def parse_duration(self):
        duration = self.data['items'][0]['contentDetails']['duration'][1:]
        ret_dur = {
            'Y': 0, 'M': 0, 'D': 0, 'h':0, 'm':0, 's':0
        }
        
        buffer = ""
        high = True
        for ch in duration:
            if ch.isalpha():
                if ch == 'T':
                    high = False
                    continue
                if buffer.isdigit():
                    ret_dur[ch.upper() if high else ch.lower()] = int(buffer)
                buffer = ""
                continue
            buffer += ch
        
        return ret_dur
    
    def get_thumbnail_link(self):
        return f'https://img.youtube.com/vi/{ self.code }/mqdefault.jpg'
    
    def get_embed_link(self):
        return f''
    
    def __eq__(self, other):
        if type(other) is type(self):
            return self.__dict__ == other.__dict__
        return False