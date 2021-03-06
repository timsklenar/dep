"""
 I do the realtime run!
"""
from __future__ import print_function
import sys
import os
import subprocess
import datetime
from multiprocessing import Pool

from pyiem.util import get_dbconn

SCENARIO = sys.argv[1]
# don't need trailing /
IDEPHOME = "/i/%s" % (SCENARIO, )
YEARS = datetime.date.today().year - 2006
# need to regenerate run files on 2 January
FORCE_RUNFILE_REGEN = (datetime.date.today().month == 1 and
                       datetime.date.today().day == 2)


class WeppRun(object):
    """ Represents a single run of WEPP

    Filenames have a 51 character restriction
    """

    def __init__(self, huc12, fpid, clifile):
        """ We initialize with a huc12 identifier and a flowpath id """
        self.huc12 = huc12
        self.huc8 = huc12[:8]
        self.subdir = "%s/%s" % (huc12[:8], huc12[8:])
        self.fpid = fpid
        self.clifile = clifile

    def get_wb_fn(self):
        ''' Return the water balance filename for this run '''
        return '%s/wb/%s/%s_%s.wb' % (IDEPHOME, self.subdir,
                                      self.huc12, self.fpid)

    def get_env_fn(self):
        ''' Return the event filename for this run '''
        return '%s/env/%s/%s_%s.env' % (IDEPHOME, self.subdir,
                                        self.huc12, self.fpid)

    def get_ofe_fn(self):
        """ Return the filename used for OFE output """
        return '%s/ofe/%s/%s_%s.ofe' % (IDEPHOME, self.subdir, self.huc12,
                                        self.fpid)

    def get_error_fn(self):
        ''' Return the event filename for this run '''
        return '%s/error/%s/%s_%s.error' % (IDEPHOME, self.subdir,
                                            self.huc12, self.fpid)

    def get_man_fn(self):
        ''' Return the management filename for this run '''
        return '%s/man/%s/%s_%s.man' % (IDEPHOME, self.subdir,
                                        self.huc12, self.fpid)

    def get_slope_fn(self):
        ''' Return the slope filename for this run '''
        return '%s/slp/%s/%s_%s.slp' % (IDEPHOME, self.subdir,
                                        self.huc12, self.fpid)

    def get_soil_fn(self):
        ''' Return the soil filename for this run '''
        return '%s/sol/%s/%s_%s.sol' % (IDEPHOME, self.subdir,
                                        self.huc12, self.fpid)

    def get_clifile_fn(self):
        ''' Return the climate filename for this run '''
        return '%s/%s' % (IDEPHOME, self.clifile)

    def get_runfile_fn(self):
        ''' Return the run filename for this run '''
        return '%s/run/%s/%s_%s.run' % (IDEPHOME, self.subdir,
                                        self.huc12, self.fpid)

    def get_yield_fn(self):
        """Filename to be used for yield output"""
        return "%s/yld/%s/%s_%s.yld" % (IDEPHOME, self.subdir, self.huc12,
                                        self.fpid)

    def make_runfile(self):
        ''' Create a runfile for our runs '''
        out = open(self.get_runfile_fn(), 'w')
        out.write("E\n")      # English units
        out.write("Yes\n")    # Run Hillslope
        out.write("1\n")      # Continuous simulation
        out.write("1\n")      # hillslope version
        out.write("No\n")     # pass file output?
        out.write("1\n")      # abbreviated annual output
        out.write("No\n")     # initial conditions output
        out.write("/dev/null\n")   # soil loss output file
        out.write("Yes\n")        # Do water balance output
        out.write("%s\n" % (self.get_wb_fn(),))   # water balance output file
        out.write("No\n")     # crop output
        out.write("No\n")     # soil output
        out.write("No\n")     # distance and sed output
        out.write("No\n")     # large graphics output
        out.write("Yes\n")    # event by event output
        out.write("%s\n" % (self.get_env_fn(),))  # event file output
        out.write("No\n")     # element output
        # out.write("%s\n" % (self.get_ofe_fn(),))
        out.write("No\n")     # final summary output
        out.write("No\n")     # daily winter output
        out.write("Yes\n")     # plant yield output
        out.write("%s\n" % (self.get_yield_fn(),))  # yield file
        out.write("%s\n" % (self.get_man_fn(),))  # management file
        out.write("%s\n" % (self.get_slope_fn(),))  # slope file
        out.write("%s\n" % (self.get_clifile_fn(),))  # climate file
        out.write("%s\n" % (self.get_soil_fn(),))  # soil file
        out.write("0\n")  # Irrigation
        out.write("%s\n" % (YEARS,))  # years 2007-
        out.write("0\n")  # route all events

        out.close()

    def run(self):
        ''' Actually run wepp for this event '''
        runfile = self.get_runfile_fn()
        if FORCE_RUNFILE_REGEN or not os.path.isfile(runfile):
            # If this scenario does not have a run file, hmmm
            if SCENARIO != '0':
                return
            self.make_runfile()
        proc = subprocess.Popen(["wepp", ],
                                stderr=subprocess.PIPE,
                                stdout=subprocess.PIPE, stdin=subprocess.PIPE)
        proc.stdin.write(open(runfile).read())
        res = proc.stdout.read()
        if res[-13:-1] != 'SUCCESSFULLY':
            print('Run HUC12: %s FPATH: %4s errored!' % (self.huc12,
                                                         self.fpid))
            efp = open(self.get_error_fn(), 'w')
            efp.write(res)
            efp.close()


def realtime_run():
    ''' Do a realtime run, please '''
    idep = get_dbconn('idep', user='nobody')
    icursor = idep.cursor()

    queue = []
    icursor.execute("""SELECT huc_12, fid, fpath, climate_file
    from flowpaths where scenario = %s""" % (SCENARIO,))
    for row in icursor:
        queue.append(row)
    return queue


def run(row):
    """ Run ! """
    wr = WeppRun(row[0], row[2], row[3])
    wr.run()


def main():
    """Go Main Go"""
    queue = realtime_run()
    pool = Pool()  # defaults to cpu-count
    sts = datetime.datetime.now()
    sz = len(queue)
    for i, _ in enumerate(pool.imap_unordered(run, queue), 1):
        if i > 0 and i % 5000 == 0:
            delta = datetime.datetime.now() - sts
            secs = delta.microseconds / 1000000. + delta.seconds
            speed = i / secs
            remaining = ((sz - i) / speed) / 3600.
            print(('%5.2fh Processed %6s/%6s [%.2f runs per sec] '
                   'remaining: %5.2fh') % (secs / 3600., i, sz, speed,
                                           remaining))


if __name__ == '__main__':
    main()
