#! /usr/bin/env python

from waflib.Configure import conf
from waflib import Task, Options
from waflib.TaskGen import extension
from waflib.Build import BuildContext

DEFAULT_PORT = '/dev/ttyACM0'

class avrdude(Task.Task):
    def run(self):
        #TODO: Abstract almost all of this
        for asource in self.inputs:
            cmd = self.env.AVRDUDE
            cmd += ' -p ' + self.mcu
            cmd += ' -c ' + self.protocol
            cmd += ' -P ' + self.env.port + ' -D -Uflash:w:' + asource.relpath() + ':i'
            #cmd += ' -v -v -v -v' #for very verbose output
            print cmd
            self.exec_command(cmd)

    def runnable_status(self):
		ret=super(avrdude,self).runnable_status()
		if ret==Task.SKIP_ME:
			return Task.RUN_ME
		return ret

def options(opt):
    opt.add_option('--with-avrdude', type='string', dest='AVRDUDE')
    opt.add_option('--port', type='string', dest='PORT', default=DEFAULT_PORT)

def configure(ctx):
    avrdude = getattr(Options.options, 'AVRDUDE', None)
    if avrdude:
        conf.env.AVRDUDE = avrdude

    ctx.find_program(['avrdude'],var='AVRDUDE')
    ctx.env.port = Options.options.PORT

@extension('.hex')
def avrdude_hook(tskg, node):
    tsk = tskg.create_task('avrdude', node, "")
    tsk.mcu = tskg.mcu
    tsk.protocol = tskg.protocol
    return tsk

class UploadContext(BuildContext):
	'''Upload the build outputs'''
	cmd='upload'
	fun='upload'
	variant=''

