#----------------------------------------------------------
# Filename: astrometry.py
#
# Description: Runs astrometry.net api on a folder of
# fits observations. Meant to be run from terminal.
#
# Author: Aiden Zelakiewicz (asz39@cornell.edu)
#----------------------------------------------------------

import os
from astroquery.astrometry_net import AstrometryNet
import argparse
import time
import json
from astropy.io import fits

start = time.time()
parser = argparse.ArgumentParser(description='Run astrometry.net on a folder of fits files or a single file.')

parser.add_argument('path', type=str, help='Absolute path to folder of fits files or a single fits file.')
parser.add_argument('--telescope', '-t', type=str, default="default", help='Key for telescope used to take the images.')
parser.add_argument('--downsample', '-d', type=int, default=4, help='Downsample factor for solving images.')
parser.add_argument('--key', type=str, help='Astrometry.net API key.')
parser.add_argument('--username', type=str, help='Astrometry.net username.')
parser.add_argument('--wcscomment', type=bool, default=False, help='Keep Astrometry.net comments and add to header.')

args = parser.parse_args()

ast = AstrometryNet()

if args.key is not None:
    import keyring
    keyring.set_password('astroquery:astrometry_net', args.username, args.key)
    if args.username is None:
        ast.api_key = keyring.get_password('astroquery:astrometry_net', '')
    else:
        ast.api_key = keyring.get_password('astroquery:astrometry_net', args.username)

# Import telescope
f = open('telescopes.json')
telescopes = json.load(f)
f.close()

tele = telescopes['telescopes'][args.telescope]

if os.path.isdir(args.path):
    for file in os.listdir(args.path):
        if file.endswith('.fit') or file.endswith('.fits'):
            print('Uploading ' + file)
            try:
                wcs_header = ast.solve_from_image(args.path + '/' + file, solve_timeout=30, scale_type='ev', scale_est=tele['pixscale'], scale_units=tele['pixscale_units'], scale_err=0.1, parity=tele['parity'], downsample_factor=args.downsample, verbose=False)
            except:
                print('Failed to solve ' + file + ' for ' + tele['name']+'.')
                print('Solving with default settings.')
                tele = telescopes['telescopes']['default']
                wcs_header = ast.solve_from_image(args.path + '/' + file, solve_timeout=300, scale_type='ul', scale_lower=tele['scale_lower'], scale_upper=tele['scale_upper'], scale_units=tele['pixscale_units'], scale_err=0.1, parity=tele['parity'], downsample_factor=args.downsample, verbose=False)
            # Open fits file and update header with wcs info
            hdul = fits.open(args.path + '/' + file, mode='update')
            # remove wcs comments and history
            if not args.wcscomment:
                wcs_header.remove('COMMENT', remove_all=True)
                wcs_header.remove('HISTORY', remove_all=True)

            hdul[0].header.update(wcs_header)
            # Save fits file
            hdul.flush()
            hdul.close()

elif os.path.isfile(args.path):
    if args.path.endswith('.fit') or args.path.endswith('.fits'):
        print('Uploading ' + args.path)
        try:
            wcs_header = ast.solve_from_image(args.path, solve_timeout=30, scale_type='ev', scale_est=tele['pixscale'], scale_units=tele['pixscale_units'], scale_err=0.1, parity=tele['parity'], downsample_factor=args.downsample, verbose=False)
        except:
            print('Failed to solve ' + args.path + ' for ' + tele['name']+'.')
            print('Solving with default settings.')
            tele = telescopes['telescopes']['default']
            wcs_header = ast.solve_from_image(args.path, solve_timeout=300, scale_type='ul', scale_lower=tele['scale_lower'], scale_upper=tele['scale_upper'], scale_units=tele['pixscale_units'], scale_err=0.1, parity=tele['parity'], downsample_factor=args.downsample, verbose=False)
        # Open fits file and update header with wcs info
        hdul = fits.open(args.path, mode='update')

        if not args.wcscomment:
            wcs_header.remove('COMMENT', remove_all=True)
            wcs_header.remove('HISTORY', remove_all=True)

        hdul[0].header.update(wcs_header)
        # Save fits file
        hdul.flush()
        hdul.close()

else:
    print('Invalid path. Please provide a valid path to a folder of fits files or a single fits file.')

end = time.time()
diff = (end - start)/60
print('Time elapsed: ' + str(round(diff,1)) + ' minutes')