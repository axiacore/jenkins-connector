#! /usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Igor Támara MIT License
import urllib2
import base64
import json

from pyquery import PyQuery as pyq


class JenkinsBuild:
    def __init__(self, base64string, base_dict):
        self.name = base_dict['number']
        self.url = base_dict['url']
        self.base64string = base64string

    def get_info(self):
        u"""Gets information about the build
        """
        request = urllib2.Request('{0}/api/json'.format(self.url))
        if self.base64string:
            request.add_header('Authorization', 'Basic {0}'.format(
                self.base64string
            ))
        result = urllib2.urlopen(request)
        self.result = json.loads(result.read())
        self.timestamp = self.result[u'timestamp']
        self.commits = len(self.result[u'changeSet'][u'items'])


class JenkinsJob:
    def __init__(self, base64string, base_dict):
        self.name = base_dict['name']
        self.url = base_dict['url']
        self.base64string = base64string

    def get_info(self):
        u"""Gets information for the job and the latest build
        """
        request = urllib2.Request("{0}/api/json".format(self.url))
        if self.base64string:
            request.add_header("Authorization", "Basic %s" % self.base64string)
        result = urllib2.urlopen(request)
        self.result = json.loads(result.read())
        self.successfull_build = JenkinsBuild(
            self.base64string,
            self.result[u'lastSuccessfulBuild']
        )
        self.successfull_build.get_info()

    def get_violations(self, v_types=['jslint', 'pep8', 'pylint']):
        """Returns the violations, receives a dictionary with the type of
        violations to be gathered, by default it is
        ['jslint', 'pep8', 'pylint']
        """
        if not hasattr(self, 'result'):
            self.get_info()
        request = urllib2.Request("{0}/violations/".format(self.url))
        retval = {'total': 0}
        if self.base64string:
            request.add_header("Authorization", "Basic %s" % self.base64string)
        try:
            result = urllib2.urlopen(request)
        except urllib2.HTTPError:
            return retval
        res = pyq(result.read())
        for typ in v_types:
            try:
                val = res(res.find(
                    'table.pane [href="#{0}"]'.format(typ)
                ).parent().parent().children()[1]).html()
                if val.find('</span>') != -1:
                    # In case the latest build lowered violations
                    val = res(res(res.find('table.pane [href="#{0}"]'.format(
                        typ)
                    ).parent().parent().children()[1])).find(
                        'span'
                    ).html().split(' ')[0]
                retval[typ] = int(val)
                retval['total'] += retval[typ]
            except (IndexError, ValueError):
                retval[typ] = 'N/A'
        return retval

    def get_sloc(self, v_types=['python', 'javascript']):
        """Returns the number of lines in the code, given by language, receives
        an array with the names of the expected languages and returns a
        dictionary that tells each language how many lines has, and the total
        count
        """
        if not hasattr(self, 'result'):
            self.get_info()
        request = urllib2.Request('{0}{1}'.format(
            self.result['lastCompletedBuild']['url'],
            'sloccountResult/languages'
        ))
        if self.base64string:
            request.add_header("Authorization", "Basic %s" % self.base64string)
        retval = {'total': 0}
        try:
            result = urllib2.urlopen(request)
        except urllib2.HTTPError:
            return {'total': 'N/A'}
        res = pyq(result.read())
        for typ in v_types:
            try:
                val = int(res(
                    '[href="languageResult/{0}"]'.format(typ)
                ).parent().parent().children('.number')[1].attrib['data'])
                retval[typ] = int(val)
                retval['total'] += retval[typ]
            except (IndexError, ValueError):
                retval[typ] = 'N/A'
        return retval

    def get_cobertura(self):
        """Returns the percentage of source code lines cobered by tests"""
        if not hasattr(self, 'result'):
            self.get_info()
        request = urllib2.Request('{0}{1}'.format(
            self.result['lastCompletedBuild']['url'],
            'cobertura'
        ))
        if self.base64string:
            request.add_header("Authorization", "Basic %s" % self.base64string)
        try:
            result = urllib2.urlopen(request)
        except urllib2.HTTPError:
            return 'N/A'
        res = pyq(result.read())
        try:
            return int(float(res(res(res('table.pane')[0]).children(
                'tr>td')[4]
            ).attr.data))
        except (IndexError, ValueError):
            return 'N/A'


