"""
TicketParser.py
Written By Jack Li
v2.0

Uses TicketMaster API to obtain information regarding concerts.
"""

import os
import time
import requests  # GET command
import json  # data formatting
from tkinter import *  # used to format GUI
from tkinter.ttk import *
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException

ROOT_URL = "https://app.ticketmaster.com"  # used for retrieving data
BASE_SEARCH = "/discovery/v2/events.json?"  # probably should be attached to ROOT_URL
API_KEY = "apikey=XZGN3MiGhFumbsF1Z93x3mGAG0M643gM"  # this is the API_Key given by ticketmaster
API_SECRET = "Q85YZTNyBffCPOX7"
TEMP_API_KEY = "apikey=XZGN3MiGhFumbsF1Z93x3mGAG0M643gM"  # I used the online API key

fields = ['Enter Artist Name', 'Enter Screenshot Delay']  # fields in GUI

# list of words that will be eliminated from the search
badwords = ["Access", "access", "ACCESS", "Access:", "access:", "ACCESS:",
            "Tribute", "tribute", "TRIBUTE", "Tribute:", "tribute:", "TRIBUTE:",
            "Rental", "rental", "RENTAL", "Rental:", "rental:", "RENTAL:",
            "Rentals", "rentals", "RENTALS", "Rentals:", "rentals:", "RENTALS:",
            "Buffet", "buffet", "BUFFET", "Buffet:", "buffet:", "BUFFET:",
            "Celebration", "celebration", "CELEBRATION", "Celebration:", "celebration:", "CELEBRATION:"]


# This is a higher level class that requests data from server
class TicketParser:
    # initializes our variables
    def __init__(self):
        self.keyword = None  # user input
        self.outputFile = None  # name of output file
        self.content = None  # raw data content
        self.next = None  # dict information about next page
        self.event_list = None  # parsed list of events

    # requests user input
    def input(self):
        raw = input('Enter keyword(s): ')
        self.keyword = '&keyword=' + raw

    # creates our output file
    def file_open(self):
        self.outputFile = open('%s.txt' % self.keyword, 'w')
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
        self.file = file  # name of output file
        self.event = event  # all parsed information regarding event
        self.valid = True  # Checks if we want the event or not
        self.venue = None  # parsed venue name
        self.location = None  # parsed location
        self.time = None  # parsed event start time
        self.date = None  # parsed event date
        self.name = None  # parsed name of event
        self.url = None  # parsed event url
        self.input = None # user inputted name
        self.livenation = 0

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
                    self.valid = False

    # parses for the URL
    def get_url(self):
        url = self.event['url']
        if url[:11] == 'http://www.':
            self.url = 'http://'+url[11:]
        elif url[:12] == 'http://www1.':
            self.url = 'http://'+url[13:]
        else:
            self.url = url

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
        self.file.write(str(self.name.encode('utf8'))[2:-1])
        self.file.write(';{}  {};'.format(self.date, self.time))
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
    ie.input = tp.keyword
    if ie.valid:
        ie.write_txt()


# The function that loops through pages and utilizes class TicketParser and IndvEvent
def search(keyword):
    tp = TicketParser()  # initializes the higher level abstraction
    for entry in keyword:  # parses based on keyword
        tempkw = entry[1].get()
        break
    tp.keyword = tempkw
    tp.file_open()
    tp.keyword = '&keyword=' + tempkw  # saves keyword and starts calling relevant functions
    tp.request()
    err = tp.get_event_list()
    if err == 0:
        for event in tp.event_list:  # find info about each event in event_list
            write_event(tp, event)
        while tp.get_next() is not None:  # go to next page
            tp.set_next_keyword()
            tp.request()
            tp.get_event_list()
            for event in tp.event_list:  # find info about each event in event_list
                write_event(tp, event)
    tp.file_close()
    print("...Data Parsing Completed\n")


def check_url(url):
    with open('timerstatus.txt') as file:
        valid = True
        txt = file.readlines()
        for line in txt:
            if url == line:
                valid = False
        # print(("{} is {}\n").format(url, valid))
        return valid


def sel_urlfix(tp, event, ssdelay):
    ie = IndvEvent(event, tp.outputFile)
    ie.get_name()
    ie.get_url()
    ie.get_venue()
    ie.get_location()
    # print("Before: {}\n".format(ie.url))
    if ie.url[:11] == 'http://www.':
        ie.url = ie.url[:7]+ie.url[11:]
    elif ie.url[:16] == 'http://concerts.':
        ie.url = ie.url[:7]+ie.url[16:]
    # print("After: {}\n".format(ie.url))
    if "ticketmaster" in ie.url:
        ie.url = ie.url[:7] + 'www1.' + ie.url[7:]
    elif "livenation" in ie.url:
        ie.livenation = 1
        ie.url = ie.url[:7]+'concerts1.'+ie.url[7:]
    else:
        ie.valid = 0
    sel_run(ie, ssdelay)


