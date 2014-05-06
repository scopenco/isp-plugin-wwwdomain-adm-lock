isp-plugin-wwwdomain-on-off
===========================

Documentation
--------
Russian description at http://blog.scopenco.net/wwwdomain-on-off-ispmanager/

ISPmanager plugin allow to block/unblock wwwdomain with admin (level 7) permissions. After block, User can't unblock wwwdomain and gets error. The main goal of this plugins is to allow to block domain without block User in some situation like DDOS atack / overloading / abuse.


Installing
----------
> cp -v etc/*.xml /usr/local/ispmgr/etc/

> cp -v addon/*.py /usr/local/ispmgr/addon/

> killall -9 ispmgr

Testing
----------
Tested on CentOS 6.

Questions?
----------
If you have questions or problems getting things
working, first try searching wiki.

If all else fails, you can email me and I'll try and respond as
soon as I get a chance.

        -- Andrey V. Scopenco (andrey@scopenco.net)
