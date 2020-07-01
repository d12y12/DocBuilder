#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
from os.path import join, abspath, dirname, exists, isfile, splitext, basename
from shutil import move, copy2, copystat
import datetime
import filecmp
import subprocess
import logging
import platform
from .minisetting import Setting
from .utils import config_logging


def is_sub_directory(base_dir, test_dir):
    # make both absolute
    base_dir = os.path.join(os.path.realpath(base_dir), '')
    test_dir = os.path.realpath(test_dir)
    return os.path.commonprefix([test_dir, base_dir]) == base_dir


def copytree(src, dst, ignore=None):
    names = os.listdir(src)
    if ignore is not None:
        ignored_names = ignore(src, names)
    else:
        ignored_names = set()

    if not os.path.exists(dst):
        os.makedirs(dst)

    for name in names:
        if name in ignored_names:
            continue

        src_name = os.path.join(src, name)
        dst_name = os.path.join(dst, name)
        if os.path.isdir(src_name):
            copytree(src_name, dst_name, ignore)
        else:
            copy2(src_name, dst_name)
    copystat(src, dst)


class BuilderManager:
    def __init__(self, setting: Setting = None):
        self.setting = Setting() if not setting else setting
        config_logging(self.setting)
        self.logger = logging.getLogger(self.__class__.__name__)

    def get_services_list(self):
        build_services = []
        publish_services = []
        if exists(self.setting['DATABASE_FILE']):
            with open(self.setting['DATABASE_FILE'], 'r', encoding="utf-8") as f:
                services = json.load(f)
            for service_name, service in services.items():
                if 'build' in service:
                    build_services.append(service_name)
                if 'publish' in service:
                    publish_services.append(service_name)
        else:
            self.logger.error("Database file not exists!")
        return build_services, publish_services

    def build_service(self, service_name: str):
        self.logger.info("build service <{}>".format(service_name))
        build_services, publish_services = self.get_services_list()
        if service_name not in build_services:
            self.logger.error('<{}> not available in Build service'.format(service_name))
            return False
        with open(self.setting['DATABASE_FILE'], 'r', encoding="utf-8") as f:
            services = json.load(f)
        build_cmds = services[service_name]['build']
        current_dir = os.getcwd()
        project_dir = join(self.setting['DATA_DIR'], service_name)
        if exists(project_dir):
            os.chdir(project_dir)
        else:
            self.logger.error("project {} not exists".format(service_name))
            return False
        cmd_results = True
        for cmd in build_cmds:
            if not cmd.startswith(("make", "cd", "cp")):
                self.logger.error("wrong build command {}".format(cmd))
                cmd_results = False
                break
            else:
                if cmd.startswith('cd'):
                    path = cmd.strip()[3:]
                    if not os.path.isabs(path):
                        path = join(project_dir, path)
                    if not is_sub_directory(project_dir, path):
                        self.logger.error("Build Failed: <cd> out of project scope")
                        cmd_results = False
                        break
                    os.chdir(path)
                else:
                    cmd = cmd.strip().split()
                    ret = subprocess.run(cmd, stdout=subprocess.PIPE)
                    if ret.returncode != 0:
                        self.logger.error("Build Failed: {}".format(ret.stdout))
                        cmd_results = False
                        break
        os.chdir(current_dir)
        return cmd_results

    def publish_service(self, service_name: str):
        self.logger.info("publish service <{}>".format(service_name))
        build_services, publish_services = self.get_services_list()
        if service_name not in publish_services:
            self.logger.error('<{}> not available in Publish service'.format(service_name))
            return False
        publish_dir = join(self.setting['PUBLISH_DIR'], service_name)
        if not exists(publish_dir):
            self.logger.error("Publish dir not exist")
            return False
        with open(self.setting['DATABASE_FILE'], 'r', encoding="utf-8") as f:
            services = json.load(f)
        original_path = services[service_name]['publish']
        project_dir = join(self.setting['DATA_DIR'], service_name)
        if not os.path.isabs(original_path):
            original_path = join(project_dir, original_path)
        if not is_sub_directory(project_dir, original_path):
            self.logger.error("Publish Failed: out of project scope")
            return False
        copytree(original_path, publish_dir)
        return True

    def get_service_config(self, service_name: str, output=''):
        self.logger.info("get service <{}> configuration".format(service_name))
        with open(self.setting['DATABASE_FILE'], 'r', encoding="utf-8") as f:
            services = json.load(f)
        if service_name not in services:
            self.logger.error("service not found")
            return False
        else:
            config = services[service_name]
            if output:
                with open(output, 'w', encoding="utf-8") as f:
                    json.dump(config, f, indent=2, ensure_ascii=False)
            else:
                print(json.dumps(config, indent=2))
            return True

    def set_crontab(self):
        if platform.system() != 'Linux':
            self.logger.warning("Not Linux system, Crontab will not set!")
        user = subprocess.run(["whoami"], stdout=subprocess.PIPE).stdout.decode('utf-8').strip()
        if user == 'root':
            self.logger.warning("you are using root user")
            print("set crontab for root user")
        self.logger.info("set crontab for user {}".format(user))
        cron_header = 'SHELL=/bin/sh\n' \
                      'PATH=/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin\n\n' \
                      '# m h dom mon dow user  command\n'
        crontab = []
        if exists(self.setting['DATABASE_FILE']):
            with open(self.setting['DATABASE_FILE'], 'r', encoding="utf-8") as f:
                services = json.load(f)
            for service_name, service in services.items():
                if 'synchronization' in service and 'crontab' in service['synchronization'] and \
                    service['synchronization']['crontab']:
                    cron = service['synchronization']['crontab']
                    app = self.setting['CMD']
                    cron_log = join(self.setting['LOG_DIR'], service_name + '.log')
                    crontab.append('{} {} {} {} >> {} 2>&1\n'.format(cron, app, '--batchrun', service_name, cron_log))
        else:
            self.logger.error("Database file not exists!")
            return False
        
        if crontab:
            cron_path = self.setting['CRON_FILE']
            cron = cron_header + "".join(crontab)
            with open(cron_path, "w") as f:
                f.write(cron)
            # "crontab -u user cron_path" need root in alpine
            if platform.system() == 'Linux':
                self.logger.info("set cron tab")
                subprocess.run(['crontab', cron_path])
            # "crond reload" not exists in alpine
            # self.logger.info("reload cron config")
            # subprocess.run(['/etc/init.d/cron', 'reload'])
        else:
            self.logger.info("No cron job found!")
        return True

    def autoconf(self):
        self.set_crontab()

    def batchrun_service(self, service_name: str):
        build_services, publish_services = self.get_services_list()
        if service_name in build_services:
            self.build_service(service_name)
        if service_name in publish_services:
            self.publish_service(service_name)

    def init(self):
        build_services, publish_services = self.get_services_list()
        build_dir = self.setting['DATA_DIR']
        publish_dir = self.setting['PUBLISH_DIR']
        with open(self.setting['DATABASE_FILE'], 'r', encoding="utf-8") as f:
                services = json.load(f)
        for service_name in build_services:
            sub_dir = join(build_dir, service_name)
            os.makedirs(sub_dir, exist_ok=True)
            src = services[service_name]['source']
            if not exists(join(sub_dir, '.git')):
                ret = subprocess.run(["git", "clone", src, sub_dir], stdout=subprocess.DEVNULL)
                if ret.returncode != 0:
                    raise RuntimeError("Clone {} failed, please try render again".format(service_name))
        for service_name in publish_services:
            sub_dir = join(publish_dir, service_name)
            os.makedirs(sub_dir, exist_ok=True)
        