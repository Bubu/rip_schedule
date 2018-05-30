#!//usr/bin/env python3
from lxml import html, etree
import requests
import datetime
from xml.etree.ElementTree import Element, SubElement, tostring

baseurl = 'http://www.rock-im-park.com'
page = requests.get(baseurl + '/spielplan')
tree = html.fromstring(page.content)


acts = tree.xpath('//div[@class="StageTime"]')

stages = {'167':'Zeppelin Stage', '168':"Beck's Park Stage", '169':"Alternarena"}


i_calendar_node = Element('iCalendar')
i_calendar_node.set('xmlns:xCal', 'urn:ietf:params:xml:ns:xcal')
v_calendar_node = SubElement(i_calendar_node, 'vcalendar')
version_node = SubElement(v_calendar_node, 'version')
version_node.text = '2.0'

prod_id_node = SubElement(v_calendar_node, 'prodid')
prod_id_node.text = '-//rip//open-event//EN'

cal_desc_node = SubElement(v_calendar_node, 'x-wr-caldesc')
cal_desc_node.text = "Rock im Park 2018"

cal_name_node = SubElement(v_calendar_node, 'x-wr-calname')
cal_name_node.text = "Spielplan"

id = 0
for session in acts:
    v_event_node = SubElement(v_calendar_node, 'vevent')

    uid_node = SubElement(v_event_node, 'uid')
    uid_node.text = str(id)

    dtstart_node = SubElement(v_event_node, 'dtstart')
    dtstart_node.text = datetime.datetime.fromtimestamp(int(session.get('data-start-time')[:-3])).strftime("%Y%m%dT%H%M%S")

    dtend_node = SubElement(v_event_node, 'dtend')
    dtend_node.text = datetime.datetime.fromtimestamp(int(session.get('data-end-time')[:-3])).strftime("%Y%m%dT%H%M%S")

    duration_node = SubElement(v_event_node, 'duration')
    duration_node.text = str(datetime.timedelta(seconds=int(session.get('data-duration')[:-2])))

    summary_node = SubElement(v_event_node, 'summary')
    summary_node.text = ''.join(session.get('data-name').split(',')[:-2])

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
    description_node = SubElement(v_event_node, 'description')
    description_node.text = description

    class_node = SubElement(v_event_node, 'class')
    class_node.text = 'PUBLIC'

    status_node = SubElement(v_event_node, 'status')
    status_node.text = 'CONFIRMED'

    try:
        url = detailstree.xpath('//a[@class="VideoThumb"]')[0].get('href')
        url = url.replace('embed/', 'watch?v=')
        url = "https:" + url
        url = url[:-11]
        if url == 'https://www.youtube.com/watch?v=':
            raise AttributeError
    except (IndexError, AttributeError):
        url = ''
        print("\t Found no video URL")
    url_node = SubElement(v_event_node, 'url')
    url_node.text = url

    location_node = SubElement(v_event_node, 'location')
    location_node.text = stages[session.get('data-stage')]

    id += 1

xml_as_string = tostring(i_calendar_node, encoding="unicode")

with open("rip_2018.xml",'w') as f:
    f.write(xml_as_string)
