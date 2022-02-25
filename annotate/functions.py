import sys
import time

# Packages for direct database access
# %pip install psycopg2
import psycopg2
import json
import requests

# Packages for data and number handling
import numpy as np
import pandas as pd
import math
from urllib.parse import quote

# Packages for calculating current time and extracting ZTF data to VOTable
from astropy.time import Time
from astropy.table import Table, QTable, Column, unique, vstack, hstack, join
from astropy.io.votable import parse_single_table, from_table, writeto
from astropy.io import ascii
from datetime import datetime

# Packages for nearMOC filtering
from mocpy import MOC
import csv

# Package for coordinates
from astropy.coordinates import SkyCoord
from astropy import units as u

# Virtual observatory package
import pyvo as vo

# Package for footprint geometric descriptions
import shapely.geometry as sg
import shapely.ops as so

# Defining function that queries ZTF database
# Returns classified object data as pandas dataframe

def ALERCE_DB_query(classifier='lightcurve', date=datetime.today().strftime("%Y-%m-%d"), novel_objects=True):
    # print('-- Connecting to ALeRCE database...')
    # Connecting to the ZTF database
    url = "https://github.com/alercebroker/usecases/raw/master/alercereaduser_v4.json"
    params = requests.get(url).json()['params']
    conn = psycopg2.connect(
        dbname=params['dbname'],
        user=params['user'],
        host=params['host'],
        password=params['password'])

    # Convert date argument to datetime object
    date = np.asarray(date.split('-'), dtype=int)
    det_date = datetime(*date)

    # Specifying the detection date bounds of the database query
    min_lastmjd = np.floor(Time(det_date, scale='utc').mjd) - 1.0
    max_lastmjd = np.floor(Time(det_date, scale='utc').mjd)

    # Defining classifier name and version for the database query
    classifiers = {'stamp': ["\'stamp_classifier\'", "\'stamp_classifier_1.0.4\'"],
                   'lightcurve': ["\'lc_classifier\'", "\'hierarchical_rf_1.1.0\'"]}
    classifier_name = classifiers[classifier][0]
    classifier_version = classifiers[classifier][1]

    # Main query string
    query='''
    SELECT
        object.oid, object.meanra, object.meandec, object.sigmara,
        object.sigmadec,object.firstmjd, object.lastmjd, object.ndet,
        probability_oid.classifier_name, probability_oid.class_name,
        probability_oid.ranking, probability_oid.probability

    FROM
        object INNER JOIN (
            SELECT
                oid, classifier_name, class_name, ranking, probability
            FROM
                probability
            WHERE
                classifier_name = %s
                AND classifier_version = %s
                AND ranking = 1
        ) AS probability_oid
        ON object.oid = probability_oid.oid

    WHERE
        object.lastmjd >= %s
        AND object.lastmjd <= %s
    ''' % (classifier_name, classifier_version, str(min_lastmjd), str(max_lastmjd))

    # print('-- Running database query...')
    # Run query - outputs as a pd.DataFrame
    dbobjects = pd.read_sql_query(query, conn)

    # Filtering objects based on if novel_objects boolean is true
    lim_ndets = {'stamp': 1, 'lightcurve': 6}
    lim_ndet = lim_ndets[classifier]
    mask = (dbobjects['ndet'] <= lim_ndet)
    apiobjects = dbobjects[mask]
    if (not novel_objects):
        apiobjects = dbobjects

    return apiobjects

# Defining function that filters ZTF objects that lie in the Chandra MOC
# Returns filtered table of ZTF object data
def mocFilter(apiobjects, moc_path):
    # Use object table with only unique OIDs
    unique_df = apiobjects.drop_duplicates(subset=['oid'])

    # Stipulation if object table is empty
    if len(unique_df)==0:
        return unique_df

    # Running mocpy filter
    mocLocation = moc_path
    moc = MOC.from_fits(mocLocation)
    mask_in_moc = moc.contains(unique_df['meanra'] * u.deg, unique_df['meandec'] * u.deg)
    ztfobjects = Table.from_pandas(unique_df[mask_in_moc])

    return ztfobjects

