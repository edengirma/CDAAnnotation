from .functions import ALERCE_DB_query, mocFilter, retrieve_ZTF_CXC_data, append_data, export_data
from .config import log_path, moc_path, cda_output_path, csc_output_path
import logging

# Configure logger
logging.basicConfig(filename=log_path, encoding='utf-8', format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p', level=logging.DEBUG)

# Main program run method
def run(archive='CDA', classifier='lightcurve', days_ago=2.0, novel_objects=True):
    try:
        logging.info('######## PROGRAM RUN START ########')
        logging.info(f'######## ARCHIVE={archive} CLASSIFIER={classifier} DAYS_AGO={days_ago} NOVEL_OBJECTS={novel_objects} ########')
        logging.info('Querying ALeRCE broker...')
        apiobjects = ALERCE_DB_query(classifier, days_ago, novel_objects)
        logging.info(f'Total ZTF objects retrieved: {len(apiobjects)}')
        if len(apiobjects)==0:
            logging.info('Done; no ZTF objects retrieved from ALeRCE.')
            logging.info('######## PROGRAM RUN END ########')
            return

        logging.info('Filtering table with Chandra MOC...')
        ztfobjects = mocFilter(apiobjects, moc_path)
        logging.info(f'Total ZTF objects passed through filter: {len(ztfobjects)}')
        if len(ztfobjects)==0:
            logging.info('Done; no ZTF object positions lie in Chandra MOC.')
            logging.info('######## PROGRAM RUN END ########')
            return

        logging.info('Retrieving CXC data for ZTF objects...')
        ztf_fullxmatch = retrieve_ZTF_CXC_data(archive, ztfobjects)
        logging.info(f'Total Chandra xmatches retrieved:{len(ztf_fullxmatch)}')

        logging.info('Outputting data...')
        output_path = {'CDA': cda_output_path,
                       'CSC': csc_output_path}[archive]
        append_data(ztf_fullxmatch, output_path)

        # print('Exporting data table')
        # export_data(ztf_fullxmatch, output_path)
        logging.info('Done; ZTF data outputted.')
        logging.info('######## PROGRAM RUN END ########')

    except Exception as err:
        logging.error(f"Unexpected {err=}, {type(err)=}")
