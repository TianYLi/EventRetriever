"""
TicketParser.py
Written By Jack Li
v2.0

Uses TicketMaster API to obtain information regarding concerts.
"""

import requests  # GET command
import json  # data formatting
from tkinter import *  # used to format GUI
from tkinter.ttk import *
import base64
from requests.auth import HTTPBasicAuth

TM_ROOT_URL = "https://app.ticketmaster.com"  # used for retrieving data
TM_BASE_SEARCH = "/discovery/v2/events.json?"  # probably should be attached to ROOT_URL
TM_API_KEY = "apikey=XZGN3MiGhFumbsF1Z93x3mGAG0M643gM"  # this is the API_Key given by ticketmaster
TM_TEMP_API_KEY = "apikey=XZGN3MiGhFumbsF1Z93x3mGAG0M643gM"  # I used the online API key

SH_ROOT_URL = "https://api.stubhub.com"
SH_BASE_SEARCH = "/login"
APP_TOKEN = "kYXeASSGZGPfM8PZVFNmP8kfuqAa"  # I used the online API key
CONSUMER_KEY = "uD6aCujaEQ4XqLFGAG_gQPZ2lv4a"  # this is the API_Key given by stubhub
CONSUMER_SECRET = "QLNrItUwCrIvfK4OCiiIcQqkKTEa"
USER_PASS = "grant_type=password&username=eliteticketempire@gmail.com&password=12Tickets34"

fields = ['Enter Artist Name']  # fields in GUI

# list of words that will be eliminated from the search
badwords = {"Access", "access", "ACCESS", "Access:", "access:", "ACCESS:",
            "Tribute", "tribute", "TRIBUTE", "Tribute:", "tribute:", "TRIBUTE:",
            "Rental", "rental", "RENTAL", "Rental:", "rental:", "RENTAL:",
            "Rentals", "rentals", "RENTALS", "Rentals:", "rentals:", "RENTALS:",
            "Buffet", "buffet", "BUFFET", "Buffet:", "buffet:", "BUFFET:",
            "Celebration", "celebration", "CELEBRATION", "Celebration:", "celebration:", "CELEBRATION:",
            "Parking", "parking", "PARKING", "Parking:", "parking:", "PARKING:"}

class TicketParserSH:
    def __init__(self):
        self.keyword = None  # user input
        self.outputFile = None  # name of output file
        self.content = None  # raw data content
        self.next = None  # dict information about next page
        self.event_list = None  # parsed list of events

    # creates our output file
    def file_open(self):
        self.outputFile = open('%sSH.txt' %self.keyword, 'w')
        self.outputFile.write('Name;Date;Venue;Link\n')

    # closes our output file
    def file_close(self):
        self.outputFile.close()

    def request(self):
        # Stubhub searching begin
        # basicAuthorizationToken = CONSUMER_KEY + ":" + CONSUMER_SECRET
        # basicAuthorizationToken = base64.b64encode(bytes(basicAuthorizationToken, 'utf-8'))
        req = requests.post(SH_ROOT_URL + SH_BASE_SEARCH, auth=HTTPBasicAuth(CONSUMER_KEY, CONSUMER_SECRET),
                            data=USER_PASS)

        token_response = req.json()
        access_token = token_response['access_token']
        # user_GUID = req.headers['X-StubHub-User-GUID']
        headers = {
            'Content-Type' : 'application/json',
            'Accept': 'application/json',
            'Accept-Encoding': 'gzip,deflate',
            'Accept-Language': 'en-US',
            'Authorization': 'Bearer ' + access_token,
            # 'x-stubhub-user-guid': user_GUID,
        }
        req = requests.request('GET', 'https://api.stubhub.com/search/catalog/events/v3', headers=headers,
                           params={'name': self.keyword, 'rows': 500})
        self.content = req.json()

    # part of the parsing
    def get_event_list(self):
        if self.content.get('events') is None:
            return -1
        self.event_list = self.content['events']
        print(self.event_list)
        return 0