def sel_run(ie, ssdelay):
    if check_url(ie.url+'\n') and ie.valid:
        ie.driver = webdriver.Chrome()
        ie.driver.implicitly_wait(30)

        ie.driver.set_window_size(1920, 1080)
        ie.driver.get(ie.url)

        try:
            ie.driver.find_element_by_css_selector("button.modal-dialog__button.landing-modal-footer__skip-button").click()
        except NoSuchElementException:
            with open('timerstatus.txt', 'a') as fille:
                fille.write('{}\n'.format(ie.url))
            print("no skip")
            #ie.driver.quit()
        if ie.livenation:
            try:
                element = ie.driver.find_element_by_xpath('//*[@id="IPEinvL122103"]/map/area[3]').click()
            except NoSuchElementException:
                print("no popup")

        try:
            element = ie.driver.find_element_by_id("ism-qp-toggle")
            if element.is_displayed():
                element.click()
        except NoSuchElementException as e:
            print("no toggle\n")

        try:
            element = ie.driver.find_element_by_css_selector("button.zoomer__control--zoomin")
            element.click()
            time.sleep(float(ssdelay))
            print("ss\n")

            root_path = "./screenshots/"
            try:
                os.makedirs(os.path.join(root_path, ie.file.strip('\n')))
                # print('made dirs ss')
            except OSError:
                # print('os dir err')
                pass
            """
            try:
                print(root_path+' -> '+ie.file.strip('\n')+' -> '+ie.venue)
                os.makedirs(os.path.join(root_path, ie.file.strip('\n'), ie.venue))
                print('made dirs event')
            except OSError:
                print('event dir err')
                pass
            """
            ie.driver.save_screenshot(root_path + ie.file.strip('\n') + "/" + ie.venue+" -- "+time.strftime("%m-%d-%y") + ".jpg")
            # print('saved ss date')

            ie.driver.quit()
        except NoSuchElementException as e:
            with open('timerstatus.txt', 'a') as fille:
                fille.write('{}\n'.format(ie.url))
            print("no zoom button\n")
            ie.driver.quit()


def selenium_helper(keyword, type, ssdelay):
    start = time.time()
    tp = TicketParser()  # initializes the higher level abstraction
    tp.keyword = '&keyword='+keyword
    tp.outputFile = keyword
    tp.request()
    err = tp.get_event_list()
    if err == 0:
        for event in tp.event_list:  # find info about each event in event_list
            sel_urlfix(tp, event, ssdelay)
        while tp.get_next() is not None:  # go to next page
            tp.set_next_keyword()
            tp.request()
            tp.get_event_list()
            for event in tp.event_list:  # find info about each event in event_list
                sel_urlfix(tp, event, ssdelay)
        #with open('timerstatus.txt', 'a') as fille:
        #    fille.write('{}: {}\n'.format(keyword,time.time() - start))
        print("...All Screenshots Taken\n")


def selenium_start(ent, option):
    for entry in ent:  # parses based on keyword
        if entry[0] == 'Enter Artist Name':
            keyword = entry[1].get()
        elif entry[0] == 'Enter Screenshot Delay':
            ssdelay = entry[1].get()
    if ssdelay == '':
        ssdelay = 4

    l = []
    if option == 1:
        # print("going through list...")
        f = open('listName.txt', 'r')
        for line in f:
            # print(line)
            l.append(line)
        f.close()
        for li in l:
            time.sleep(2)
            # print('1')
            selenium_helper(li, 1, ssdelay)
    else:
        time.sleep(2)
        selenium_helper(keyword, 0, ssdelay)


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
    b1.pack(side=LEFT, padx=10, pady=5)
    b1 = Button(gui, text='Screenshot', command=(lambda e=ents: selenium_start(e, 0)))
    b1.pack(side=LEFT, padx=10, pady=5)
    b1 = Button(gui, text='ListSS', command=(lambda e=ents: selenium_start(e, 1)))
    b1.pack(side=LEFT, padx=10, pady=5)
    b2 = Button(gui, text='Quit', command=gui.quit)
    b2.pack(side=RIGHT, padx=10, pady=5)
    mainloop()
