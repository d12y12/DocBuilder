#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import optparse
from builder.utils import get_version, set_logger
from builder import BuilderManager
from builder.minisetting import Setting


def print_cmd_header():
    print('DocBuilder {}'.format(get_version()))


def print_cmd_result(success=True):
    if success:
        print("Success")
    else:
        print("Failed")
        print("Please check log")


def usage_error(error: str):
    print("Usage Error: {} {}".format(os.path.basename(__file__), error))
    print("Try {} -h for more information".format(os.path.basename(__file__)))


def process(options, args):
    setting = Setting()

    if options.logfile:
        set_logger(setting, log_enable=True, log_file=options.logfile)

    if options.loglevel:
        set_logger(setting, log_enable=True, log_level=options.loglevel)

    if options.logdir:
        set_logger(setting, log_enable=True, log_dir=options.logdir)

    if options.nolog:
        set_logger(setting, log_enable=False)

    builder_manager = BuilderManager(setting)

    if options.list:
        if len(args) > 0:
            usage_error("--list take no argument")
            return False
        build_services, publish_services = builder_manager.get_services_list()
        print("Available Build Service: {}".format(build_services))
        print("Available Publish Service: {}".format(publish_services))
        return True
    if options.build:
        if len(args) != 1:
            usage_error("--build only take 1 argument <service name>")
            return False
        service_name = args[0]
        print_cmd_result(builder_manager.build_service(service_name))
        return True
    if options.publish:
        if len(args) != 1:
            usage_error("--publish only take 1 argument <service name>")
            return False
        service_name = args[0]
        print_cmd_result(builder_manager.publish_service(service_name))
        return True
    if options.autoconf:
        if len(args) > 0:
            usage_error("--autoconf take no argument")
            return False
        builder_manager.autoconf()
        return True
    if options.batchrun:
        if len(args) != 1:
            usage_error("--batchrun only take 1 argument <service name>")
            return False
        service_name = args[0]
        builder_manager.batchrun_service(service_name)
        return True


def cli(argv=None):
    print_cmd_header()
    if argv is None:
        argv = sys.argv

    usage = "usage: %prog [options] [service name]"
    parser = optparse.OptionParser(formatter=optparse.TitledHelpFormatter(),
                                   conflict_handler='resolve', usage=usage)
    group_global = optparse.OptionGroup(parser, "Global Options")
    group_global.add_option("--logdir", metavar="PATH",
                            help="Log directory. if omitted local log directory will be created")
    group_global.add_option("--logfile", metavar="FILE",
                            help="log file. if omitted stderr will be used")
    group_global.add_option("--loglevel", metavar="LEVEL", default=None,
                            help="log level (default: DEBUG)")
    group_global.add_option("--nolog", action="store_true",
                            help="disable logging completely")
    parser.add_option_group(group_global)

    parser.add_option("--list", action='store_true', dest='list',
                      help="List all services names available")
    parser.add_option("--build", action='store_true', dest="build",
                      help="Build doc for <service name>")
    parser.add_option("--publish", action='store_true', dest="publish",
                      help="Publish for <service name>")

    group_devspace = optparse.OptionGroup(parser, "Devspace Options")
    group_devspace.add_option("--autoconf", action='store_true', dest="autoconf",
                              help="Auto add service avaialbe and update crontab")
    group_devspace.add_option("--batchrun", action='store_true', dest="batchrun",
                              help="Run build and publish for <service name>")
    parser.add_option_group(group_devspace)

    if len(argv) == 1:
        parser.print_help()
    else:
        options, args = parser.parse_args(args=argv[1:])
        process(options, args)


if __name__ == '__main__':
    cli()
