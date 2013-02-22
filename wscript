#! /usr/bin/env python
# encoding: utf-8

from waflib import Options

def options(opt):
    opt.load('c cxx')
    opt.load('arduino', tooldir='waf-tools')
    opt.load('avr-gcc', tooldir='waf-tools')
    opt.load('avr-gxx', tooldir='waf-tools')
    opt.load('avrdude', tooldir='waf-tools')


def configure(conf):
    conf.load('arduino', tooldir='waf-tools')
    conf.load('avr-gcc', tooldir='waf-tools')
    conf.load('avr-gxx', tooldir='waf-tools')
    conf.load('avrdude', tooldir='waf-tools')

    #conf.check_libraries('SPI', path='/usr/share/arduino/libraries')

def upload(bld):
    bld(features='avrdude', source='build/firmware.hex')

def build(bld):
    sources = ['test/Blink.cpp'];

    bld(target='firmware.elf',
        features='c cxx cprogram avr-gcc arduino',
        source=sources,
        includes=['.'],
        use = 'core SPI')