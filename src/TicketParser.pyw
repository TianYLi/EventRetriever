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

ROOT_URL = "https://app.ticketmaster.com"  # used for retrieving data
BASE_SEARCH = "/discovery/v2/events.json?"  # probably should be attached to ROOT_URL
API_KEY = "apikey=XZGN3MiGhFumbsF1Z93x3mGAG0M643gM"  # this is the API_Key given by ticketmaster
TEMP_API_KEY = "apikey=XZGN3MiGhFumbsF1Z93x3mGAG0M643gM"  # I used the online API key

fields = ['Enter Artist Name']  # fields in GUI

# list of words that will be eliminated from the search
badwords = {"Tribute", "tribute", "TRIBUTE",
            "Access", "access", "ACCESS",
            "Rental", "rental", "RENTAL",
            "Rentals", "rentals", "RENTALS",
            "Buffet", "buffet", "BUFFET",
            "Celebration", "celebration", "CELEBRATION"}


# This is a higher level class that requests data from server
class TicketParser:
    # initializes our variables
    def __init__(self):
        self.keyword = None         # user input
        self.outputFile = None      # name of output file
        self.content = None         # raw data content
        self.next = None            # dict information about next page
        self.event_list = None      # parsed list of events

    # requests user input
    def input(self):
        raw = input('Enter keyword(s): ')
        self.keyword = '&keyword=' + raw

    # creates our output file
    def file_open(self):
        self.outputFile = open('%s.txt' %self.keyword, 'w')
        self.outputFile.write('Name;Date;Venue;Link\n')

    # closes our output file
    def file_close(self):
        self.outputFile.close()

    # requests data from website and stores it as json
    def request(self):
        req = requests.request('GET', ROOT_URL + BASE_SEARCH + API_KEY + self.keyword)
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
        # print(link_next_href)
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
class IndvEvent(TicketParser):
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
        for word in words:
            for w in badwords:
                if w == word:
                    print("{} is invalid".format(words))
                    self.valid = False
                    break

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
                print("{} is invalid".format(indv_venue))
                self.valid = False
                continue
            location_parse = indv_venue.get('timezone').split('/')[0]
            # we only want events in America and Canada
            if location_parse != 'America' and location_parse != 'Canada':
                print("{} is invalid".format(location_parse))
                self.valid = False
                continue
            self.location = location_parse

    # parses for Date and Time
    def get_date_time(self):
        event_dates = self.event['dates']
        event_start_time = event_dates['start']
        # we do not want events with no start time
        if event_start_time.get('localTime') is None:
            print("{} is invalid".format(event_start_time))
            self.valid = False
        else:
            event_start_time = event_dates['start']
            self.time = event_start_time['localTime']
            self.date = event_start_time['localDate']
            splitdate = self.date.split('-')
            self.date = splitdate[1] + "/" + splitdate[2] + "/" + splitdate[0]

    # write to the output file
    def write_txt(self):
        self.file.write('{};'.format(self.name))
        self.file.write('{}  {};'.format(self.date, self.time))
        self.file.write('{};'.format(self.venue))
        self.file.write('{};\n'.format(self.url))


# helper function
def write_event(tp, event):
    ie = IndvEvent(event, tp.outputFile)
    ie.get_venue()
    ie.get_location()
    ie.get_date_time()
    ie.get_name()
    ie.get_url()
    if ie.valid:
        ie.write_txt()
    else:
        print("invalid")

# The function that loops through pages and utilizes class TicketParser and IndvEvent
def search(keyword):
    tp = TicketParser()                             # initializes the higher level abstraction
    for entry in keyword:                           # parses based on keyword
        tempkw = entry[1].get()
        break
    tp.keyword = tempkw
    tp.file_open()

    tp.keyword = '&keyword=' + tempkw               # saves keyword and starts calling relevant functions
    tp.request()
    err = tp.get_event_list()
    if err == 0:
        for event in tp.event_list:                     # find info about each event in event_list
            write_event(tp, event)
        while tp.get_next() is not None:                # go to next page
            tp.set_next_keyword()
            tp.request()
            for event in tp.event_list:                     # find info about each event in event_list
                write_event(tp, event)
    tp.file_close()
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
