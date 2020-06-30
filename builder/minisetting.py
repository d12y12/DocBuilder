#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from os.path import join, dirname, abspath


class Setting:
    def __init__(self):
        self.attribute = {
            "CMD": abspath(join(dirname(dirname(abspath(__file__))), "docbuilder.py")),
            "VERSION": join(dirname(dirname(abspath(__file__))), "VERSION"),
            "LOG_ENABLED": True,
            "LOG_FORMAT": '%(asctime)s:%(name)s:%(levelname)s:%(message)s',
            "LOG_LEVEL": 'DEBUG',
            "LOG_FILE": None,
            "LOG_DIR": join(dirname(dirname(abspath(__file__))), "log"),
            "DATABASE_FILE": join(dirname(dirname(abspath(__file__))), "database.json"),
            "PUBLISH_DIR": "/share",
            "DATA_DIR": '/docs',
            "CRON_FILE": join(dirname(dirname(abspath(__file__))), "crontab")
        }

    def __getitem__(self, name):
        return self.attribute[name]

    def __setitem__(self, name, value):
        self.attribute[name] = value

    def __contains__(self, name):
        return name in self.attribute

    def __iter__(self):
        return iter(self.attribute)

    def __len__(self):
        return len(self.attribute)
