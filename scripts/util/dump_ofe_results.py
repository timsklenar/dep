"""Summarize the OFE files"""
from __future__ import print_function
import os
import datetime

import pandas as pd
from pyiem.dep import read_ofe, read_man, read_slp

""""
                     No-till (1)   (2-5)
  B - Soy               B1          B25    IniCropDef.Default
  F - forest            F1          F25    IniCropDef.Tre_2239
  G - Sorghum
  P - Pasture           P1          P25    IniCropDef.gra_3425
  C - Corn              C1          C25    IniCropDef.Default
  R - Other crops       R1          R25    IniCropDef.Aft_12889
  T - Water
  U - Developed
  X - Unclassified
  I - Idle
  L - Double Crop  (started previous year)
  W - Wheat
  N - ???  *see 27 Sep 2016 email from dave, it is unused, so treat as I*
"""
LABEL2CODE = {'soybean2': 'B',
              'Corn': 'C',
              'Tre_2932': 'I',
              'bromegr1': 'P',
              'Bar_8319': 'W'}
YEARS = (2016 - 2007) + 1


def get_rotation_string(manres, ofe):
    """Uffff"""
    codes = []
    for rot in manres['rotations']:
        idx = rot[ofe - 1]['yearindex']
        ntype = manres['scens'][idx - 1]['ntype']
        codes.append(LABEL2CODE[manres['crops'][ntype - 1]['crpnam']])
    return "".join(codes)


def main():
    """Go Main Go"""
    # ['id', 'CropRotationString', 'slope',
    #                           'rainfall', 'runoff', 'detach', 'delivery'])
    rows = []
    for root, _dirs, files in os.walk("/i/0/ofe"):
        for filename in files:
            ofedf = read_ofe("%s/%s" % (root, filename))
            # Drop any 2017+ data
            ofedf = ofedf[ofedf['date'] < datetime.date(2017, 1, 1)]
            # Figure out the crop string
            man = "%s/%s" % (root.replace("ofe", "man"),
                             filename.replace("ofe", "man"))
            try:
                manres = read_man(man)
            except:
                print("failure reading %s" % (man,))
                continue

            slp = "%s/%s" % (root.replace("ofe", "slp"),
                             filename.replace("ofe", "slp"))
            slpres = read_slp(slp)

            for ofe in ofedf['ofe'].unique():
                myofe = ofedf[ofedf['ofe'] == ofe]
                length = slpres[ofe - 1]['x'][-1] - slpres[ofe - 1]['x'][0]
                slp = ((slpres[ofe - 1]['y'][0] - slpres[ofe - 1]['y'][-1]) /
                       length)
                rows.append({
                    'id': "%s_%s" % (filename[:-4], ofe),
                    'huc12': filename[:12],
                    'fpath': filename.split("_")[1][:-4],
                    'ofe': ofe,
                    'CropRotationString': (
                        get_rotation_string(manres, ofe)[:YEARS]),
                    'slope[1]': slp,
                    'rainfall': -1,
                    'runoff[mm/yr]': myofe['runoff'].sum() / YEARS,
                    'detach': -1,
                    'length[m]': length,
                    'delivery[t/a/yr]': (
                        myofe['sedleave'].sum() / YEARS / length * 4.463)
                    })

    df = pd.DataFrame(rows)
    df.to_csv('results.csv', index=False)


if __name__ == '__main__':
    main()
