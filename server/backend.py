#!/usr/bin/python

from google.appengine.ext import db
from google.appengine.api.urlfetch import fetch
from muni import scrape
from django.utils import simplejson
import logging

class APIResult(db.Model):
    query = db.StringProperty(required=True)
    json = db.TextProperty(required=True)
    lastfetch = db.DateTimeProperty(auto_now_add=True)

def fetch_one(query):
    results = query.fetch(1)
    if len(results) > 0:
        return results[0]
    return None

def fetch_wireless_url(path):
    url = 'http://www.nextbus.com/wireless/' + path
    logging.info("Fetching URL: %s" % url)
    response = fetch(url, headers={'User-Agent': 'test'})
    if response.status_code != 200:
        raise "Bad status %d" % response.status_code
    return response.content

def url_to_query(url):
    return url[url.index('?')+1:]

def get_routes():
    KEY = 'a=sf-muni'
    routes = fetch_one(APIResult.all().filter('query =', KEY))
    if routes:
        # TODO check date
        return routes.json

    html = fetch_wireless_url('miniRoute.shtml?' + KEY)
    scraper = scrape.Wireless()
    routes = scraper.scrape_routes(html)

    json_data = [{'name': r.name, 'url': url_to_query(r.url)}
                 for r in routes]
    json = simplejson.dumps(json_data)
    result = APIResult(query=KEY, json=json)
    result.put()
    return result.json

def get_route(query):
    route = fetch_one(APIResult.all().filter('query =', query))
    if route:
        # TODO check date
        return route.json

    scraper = scrape.Wireless()
    html = fetch_wireless_url('miniDirection.shtml?' + query)
    dirs = scraper.scrape_directions(html)

    stops0 = scraper.scrape_stops(fetch_wireless_url(dirs[0].url))
    stops1 = scraper.scrape_stops(fetch_wireless_url(dirs[1].url))

    json_data = [
        {'direction': dirs[0].name,
         'stops': [{'name': s.name, 'url': url_to_query(s.url)}
                   for s in stops0]},
        {'direction': dirs[1].name,
         'stops': [{'name': s.name, 'url': url_to_query(s.url)}
                   for s in stops1]},
    ]
    json = simplejson.dumps(json_data)
    result = APIResult(query=query, json=json)
    result.put()
    return result.json