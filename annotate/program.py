from .functions import ALERCE_DB_query, mocFilter, retrieve_ZTF_CXC_data, append_data, export_data
from .config import log_path, moc_path, cda_output_path, csc_output_path
import logging
from datetime import datetime

# Configure logger
FORMAT='%(asctime)s - %(levelname)s - %(message)s'
DATEFMT='%Y-%m-%d %H:%M:%S'
logging.basicConfig(filename=log_path, format=FORMAT, datefmt=DATEFMT, level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Main program run method
def run(archive='CDA', classifier='lightcurve', date=datetime.today().strftime("%Y-%m-%d"), novel_objects=True):
    try:
        logger.info('######## PROGRAM RUN START ########')
        logger.info(f'######## ARCHIVE={archive} CLASSIFIER={classifier} DATE={date} NOVEL_OBJECTS={novel_objects} ########')
        logger.info('Querying ALeRCE broker...')
        apiobjects = ALERCE_DB_query(classifier, date, novel_objects)
        logger.info(f'Total ZTF objects retrieved: {len(apiobjects)}')
        if len(apiobjects)==0:
            logger.info('Done; no ZTF objects retrieved from ALeRCE.')
            logger.info('######## PROGRAM RUN END ########')
            return

        logger.info('Filtering table with Chandra MOC...')
        ztfobjects = mocFilter(apiobjects, moc_path)
        logger.info(f'Total ZTF objects passed through filter: {len(ztfobjects)}')
        if len(ztfobjects)==0:
            logger.info('Done; no ZTF object positions lie in Chandra MOC.')
            logger.info('######## PROGRAM RUN END ########')
            return

        logger.info('Retrieving CXC data for ZTF objects...')
        ztf_fullxmatch = retrieve_ZTF_CXC_data(archive, ztfobjects)
        logger.info(f'Total Chandra xmatches retrieved: {len(ztf_fullxmatch)}')

        if len(ztf_fullxmatch)==0:
            logger.info('Done; no CXC data retrieved for ZTF objects.')
            logger.info('######## PROGRAM RUN END ########')
            return

        logger.info('Outputting data...')
        output_path = {'CDA': cda_output_path,
                       'CSC': csc_output_path}[archive]+date+'.xml'
        export_data(ztf_fullxmatch, output_path)

        logger.info('Done; ZTF data outputted.')
        logger.info('######## PROGRAM RUN END ########')

    except Exception as err:
        logger.exception(err)
        logger.info('######## PROGRAM RUN END ########')
