import sys, logging, codecs

from subprocess import Popen, PIPE, STDOUT
from select import poll, POLLIN

logging.basicConfig()
logger = logging.getLogger('loggerQR')

Python3 = sys.version_info[0] == 3
BaseString = str if Python3 else getattr( str, '__base__' )
Encoding = 'utf-8' if Python3 else None

class NullCodec( object ):
    "Null codec for Python 2"
    @staticmethod
    def decode( buf ):
        "Null decode"
        return buf

    @staticmethod
    def encode( buf ):
        "Null encode"
        return buf


if Python3:
    def decode( buf ):
        "Decode buffer for Python 3"
        return buf.decode( Encoding )

    def encode( buf ):
        "Encode buffer for Python 3"
        return buf.encode( Encoding )
    getincrementaldecoder = codecs.getincrementaldecoder( Encoding )
else:
    decode, encode = NullCodec.decode, NullCodec.encode

    def getincrementaldecoder():
        "Return null codec for Python 2"
        return NullCodec


def check_prereqs(*args):
    "Check for necessary programs"

    prereqs = args[0]

    for p in prereqs:
        if not quietRun('which ' + p):
            raise Exception((
                'Could not find %s - make sure that it is '
                'installed and in your $PATH') % p)

# This is a bit complicated, but it enables us to
# monitor command output as it is happening

# pylint: disable=too-many-branches,too-many-statements
def errRun( *cmd, **kwargs ):
    """Run a command and return stdout, stderr and return code
       cmd: string or list of command and args
       stderr: STDOUT to merge stderr with stdout
       shell: run command using shell
       echo: monitor output to console"""
    # By default we separate stderr, don't run in a shell, and don't echo
    stderr = kwargs.get( 'stderr', PIPE )
    shell = kwargs.get( 'shell', False )
    echo = kwargs.get( 'echo', False )

    if echo:
        # cmd goes to stderr, output goes to stdout
        logger.error( cmd, '\n' )
    if len( cmd ) == 1:
        cmd = cmd[ 0 ]
    # Allow passing in a list or a string
    if isinstance( cmd, BaseString ) and not shell:
        cmd = cmd.split( ' ' )
        cmd = [ str( arg ) for arg in cmd ]
    elif isinstance( cmd, list ) and shell:
        cmd = " ".join( arg for arg in cmd )

    # logger.error( '*** errRun:', str(cmd), '\n' )

    popen = Popen( cmd, stdout=PIPE, stderr=stderr, shell=shell )
    # We use poll() because select() doesn't work with large fd numbers,
    # and thus communicate() doesn't work either
    out, err = '', ''
    poller = poll()
    poller.register( popen.stdout, POLLIN )
    fdToFile = { popen.stdout.fileno(): popen.stdout }
    fdToDecoder = { popen.stdout.fileno(): getincrementaldecoder() }
    outDone, errDone = False, True
    if popen.stderr:
        fdToFile[ popen.stderr.fileno() ] = popen.stderr
        fdToDecoder[ popen.stderr.fileno() ] = getincrementaldecoder()
        poller.register( popen.stderr, POLLIN )
        errDone = False
    while not outDone or not errDone:
        readable = poller.poll()
        for fd, event in readable:
            f = fdToFile[ fd ]
            decoder = fdToDecoder[ fd ]
            if event & POLLIN:
                data = decoder.decode( f.read( 1024 ) )
                if echo:
                    logger.debug( data )
                if f == popen.stdout:
                    out += data
                    if data == '':
                        outDone = True
                elif f == popen.stderr:
                    err += data
                    if data == '':
                        errDone = True
            else:  # POLLHUP or something unexpected
                if f == popen.stdout:
                    outDone = True
                elif f == popen.stderr:
                    errDone = True
                poller.unregister( fd )

    returncode = popen.wait()
    # Python 3 complains if we don't explicitly close these
    popen.stdout.close()
    if stderr == PIPE:
        popen.stderr.close()
    logger.info( out, err, returncode )
    return out, err, returncode

# pylint: enable=too-many-branches
def quietRun( cmd, **kwargs ):
    "Run a command and return merged stdout and stderr"
    return errRun( cmd, stderr=STDOUT, **kwargs )[ 0 ]