"""
Written By Jack Li
v1.0

Uses TicketMaster API to obtain information regarding concerts
"""


# links
import requests  # GET command
import json  # data formatting
from tkinter import *  # used to format GUI

ROOT_URL = "https://app.ticketmaster.com"  # used for retrieving data
BASE_SEARCH = "/discovery/v2/events.json?"  # probably should be attached to ROOT_URL
API_KEY = "apikey=XZGN3MiGhFumbsF1Z93x3mGAG0M643gM"  # this is the API_Key given by ticketmaster
TEMP_API_KEY = "apikey=XZGN3MiGhFumbsF1Z93x3mGAG0M643gM"  # I used the online API key

fields = 'Keyword', 'Setting'  # fields in GUI


# This is a higher level class that requests data from server
class TicketParser:
    # initializes our variables
    def __init__(self):
        self.keyword = None
        self.outputFile = None
        self.content = None
        self.next = None
        self.event_list = None

    # requests user input
    def input(self):
        raw = input('Enter keyword(s): ')
        self.keyword = '&keyword=' + raw

    # creates our output file
    def file_open(self):
        print('{}'.format(self.keyword))
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
        _embedded = self.content['_embedded']
        self.event_list = _embedded['events']


# This parses each individual event
class IndvEvent(TicketParser):
    # initializes all variables used by IndvEvent
    def __init__(self, event, file):
        self.file = file
        self.event = event
        self.valid = True
        self.venue = None
        self.location = None
        self.time = None
        self.date = None
        self.name = None
        self.url = None

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
        for word in words:
            if word == "Tribute" or word == "tribute" or word == "TRIBUTE":
                self.valid = False
            if word == "Access" or word == "access":
                self.valid = False

    # parses for the URL
    def get_url(self):
        self.url = self.event['url']
        # self.url = "#{}#outlauto#".format(self.event['url'])

    # parses for location
    def get_location(self):
        event_embedded = self.event['_embedded']
        event_venues = event_embedded['venues']
        for indv_venue in event_venues:
            if indv_venue.get('timezone') is None:
                self.valid = False
                continue
            location_parse = indv_venue.get('timezone').split('/')[0]
            if location_parse != 'America' and location_parse != 'Canada':
                self.valid = False
                continue
            self.location = location_parse

    # parses for Date and Time
    def get_date_time(self):
        """Maybe use DateTBA and DateTBD"""
        event_dates = self.event['dates']
        event_start_time = event_dates['start']
        if event_start_time.get('localTime') is None:
            self.valid = False
            print()
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


# recursively prints out everything in the json file
# not quite working (used for testing)
def recursion_print(rec, f, rank):
    f.write("\n")
    f.write(" " * rank * 2)
    if type(rec) is list:
        for x in rec:
            print("{}: ".format(x))
            f.write("{}: ".format(x))
            if type(x) is dict:
                for y in x:
                    f.write("{}: ".format(y))
                    # print("{}: ".format(y))
                    recursion_print(x[y], f, rank + 1)
            else:
                f.write("{}: ".format(rec[x]))
                recursion_print(rec[x], f, rank + 1)

    if type(rec) is dict:
        for z in rec:
            f.write("{}: ".format(z))
            # print("{}: ".format(z))
            recursion_print(rec[z], f, rank + 1)
        f.write("{} ".format(rec))
        f.write("\n")
        # print(rec)


# The function that loops through pages and utilizes class TicketParser and IndvEvent
def search(keyword):
    tp = TicketParser()
    for entry in keyword:
        tempkw = entry[1].get()
        break
    tp.keyword = tempkw
    tp.file_open()
    tp.keyword = '&keyword=' + tempkw
    tp.request()
    tp.get_event_list()
    for event in tp.event_list:
        ie = IndvEvent(event, tp.outputFile)
        ie.get_venue()
        ie.get_location()
        ie.get_date_time()
        ie.get_name()
        ie.get_url()
        if ie.valid:
            ie.write_txt()

    while tp.get_next() is not None:
        f = open('raw.txt', 'w')
        # recursionPrint(tp.content, f, 0)
        tp.set_next_keyword()
        tp.request()
        tp.get_event_list()
        for event in tp.event_list:
            ie = IndvEvent(event, tp.outputFile)
            ie.get_venue()
            ie.get_location()
            ie.get_date_time()
            ie.get_name()
            ie.get_url()
            if ie.valid:
                ie.write_txt()
    tp.file_close()


# Creates the GUI form
def makeform(root, fields):
    entries = []
    for field in fields:
        row = Frame(root)
        lab = Label(row, width=22, text=field + ": ", anchor='w')
        ent = Entry(row)
        ent.insert(0, "0")
        row.pack(side=TOP, fill=X, padx=5, pady=5)
        lab.pack(side=LEFT)
        ent.pack(side=RIGHT, expand=YES, fill=X)
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
    ents = makeform(gui, fields)
    gui.bind('<Return>', (lambda event, e=ents: search(e)))
    b1 = Button(gui, text='Search', command=(lambda e=ents: search(e)))
    b1.pack(side=LEFT, padx=5, pady=5)
    b2 = Button(gui, text='Quit', command=gui.quit)
    b2.pack(side=LEFT, padx=5, pady=5)
    mainloop()
