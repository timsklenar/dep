""" Create table with xref between gssurgo values and file names """
import dbflib
import psycopg2

PGCONN = psycopg2.connect(database='idep', host='iemdb')
cursor = PGCONN.cursor()

cursor.execute("""DELETE from xref_surgo""")

dbf = dbflib.open('../../data/s/iaMU.tif.vat.dbf')
for i in range(dbf.record_count()):
    row = dbf.read_record(i)
    cursor.execute("""INSERT into xref_surgo(surgo, soilfile) VALUES
    (%s, %s)""", (row['Value'], row['WEPP_SOL']))
    
cursor.close()
PGCONN.commit()
PGCONN.close()