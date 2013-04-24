#! /usr/bin/env python
# encoding: utf-8

from waflib import Options

def options(opt):
    opt.load('c cxx')
    opt.load('arduino avr-gcc avr-gxx avrdude', tooldir='waftools')


def configure(conf):
    conf.load('arduino avr-gcc avr-gxx avrdude', tooldir='waftools')
    conf.check_libraries('SPI')

def upload(bld):
    bld(features='avrdude', source='build/firmware.hex')

def build(bld):
    sources = ['test/Blink.c'];

    bld(target='firmware.elf',
        features='c cxx cprogram avr-gcc arduino',
        source=sources,
        includes=['.'],
        use = 'core SPI')
