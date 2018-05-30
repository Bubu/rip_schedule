#!//usr/bin/env python3
from lxml import html, etree
import requests
import datetime
from xml.etree.ElementTree import Element, SubElement, tostring

baseurl = 'http://www.rock-am-ring.com'
page = requests.get(baseurl + '/spielplan')
tree = html.fromstring(page.content)


acts = tree.xpath('//div[@class="StageTime"]')

stages = {'164':'Volcano Stage', '165':"Beck's Crater Stage", '166':"Alternastage"}
DAYS = {1 : '2018-06-01', 2 : '2018-06-02', 3 : '2018-06-03'}


schedule_node = Element('schedule')
version_node = SubElement(schedule_node, 'version')
version_node.text = '1'

conference_node = SubElement(schedule_node, 'conference')
acronym_node = SubElement(conference_node, 'acronym')
acronym_node.text = 'RaR 2018'
title_node = SubElement(conference_node, 'title')
title_node.text = 'Rock am Ring 2018'
start_node = SubElement(conference_node, 'start')
start_node.text = '2018-06-01'
end_node = SubElement(conference_node, 'end')
end_node.text = '2018-06-03'
days_node = SubElement(conference_node, 'days')
days_node.text = '3'
day_change_node = SubElement(conference_node, 'day_change')
day_change_node.text = '09:00:00'

day1_node = SubElement(schedule_node, 'day')
day1_node.set('date', '2018-06-01')
day1_node.set('index', '1')

day2_node = SubElement(schedule_node, 'day')
day2_node.set('date', '2018-06-02')
day2_node.set('index', '2')

day3_node = SubElement(schedule_node, 'day')
day3_node.set('date', '2018-06-03')
day3_node.set('index', '3')

id = 0
for session in acts:
    date = datetime.datetime.fromtimestamp(int(session.get('data-start-time')[:-3]))
    if date.hour < 9:
        print("\tshifting to previous day")
        print("before: " + str(date))
        date = date - datetime.timedelta(days=1)

    if date.strftime("%Y-%m-%d") == DAYS[1]:
        day = day1_node
    elif date.strftime("%Y-%m-%d") == DAYS[2]:
        day = day2_node
    elif date.strftime("%Y-%m-%d") == DAYS[3]:
        day = day3_node
    else:
        print(date)
        raise ValueError

    roomquery = 'room[@name="' + stages[session.get('data-stage')] + '"]'
    room = day.find(roomquery)
    if not room:
        room_node = SubElement(day, 'room')
        room_node.set('name', stages[session.get('data-stage')])
    else:
        room_node = room
    event_node = SubElement(room_node, 'event')
    event_node.set('guid', str(id))
    event_node.set('id', str(id))

    date_node = SubElement(event_node, 'date')
    date_node.text = datetime.datetime.fromtimestamp(int(session.get('data-start-time')[:-3])).strftime("%Y-%m-%d")
    start_node = SubElement(event_node, 'start')
    start_node.text = datetime.datetime.fromtimestamp(int(session.get('data-start-time')[:-3])).strftime("%H:%M")

    duration_node = SubElement(event_node, 'duration')
    duration_node.text = str(datetime.timedelta(seconds=int(session.get('data-duration')[:-2])))

    etitle_node = SubElement(event_node, 'title')
    etitle_node.text = ''.join(session.get('data-name').split(',')[:-2])

    detailsurl = baseurl + session.xpath('a[@class="StageTime-link"]')[0].get('href')
    print("Parsing " + detailsurl + ' ...')
    detailspage = requests.get(detailsurl)
    detailstree = html.fromstring(detailspage.content)
    try:
        description_element = detailstree.xpath('//div[@class="CollapsedText collapsed"]|//div[@class="CollapsedText"]')[0]
        description_element = html.fromstring(etree.tostring(description_element).replace(b'<br/> <br/>', b'\n\n'))
        description = '\n\n'.join([p.text_content() for p in description_element.getchildren()])
    except IndexError:
        description = ''
        print("\tFound no description")
    description_node = SubElement(event_node, 'description')
    description_node.text = description

    try:
        url = detailstree.xpath('//a[@class="VideoThumb"]')[0].get('href')
        url = url.replace('embed/', 'watch?v=')
        url = "https:" + url
        url = url[:-11]
        if url == 'https://www.youtube.com/watch?v=':
            raise AttributeError
    except (IndexError, AttributeError):
        url = ''
        print("\tFound no video URL")

    links_node = SubElement(event_node, 'links')
    if url != '':
        link_node = SubElement(links_node, 'link')
        link_node.set('href', url)
        link_node.text = "Youtube"

    eroom_node = SubElement(event_node, 'room')
    eroom_node.text = stages[session.get('data-stage')]

    id += 1

xml_as_string = tostring(schedule_node, encoding="unicode")

with open("rar_2018.xml",'w') as f:
    f.write(xml_as_string)