class JenkinsConnector:
    """You can get the list of running projects in a jenkins instance
    jen = JenkinsConnector('https://jenkins.shiningpanda-ci.com/ipython/')
    print jen.jobs.keys()
    You can get the latest successful build of all the active projects
    print jen.latest_build()
    or you can grab the latest successful information for a particular job
    print jen.latest_build('ipython-docs')

    You can optionally send username and password to get the information from
    your auth basic protected jenkins instance
    jen = JenkinsConnector('https://your.jenkins.io/', username='me', password='secret')
    """
    def __init__(self, url, username=None, password=None):
        self.base_server = url
        self.jobs = []
        self.base64string = None
        if username and password:
            self.base64string = base64.encodestring('{0}:{1}'.format(
                username,
                password
            )).replace('\n', '')
        self.get_jobs()

    def get_jobs(self):
        request = urllib2.Request("{0}/api/json".format(self.base_server))
        if self.base64string:
            request.add_header("Authorization", "Basic {0}".format(
                self.base64string
            ))

        try:
            result = urllib2.urlopen(request)
        except urllib2.HTTPError, e:
            if hasattr(e, 'code') and e.code == 403:
                print '403 - you need to authenticate'
            else:
                raise e
        else:
            self.result = json.loads(result.read())
            self.jobs = {}
            for job in self.result['jobs']:
                if job['color'] != u'disabled':
                    self.jobs[job['name']] = JenkinsJob(self.base64string, job)

    def get_info(self):
        u"""Gets the information for all active builds
        """
        for key in self.jobs:
            self.jobs[key].get_info()

    def latest_build(self, job_name=None):
        u"""Offers the latest build for a job, if no job is given
        looks inside all the builds to look for the correct one
        """
        if not job_name:
            # Looking the latest build
            if not reduce(
                lambda u, v: hasattr(u, 'result') and hasattr(v, 'result'),
                self.jobs,
                True
            ):
                self.get_info()
            result = sorted(
                self.jobs.values(),
                key=lambda u: u.successfull_build.timestamp
            )[-1]
        elif not hasattr(self.jobs[job_name], 'result'):
            # Latest build for specific job
            result = self.jobs[job_name]
            result.get_info()
        else:
            # Latest build for initialized job
            result = self.jobs[job_name]
        return u'{0},{1},{2}'.format(
            result.name,
            result.successfull_build.timestamp,
            result.successfull_build.commits,
        )

    def get_build(self, name, url):
        """Receives the name of the job and the url of some build,
        If the build has changesets returns a string
        containing
            name,timestamp of the build,number of commits
        otherwise returns
            ''
        """
        request = urllib2.Request("{0}/api/json".format(url))
        if self.base64string:
            request.add_header("Authorization", "Basic {0}".format(
                self.base64string
            ))

        try:
            result = urllib2.urlopen(request)
        except urllib2.HTTPError, e:
            if hasattr(e, 'code') and e.code == 403:
                print '403 - you need to authenticate'
            else:
                raise e
        else:
            result = json.loads(result.read())
            commits = len(result[u'changeSet'][u'items'])
            if commits:
                return u'{0},{1},{2}'.format(
                    name,
                    result['timestamp'],
                    commits,
                )
        return ''

    def qualityindicators(self, job_list=None):
        """Shows in the standard output statistics that offer information for
        quality indicators used in Axiacore.
        Receives as parameter a list of names of projects to be evaluated,
        or it can be a string suffix for the names of the projects you want,
        if not given, tries to extract all the projects wit suffix - Testing.
        """
        if job_list is None:
            job_list = [name for name in self.jobs if name.endswith(' - Testing')]
        elif isinstance(job_list, str) or isinstance(job_list, unicode):
            job_list = [name for name in self.jobs if name.endswith(job_list)]
        totcob = 0
        cantcob = 0
        cantsloc = 0
        totvio = 0
        totsloc = 0
        jobs = {
            'items': [],
        }
        for job in job_list:
            cobertura = self.jobs[job].get_cobertura()
            violations = self.jobs[job].get_violations()['total']
            sloc = self.jobs[job].get_sloc()['total']
            jobs['items'].append({
                'job': job,
                'coverage': cobertura,
                'violations': violations,
                'sloc': sloc,
            })
            # Summarry calculation
            if cobertura != 'N/A':
                totcob += cobertura
                cantcob += 1
            if sloc != 'N/A':
                totsloc += sloc
                cantsloc += 1
            totvio += violations

        # Summary fixes for no available data
        if cantcob == 0:
            promcob = 0
        else:
            promcob = totcob/cantcob
        if totsloc == 0:
            violationindex = 0
        else:
            violationindex = (10000*totvio)/totsloc

        jobs['summary'] = {
            'promcob': promcob,
            'totvio': totvio,
            'totsloc': totsloc,
            'violationindex': violationindex,
        }

        return jobs

    def show_qualityindicators(self, job_list=None):
        result = self.qualityindicators(job_list)
        title = u'{0:^46} {1:^12} {2:^12} {3:^12}'.format(
            u'Proyecto',
            u'Cobertura',
            u'Violaciones',
            u'SLOC',
        )
        output = [title]
        for item in result['items']:
            output.append(u'{job:<46} {coverage:>10} {violations:>10} {sloc:>10}'.format(
                **item)
            )

        pretty = result['summary']
        pretty['total'] = u'Total'
        output.append(
            u'{total:^46} {promcob:>10} {totvio:>10} {totsloc:>10} {violationindex:>10}'.format(
                **pretty)
            )
        for line in output:
            print line
