# Copyright 2015 Canonical, Ltd.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import copy
import datetime
import logging
import os
import yaml


log = logging.getLogger("subiquity.curtin")

TMPDIR = '/tmp'
CURTIN_SEARCH_PATH = ['/usr/local/curtin/bin', '/usr/bin']
CURTIN_INSTALL_PATH = ['/media/root-ro', '/']
CURTIN_INSTALL_LOG = '/tmp/subiquity-curtin-install.log'
CURTIN_POSTINSTALL_LOG = '/tmp/subiquity-curtin-postinstall.log'
CONF_PREFIX = os.path.join(TMPDIR, 'subiquity-config-')
CURTIN_NETWORK_CONFIG_FILE = CONF_PREFIX + 'network.yaml'
CURTIN_STORAGE_CONFIG_FILE = CONF_PREFIX + 'storage.yaml'
CURTIN_PRESERVED_CONFIG_FILE = CONF_PREFIX + 'storage-preserved.yaml'
POST_INSTALL_CONFIG_FILE = CONF_PREFIX + 'postinst.yaml'
CURTIN_CONFIGS = {
    'network': CURTIN_NETWORK_CONFIG_FILE,
    'storage': CURTIN_STORAGE_CONFIG_FILE,
    'postinstall': POST_INSTALL_CONFIG_FILE,
    'preserved': CURTIN_PRESERVED_CONFIG_FILE,
}

CURTIN_CONFIG_BASE = {
    'reporting': {
        'subiquity': {
            'type': 'print',
            },
        },

    'partitioning_commands': {
        'builtin': 'curtin block-meta custom',
        },
    }


# TODO, this should be moved to the in-target cloud-config seed so on first
# boot of the target, it reconfigures datasource_list to none for subsequent
# boots.
POST_INSTALL_CONFIG = {
    'write_files': {
        'postinst_metadata': {
            'path': 'var/lib/cloud/seed/nocloud-net/meta-data',
            'content': 'instance-id: inst-3011',
            },
        'postinst_userdata': {
            'path': 'var/lib/cloud/seed/nocloud-net/user-data',
            # 'content' gets filled in later
            },
        }
    }


def curtin_userinfo_to_config(userinfo):
    user = {
        'name': userinfo['username'],
        'gecos': userinfo['realname'],
        'passwd': userinfo['password'],
        'shell': '/bin/bash',
        'groups': 'admin',
        'lock-passwd': False,
        }
    if 'ssh_import_id' in userinfo:
        user['ssh_import_id'] = [userinfo['ssh_import_id']]
    return [user]

def curtin_hostinfo_to_config(hostinfo):
    return {
        'hostname': hostinfo['hostname'],
        }


def curtin_write_postinst_config(userinfo):
    cloud_init_config = {
        'users': curtin_userinfo_to_config(userinfo),
        'hostname': userinfo['hostname'],
    }
    userdata = '#cloud-config\n' + yaml.dump(cloud_init_config)
    config = copy.deepcopy(POST_INSTALL_CONFIG)
    config['write_files']['postinst_userdata']['content'] = userdata
    with open(POST_INSTALL_CONFIG_FILE, 'w') as conf:
        datestr = '# Autogenerated by SUbiquity: {} UTC\n'.format(
            str(datetime.datetime.utcnow()))
        conf.write(datestr)
        conf.write(yaml.dump(config))


def curtin_write_storage_actions(path, log, actions):
    config = copy.deepcopy(CURTIN_CONFIG_BASE)
    config['storage'] = {
        'version': 1,
        'config': actions,
        }
    config['install'] = {
        'log_file': log,
        }
    datestr = '# Autogenerated by SUbiquity: {} UTC\n'.format(
        str(datetime.datetime.utcnow()))
    with open(path, 'w') as conf:
        conf.write(datestr)
        conf.write(yaml.dump(config))


from collections import OrderedDict
def setup_yaml():
    """ http://stackoverflow.com/a/8661021 """
    represent_dict_order = lambda self, data:  self.represent_mapping('tag:yaml.org,2002:map', data.items())
    yaml.add_representer(OrderedDict, represent_dict_order)
setup_yaml()


def curtin_write_network_config(netplan_config):
    # As soon as curtin and cloud-init support v2 network config
    # (RSN!) we can just pass this sensibly to curtin. But for now,
    # just use write_files to install the config and make sure curtin
    # and cloud-init doesn't do any networking stuff of their own
    # accord.
    curtin_conf = {
        'write_files': {
            'netplan': {
                'path': 'etc/netplan/00-installer.yaml',
                'content': netplan_config,
                'permissions': '0600',
            },
            'nonet': {
                'path': 'etc/cloud/cloud.cfg.d/subiquity-disable-cloudinit-networking.cfg',
                'content': 'network: {config: disabled}\n',
            }
        },
        'network_commands': {'builtin': []},
    }
    curtin_config = yaml.dump(curtin_conf, default_flow_style=False)
    datestr = '# Autogenerated by SUbiquity: {} UTC\n'.format(
        str(datetime.datetime.utcnow()))
    with open(CURTIN_NETWORK_CONFIG_FILE, 'w') as conf:
        conf.write(datestr)
        conf.write(curtin_config)


def curtin_find_curtin():
    for p in CURTIN_SEARCH_PATH:
        curtin = os.path.join(p, 'curtin')
        if os.path.exists(curtin):
            log.debug('curtin found at: {}'.format(curtin))
            return curtin
    # This ensures we fail when we attempt to run curtin
    # but it's not present
    return '/bin/false'


def curtin_find_install_path():
    for p in CURTIN_INSTALL_PATH:
        if os.path.exists(p):
            log.debug('install path set: {}'.format(p))
            return p


def curtin_install_cmd(configs):
    '''
    curtin -vvv --showtrace install -c $CONFIGS cp:///
    '''
    curtin = curtin_find_curtin()
    install_path = curtin_find_install_path()

    install_cmd = [curtin, '-vvv', '--showtrace']
    for c in configs:
        install_cmd += ['-c', '{}'.format(c)]
    install_cmd += ['install', 'cp://{}'.format(install_path)]
    log.info('curtin install command: {}'.format(" ".join(install_cmd)))

    return install_cmd
