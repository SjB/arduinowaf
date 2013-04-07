#! /usr/bin/env python
# encoding: utf-8

import os, sys
from waflib import Configure, Options, Utils, ConfigSet
from waflib.Configure import conf
from waflib.TaskGen import extension, feature, after, before

from arduinoBoard import BoardFileParser

#from waflib.Tools import ccroot
#from waflib.Configure import conf
#from waflib import Task

DEFAULT_ARDUINO_DIR = '/usr/share/arduino'
DEFAULT_BOARD = 'uno'

def options(opt):
    global DEFAULT_ARDUINO_DIR

    opt.add_option('--arduino-rootpath', type='string', dest='ARDUINODIR', default=DEFAULT_ARDUINO_DIR)
    opt.add_option('--board', type='string', dest='BOARD', default=DEFAULT_BOARD)

def configure(conf):
    arduino_path = getattr(Options.options, 'ARDUINODIR', None)

    if not os.path.exists(arduino_path):
        conf.fatal('You must specify the arduino install directory')

    conf.env.ARDUINODIR = arduino_path

    board = getattr(Options.options, 'BOARD', 'uno')
    conf.check_board(board);

@conf
def check_board(self, *k, **kw):

    if k:
        kw['board_name'] = k[0]

    if not 'env' in kw:
        kw['env'] = self.env

    env = kw['env']

    board_file = os.path.join(self.env.ARDUINODIR, 'hardware', 'arduino', 'boards.txt')
    parser = BoardFileParser(board_file)


    arduino_board = parser.parseABoardConfig(boardName=kw['board_name'])
    if 0 == len(arduino_board):
        self.fatal('Board %s not found.' %  board_name)

    board = arduino_board[0]

    self.env.arduino = dict()

    self.env.arduino['build'] = board.configs['build']
    self.env.arduino['upload'] = board.configs['upload']

    config = self.env.arduino['build']
    self.env.arduino['core_path'] = os.path.join(env.ARDUINODIR, 'hardware', 'arduino', 'cores', config['core'])
    self.env.arduino['variant_path'] = os.path.join(env.ARDUINODIR, 'hardware', 'arduino', 'variants', config['variant'])

    appu = self.env.append_unique
    appu('INCLUDES', [self.env.arduino['core_path'], self.env.arduino['variant_path']])
    appu('CFLAGS', ['-mmcu=%s' % config['mcu'], '-DF_CPU=%s' % config['f_cpu']])
    appu('CXXFLAGS', ['-mmcu=%s' % config['mcu'], '-DF_CPU=%s' % config['f_cpu']])
    appu('LINKFLAGS', ['-mmcu=%s' % config['mcu']])


@conf
def check_libraries(self, *k, **kw):
    """
    Check if the library exist and add it to the list of dependencies
    """

    if k:
        lst = k[0].split()
        kw['package'] = lst[0]
        kw['args'] = ' '.join(lst[1:])

    if not 'env' in kw:
        kw['env'] = self.env

    env = kw['env']

    if not 'path' in kw:
        kw['path'] = os.path.join(self.env.ARDUINODIR, 'libraries')

    uselib = kw.get('uselib_store', kw['package'].upper())

    lib_path = os.path.join(kw['path'], kw['package'])
    lib_node = self.root.find_node(lib_path)

    appu = env.append_unique
    appu('PATH_' + uselib, lib_node.abspath())
    appu('INCLUDES', lib_node.abspath())


def build_arduino_lib(tgen, name):
    uselib = name.upper()
    path = getattr(tgen.env, 'PATH_' + uselib, [])

    lib_path = tgen.bld.root.find_node(path)
    # need to compile all c/cpp file in subdirectories also.
    srcs = lib_path.ant_glob(['**/*.c', '**/*.cpp'])

    # need to include all .h files in located in subdirectories.
    includes = [os.path.dirname(x.abspath()) for x in lib_path.ant_glob('**/*.h')]

    cflags = ['-Os', '-MMD', '-DARDUINO=100',
        '-ffunction-sections', '-fdata-sections', '-c', '-Wall',
        '-fno-exceptions', '-fno-strict-aliasing']

    tgen = tgen.bld(target=name,
        name = name,
        features = 'c cxx cxxstlib avr-gcc',
        source = srcs,
        includes = includes,
        cflags = cflags,
        cxxflags = cflags,
        linkflags=['-Os'])

@feature('arduino')
@before('process_source')
def include_extralib_source(self):
    use = getattr(self, 'use', [])
    use = Utils.to_list(use)

    for dep in use:
        if dep in ['core']:
            continue

        build_arduino_lib(self, dep)


def build_arduino_core(tgen):
        env = getattr(tgen, 'env', tgen.bld.env)
        arduino_cfg = getattr(env, 'arduino', None)
        if not arduino_cfg:
            fatal('Missing board configuration')
        config = arduino_cfg['build']

        arduino_node = tgen.bld.root.find_node(env.arduino['core_path'])
        if not arduino_node:
            tgen.bld.fatal('Arduino source path %s does not exist' % arduino_path)

        srcs = arduino_node.ant_glob('*.c')
        srcs += arduino_node.ant_glob('*.cpp')

        cflags = ['-Os', '-MMD', '-DARDUINO=100',
            '-ffunction-sections', '-fdata-sections', '-c', '-Wall',
            '-fno-exceptions', '-fno-strict-aliasing']

        tgen = tgen.bld(target='core',
            name = 'core',
            features = 'c cxx cxxstlib avr-gcc',
            source = srcs,
            cflags = cflags,
            cxxflags = cflags,
            linkflags=['-Os'])


@feature('arduino')
@before('process_source')
def include_arduino_source(self):
    # Load all arduino source
    use = getattr(self, 'use', None)
    if 'core' in use:
        build_arduino_core(self)


@feature('avrdude')
@before('process_source')
def configure_avrdude(self):
    if not getattr(self, 'mcu', None):
        self.mcu = self.env.arduino['build']['mcu']

    if not getattr(self, 'protocol', None):
        self.protocol = self.env.arduino['upload']['protocol']
