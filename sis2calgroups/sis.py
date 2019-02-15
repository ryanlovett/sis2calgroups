# vim:set et sw=4 ts=4:
import logging
import sys

import requests

# logging
logging.basicConfig(stream=sys.stdout, level=logging.WARNING)
logger = logging.getLogger(__name__)

# Various SIS endpoints
enrollments_uri = "https://apis.berkeley.edu/sis/v2/enrollments"
descriptors_uri = enrollments_uri + '/terms/{}/classes/sections/descriptors'
sections_uri = enrollments_uri + "/terms/{}/classes/sections/{}"
classes_sections_uri = "https://apis.berkeley.edu/sis/v1/classes/sections"
terms_uri = "https://apis.berkeley.edu/sis/v1/terms"

section_codes = ['LEC', 'SES', 'WBL', 'LAB']

def filter_lectures(sections, relevant_codes=section_codes):
    '''
    Given a list of SIS sections:
       [{'code': '32227', 'description': '2019 Spring ASTRON 128 001 LAB 001'}]
    return only the section codes which are lectures.
    '''
    codes = []
    for section in sections:
        desc_words = set(section['description'].split())
        if len(set(desc_words) & set(relevant_codes)) > 0:
            codes.append(section['code'])
    return codes

def get_items(uri, params, headers, item_type):
    '''Recursively get a list of items (enrollments, ) from the SIS.'''
    #logger.debug("get_items: {}".format(uri))
    #logger.debug("  params: {}".format(params))
    #logger.debug("  headers: {}".format(headers))
    r = requests.get(uri, params=params, headers=headers)
    if r.status_code == 404:
        logger.debug('NO MORE {}'.format(item_type))
        return []
    else:
        pass
        logger.debug('FOUND {}'.format(item_type))
    data = r.json()
    # Return if there is no response (e.g. 404)
    if 'response' not in data['apiResponse']:
        logger.debug('404 No response')
        return[]
    # Return if the UID has no items
    elif item_type not in data['apiResponse']['response']:
        logger.debug('No {}'.format(item_type))
        return []
    # Get this page's items
    items = data['apiResponse']['response'][item_type]
    # If we are not paginated, just return the items
    if 'page-number' not in params:
        return items
    # Get the next page's items
    params['page-number'] += 1
    items += get_items(uri, params, headers, item_type)
    logger.debug('num {}: {}'.format(item_type, len(items)))
    #logger.debug(items)
    return items

def get_term_id(app_id, app_key, position='Current'):
    '''Given a temporal position of Current, Previous, or Next, return
       the corresponding term's ID.'''
    headers = {
        "Accept": "application/json",
        "app_id": app_id, "app_key": app_key
    }
    params = { "temporal-position": position }
    uri = terms_uri
    terms = get_items(uri, params, headers, 'terms')
    return terms[0]['id']

def normalize_term_id(app_id, app_key, sis_term_id):
    '''Convert temporal position (current, next, previous) to a numeric term id,
       or passthrough a numeric term id.'''
    if sis_term_id is None or sis_term_id.isalpha():
        sis_term_id = get_term_id(app_id, app_key, sis_term_id)
    return sis_term_id

def get_lecture_section_ids(e_id, e_key, term_id, subject_area, catalog_number):
    '''
      Given a term, subject, and course number, return the lecture section ids.
      We only care about the lecture enrollments since they contain a superset
      of the enrollments of all other section types (lab, dis).
    '''
    headers = { "Accept": "application/json", "app_id": e_id, "app_key": e_key }
    params = {
        'page-number': 1,
        "subject-area-code": subject_area,
        "catalog-number": catalog_number,
    }
    # Retrieve the sections associated with the course which includes
    # both lecture and sections.
    uri = descriptors_uri.format(term_id)
    sections = get_items(uri, params, headers, 'fieldValues')
    return filter_lectures(sections)

def get_enrollments(e_id, e_key, term_id, subject_area, catalog_number):
    '''Gets a course's enrollments from the SIS.'''
    logger.debug("get_enrollments: {}".format(catalog_number))

    # get the lectures
    lecture_codes = get_lecture_section_ids(e_id, e_key, term_id,
                        subject_area, catalog_number)

    headers = { "Accept": "application/json", "app_id": e_id, "app_key": e_key }
    params = {
        "page-number": 1,
        "page-size": 100,
    }
    # get the enrollments in each lecture
    enrollments = []
    for lecture_code in lecture_codes:
        uri = sections_uri.format(term_id, lecture_code)
        enrollments += get_items(uri, params, headers,
                            'classSectionEnrollments')
    logger.info('{} {}'.format(catalog_number, len(enrollments)))
    return enrollments


def filter_section_instructors(section):
    '''Extract the campus-uid of instructors from a section.'''
    uids = set()
    if 'meetings' not in section: return uids
    meetings = section['meetings']
    for meeting in meetings:
        if 'assignedInstructors' not in meeting: continue
        instructors = meeting['assignedInstructors']
        for instructor in instructors:
            if 'identifiers' not in instructor['instructor']: continue
            identifiers = instructor['instructor']['identifiers']
            for identifier in identifiers:
                # {'disclose': True, 'id': '1234', 'type': 'campus-uid'}
                if 'disclose' not in identifier: continue
                if not identifier['disclose']: continue
                if identifier['type'] != 'campus-uid': continue
                uids.add(identifier['id'])
    return uids

def get_sections(c_id, c_key, term_id, subject_area, catalog_number):
    '''Given a term, subject, and SIS catalog number, returns a list of
       instructors and a list of GSIs.'''
    logger.info(f'{term_id} {subject_area} {catalog_number}')
    headers = { "Accept": "application/json", "app_id": c_id, "app_key": c_key }
    params = {
        "subject-area-code": subject_area.upper(),
        "catalog-number": catalog_number.upper(),
        "term-id": term_id,
        "page-size": 400,
        "page-number": 1
    }

    # Retrieve the sections associated with the course which includes
    # both lecture and sections.
    logger.debug(f'{classes_sections_uri}')
    logger.debug(f'{params}')
    logger.debug(f'{headers}')
    sections = get_items(classes_sections_uri, params, headers, 'classSections')
    return sections

def section_is_primary(section):
    return section['association']['primary']

def get_enrollment_uids(enrollments):
    '''Given an SIS enrollment, return the student's campus UID.'''
    def campus_uid(enrollment):
        for identifier in enrollment['student']['identifiers']:
            if identifier['type'] == 'campus-uid':
                return identifier['id']
    return list(map(lambda x: campus_uid(x), enrollments))

def get_enrollment_emails(enrollments):
    '''Given an SIS enrollment, return the student's campus email.'''
    def campus_email(enrollment):
        emails = {}
        for email in enrollment['student'].get('emails', []):
            if email['type']['code'] == 'CAMP': return email['emailAddress']
        return None
    return list(map(lambda x: campus_email(x), enrollments))

def enrollment_status(enrollment):
    '''Returns 'E', 'W', or 'D'.'''
    return str(enrollment['enrollmentStatus']['status']['code'])

def filter_enrollment_status(enrollments, status):
    return list(filter(lambda x: enrollment_status(x) == status, enrollments))
