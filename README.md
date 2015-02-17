jenkins-connector
=================

[![PyPI version](https://badge.fury.io/py/jenkinsconnector.svg)](http://badge.fury.io/py/jenkinsconnector)


A library to communicate with jenkins

Install it like this:

    pip install jenkinsconnector


Use it like this:

    from jenkinsconnector import JenkinsConnector
    jcon = JenkinsConnector(yourjenkins, youruser, yourpassword)
    result = jcon.qualityindicators(['project name 1', ..., 'project name n']
    print result

It usually seeks for the cobertura report, violations and gives you summary
information of all the involved projects

Common Use cases:

You can get the list of running projects in a jenkins instance with:

    jen = JenkinsConnector('https://jenkins.shiningpanda-ci.com/ipython/')
    print jen.jobs.keys()

You can get the latest successful build of all the active projects

    print jen.latest_build()

or you can grab the latest successful information for a particular job

    print jen.latest_build('ipython-docs')

You can optionally send username and password to get the information from
your auth basic protected jenkins instance:

    jen = JenkinsConnector('https://your.jenkins.io/', username='me', password='secret')

