#!/usr/bin/env python

# 2019-08-28 Peter.Kutschera@ait.ac.at: Initial version

import os
import sys
import datetime
import iso8601
from dateutil import tz
import requests
import json
import re
from dotenv import load_dotenv
import argparse
import html

verbose = 0

venturesPath = "ventures"
# New: should got there but does not work
# venturesPath = "topics/13182/ventures"

def readFromPos(url, offset=0):
    """Get the next bunch of PoS solutions"""
    headers = {'content-type': 'application/json', 'accept': 'application/json'}
    fullUrl = "{0}/en/group_export?_format=json&type=solution&may_reproduce=1&offset={1}".format (url, offset)
    if verbose:
        print ("< PoS: GET ", fullUrl, file=sys.stderr)
    response = requests.get (fullUrl, headers=headers)  # verify=False
    if response.status_code != 200:
        raise Exception ("Error getting PoS data: {0}".format (response.text))
    jsonData = response.json() if callable (response.json) else response.json
    return jsonData


def posGenerator (url):
    """Delivers PoS solutions"""
    offset = 0
    data = readFromPos (posUrl)
    while len (data) > 0:
        if verbose > 2:
            print (data, file=sys.stderr)
        for d in data:
            # Correct encoded special chars, e.g. 
            # 'AIR&#039;s Life and Health Models'
            d["title"] = html.unescape (d["title"])
            yield (d)
        offset += len (data)
        data = readFromPos (posUrl, offset)


def getAuthToken (url, email, password, uid, secret):
    """Get oauth token from cmine"""
    headers = {'content-type': 'application/json', 'accept': 'application/json'}
    data = {
        'grant_type': 'password',
        'scope': 'admin',
        'admin_email': email,
        'password': password,
        'client_id': uid,
        'client_secret': secret
    }
    fullUrl = "{}/oauth/token".format (url)
    if verbose:
        print ("> CMINE: POST ", fullUrl, "data = ", data, file=sys.stderr)
    response = requests.post (fullUrl, headers=headers, data=json.dumps (data))  # verify=False
    if response.status_code != 200:
        # print ("Response: ", response, file=sys.stderr)
        print ("Response headers: ", response.headers, file=sys.stderr)
        print ("Response text: ", response.text, file=sys.stderr)
        raise Exception ("Error getting oauth token from CMINE: {0}".format (response.text))
    jsonData = response.json() if callable (response.json) else response.json
    if verbose > 2:
        print ("Response data: ", json.dumps (jsonData, indent=2), file=sys.stderr)
    return jsonData['access_token']


def getMyUserId (url, token):
    """Get own user id from cmine"""
    headers = {
        'content-type': 'application/json',
        'accept': 'application/json',
        'Authorization': 'Bearer {}'.format (token)
        }
    fullUrl = "{}/api/admin/v1/me".format (url)
    if verbose:
        print ("< CMINE: GET ", fullUrl, "headers = ", headers, file=sys.stderr)
    response = requests.get (fullUrl, headers=headers)  # verify=False
    if response.status_code != 200:
        # print ("Response: ", response, file=sys.stderr)
        print ("Response headers: ", response.headers, file=sys.stderr)
        print ("Response text: ", response.text, file=sys.stderr)
        raise Exception ("Error getting 'me' from CMINE: {0}".format (response.text))
    jsonData = response.json() if callable (response.json) else response.json
    if verbose > 1:
        print ("Response data: ", json.dumps (jsonData, indent=2), file=sys.stderr)
    return jsonData["admin"]["id"]


def getUserId (url, token, user_email):
    """Get user id for given user from cmine"""
    headers = {
        'content-type': 'application/json',
        'accept': 'application/json',
        'Authorization': 'Bearer {}'.format (token)
        }
    fullUrl = "{}/api/admin/v1/users".format (url)
    if verbose:
        print ("< CMINE: GET ", fullUrl, "headers = ", headers, file=sys.stderr)
    response = requests.get (fullUrl, headers=headers)  # verify=False
    if response.status_code != 200:
        # print ("Response: ", response, file=sys.stderr)
        print ("Response headers: ", response.headers, file=sys.stderr)
        print ("Response text: ", response.text, file=sys.stderr)
        raise Exception ("Error gettung users from CMINE: {0}".format (response.text))
    jsonData = response.json() if callable (response.json) else response.json
    if verbose > 1:
        print ("Response data: ", json.dumps (jsonData, indent=2), file=sys.stderr)
    ids = [u["id"] for u in jsonData["users"] if u["email"] == user_email]
    if len (ids) == 0:
        raise Exception ("Error gettung userId for {} from CMINE: not found".format (user_email))
    return ids[0]