# This parses each individual event
class IndvEventSH(TicketParserSH):
    # initializes all variables used by IndvEvent
    def __init__(self, event, file):
        self.file = file  # name of output file
        self.event = event  # all parsed information regarding event
        self.valid = True  # Checks if we want the event or not
        self.venue = None  # parsed venue name
        self.location = None  # parsed location
        self.dateTimeLocal = None  # parsed event start time
        self.dateTimeUTC = None  # parsed event date
        self.outputDate = None
        self.name = None  # parsed name of event
        self.url = None  # parsed event url

    # parses for the venue
    def get_venue(self):
        event_venue = self.event['venue']
        if event_venue['country'] != "US" and event_venue['country'] != "Canada":
            self.valid = False
            return 0
        self.venue = event_venue['name']
        print(self.venue)
        return 1

    # parses for the event name
    def get_name(self):
        self.name = self.event['name']
        words = self.name.split(" ")
        for word in words:
            for w in badwords:
                if w == word:
                    self.valid = False
                    return False
        desc = self.event['description']
        words = desc.split(" ")
        for w in badwords:
            if w in words:
                self.valid = False
                return False
        print(self.name)
        return True

    # parses for the URL
    def get_url(self):
        url_ext = self.event['webURI']
        self.url = "https://www.stubhub.com/"+url_ext
        print(self.url)

    # parses for Date and Time
    def get_date_time(self):
        if self.event.get('eventDateLocal') is None or self.event.get('eventDateUTC') is None:
            self.valid = False
        else:
            self.dateTimeLocal = self.event['eventDateLocal']
            self.dateTimeLocal = self.dateTimeLocal.replace(' ', '')[:-5].upper()
            self.dateTimeUTC = self.event['eventDateUTC']
            self.dateTimeUTC = self.dateTimeUTC.replace(' ', '')[:-5].upper()
            print(self.dateTimeLocal)
            print(self.dateTimeUTC)
            self.outputDate = self.dateTimeLocal.split('T')[0]
            self.outputTime = self.dateTimeLocal.split('T')[1]
            splitdate = self.outputDate.split('-')
            self.outputDate = splitdate[1]+"/"+splitdate[2]+"/"+splitdate[0]
            print(self.outputDate)
            print(self.outputTime)
    # write to the output file
    def write_txt(self):
        self.file.write(self.name.encode('utf8'))
        self.file.write(';{}  {};'.format(self.outputDate, self.outputTime))
        self.file.write('{};'.format(self.venue))
        self.file.write('{};\n'.format(self.url))


# This is a higher level class that requests data from server
class TicketParserTM:
    # initializes our variables
    def __init__(self):
        self.keyword = None         # user input
        self.outputFile = None      # name of output file
        self.content = None         # raw data content
        self.next = None            # dict information about next page
        self.event_list = None      # parsed list of events

    # creates our output file
    def file_open(self):
        self.outputFile = open('%sTM.txt' %self.keyword, 'w')
        self.outputFile.write('Name;Date;Venue;Link\n')

    # closes our output file
    def file_close(self):
        self.outputFile.close()

    # requests data from website and stores it as json
    def request(self):
        req = requests.request('GET', TM_ROOT_URL + TM_BASE_SEARCH + TM_API_KEY + self.keyword)
        unicode = requests.utils.get_unicode_from_response(req)
        self.content = json.loads(unicode)

    # gets information about the next page of data
    def get_next(self):
        links = self.content['_links']
        self.next = links.get('next')
        return self.next

    # used to move to the next page
    def set_next_keyword(self):
        link_next_href = self.next['href']
        spliced = link_next_href.split("?")
        self.keyword = '&' + spliced[1].split("{")[0]

    # part of the parsing
    def get_event_list(self):
        if self.content.get('_embedded') is None:
            return -1
        _embedded = self.content['_embedded']
        self.event_list = _embedded['events']
        return 0


