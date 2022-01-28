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
After changing your working directory to where the repository folder has been saved (`cd /Path/To/CDAAnnotation`), run the following command:
```
python -m annotate [-h] [--a ARCHIVE] [--c CLASSIFER]
                   [--d DATE] [--n NOVEL_OBJECTS]
```

## Optional arguments:
```
  -h, --help         Show this help message and exit
  --a ARCHIVE        Workflow branch - CDA or CSC (default: CDA)
  --c CLASSIFER      ZTF Classifier - stamp or lightcurve (default:
                     lightcurve)
  --d DATE           Date of detection that ALeRCE database is queried. Formatted as YYYY-MM-DD
                     (default: Current date)
  --n NOVEL_OBJECTS  Whether only newly detected objects are retrieved from
                     ALeRCE - 1=True, 0=False (default: 1)
```
