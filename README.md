# CDAAnnotation
Annotation project connecting the Chandra Data Archive &amp; Source Catalog with [ALeRCE](http://alerce.science/).

## Optional arguments:
  -h, --help         Show this help message and exit
  --a ARCHIVE        Workflow branch - CDA or CSC (default: CDA)
  --c CLASSIFER      ZTF Classifier - stamp or lightcurve (default:
                     lightcurve)
  --d DAYS_AGO       Amount of days ago the ALerCE database is queried
                     (default: 2.0)
  --n NOVEL_OBJECTS  Whether only newly detected objects are retrieved from
                     ALeRCE - 1=True, 0=False (default: 1)