# This parses each individual event
class IndvEventTM(TicketParserTM):
    # initializes all variables used by IndvEvent
    def __init__(self, event, file):
        self.file = file        # name of output file
        self.event = event      # all parsed information regarding event
        self.valid = True       # Checks if we want the event or not
        self.venue = None       # parsed venue name
        self.location = None    # parsed location
        self.time = None        # parsed event start time
        self.date = None        # parsed event date
        self.name = None        # parsed name of event
        self.url = None         # parsed event url

    # parses for the venue
    def get_venue(self):
        event_embedded = self.event['_embedded']
        event_venues = event_embedded['venues']
        for indv_venue in event_venues:
            if indv_venue.get('name') is None:
                self.valid = False
                continue
            self.venue = indv_venue['name']

    # parses for the event name
    def get_name(self):
        self.name = self.event['name']
        words = self.name.split(" ")
        # checks through list of bad words to determine events we do not want
        for w in badwords:
            if w in words:
                self.valid = False
                return False

    # parses for the URL
    def get_url(self):
        self.url = self.event['url']

    # parses for location
    def get_location(self):
        event_embedded = self.event['_embedded']
        event_venues = event_embedded['venues']
        # we do not want events with no region
        for indv_venue in event_venues:
            if indv_venue.get('timezone') is None:
                # print("{} is invalid".format(indv_venue))
                self.valid = False
                continue
            location_parse = indv_venue.get('timezone').split('/')[0]
            # we only want events in America and Canada
            if location_parse != 'America' and location_parse != 'Canada':
                self.valid = False
                continue
            self.location = location_parse

    # parses for Date and Time
    def get_date_time(self):
        event_dates = self.event['dates']
        event_start_time = event_dates['start']
        # we do not want events with no start time
        if event_start_time.get('localTime') is None:
            self.valid = False
        else:
            event_start_time = event_dates['start']
            self.time = event_start_time['localTime']
            self.date = event_start_time['localDate']
            splitdate = self.date.split('-')
            self.date = splitdate[1] + "/" + splitdate[2] + "/" + splitdate[0]

    # write to the output file
    def write_txt(self):
        self.file.write(self.name.encode('utf8'))
        self.file.write(';{}  {};'.format(self.date, self.time))
        self.file.write('{};'.format(self.venue))
        self.file.write('{};\n'.format(self.url))


# helper function
def write_event_tm(tp, event):
    ie = IndvEventTM(event, tp.outputFile)
    ie.get_venue()
    ie.get_location()
    ie.get_date_time()
    ie.get_name()
    ie.get_url()
    if ie.valid:
        ie.write_txt()


def write_event_sh(tp, event):
    print("\nyayevents")
    print(event)
    ie = IndvEventSH(event, tp.outputFile)
    if ie.get_name():
        ie.get_venue()
        ie.get_url()
        ie.get_date_time()
    if ie.valid:
        ie.write_txt()


# The function that loops through pages and utilizes class TicketParser and IndvEvent
def search(keyword):
    tptm = TicketParserTM()                             # initializes the higher level abstraction
    tpsh = TicketParserSH()
    for entry in keyword:                           # parses based on keyword
        tempkw = entry[1].get()
        break
    tptm.keyword = tempkw
    tptm.file_open()

    tpsh.keyword = tempkw
    tpsh.file_open()
    tpsh.request()
    print(tpsh.content)
    err = tpsh.get_event_list()
    print(tpsh.event_list)
    if err == 0:
        for event in tpsh.event_list:
            write_event_sh(tpsh, event)

    tpsh.file_close()

    # Ticket Master API Search Begin
    tptm.keyword = '&keyword=' + tempkw               # saves keyword and starts calling relevant functions
    tptm.request()
    err = tptm.get_event_list()
    if err == 0:
        # for event in tptm.event_list:                     # find info about each event in event_list
            # write_event(tptm, event)
        while tptm.get_next() is not None:                # go to next page
            tptm.set_next_keyword()
            tptm.request()
            tptm.get_event_list()
            for event in tptm.event_list:                     # find info about each event in event_list
                write_event_tm(tptm, event)
    tptm.file_close()
    print("...Data Parsing Completed\n")


# Creates the GUI form
def makeform(root):
    entries = []
    for field in fields:
        row = Frame(root)
        lab = Label(row, width=22, text=field + ": ", anchor='w')
        ent = Entry(row)
        row.pack(side=TOP, fill=X, padx=5, pady=5)
        lab.pack(side=LEFT)
        ent.pack(side=RIGHT, expand=YES, fill=X, pady=5, padx=5)
        entries.append((field, ent))
    return entries


# obtains user input
def fetch(entries):
    for entry in entries:
        field = entry[0]
        text = entry[1].get()
        print('%s: "%s"' % (field, text))

# main function initializes GUI
if __name__ == '__main__':
    gui = Tk()
    gui.title('Event Retriever')
    ents = makeform(gui)
    gui.bind('<Return>', (lambda event, e=ents: search(e)))
    b1 = Button(gui, text='Search', command=(lambda e=ents: search(e)))
    b1.pack(side=LEFT, padx=20, pady=5)
    b2 = Button(gui, text='Quit', command=gui.quit)
    b2.pack(side=RIGHT, padx=20, pady=5)
    mainloop()
