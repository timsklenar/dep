"""
 My goal in life is to manage the database schema, so when things change, this
 script can handle it all.  I am run like so:
 
     python schema_manager.py
     
"""

DBS = ['idep',]

import psycopg2
import os
import sys

# Here we go! 
def run_db(dbname):
    """ Lets do an actual database """
    dbconn = psycopg2.connect(database='idep',
                              host='iemdb')
    cursor = dbconn.cursor()
    
    # Step 1: Determine schema version
    try:
        cursor.execute("""SELECT version from iem_version 
            where name = 'schema'""")
        row = cursor.fetchone()
        baseversion = row[0]
    except:
        baseversion = 0
        cursor.close()
        dbconn.commit()
        cursor = dbconn.cursor()
    
    print 'Database: %s has revision: %s' % (dbname, baseversion)
    
    while True:
        baseversion += 1
        fn = 'upgrade/%s.sql' % (baseversion,)
        if not os.path.isfile(fn):
            break
        print ' -> Attempting schema upgrade #%s ...' % (baseversion,),
        sys.stdout.flush()
        try:
            cursor.execute( open(fn).read() )
            cursor.execute("""UPDATE iem_version SET version = %s 
            WHERE name = 'schema'""", (baseversion,))
            print ' Done!'
        except Exception, exp:
            print ' ERROR %s' % (exp,),
            break
            
        
    
    cursor.close()
    dbconn.commit()
    dbconn.close()
    
    
    
    
if __name__ == '__main__':
    for db in DBS:
        run_db(db)