def getCustomAttributes (url, token, pattern=None):
    """Search for configured attributes in cmine"""
    headers = {
        'content-type': 'application/json',
        'accept': 'application/json',
        'Authorization': 'Bearer {}'.format (token)
        }
    fullUrl = "{}/api/admin/v1/settings/customizable_attributes".format (url)
    if verbose:
        print ("< CMINE: GET ", fullUrl, "headers = ", headers, file=sys.stderr)
    response = requests.get (fullUrl, headers=headers)  # verify=False
    if response.status_code != 200:
        # print ("Response: ", response, file=sys.stderr)
        print ("Response headers: ", response.headers, file=sys.stderr)
        print ("Response text: ", response.text, file=sys.stderr)
        raise Exception ("Error getting 'pages_customizable' from CMINE: {0}".format (response.text))
    jsonData = response.json() if callable (response.json) else response.json
    if verbose > 1:
        print ("Response data: ", json.dumps (jsonData, indent=2), file=sys.stderr)
    return [a["name"] for a in jsonData["customizable_attributes"] if (pattern is None) or re.search (pattern, a["display_name"], re.IGNORECASE)]


def getVentures (url, token, user_id=None):
    """list ventures on CMINE"""
    result = {}
    headers = {
        'content-type': 'application/json',
        'accept': 'application/json',
        'Authorization': 'Bearer {}'.format (token)
        }
    fullUrl = "{}/api/admin/v2/{}".format (url, venturesPath)
    # This does NOT work
    # if user_id:
    #     fullUrl = "{}?user_id={}".format (fullUrl, user_id)
    while fullUrl is not None:
        if verbose:
            print ("< CMINE: GET ", fullUrl, "headers = ", headers, file=sys.stderr)
        response = requests.get (fullUrl, headers=headers)  # verify=False
        if response.status_code != 200:
            # print ("Response: ", response, file=sys.stderr)
            print ("Response headers: ", response.headers, file=sys.stderr)
            print ("Response text: ", response.text, file=sys.stderr)
            raise Exception ("Error getting ventures from CMINE: {0}".format (response.text))
        jsonData = response.json() if callable (response.json) else response.json
        if verbose > 1:
            print ("Response headers: ", response.headers, file=sys.stderr)
            print ("Response data: ", json.dumps (jsonData, indent=2), file=sys.stderr)
        # this was really nice but can not detect duplicate names
        # result.update ({v["high_level_pitch"]: {"id": v["id"], "still_exists": False, "updated_at": v["updated_at"]} for v in jsonData["ventures"] if user_id is None or user_id == v["user_id"]})
        # so use this instead:
        for v in jsonData["ventures"]:
            if user_id is None or user_id == v["user_id"]:
                # this are my ventures
                if v["high_level_pitch"] in result:
                    print ("Delete duplicate venture:", v["high_level_pitch"], file=sys.stderr)
                    deleteVenture (url, token, v["id"])
                else:
                    result[v["high_level_pitch"]] = {"id": v["id"], "still_exists": False, "updated_at": v["updated_at"]}

        fullUrl = None
        if 'Link' in response.headers:
            # print ("Link: ", response.headers["Link"], file=sys.stderr)
            for link in response.headers["Link"].split (", "):
                if link.endswith('rel="next"'):
                    fullUrl = re.sub ("^<|>.*$", "", link)
    return result


