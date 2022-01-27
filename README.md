# CDAAnnotation
Annotation project connecting the Chandra Data Archive &amp; Source Catalog with [ALeRCE](http://alerce.science/).

## Dependencies
- astropy (>= 5.0)
- datetime (>= 4.3)
- mocpy (>= 0.10.0)
- numpy (>= 1.21.2)
- pandas (>= 1.3.5)
- psycopg2 (>= 2.8.6)
- python (>= 3.9.7)
- pyvo (>= 1.2.1)
- requests (>= 2.27.1)
- shapely (>= 1.7.1)

## Usage
```
python -m annotate [-h] [--a ARCHIVE] [--c CLASSIFER]
                   [--d DAYS_AGO] [--n NOVEL_OBJECTS]
```

## Optional arguments:
```
  -h, --help         Show this help message and exit
  --a ARCHIVE        Workflow branch - CDA or CSC (default: CDA)
  --c CLASSIFER      ZTF Classifier - stamp or lightcurve (default:
                     lightcurve)
  --d DAYS_AGO       Amount of days ago the ALerCE database is queried
                     (default: 2.0)
  --n NOVEL_OBJECTS  Whether only newly detected objects are retrieved from
                     ALeRCE - 1=True, 0=False (default: 1)
```
