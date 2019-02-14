#!/usr/bin/python3
# vim: set et sw=4 ts=4:

# Given a base folder within CalGroups, and a course specified by an academic
# term, department, and course number:
#  - fetch the course roster from sis
#  - create a folder structure and groups in CalGroups under the base folder
#  - replace members of the calgroup roster with those from the sis

# Requires SIS and CalGroups API credentials.

# CalGroups API
# https://calnetweb.berkeley.edu/calnet-technologists/calgroups-integration/calgroups-api-information

import argparse
import json
import logging
import os
import sys

from sis2calgroups import calgroups, grouper, sis

# We use f-strings from python >= 3.6.
assert sys.version_info >= (3, 6)

# logging
logging.basicConfig(stream=sys.stdout, level=logging.WARNING)
logger = logging.getLogger('sis2calgroups')
#logger.setLevel(logging.DEBUG)

secret_keys = [
    'sis_enrollments_id', 'sis_enrollments_key',
        'sis_classes_id', 'sis_classes_key',
          'sis_terms_id', 'sis_terms_key',
          'grouper_user', 'grouper_pass'
]

subgroups = ['enrolled', 'waitlisted', 'instructors', 'gsis']
subgroup_statuses = {
    'enrolled': 'E',
    'waitlisted': 'W',
    'dropped': 'D'
}

def has_all_keys(d, keys):
    return all (k in d for k in keys)

def read_json_data(filename, required_keys):
    '''Read and validate data from a json file.'''
    if not os.path.exists(filename):
        raise Exception(f"No such file: {filename}")
    data = json.loads(open(filename).read())
    # check that we've got all of our required keys
    if not has_all_keys(data, required_keys):
        missing = set(required_keys) - set(data.keys())
        s = f"Missing parameters in {filename}: {missing}"
        raise Exception(s)
    return data

def read_credentials(filename, required_keys=secret_keys):
    '''Read credentials from {filename}. Returns a dict.'''
    return read_json_data(filename, required_keys)

def course_name(subject_area, catalog_number):
    '''Return a conventionally formatted course name, e.g. "stat-123".'''
    return f'{subject_area}-{catalog_number}'

def sis2calgroups(base_group, sis_term_id, subject_area, catalog_number,
    credentials, subgroups, dryrun=False):

    course = course_name(subject_area, catalog_number)

    # Convert temporal position (current, next, previous) to a term id
    if sis_term_id is None or sis_term_id.isalpha():
        sis_term_id = sis.get_term_id(
            credentials['sis_terms_id'], credentials['sis_terms_key'],
            sis_term_id
        )

    if not dryrun:
        grouper_auth = grouper.auth(
            credentials['grouper_user'], credentials['grouper_pass']
        )
        course_group = calgroups.create_folders(grouper_auth,
            base_group, sis_term_id, course, subgroups)

    # fetch student enrollments
    student_subgroups = set(['enrolled', 'waitlisted', 'dropped']) & set(subgroups)
    if len(student_subgroups) > 0:
        enrollments = sis.get_enrollments(
            credentials['sis_enrollments_id'],
            credentials['sis_enrollments_key'],
            sis_term_id, subject_area, catalog_number
        )

    # filter the student uids by enrollment status
    uids = {}
    for student_subgroup in student_subgroups:
        subgroup_status = subgroup_statuses[student_subgroup]
        uids[student_subgroup] = sis.get_enrollment_uids(
            sis.filter_enrollment_status(enrollments, subgroup_status))

    # fetch section data; includes primary (usually LEC) and others (i.e. LAB)
    instructor_subgroups = set(['instructors', 'gsis']) & set(subgroups)
    if len(instructor_subgroups) > 0:
        sections = sis.get_sections(
            credentials['sis_classes_id'],
            credentials['sis_classes_key'],
            sis_term_id, subject_area, catalog_number)
        # filter the uids by instructor or gsi
        # in sis, instructors of primary sections are the instructors.
        # the instructors of the other sections are the gsis.
        for section in sections:
            section_uids = sis.filter_section_instructors(section)
            if sis.section_is_primary(section):
                uids['instructors'] = section_uids
            else:
                uids['gsis'] = section_uids

    if dryrun:
        for subgroup in subgroups:
            print(f'_{subgroup}')
            for uid in uids[subgroup]: print(uid)
    else:
        calgroups.populate_groups(grouper_auth, course_group, uids, subgroups)

def valid_term(string):
    valid_terms = ['Current', 'Next', 'Previous']
    if string.isdigit() or string in valid_terms:
        return string
    msg = f"{string} is not a term id or one of {valid_terms}"
    raise argparse.ArgumentTypeError(msg)

def csv_list(string):
   return string.split(',')

## main
def main():
    parser = argparse.ArgumentParser(
        description="Create CalGroups from SIS data.")
    parser.add_argument('-b', dest='base_group', required=True,
        help='Base Grouper group, e.g. edu:college:dept:classes.')
    parser.add_argument('-t', dest='sis_term_id', type=valid_term,
        default='Current',
        help='SIS term id or position, e.g. 2192. Default: Current')
    parser.add_argument('-s', dest='subject_area', required=True,
        help='SIS subject area, e.g. ASTRON.')
    parser.add_argument('-c', dest='catalog_number', required=True,
        help='SIS course catalog number, 128.')
    parser.add_argument('-C', dest='credentials',
        default='/root/.sis2calgroups.json', help='Credentials file.')
    parser.add_argument('-v', dest='verbose', action='store_true',
        help='Be verbose.')
    parser.add_argument('-d', dest='debug', action='store_true',
        help='Debug.')
    parser.add_argument('-S', dest='subgroups', default=','.join(subgroups),
        type=csv_list, help='Limit operation to specific subgroups.')
    parser.add_argument('-n', dest='dryrun', action='store_true',
        help='Dry run. Print enrollments without updating CalGroups.')
    args = parser.parse_args()
    
    if args.verbose:
        logger.setLevel(logging.INFO)
    elif args.debug:
        logger.setLevel(logging.DEBUG)
    
    # read credentials from credentials file
    credentials = read_credentials(args.credentials)
    
    sis2calgroups(args.base_group, args.sis_term_id, args.subject_area.lower(),
        args.catalog_number, credentials, args.subgroups, args.dryrun)
