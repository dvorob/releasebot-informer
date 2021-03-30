#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Realize jira methods
"""
from enum import Enum
from jira import JIRA
from utils import logging
import config
import jira.exceptions
import re

__all__ = ['JiraConnection']
logger = logging.setup()

class JiraTransitions(Enum):
    TODO_WAIT = '321'
    WAIT_TODO = '41'
    TODO_PARTIAL = '191'
    PARTIAL_CONFIRM = '211'
    PARTIAL_RESOLVED = '241'
    PARTIAL_WAIT = '321'
    CONFIRM_FULL = '101'
    CONFIRM_WAIT = '321'
    FULL_RESOLVED = '241'
    FULL_WAIT = '321'

class JiraConnection:

    def __init__(self):
        self.options = {
            'server': config.jira_host, 'verify': False
        }
        self.jira = JIRA(self.options, basic_auth=(config.jira_user, config.jira_pass))

    def issue(self, issue: str) -> jira.Issue:
        """
            Get Jira task information
        """
        try:
            issue = self.jira.issue(issue)
            return issue
        except Exception as e:
            logger.exception('jira issue %s', e)

    def watchers(self, issue: str):
        """
            Get Jira watchers information
        """
        try:
            watchers = self.jira.watchers(issue)
            return watchers
        except Exception as e:
            logger.exception('jira issue %s', e)

    def jira_search(self, query):
        """
            Get list of Jira tasks
        """
        issues = self.jira.search_issues(query, maxResults=1000)
        return issues

    def add_comment(self, jira_issue_id, comment):
        """
            Add comment to Jira task
            :return:
        """
        self.jira.add_comment(jira_issue_id, comment)

    def assign_issue(self, jira_issue_id, for_whom_assign):
        """
            Assign task to for_whom_assign
            :param jira_issue_id - ADMSYS-12345
            :param for_whom_assign - None, Xerxes, anybody else
        """
        self.jira.assign_issue(jira_issue_id, for_whom_assign)

    def transition_issue(self, jira_issue_id, transition_id):
        try:
            self.jira.transition_issue(jira_issue_id, transition_id)
        except jira.exceptions.JIRAError as err:
            logger.error('transition_issue %s', err)

    def transition_issue_with_resolution(self, jira_issue_id, transition_id, resolution):
        try:
            self.jira.transition_issue(jira_issue_id, transition_id, resolution=resolution)
        except jira.exceptions.JIRAError as err:
            logger.error('transition_issue %s', err)

#########################################################################################
#        Custom functions
#########################################################################################

def jira_get_approvers_list(issue_key: str) -> list:
    """
       Отобрать список акков согласующих из jira_таски и обрезать от них email, оставив только account_name
    """
    try:
        issue = JiraConnection().issue(issue_key)
        approvers = [item.name for item in issue.fields.customfield_15408]
        logger.info('-- JIRA GET APPROVERS LIST %s %s', issue, approvers)
        return approvers
    except Exception as e:
        logger.exception('Exception in JIRA GET APPROVERS LIST %s', e)


def jira_get_watchers_list(issue_key: str) -> list:
    """
       Отобрать список акков согласующих из jira_таски и обрезать от них email, оставив только account_name
    """
    try:
        watcherList = JiraConnection().watchers(issue_key)
        watchers = [w.name for w in watcherList.watchers]
        logger.info('-- JIRA GET WATCHERS LIST %s %s', issue_key, watchers)
        return watchers
    except Exception as e:
        logger.exception('Exception in JIRA GET WATCHERS LIST %s', e)
