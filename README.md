isp-plugin-wwwdomain-adm-lock
===========================

Documentation
--------
Russian description at http://blog.scopenco.net/wwwdomain-adm-lock-ispmanager/

ISPmanager plugin allows lock/unlock www domain with admin (level 7) permissions. After lock, User will see forbidden page or page you selected for lock state. The main goal of this plugin is to allow to lock domain without locking all User's domains in situations like DDOS atack / overloading / abuse.


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
