"""Process provided DBF files into the database

Brian Gelder provides me a zipfile full of dbfs (one per HUC12).  This script
consumes those dbf files and places them in the database.

    python flowpath_importer.py <scenario> <path to dbf files in ../../data/>

"""
from __future__ import print_function
import glob
import os
import sys

import shapefile
from tqdm import tqdm
import pandas as pd
import psycopg2

print("BE CAREFUL!  The dbf files may not be 5070, but 26915")

SCENARIO = int(sys.argv[1])
PREFIX = 'g4'
# TRUNC_GRIDORDER_AT = int(sys.argv[3])

PGCONN = psycopg2.connect(database='idep', host='iemdb')
INSERT_SQL = """
    INSERT into flowpath_points(flowpath, segid,
    elevation, length,  surgo, management, slope, geom,
    lu2007, lu2008, lu2009, lu2010, lu2011, lu2012, lu2013,
    lu2014, lu2015, lu2016, lu2017, scenario, gridorder)
    values(%s, %s, %s, %s, %s, %s, %s, 'SRID=5070;POINT(%s %s)',
    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
"""


def get_flowpath(cursor, huc12, fpath):
    """Get or create a database flowpath identifier

    Args:
      cursor (psycopg2.cursor): database cursor
      huc12 (str): HUC12 identifier
      fpath (int): the flowpath id value for this HUC12

    Returns:
      int the value of this huc12 flowpath
    """
    cursor.execute("""
    SELECT fid from flowpaths where huc_12 = %s and fpath = %s
    and scenario = %s
    """, (huc12, fpath, SCENARIO))
    if cursor.rowcount == 0:
        cursor.execute("""
        INSERT into flowpaths(huc_12, fpath, scenario)
        values (%s, %s, %s) RETURNING fid
        """, (huc12, fpath, SCENARIO))
    return cursor.fetchone()[0]


def get_data(filename):
    """Converts a dbf file into a pandas dataframe

    Args:
      filename (str): The dbf filename to process

    Returns:
      pd.DataFrame with the dbf data included.
    """
    # hack to read just dbf file
    # https://github.com/GeospatialPython/pyshp/issues/35
    dbf = shapefile.Reader(dbf=open(filename, 'rb'))
    rows = dbf.records()
    fields = dbf.fields[1:]
    field_names = [field[0] for field in fields]
    df = pd.DataFrame(rows)
    df.columns = field_names
    return df


def process(cursor, filename, huc12df):
    """Processing of a HUC12's data into the database

    Args:
      cursor (psycopg2.cursor): database cursor
      filename (str): the dbf filename
      huc12df (pd.DataFrame): the dataframe containing the dbf data

    Returns:
      None
    """
    # We get the huc12 code based on the filename
    huc12 = filename[-16:-4]
    huc8 = huc12[:-4]
    # the inbound dataframe has lots of data, one row per flowpath point
    # We group the dataframe by the column which uses a PREFIX and the huc8
    for flowpath, df in huc12df.groupby('%s%s' % (PREFIX, huc8)):
        # never do flowpath zero!
        if flowpath == 0:
            continue
        # Sort along the length column, which orders the points from top
        # to bottom
        df = df.sort_values('%sLen%s' % (PREFIX, huc8[:5]), ascending=True)
        # Get or create the flowpathid from the database
        fid = get_flowpath(cursor, huc12, flowpath)
        # Remove any previous data for this flowpath
        cursor.execute("""
            DELETE from flowpath_points WHERE flowpath = %s
            and scenario = %s
            """, (fid, SCENARIO))
        linestring = []
        sz = len(df.index)
        for segid, (_, row) in enumerate(df.iterrows()):
            if (segid+1) == sz:  # Last row!
                # This effectively repeats the slope of the previous point
                # by having a negative dx and negative dy below. <hack>
                row2 = df.iloc[segid-1]
            else:
                row2 = df.iloc[segid+1]
            dy = row['ep3m%s' % (huc8[:6],)] - row2['ep3m%s' % (huc8[:6],)]
            dx = (row2['%sLen%s' % (PREFIX, huc8[:5])] -
                  row['%sLen%s' % (PREFIX, huc8[:5])])
            gridorder = 4
            # Some optional code here that was used for the grid order work
            # gridorder = row['gord_%s' % (huc8[:5], )]
            # if gridorder > TRUNC_GRIDORDER_AT:
            #    continue
            if dx == 0:
                slope = 0
            else:
                slope = dy/dx
            lu = row['CropRotatn'].strip()
            # print "%3s %7.1f %7.1f %7.4f %s" % (segid, dx, dy, slope, lu)
            if lu == "":
                lu = [None, ] * 8

            # OK, be careful here.  the landuse codes start in 2008 as there
            # is no national coverage in 2007.  So for 2007, we will repeat
            # the value for 2009.
            # no 2016 data, so repeat 2014 value
            args = (fid, segid, row['ep3m%s' % (huc8[:6],)]/100.,
                    row['%sLen%s' % (PREFIX, huc8[:5])]/100.,
                    row['gSSURGO'], row['Management'], slope, row['X'],
                    row['Y'], lu[1], lu[0], lu[1], lu[2],
                    lu[3], lu[4], lu[5], lu[6], lu[7], lu[6], lu[7],
                    SCENARIO, gridorder)
            cursor.execute(INSERT_SQL, args)

            linestring.append("%s %s" % (row['X'], row['Y']))

        # Line string must have at least 2 points
        if len(linestring) > 1:
            sql = """
                UPDATE flowpaths SET geom = 'SRID=5070;LINESTRING(%s)'
                WHERE fid = %s and scenario = %s
            """ % (",".join(linestring), fid, SCENARIO)
            cursor.execute(sql)
        else:
            # Cull our work above if this flowpath is too short
            cursor.execute("""
                DELETE from flowpath_points
                where flowpath = %s and scenario = %s
            """, (fid, SCENARIO))
            cursor.execute("""
                DELETE from flowpaths where fid = %s
                and scenario = %s
            """, (fid, SCENARIO))


def main():
    """Our main function, the starting point for code execution"""
    # Change the working directory to where we have data files
    os.chdir("../../data/%s" % (sys.argv[2],))
    # collect up the dbfs in that directory
    fns = glob.glob("*.dbf")
    i = 0
    cursor = PGCONN.cursor()

    for fn in tqdm(fns):
        # Save our work every 100 dbfs, so to keep the database transaction
        # at a reasonable size
        if i > 0 and i % 100 == 0:
            PGCONN.commit()
            cursor = PGCONN.cursor()
        df = get_data(fn)
        process(cursor, fn, df)
        i += 1

    # Commit the database changes
    cursor.close()
    PGCONN.commit()


if __name__ == '__main__':
    main()
