import logging
import sys

from sis2calgroups import grouper

logging.basicConfig(stream=sys.stdout, level=logging.WARNING)
logger = logging.getLogger('calgroups')

def child_id(calgroup, child):
    '''Given a:base:group for a course, return a:base:group:group-child.'''
    els = calgroup.split(':')
    return ':'.join(els + [els[-1] + '-' + str(child)])
    
def create_folders(grouper_auth, base_group, term_id, course_name, subgroups):
    '''
    '''
    # term ~ {base_group}:stat-classes-2188
    term_group = child_id(base_group, term_id)
    # course_group ~ {term_group}:stat-classes-2188-stat-243'''
    course_group = child_id(term_group, course_name)
    logger.info(course_group)

    # create the folder for the term
    out = grouper.create_stem(grouper_auth, term_group, term_id)
    logger.info(f"creating stem {term_id}")
    # create the folder for the course
    out = grouper.create_stem(grouper_auth, course_group, course_name)
    logger.info(f"creating stem {course_name}")
    # create the groups for the course
    for subgroup in subgroups:
        group = child_id(course_group, subgroup)
        logger.info(f"creating group {group}")
        out = grouper.create_group(grouper_auth, group, subgroup)
    return course_group

def populate_group(grouper_auth, course_group, subgroup, uids):
	num = len(uids)
	group = child_id(course_group, subgroup)
	logger.info(f"setting {num} users in {group}")
	grouper.replace_users(grouper_auth, group, uids)

def create_all_group(grouper_auth, course_group, group_name):
	'''Create an "all" group that contains all students, instructors,
	   admins, etc. We specify a friendly name for the name since Google Groups
       and perhaps AD will use it.'''
	group_id = child_id(course_group, 'all')
	grouper.create_group(grouper_auth, group_id, group_name):

	# put other subgroups into this one
	uids = get_subgroup_uids(grouper_auth, course_group)
	grouper.replace_users(grouper_auth, group, uids)
