This project is no longer maintained. Please see these instead:

 - https://github.com/ryanlovett/sis-cli
 - https://github.com/ryanlovett/grouper-cli


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

Credentials
-----------
sis2calgroups authenticates to various SIS and CalGroups endpoints.
Supply the credentials in a JSON file of the form:
```
{
	"sis_enrollments_id": "...",
	"sis_enrollments_key": "...",
	"sis_classes_id": "...",
	"sis_classes_key": "...",
	"sis_terms_id": "...",
	"sis_terms_key": "...",
	"grouper_user": "...",
	"grouper_pass": "..."
}
```
Request credentials for the SIS Enrollments, Classes, and Terms APIs through
[API Central](https://api-central.berkeley.edu). Request Grouper/CalGroups access through [CalNet](https://calnetweb.berkeley.edu/calnet-technologists/calgroups-integration/calgroups-api-information) via [calnet-admin@berkeley.edu](mailto:calnet-admin@berkeley.edu).