# Defining functions necessary for programmatically scraping CSC2 web application
def urlgenerate(ra, dec, sr):
    url = 'cda.cfa.harvard.edu/cscweb/rest/cone-search-indiv-by-coords.do?json={"selectQualifier":{"selectClause":"all"},"coords":{"ra":%s,"dec":%s,"sr":{"value":"%s","unit":"arcsec"}},"userSuppliedRAandDEC":null}' % (ra, dec, sr)
    encoded_url = quote(url, safe='/?="')
    full_encoded_url = 'http://'+encoded_url
    return(full_encoded_url)

def retrieve_lim_sens(ra_array, dec_array, sr):
    rows = []
    names = []

    try:
        for i in range(len(ra_array)):
            (ra, dec) = (ra_array[i], dec_array[i])
            url = urlgenerate(ra, dec, sr)

            nodes = requests.get(url).json()
            if i==0:
                names = [('csc_%s' % element['name']) for element in nodes['value']['limSenVOTable']['fields']]
            row = nodes['value']['limSenVOTable']['tabledata']
            rows.append(row[0])
    except TypeError as te:
        (ra, dec)=(ra_array, dec_array)
        url = urlgenerate(ra, dec, sr)
        nodes = requests.get(url).json()
        names = [('csc_%s' % element['name']) for element in nodes['value']['limSenVOTable']['fields']]
        row = nodes['value']['limSenVOTable']['tabledata']
        rows.append(row[0])

    limSenTable = Table(rows=rows, names=names)
    return(limSenTable)

