#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Realize jira methods
"""
from jira import JIRA
import jira.exceptions
from app import config
from app.utils import logging

__all__ = ['JiraTools']
logger = logging.setup()


class JiraTools:
    """
        Implementations of Jira methods
    """

    def __init__(self):
        self.options = {
            'server': config.jira_host, 'verify': False
        }
        # self.jira_connect = JIRA(self.options, basic_auth=(config.jira_user, config.jira_pass))
        self.jira = JIRA(self.options, basic_auth=(config.jira_user, config.jira_pass))

    def jira_issue(self, query):
        """
            Get Jira task information
        """
        try:
            issue = self.jira.issue(query)
            return issue
        except Exception:
            logger.exception('jira_issue')

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
        """
            Moved issue to some other step
            321 - from looking_for_assignee to waiting_release_master
            41 -
            191 -
            241 -
            211 -
            101 -
        """
        try:
            self.jira.transition_issue(jira_issue_id, transition_id)
        except jira.exceptions.JIRAError as err:
            logger.error('transition_issue %s', err)
