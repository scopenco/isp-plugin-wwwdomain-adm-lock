#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Andrey Skopenko <andrey@scopenco.net>

__author__ = 'Andrey Scopenco'

import sys
sys.path.insert(0, '/usr/local/ispmgr/addon')
from cli import ExitOk, Log, xml_doc, xml_error, domain_to_idna

from os import path, access, F_OK, W_OK, R_OK, chdir, getpid
from sys import stdin, stderr
from StringIO import StringIO
import subprocess as sp
from traceback import format_exc

try:
    import xml.etree.cElementTree as etree
except ImportError:
    try:
        import xml.etree.ElementTree as etree
    except ImportError:
        print 'Failed to import ElementTree from any known place'


# configs
PLUGIN_NAME = 'wwwdomain_adm_lock_f'
INC = '/usr/local/ispmgr/etc/wwwdomain_adm_lock.inc'
LOCK_TEMPLATE = '''# domain %s\n\
server {\n\
\tlisten %s:80;\n\
\tserver_name %s;\n\
\tlocation / {\n\
\t\troot /var/www/disabled;\n\
\t\tindex index2.html;\n\
\t}\n\
}\n\
# domain %s\n'''


def mgr_query(func, keys, out=None):
    '''func used for run mgrctl'''

    keys_str = ' '.join(['='.join(map(str, k)) for k in keys])
    q = '''%s %s''' % (func, keys_str)
    if out is None:
        res = sp.Popen('sbin/mgrctl -m ispmgr -o xml %s' % q, shell=True,
                       stdout=sp.PIPE, stderr=sp.PIPE).communicate()[0]
    else:
        res = sp.Popen('sbin/mgrctl -m ispmgr -o text %s' % q, shell=True,
                       stdout=sp.PIPE, stderr=sp.PIPE).communicate()[0]
    return res


def reload_nginx():
    '''Func used for nginx reload'''
    reload = '/etc/rc.d/init.d/nginx reload'
    res = sp.Popen(reload, shell=True, stdout=sp.PIPE, stderr=sp.PIPE)
    log.write(reload)
    if not res.stdout:
        output = res.stdout.read()
    else:
        output = res.stderr.read()
    for out in output.split('\n'):
        if out != '':
            log.write(out)
    return 0


def wrap(action):
    '''Decorator used for checking all given params'''

    def checkall(*args, **kwargs):
        elid = params.find('elid')
        if elid is not None:
            ellist = elid.text

            # restart nginx flag
            do_nginx_reload = False

            for elid in ellist.encode('utf-8').split(', '):
                # get credentials for domain
                doc = mgr_query('wwwdomain.edit', [['elid', elid]])
                xmldoc = etree.parse(StringIO(doc))
                domain = xmldoc.find('domain').text
                alias = xmldoc.find('alias').text
                ip = xmldoc.find('ip').text

                # convert domain and aliases to idna
                domains = [domain, ]
                if alias:
                    domains.append(alias)

                # convert domains to idna
                domains_idna = []
                for d in domains:
                    domains_idna.append(domain_to_idna(d.encode('utf-8')))
                domains = ' '.join(domains_idna)

                # disable/enable domains
                res = action(domains, ip, *args, **kwargs)
                if res == 0:
                    do_nginx_reload = True
                if res == 1:
                    print xml_error('access to inc file problem',
                                    code_num='1')
                    return 0
                if res == 2:
                    log.write('nothing to do')

            print xml_doc('ok')
            if do_nginx_reload:
                reload_nginx()

        else:
            print xml_error('no domain selected', code_num='1')
            return 0
    return checkall


@wrap
def turn_off_www(domains, ip):
    '''Disable domain by adding section to INC'''

    log.write('try to disable domain(s) %s with ip %s' % (domains, ip))

    # if INC not exist
    if not access(INC, R_OK):
        return 1

    # read all line from INC to content
    with open(INC, 'r') as f:
        content = f.read()

    # if host always added then return
    if ('server {\n\tlisten %s:80;\n\tserver_name %s' % (
            ip, domains)) in content:
        log.write('record found in %s' % INC)
        return 2

    # now add rec to INC
    log.write('add record to %s' % INC)
    dir = LOCK_TEMPLATE % (domains, ip, domains, domains)
    # add new zone to the end of INC
    content += dir
    # write new data to file
    with open(INC, 'w') as f:
        f.write(content)
    return 0


@wrap
def turn_on_www(domains, ip):
    '''Enable domain by removing section to INC'''

    log.write('try to enable domain(s) %s with ip %s' % (domains, ip))

    # if INC not exist
    if not access(INC, R_OK):
        return 1

    # read all line from INC to content
    with open(INC, 'r') as f:
        content = f.read()

    # if not exist in INC, terminate
    if not ('server {\n\tlisten %s:80;\n\tserver_name %s' % (
            ip, domains)) in content:
        log.write('record not found in %s' % INC)
        return 2

    # remove record from INC
    log.write('remove record from %s' % INC)
    # split content by '# domain'
    content_l = content.split('# domain %s\n' % domains)
    content = content_l[0] + content_l[2]
    # write new data to file
    with open(INC, 'w') as f:
        f.write(content)
    return 0


if __name__ == '__main__':
    chdir('/usr/local/ispmgr/')

    # activate logging
    # stderr ==> ispmgr.log
    log = Log(plugin=PLUGIN_NAME)
    stderr = log

    try:
        log.write('start plugin')
        xmldoc = etree.parse(stdin).getroot()
        level = int(xmldoc.get('level'))
        params = xmldoc.find('params')
        func = params.find('func').text
        log.write('level %s, func %s' % (level, func))

        if level != 7:
            print xml_error('access denied', code_num='1')
            raise ExitOk('done')

        if func == 'wwwdomain_adm_lock.enable':
            turn_on_www()
        elif func == 'wwwdomain_adm_lock.disable':
            turn_off_www()

        raise ExitOk('done')

    except ExitOk, e:
        log.write(e)
    except:
        print xml_error('please contact support team', code_num='1')
        log.write(format_exc())
        exit(0)