# Defining conesearch and tapservice functions for relevant branches of workflow
# Returns astropy table with cone search and tap service results
# As well as numpy array with number of results per ZTF oid
def coneTAPsearch(archive, ztfobjects):
    vo_url = {'CDA': 'https://cda.cfa.harvard.edu/cxcscs/coneSearch',
              'CSC': 'http://cda.cfa.harvard.edu/csc2scs/coneSearch'}[archive]

    maxrad = {'CDA': 50.0 * u.arcmin, 'CSC': 1.0 * u.arcmin}[archive]

    # Defining variables for cone search and initalizing cone search results array
    skycoords = SkyCoord(ra=ztfobjects['meanra']*u.degree,
                         dec=ztfobjects['meandec']*u.degree,
                         frame='icrs')
    cxc_results = []

    # Cone search service URL
    cone = vo.dal.SCSService(vo_url)

    # Running cone search in CSC for each ZTF object
    for i in range(len(ztfobjects)):
        rdata = cone.search(pos=skycoords[i], radius=maxrad).to_table().as_array().data
        results = pd.DataFrame(data=rdata)
        oid = pd.DataFrame(data=np.full(len(results), ztfobjects['oid'][i]))
        results['oid']=oid

        if i == 0:
            cxc_results = results
            continue

        cxc_results = pd.concat([cxc_results, results])

    field_name = {'CDA': 'obs_id', 'CSC': 'name'}[archive]
    cfield_name = {'CDA': 'obsid', 'CSC': field_name}[archive]
    tap_url = {'CDA': "https://cda.cfa.harvard.edu/cxctap/",
               'CSC': "http://cda.cfa.harvard.edu/csc2tap/"}[archive]

    # Stipulation if there are no cone search results for any objects:
    # Return empty arrays and end method
    if len(cxc_results)==0:
        return([],[])

    # Defining variables for tapservice query
    ## Taking names of retrieved CXC obsIDs or source names to pass through query
    #obsids = set(cxc_results[cfield_name].str.decode("utf-8"))
    obsids = set(cxc_results[cfield_name])
    tobsids = tuple(obsids)
    query_str = 'IN {}'.format(tobsids)

    # Stipulation if there is only one obsID/source name in the results table
    if len(cxc_results)==1:
        tobsids=str(tobsids[0])
        query_str = "= \'{}\'".format(tobsids)

    query_CDA = '''
    SELECT
        o.obs_id, o.obs_creation_date, o.s_ra, o.s_dec, o.s_region
    FROM
        ivoa.ObsCore AS o
    WHERE
        o.dataproduct_type = 'event' AND o.obs_id {}
    '''.format(query_str)

    query_CSC = '''
    SELECT
        m.name, m.ra, m.dec,
        m.err_ellipse_r0, m.err_ellipse_r1, m.err_ellipse_ang,
        m.significance, m.likelihood,
        m.flux_aper_b, m.flux_aper_lolim_b, m.flux_aper_hilim_b,
        m.flux_aper_w, m.flux_aper_lolim_w, m.flux_aper_hilim_w,
        m.conf_flag, m.dither_warning_flag, m.extent_flag, m.pileup_flag,
        m.sat_src_flag, m.streak_src_flag, m.var_flag,
        m.hard_hm, m.hard_hm_lolim, m.hard_hm_hilim,
        m.hard_hs, m.hard_hs_lolim, m.hard_hs_hilim,
        m.hard_ms, m.hard_ms_lolim, m.hard_ms_hilim,
        m.var_intra_index_b, m.var_intra_prob_b,
        m.var_intra_index_w, m.var_intra_prob_w,
        m.var_inter_index_b, m.var_inter_prob_b,
        m.var_inter_index_w, m.var_inter_prob_w,
        m.acis_num, m.hrc_num, m.acis_time, m.hrc_time
    FROM
        csc2.master_source AS m
    WHERE
        m.name {}
    '''.format(query_str)

    query = {'CDA': query_CDA, 'CSC': query_CSC}[archive]

    # Tap service URL connection
    tapservice = vo.dal.TAPService(tap_url)

    # Run tapservice query
    tapresult = tapservice.search(query)

    # Formatting tapservice result table, getting rid of duplicate entries
    tresult = tapresult.to_table()
    tresult = unique(tresult, keys=field_name)

    # Formatting cone search result array to combine with tapservice result table
    cresult = Table.from_pandas(cxc_results)
    cresult[field_name]=cresult[cfield_name].astype(object)
    if archive == 'CDA':
        cresult.remove_column(cfield_name)

    ## Finding overlapping observations/sources for properly combining two result tables
    shared_obs = [o for o in tresult[field_name] if o in cresult[field_name]]
    cresult.add_index(field_name)
    cresult = Table(cresult.loc[shared_obs])

    ## Adding extra rows to tapservice query table if necessary, as some ZTF oids will have the same cone search match
    if len(tresult) > 1:
        cresult.sort(field_name)
        tresult.sort(field_name)
        cresult_byname = cresult.group_by(field_name)
        n_matches = [len(g) for g in cresult_byname.groups]
        tresult = Table(np.repeat(tresult, n_matches))

    # Join cone and tapservice result tables
    colkeys = [field_name]
    if len(tresult) > 1:
        colkeys = [e for e in cresult.colnames if (e in tresult.colnames and (np.sort(tresult[e])==np.sort(cresult[e])).all())]

    cresult.remove_columns(colkeys)
    tcresults = hstack([tresult, cresult], join_type='exact')

    # Save array with number of results from each ZTF oid
    tcresults_byoid = tcresults.group_by('oid')
    n_results = [len(g) for g in tcresults_byoid.groups]

    return (tcresults, n_results)

