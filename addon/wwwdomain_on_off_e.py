#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Andrey Skopenko <andrey@scopenco.net>

__author__ = "Andrey Scopenco"

import sys
sys.path.insert(0, '/usr/local/ispmgr/addon')
from cli import ExitOk, Log, xml_doc, xml_error, domain_to_idna

from os import path, access, F_OK, W_OK, chdir
from sys import stdin, stderr
from pwd import getpwuid, getpwnam
from traceback import format_exc
import re

try:
    import xml.etree.cElementTree as etree
except ImportError:
    try:
        import xml.etree.ElementTree as etree
    except ImportError:
        print "Failed to import ElementTree from any known place"


PLUGIN_NAME = 'wwwdomain_on_off_e'
INC = '/usr/local/ispmgr/etc/wwwdomain_on_off.inc'


def add_inc():
    ''' Add nginx configuration file '''

    # get path to nginx.conf
    with open('etc/ispmgr.conf', 'r') as f:
        for line in f:
            args = line.strip().split()
            if len(args) == 3 and \
                    args[0] == 'path' and \
                    args[1] == 'nginx.conf':
                log.write('path for nginx.conf is %s' % args[2])
                path = args[2]
                break

    # check if INC exists
    need_to_add_inc = True
    with open(path, 'r') as f:
        for line in f:
            if INC in line.strip():
                log.write('found %s in %s' % (INC, path))
                need_to_add_inc = False
                break

    # add INC to nginx.conf
    if need_to_add_inc:
        log.write('not found %s in %s, try to add...' % (INC, path))
        with open(path, 'r') as f:
            content = f.readlines()

        # add INC to nginx.conf
        content_m = []
        for l in range(len(content)):
            content_m.append(content[l])
            if content[l].strip().split() == 'http {'.split():
                content_m.append('    include %s;\n' % INC)
                log.write('append %s to %s' % (INC, path))

        # write new nginx.conf
        with open(path, 'w') as f:
            f.writelines(content_m)


if __name__ == "__main__":
    chdir('/usr/local/ispmgr/')

    # activate logging
    # stderr ==> ispmgr.log
    log = Log(plugin=PLUGIN_NAME)
    stderr = log

    try:
        log.write('start plugin')
        # read INC or create new
        if access(INC, F_OK):
            with open(INC, 'r') as f:
                content = f.read()
            add_inc()
        else:
            add_inc()
            with open(INC, 'w') as f:
                f.write('')
            content = ''

        # get xml options
        xmldoc = etree.parse(stdin).getroot()
        # get user name and level to set home dir
        level = xmldoc.get('level')
        user = xmldoc.get('user')
        if int(level) in [6, 7]:
            home_dir = ''
        else:
            home_dir = getpwnam(user).pw_dir
        log.write('user %s, level %s, home %s' % (user, level, home_dir))

        # find all disabled users in ispmgr.conf
        with open('etc/ispmgr.conf', 'r') as f:
            ispconf = f.read()
        disabledusers = re.findall(
            r'Account\s+"([^"]*)"\s*{[^}]*?\n\s*AdmDisabled\s+yes\s*\n[^}]*}',
            ispconf, re.S)

        # data exp for user:
        # <elem><name>test1.domain.com</name>
        # <ip>192.168.0.1</ip>
        # <docroot>/www/test1.domain.com</docroot>
        # <active /></elem>
        for elem in xmldoc.findall('elem'):
            # if user perms then owner is user alse, find user by owner elem
            if int(level) == 5:
                owner = user
            else:
                owner = elem.find('owner').text

            # if user is disabled,
            # then nothing to activate! all domains always disabled
            if owner in disabledusers:
                continue

            # check if domain exist in INC and activate if not
            name = elem.find('name').text
            # convert name to idna
            domain_name = domain_to_idna(name.encode('utf-8'))
            domain_ip = elem.find('ip').text
            if not ('server {\n\tlisten %s:80;\n\tserver_name %s' % (
                    domain_ip, domain_name)) in content:
                etree.SubElement(elem, 'active')
            else:
                log.write('disabled %s, %s' % (domain_name, domain_ip))

        # print xml output to view on/off elements
        print(etree.tostring(xmldoc, encoding="UTF-8"))

        raise ExitOk('done')

    except ExitOk, e:
        log.write(e)
    except:
        print xml_error('please contact support team', code_num='1')
        log.write(format_exc())
        exit(0)
