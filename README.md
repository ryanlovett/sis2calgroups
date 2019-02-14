sis2calgroups
=============
Create CalGroups based on enrollment and instructor data in SIS.

Requires SIS and CalGroups API credentials.

```
usage: sis2calgroups [-h] -b BASE_GROUP [-t SIS_TERM_ID] -s SUBJECT_AREA -c
                     CATALOG_NUMBER [-C CREDENTIALS] [-v] [-d] [-S SUBGROUPS]
                     [-n]

Create CalGroups from SIS data.

optional arguments:
  -h, --help         show this help message and exit
  -b BASE_GROUP      Base Grouper group, e.g. edu:college:dept:classes.
  -t SIS_TERM_ID     SIS term id or position, e.g. 2192. Default: Current
  -s SUBJECT_AREA    SIS subject area, e.g. ASTRON.
  -c CATALOG_NUMBER  SIS course catalog number, 128.
  -C CREDENTIALS     Credentials file.
  -v                 Be verbose.
  -d                 Debug.
  -S SUBGROUPS       Limit operation to specific subgroups.
  -n                 Dry run. Print enrollments without updating CalGroups.
```

Example
-------
Create a folder and group structure in CalGroups for the current term's Driver's Ed 101:

`sis2calgroups -b edu:berkeley:org:myorg:myorgs_classes -s driversed -c 101`