# Function that returns astropy table with ZTF object info and CXC info combined
def ZTF_CXC_xmatch(archive, ztfobjects, tcresults, n_results):

    # Filtering ztfobjects with xmatch results
    tcresults_byoid = tcresults.group_by('oid')
    keys = tcresults_byoid.groups.keys['oid'].data
    ztfobjects.add_index('oid')
    maskedztf = Table(ztfobjects.loc[keys])

    # Stipulation if there is only one ZTF object that's been matched with CXC data
    if len(keys)==1:
        maskedztf = Table(np.repeat(maskedztf, n_results[0]))
        n_results = np.repeat(n_results, n_results[0])

    maskedztf.add_column(n_results, name='n_results')

    # Initializing new data columns for tap service and cone search results
    prefix = {'CDA':'cda_%s', 'CSC':'csc_%s'}[archive]
    for colname in tcresults.colnames:
        maskedztf[prefix%(colname)] = np.full(len(maskedztf), None)

    # Formatting filtered ztf object array
    mztf = maskedztf.as_array()
    ztf_fr = []

    if len(keys) > 1:
        # Adding extra rows, according to the number of cone search results each ZTF object has
        ztf_fr = mztf
        ztf_nres = n_results[n_results != 0]
        ztf_fr = Table(np.repeat(ztf_fr,n_results))

    else:
        ztf_fr = Table(mztf)

    # Sort both ztfobjects table and tap service/cone search results table by ZTF oid
    # so that we can easily assign columns
    if len(tcresults) > 1:
        ztf_fr.sort('oid')
        tcresults.sort('oid')

    # Filling new data columns in ztfobjects table
    for colname in tcresults.colnames:
        ztf_fr[prefix%(colname)] = tcresults[colname]

    ztf_fr.remove_column(prefix%('oid'))
    return ztf_fr

# Defining function that filters out ZTF observations that are in the Chandra footprint
# Returns astropy table of filtered through ZTF obs
def ZTF_in_footprint(ztfobs):
    # Initializing column for boolean that marks whether a ZTF object is in the chandra footprint
    ztfobs['in_poly']=np.full(len(ztfobs), None)
    ztf_in_poly=[]

    # Defining different tables for ztf objects with cone search matches in/out of footprint
    cxc_observed_statuses = ['archived', 'observed']
    mask = np.in1d(ztfobs['cda_status'].astype(str),cxc_observed_statuses)
    observedztf = ztfobs[mask]

    for i in range(len(observedztf)):
        region = observedztf['cda_s_region'][i]
        if (type(region)==type(None)):
            ztf_in_poly.append(None)
            continue

        # Constructing footprint region with shapely polygon
        ## region = region.decode().replace(")","").split('POLYGON')
        region = region.replace(")","").split('POLYGON')
        polygon_coords = [np.stack((a.split()[::2], a.split()[1::2]), axis=-1).astype(float) for a in region[1:]]

        polygons = [sg.Polygon(c) for c in polygon_coords]

        # Define ZTF object position as shapely point
        point = sg.Point(np.asarray([observedztf['meanra'][i],observedztf['meandec'][i]]).astype(float))

        # Use shapely within() method to determine if point is in polygon
        in_poly = set([point.within(poly) for poly in polygons])
        ztf_in_poly.append((True in in_poly))

    # Fill in_poly table column with the constructed in_poly array
    ztfobs['in_poly'][mask]=np.asarray(ztf_in_poly)

    ztf_infootprint = ztfobs[ztfobs['in_poly'] == True]

    return ztf_infootprint

def retrieve_ZTF_CXC_data(archive, ztfobjects):
    # Finding and saving limiting sensitivities in CSC for each ZTF object
    ## if archive=='CSC':
    limSenTable = retrieve_lim_sens(ztfobjects['meanra'], ztfobjects['meandec'], 20)
    ztfobjects = hstack([ztfobjects, limSenTable])

    # Run cone search and tapservice query
    (tcresults, n_results)=coneTAPsearch(archive, ztfobjects)

    # Create table with full ztf xmatch information
    ztfcxc = []
    if len(tcresults)==0:
        return Table(names=tuple(ztfobjects.columns))
        ## return ztfcxc

    else:
        ztfcxc = ZTF_CXC_xmatch(archive, ztfobjects, tcresults, n_results)

    if archive=='CSC':
        return ztfcxc
    elif archive=='CDA':
        return ZTF_in_footprint(ztfcxc)

# Defining a function that allows you to export an astropy data table
# into a VOTable
def export_data(datatable, filename):
    votable = from_table(datatable)
    writeto(votable, filename)

# Defining a function that allows you append astropy table rows to an
# existing VOTable
def append_data(data, template_path, output_path):
    old_table = parse_single_table(template_path).to_table()
    new_table = vstack([template_path, data])
    votable = from_table(new_table)

    writeto(votable, output_path)