def deleteVenture (url, token, venture_id):
    """Delete one venture on CMINE"""
    headers = {
        'content-type': 'application/json',
        'accept': 'application/json',
        'Authorization': 'Bearer {}'.format (token)
        }
    fullUrl = "{}/api/admin/v2/{}/{}".format (url, venturesPath, venture_id)
    if verbose:
        print ("> CMINE: DELETE ", fullUrl, "headers = ", headers, file=sys.stderr)
    response = requests.delete (fullUrl, headers=headers)  # verify=False
    if response.status_code != 204:
        # print ("Response: ", response, file=sys.stderr)
        print ("Response headers: ", response.headers, file=sys.stderr)
        print ("Response text: ", response.text, file=sys.stderr)
        raise Exception ("Error deleting ventures with id {2} from CMINE: {0} {1}".format (response.status_code, response.text, venture_id))


def writeToCmine (url, token, user_id, venture_id, trl_attr_name, p, posUrl):
    """Write one Solution to CMINE"""
    global lastUpdated
    if verbose > 1:
        print ("*" * 50, file=sys.stderr)
    print ("Processing {}".format (p["title"]), file=sys.stderr)
    if verbose > 1:
        print ("PoS: ", json.dumps (p, indent=2), file=sys.stderr)
    #   Map and send
    #     {
    #   "venture[company_name]": "Hello, world!",
    #   "venture[business_stage]": "Hello, world!",
    #   "venture[high_level_pitch]": "Hello, world!",
    #   "venture[product]": "Hello, world!",
    #   "venture[user_id]": 1,
    #   "venture[customizable_attributes]": [],
    #   "venture[company_size]": "Hello, world!",
    #   "venture[industry_ids]": [
    #     1
    #   ],
    #   "venture[logo]": "Hello, world!",
    #   "venture[cover_picture]": "Hello, world!",
    #   "venture[company_website]": "Hello, world!",
    #   "venture[twitter]": "Hello, world!",
    #   "venture[facebook]": "Hello, world!",
    #   "venture[angel_list]": "Hello, world!",
    #   "venture[currently_fundraising]": true,
    #   "venture[feedable_at]": "Hello, world!",
    #   "venture[fundraising_at]": "Hello, world!",
    #   "venture[fundraising_amount]": 1,
    #   "venture[help]": "Hello, world!",
    #   "venture[non_profit]": true,
    #   "venture[video_html]": "Hello, world!",
    #   "venture[created_date]": "Hello, world!",
    #   "venture[fundraising_currency]": "Hello, world!",
    #   "venture[linkedin]": "Hello, world!",
    #   "venture[tagline]": "Hello, world!",
    #   "venture[locations][address]": [],
    #   "venture[locations][city]": [],
    #   "venture[locations][country_code]": [],
    #   "venture[funding_rounds][amount]": [
    #     1
    #   ],
    #   "venture[funding_rounds][currency]": [],
    #   "venture[funding_rounds][funding_type]": [],
    #   "venture[funding_rounds][closed_date]": [],
    #   "venture[funding_rounds][press_url]": [],
    #   "venture[funding_rounds][investors][name]": [],
    #   "venture[funding_rounds][investors][url]": [],
    #   "venture[team_members][user_id]": [
    #     1
    #   ],
    #   "venture[team_members][role]": [],
    #   "venture[team_members][status]": []
    # }
    ##############
    # From PoS (Version 2019-09-11 in the morning)
    # {
    #   "id": "20",
    #   "language": "English",
    #   "langcode": "en",
    #   "base_url": "https://pos-dev.driver-project.eu",
    #   "title": "CrowdTasker",
    #   "group_uri": "/en/group/20",
    #   "usage_rights": "CC BY 4.0 license",
    #   "type": "Solution",
    #   "provider": "AIT Austrian Institute of Technology GmbH.",
    #   "provider_uri": "/en/node/1056",
    #   "summary_short": "CrowdTasker enables crisis managers to instruct large numbers of non-institutional (either spontaneous or pre-registered) volunteers with customizable tasks, contextual information, warnings and alerts, as well as to crowdsource information from them.",
    #   "summary": "<p>CrowdTasker enables crisis managers to instruct large numbers of non-institutional (either spontaneous or pre-registered) volunteers with customizable tasks, contextual information, warnings and alerts, as well as to crowdsource information from them. <p />\n<p>The received feedback is evaluated and visualized and provides \n    <p>Unstable condition involving an impending abrupt or significant change that requires urgent attention and action to protect life, assets, property or the environment.<br />&#13;\n </p>&#13;\n<p>\n    \n    read more    \n    </p>\n   managers with a detailed overview of the situation, which is used in turn to trigger adequate \n    <p>Situation where widespread human, material, economic or environmental losses have occurred which exceeded the ability of the affected organisation, community or society to respond and recover using its own resources.</p>&#13;\n<p>\n    \n    read more    \n    </p>\n   relief services.</p>\n\n<p>When working with the volunteers that are already at a disaster site CrowdTasker allows the crisis managers to:</p>\n\nDramatically reduce the time and effort needed to exchange information with these volunteers;\n\tDifferentiate between the volunteers based on their profiles (e.g. skills, health) and positions\n\tAddress the people that potentially possess local knowledge;\n\tAlleviate the workload for \n    <p>Sudden, urgent, usually unexpected occurrence or event requiring immediate action.<br />&#13;\nNote 1 to entry: An emergency is usually a disruption or condition that can often be anticipated or prepared for, but seldom exactly foreseen.</p>&#13;\n<p>\n    \n    read more    \n    </p>\n   and \n    <p>Actions taken during or immediately after a disaster in order to save lives, reduce health impacts, ensure public safety and meet the basic subsistence needs of the people affected.</p>&#13;\n<p>\n    \n    read more    \n    </p>\n   organizations;\n",
    #   "innovation_stage": "Stage 4: Early Adoption/ Distribution",
    #   "innovation_stage_uri": "/en/taxonomy/term/8",
    #   "trl": "TRL 7 - System prototype demonstration in operational environment",
    #   "trl_uri": "/en/taxonomy/term/16",
    #   "illustration_title": "Situation ",
    #   "illustration_uri": "/sites/default/files/public/styles/large/public/2018-10/CrowdTasker%253ACrowdtaskingsolutionformanagingofthepre-registeredvolunteers0.png.png?itok=CyRW8xy5 ",
    #   "video_url": "",
    #   "last_changed": "15 hours 45 minutes ago",
    #   "last_changed_on": "2019-09-10T17:07:26+0200"
    # },
    c = {
        "venture": {
            # From PoS
            "high_level_pitch": p["title"],
            "product": p["summary"] if p["summary"] else "Blank",
            # "product": p["summary_short"] if p["summary_short"] else "Blank",
            "company_name": p["provider"] if p["provider"] else "DRIVER+",
            "company_website": "{}{}".format (p["base_url"], p["group_uri"]),
            "user_id": user_id,   # the user with the same email as the admin doing the import
            "logo": "https://s3-eu-west-1.amazonaws.com/kit-eu-preprod/assets/networks/550/picture/-original.jpg?1567692929",
            "business_stage": "unknown",
            # "business_stage": p["innovation_stage"],   # Response text:  {"status":400,"errors":"venture[business_stage] does not have a valid value"}
            "locations": [
                {
                    "address": "Giefinggasse 4",
                    "citty": "Vienna",
                    "country_code": "AT"
                }
            ]
        }
    }
    # https://pos.driver-project.eu/themes/reboot/logo.svg
    if "illustration_uri" in p:
        c["venture"]["cover_picture"] = "{}{}".format(p["base_url"], p["illustration_uri"]).strip()

    if "video_url" in p:
        videoUrl = p["video_url"]
        if videoUrl:
            # This is what I get from PoS:
            # link = "https://youtu.be/4t5ScCh6XU0"
            # This is what youtube offers to embed the video:
            # link = '<iframe width="560" height="315" src="https://www.youtube.com/embed/4t5ScCh6XU0" frameborder="0" allow="accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>'
            # this is from the CMINE REST GET of the example project:
            # link = "<iframe class=\"embedly-embed\" src=\"//cdn.embedly.com/widgets/media.html?src=https%3A%2F%2Fwww.youtube.com%2Fembed%2FlwWG0ecPV80%3Ffeature%3Doembed&url=http%3A%2F%2Fwww.youtube.com%2Fwatch%3Fv%3DlwWG0ecPV80&image=https%3A%2F%2Fi.ytimg.com%2Fvi%2FlwWG0ecPV80%2Fhqdefault.jpg&key=dbe53e8b4d2c414baa1bb5daf229ae72&type=text%2Fhtml&schema=youtube\" width=\"854\" height=\"480\" scrolling=\"no\" frameborder=\"0\" allow=\"autoplay; fullscreen\" allowfullscreen=\"true\"></iframe>"
            # this is what I try:
            link = '<iframe class="embedly-embed" src="{}" width="854" height="480" scrolling="no" frameborder="0" allow="autoplay; fullscreen" allowfullscreen="true"></iframe>'.format (videoUrl)
            # see https://www.urldecoder.io/python/
            # https://stackoverflow.com/questions/44188759/auto-embeding-videos-from-youtube-python-html
            c["venture"]["video_html"] = link

    if trl_attr_name is not None:
        if "trl" in p:
            c["venture"]["customizable_attributes"] = [
                {
                    trl_attr_name: [
                        # "TRL 4 \u2013 technology validated in lab"
                        p["trl"]
                    ]
                }
            ]

    if verbose > 1:
        print ("CMINE: ", json.dumps (c, indent=2), file=sys.stderr)

    # post or put c
    headers = {
        'content-type': 'application/json',
        'accept': 'application/json',
        'Authorization': 'Bearer {}'.format (token)
        }
    fullUrl = "{}/api/admin/v2/{}".format (url, venturesPath)
    if venture_id is None:
        if verbose:
            print ("> CMINE: POST ", fullUrl, file=sys.stderr)
        response = requests.post (fullUrl, headers=headers, data=json.dumps (c))  # verify=False
    else:
        fullUrl = "{}/{}".format (fullUrl, venture_id)
        # location: id needed in PUT! So...
        c["venture"].pop ("locations", None)
        if verbose:
            print ("> CMINE: PUT ", fullUrl, file=sys.stderr)
        response = requests.put (fullUrl, headers=headers, data=json.dumps (c))  # verify=False
    if response.status_code not in [200, 201]:
        if verbose <= 1:
            print ("CMINE: ", json.dumps (c, indent=2), file=sys.stderr)
        # print ("Response: ", response, file=sys.stderr)
        print ("Response headers: ", response.headers, file=sys.stderr)
        print ("Response text: ", response.text, file=sys.stderr)
        raise Exception ("Error posting '{2}' to CMINE: {0} {0}".format (response.status_code, response.text, p["title"]))
    if verbose > 1:
        print ("Response headers: ", response.headers, file=sys.stderr)
        print ("Response text: ", response.text, file=sys.stderr)
        jsonData = response.json() if callable (response.json) else response.json
        print ("CMINE Response data: ", json.dumps (jsonData, indent=2), file=sys.stderr)

    # tc = iso8601.parse_date(d["last_changed_on"])   # "2018-11-30T11:54:00+0100"


