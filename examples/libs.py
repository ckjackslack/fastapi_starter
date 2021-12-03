from collections import OrderedDict
from OSMPythonTools.api import Api
from OSMPythonTools.data import Data, dictRangeYears, ALL
from OSMPythonTools.overpass import Overpass, overpassQueryBuilder
from OSMPythonTools.nominatim import Nominatim

api = Api()
way = api.query('way/5887599')
print(way.tag('building'))
print(way.tag('architect'))
print(way.tag('website'))

overpass = Overpass()
result = overpass.query('way["name"="Stephansdom"]; out body;')
stephansdom = result.elements()[0]
print(stephansdom.tag('name:en'))
print(stephansdom.tag('addr:street'), stephansdom.tag('addr:housenumber'))
print(stephansdom.tag('addr:postcode'), stephansdom.tag('addr:city'))
print(stephansdom.tag('building'), stephansdom.tag('denomination'))

nominatim = Nominatim()
areaId = nominatim.query('Vienna, Austria').areaId()
print(areaId)
query = overpassQueryBuilder(area = areaId,
    elementType = 'node', selector = '"natural"="tree"',
    out = 'count')
result = overpass.query(query)
print(result.countElements())

result = overpass.query(query, date = '2013-01-01T00:00:00Z',
    timeout = 60)
print(result.countElements())

dimensions = OrderedDict([
    ('year', dictRangeYears(2013, 2017.5, 1)),
    ('city', OrderedDict({
        'berlin': 'Berlin, Germany',
        'paris': 'Paris, France',
        'vienna': 'Vienna, Austria',
    })),
])

def fetch(year, city):
    areaId = nominatim.query(city).areaId()
    query = overpassQueryBuilder(area = areaId,
        elementType = 'node', selector = '"natural"="tree"',
        out = 'count')
    return overpass.query(query, date = year, timeout = 60).countElements()

data = Data(fetch, dimensions)
data.plot(city = ALL, filename = 'example.png')
print(data.select(city = ALL).getCSV())
