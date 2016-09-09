#!/usr/bin/env python

import re
import sys
import argparse

# from this point non-standard library imports
import requests

LOGIN_URL = "https://videocollege.tue.nl/Mediasite/Login/?ReturnUrl=%2FMediasite%2FCatalog%2FFull%2Fc2530f3a273842c480d40365fcbf216321%2F"
SEARCH_URL = "http://videocollege.tue.nl/Mediasite/Catalog/Data/Search"
PLAYER_URL = "http://videocollege.tue.nl/Mediasite/PlayerService/PlayerService.svc/json/GetPlayerOptions"

FAKE_USERAGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/27.0.1453.93 Safari/537.36'
HEADERS = {'User-Agent': FAKE_USERAGENT}

def init_session(user, pw):
    sess = requests.session()

    sess.headers.update(HEADERS)

    login_form = {'UserName': user,
                  'Password': pw,
                  'RememberMe': False}

    sess.post(LOGIN_URL, data=login_form, headers=HEADERS)

    return sess


def search(sess, term):
    payload = {"IsViewPage": True,
               "Type":"search",
               "CatalogId":"c2530f3a-2738-42c4-80d4-0365fcbf2163",
               "AuthTicket":"null",
               "SearchTerm":term,
               "FacetFilters": [{"Key":"CatalogIds",
                                 "Value":"c2530f3a-2738-42c4-80d4-0365fcbf2163"}],
               "CurrentPage":0,
               "ItemsPerPage":20,
               "SortBy":"Date",
               "SortDirection":"Descending",
               "PreviewKey":"null",
               "Tags":[]
              }

    resp = sess.post(SEARCH_URL, json=payload, headers=HEADERS)

    json = resp.json()

    return sorted([(e['Name'], e['Id']) for e in json['PresentationDetailsList']])


def get_urls_by_id(sess, id_, prio):
    payload = {"getPlayerOptionsRequest":
                    {"ResourceId":id_,
                     "QueryString":"?catalog=c2530f3a-2738-42c4-80d4-0365fcbf2163",
                     "UseScreenReader":False,
                     "UrlReferrer":""
                    }
              }

    resp = sess.post(PLAYER_URL, json=payload, headers=HEADERS)

    json = resp.json()

    streams = json['d']['Presentation']['Streams']

    return [url['Location'] for s in streams if s['Priority'] <= prio for url in s['VideoUrls']]


def construct_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('course_code')
    parser.add_argument('regex_match', nargs='?')
    parser.add_argument('-p', '--priority', default=1,
            help='select only streams with this max priority', type=int)
    parser.add_argument('-u', '--username', default=1, required=True,
            help='username to login into videocollege.tue.nl')
    parser.add_argument('-pw', '--password', default=1, required=True,
            help='password to login into videocollege.tue.nl')

    return parser


if __name__ == "__main__":
    parser = construct_parser()
    opts = parser.parse_args()

    sess = init_session(opts.username, opts.password)

    lectures = search(sess, opts.course_code)

    do_search = not bool(opts.regex_match)

    for (name, id_) in lectures:
        if do_search:
            print(name)
        elif re.match('.*' + opts.regex_match + '.*', name):
            urls = get_urls_by_id(sess, id_, opts.priority)
            for url in urls:
                print(url)