if __name__ == '__main__':
    load_dotenv()
    parser = argparse.ArgumentParser(description='Sync Pos to CMINE')
    parser.add_argument('--pos-url', help='PoS REST endpoint', default=os.getenv ("pos_url"))
    parser.add_argument('--cmine-url', help='CMINE REST endpoint', default=os.getenv ("cmine_url"))
    parser.add_argument('--cmine-email', help='CMINE admin eamil', default=os.getenv ("cmine_email"))
    parser.add_argument('--cmine-password', help='CMINE admin password', default=os.getenv ("cmine_password"))
    parser.add_argument('--cmine-owner', help='CMINE solution ownners eamil', default=os.getenv ("cmine_owner"))
    parser.add_argument('--cmine-client-id', help='CMINE client UID', default=os.getenv ("cmine_client_id"))
    parser.add_argument('--cmine-client-secret', help='CMINE client secret', default=os.getenv ("cmine_client_secret"))

    parser.add_argument('--verbose', '-v', help='Be verbose (can be used multiple times)', action="count")

    parser.add_argument('--test', '-t', help='Test something instead of doing useful work', choices=["PoS", "me", "users", "ventures", "custom"])
    parser.add_argument ('--one', help="Copy only one solution", action="store_true")
    parser.add_argument ('--delete', help="Delete ALL my solutions", action="store_true")

    args = parser.parse_args()

    if args.verbose:
        verbose = args.verbose
    for a in ['pos_url', 'cmine_url', 'cmine_email', 'cmine_password', 'cmine_owner', 'cmine_client_id', 'cmine_client_secret']:
        if not getattr (args, a):
            print ("Provide argument '--{}' or enviroment variable '{}'!".format (a.replace('_', '-'), a), file=sys.stderr)
            exit (1)
    posUrl = args.pos_url
    cmineUrl = args.cmine_url

    if args.test:
        if "PoS" == args.test:
            print (json.dumps ([d for d in posGenerator(posUrl)]))
            exit (0)
        token = getAuthToken(cmineUrl, args.cmine_email, args.cmine_password, args.cmine_client_id, args.cmine_client_secret)
        if "me" == args.test:
            getMyUserId (cmineUrl, token)
        if "users" == args.test:
            getUserId (cmineUrl, token, args.cmine_owner)
        if "ventures" == args.test:
            print ("Ventures by name: ", getVentures (cmineUrl, token), file=sys.stderr)
        if "custom" == args.test:
            print ("Custom TRL attributes: ", getCustomAttributes (cmineUrl, token, "(Trl)"), file=sys.stderr)
        exit(0)

    if args.delete:
        token = getAuthToken(cmineUrl, args.cmine_email, args.cmine_password, args.cmine_client_id, args.cmine_client_secret)
        user_id = getUserId (cmineUrl, token, args.cmine_owner)
        myName2id = getVentures(cmineUrl, token, user_id)
        for name, d in myName2id.items():
            print ("! CMINE: delete '{}'".format(name))
            deleteVenture(cmineUrl, token, d["id"])
            if args.one:
                exit(0)
        exit(0)

    token = None
    user_id = None
    name2id = {}
    for d in posGenerator(posUrl):
        if verbose > 2:
            print (d, file=sys.stderr)
        if token is None:
            token = getAuthToken(cmineUrl, args.cmine_email, args.cmine_password, args.cmine_client_id, args.cmine_client_secret)
            user_id = getUserId (cmineUrl, token, args.cmine_owner)
            name2id = getVentures(cmineUrl, token, user_id)
            if verbose:
                print ("Available on CMINE: ", name2id.keys(), file=sys.stderr)
            trl_attr_names = getCustomAttributes (cmineUrl, token, "(Trl)")
            if len (trl_attr_names) == 1:
                trl_attr_name = trl_attr_names[0]
            else:
                trl_attr_name = None
                print ("Could not identify TRL custom attribute. Candidates are ", trl_attr_names)
            # testAccessToken (cmineUrl, token)

        # prepare CMINE update
        idCMINE = None
        needUpdate = True
        if d["title"] in name2id:
            idCMINE = name2id[d["title"]]["id"]
            # Is PoS newer than CMINE?
            # CMINE: "updated_at": "2019-09-04T12:08:09Z",
            tCMINE = iso8601.parse_date(name2id[d["title"]]["updated_at"]).astimezone(tz.tzutc()).replace (tzinfo=None)
            # PoS: "changed": "2019-09-10T17:07:26+0200"
            tPoS = iso8601.parse_date(d["changed"]).astimezone(tz.tzutc()).replace (tzinfo=None)
            # print ("tCMINE: ", tCMINE, file=sys.stderr)
            # print ("tPoS:   ", tPoS, file=sys.stderr)
            needUpdate = tPoS > tCMINE
        if needUpdate:
            writeToCmine (cmineUrl, token, user_id, idCMINE, trl_attr_name, d, posUrl)
        if d["title"] in name2id:
            name2id[d["title"]]["still_exists"] = True
        if args.one:
            exit (0)

    # TODO: use names2id.still_exists=False
    for n, d in name2id.items():
        if not d["still_exists"]:
            print ("delete {}".format (n), file=sys.stderr)
            # deleteVenture(cmineUrl, token, d["id"])
