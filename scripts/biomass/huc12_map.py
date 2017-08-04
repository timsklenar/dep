"""Draw a fancy map"""
import sys

import psycopg2
import numpy as np
from pyiem.plot import MapPlot
from shapely.wkb import loads
from matplotlib.patches import Polygon
import matplotlib.colors as mpcolors
import matplotlib.pyplot as plt
import cartopy.crs as ccrs


def main():
    """GO!"""
    pgconn = psycopg2.connect(database='idep', host='localhost', port=5555,
                              user='nobody')
    cursor = pgconn.cursor()

    scenario = int(sys.argv[1])
    mp = MapPlot(sector='iowa', axisbg='white', nologo=True,
                 subtitle='1 Jan 2008 thru 31 Dec 2016',
                 caption='Daily Erosion Project',
                 title=('Harvest Index 0.8 Change in Soil Delivery '
                        'from Baseline'))

    cursor.execute("""
    with baseline as (
        SELECT huc_12, sum(avg_delivery) * 4.463 as loss from results_by_huc12
        where valid between '2008-01-01' and '2017-01-01' and
        scenario = 0 GROUP by huc_12),
    scenario as (
        SELECT huc_12, sum(avg_delivery) * 4.463 as loss from results_by_huc12
        where valid between '2008-01-01' and '2017-01-01' and
        scenario = %s GROUP by huc_12),
    agg as (
        SELECT b.huc_12, b.loss as baseline_loss, s.loss as scenario_loss from
        baseline b LEFT JOIN scenario s on (b.huc_12 = s.huc_12))

     SELECT ST_Transform(simple_geom, 4326),
     (scenario_loss  - baseline_loss) / 9.0 as val, i.huc_12
     from huc12 i JOIN agg d on (d.huc_12 = i.huc_12)
     WHERE i.states ~* 'IA' ORDER by val DESC

    """, (scenario, ))

    # bins = np.arange(0, 101, 10)
    bins = [-5, -2, -1, -0.5, 0, 0.5, 1, 2, 5]
    cmap = plt.get_cmap("BrBG_r")
    cmap.set_under('purple')
    cmap.set_over('black')
    norm = mpcolors.BoundaryNorm(bins, cmap.N)

    for row in cursor:
        # print "%s,%s" % (row[2], row[1])
        polygon = loads(row[0].decode('hex'))
        arr = np.asarray(polygon.exterior)
        points = mp.ax.projection.transform_points(ccrs.Geodetic(),
                                                   arr[:, 0], arr[:, 1])
        c = cmap(norm([float(row[1]), ]))[0]
        p = Polygon(points[:, :2], fc=c, ec='k', zorder=2, lw=0.1)
        mp.ax.add_patch(p)

    mp.draw_colorbar(bins, cmap, norm, units='T/a')

    mp.drawcounties()
    mp.postprocess(filename='test.png')


if __name__ == '__main__':
    main()