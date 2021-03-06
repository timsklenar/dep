#!/usr/bin/env python
"""GeoJSON service for HUC12 data"""
import sys
import json
import cgi
import datetime

import memcache
from jenks import jenks
from pyiem.util import get_dbconn


def myjenks(array, label):
    """Create classification breaks for the array"""
    a = list(set(jenks(array, 6)))
    # Some failures happen when number of values > 0 is less than 6
    # sys.stderr.write(label + str(a))
    a.sort()
    if max(a) == 0:
        return [0]
    if a[1] < 0.01:
        newa = [a[0]]
        for _ in a[1:]:
            if _ > 0.01:
                newa.append(_)
        a = newa
    # sys.stderr.write(label + str(a))
    if max(a) == 0 or len(a) < 2:
        return [0]
    if a[0] == 0 and a[1] > 0.001:
        a[0] = 0.001
    return [float(_) for _ in a]


def do(ts, ts2, domain):
    """Do work"""
    pgconn = get_dbconn('idep')
    cursor = pgconn.cursor()
    utcnow = datetime.datetime.utcnow()
    dextra = "valid = %s"
    args = (ts,)
    if ts2 is not None:
        dextra = "valid >= %s and valid <= %s"
        args = (ts, ts2)
    domainextra = ''
    if domain is not None:
        domainextra = " and states ~* '%s'" % (domain[:2].upper(),)
    cursor.execute("""WITH data as (
        SELECT ST_asGeoJson(ST_Transform(simple_geom, 4326), 4) as g,
        huc_12
        from huc12 WHERE scenario = 0 """ + domainextra + """), obs as (
        SELECT huc_12,
            sum(coalesce(avg_loss, 0)) * 4.463 as avg_loss,
            sum(coalesce(avg_delivery, 0)) * 4.463 as avg_delivery,
            sum(coalesce(qc_precip, 0)) / 25.4 as qc_precip,
            sum(coalesce(avg_runoff, 0)) / 25.4 as avg_runoff
        from results_by_huc12 WHERE
        """+dextra+""" and scenario = 0 GROUP by huc_12)

        SELECT d.g, d.huc_12,
        coalesce(o.avg_loss, 0),
        coalesce(o.qc_precip, 0),
        coalesce(o.avg_delivery, 0),
        coalesce(o.avg_runoff, 0)
        from data d LEFT JOIN obs o ON (d.huc_12 = o.huc_12)
    """, args)
    res = {'type': 'FeatureCollection',
           'features': [],
           'generation_time': utcnow.strftime("%Y-%m-%dT%H:%M:%SZ"),
           'count': cursor.rowcount}
    avg_loss = []
    qc_precip = []
    avg_delivery = []
    avg_runoff = []
    for row in cursor:
        avg_loss.append(row[2])
        qc_precip.append(row[3])
        avg_delivery.append(row[4])
        avg_runoff.append(row[5])
        res['features'].append(dict(type="Feature",
                                    id=row[1],
                                    properties=dict(
                                        avg_loss=row[2],
                                        qc_precip=row[3],
                                        avg_delivery=row[4],
                                        avg_runoff=row[5]),
                                    geometry=json.loads(row[0])
                                    ))
    res['jenks'] = dict(avg_loss=myjenks(avg_loss, 'avg_loss'),
                        qc_precip=myjenks(qc_precip, 'qc_precip'),
                        avg_delivery=myjenks(avg_delivery, 'avg_delivery'),
                        avg_runoff=myjenks(avg_runoff, 'avg_runoff'))
    return json.dumps(res)


def main():
    """Do Fun things"""
    sys.stdout.write("Content-Type: application/vnd.geo+json\n\n")
    form = cgi.FieldStorage()
    cb = form.getfirst('callback', None)
    domain = form.getfirst('domain', None)
    ts = datetime.datetime.strptime(form.getfirst('date', '2015-05-05'),
                                    '%Y-%m-%d')
    ts2 = None
    if form.getfirst('date2', None) is not None:
        ts2 = datetime.datetime.strptime(form.getfirst('date2'), '%Y-%m-%d')

    mckey = ("/geojson/huc12/%s/%s/%s"
             ) % (ts.strftime("%Y%m%d"),
                  '' if ts2 is None else ts2.strftime("%Y%m%d"),
                  '' if domain is None else domain)
    mc = memcache.Client(['iem-memcached:11211'], debug=0)
    res = mc.get(mckey)
    if not res:
        res = do(ts, ts2, domain)
        mc.set(mckey, res, 3600)

    if cb is None:
        sys.stdout.write(res)
    else:
        sys.stdout.write("%s(%s)" % (cb, res))


if __name__ == '__main__':
    main()
