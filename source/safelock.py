#! /usr/bin/python3
'''
    Server for Multiprocess-safe locks.
    Client side is denova.os.lock.

    When you install "safelock" from PyPI, all the dependencies, including the
    client side, are automatically installed.

    Copyright 2019-2021 DeNova
    Last modified: 2020-06-20

    Written because none of the standard python locking mechanisms work reliably.

    To do: Drop privs

    This file is open source, licensed under GPLv3 <http://www.gnu.org/licenses/>.
'''

import os
import socketserver
import sys
from traceback import format_exc

# constants shared with denova.os.lock and safelock are
# in denova.os.lock so they can be imported easily by apps
from denova.os import lock
from denova.os.process import is_pid_active, is_program_running
from denova.os.user import require_user
from denova.python.log import Log
from denova.python.times import timestamp


CURRENT_VERSION = '1.2.8'
COPYRIGHT = 'Copyright 2019-2021 DeNova'
LICENSE = 'GPLv3'

# globals so they aren't initialized on every connection
locks = {}
count = 0
log = Log()


class LockServer(socketserver.BaseRequestHandler):
    """ The request handler class for our server.

        It is instantiated once per connection to the server, and must
        override the handle() method to implement communication to the
        client.
    """

    def handle(self):

        try:
            #log('') # white space separating connections
            #log('connect')
            data = self.request.recv(lock.MAX_PACKET_SIZE)
            #log('received data: {}'.format(data)) # DEBUG
            if data.strip():
                #log('stripped data: {}'.format(data)) # DEBUG
                request = eval(data.decode())

                action = request[lock.ACTION_KEY]
                lockname = request[lock.LOCKNAME_KEY]
                pid = request[lock.PID_KEY]

                if action == lock.LOCK_ACTION:
                    response = self.lock(action, lockname, pid)

                # unlock
                elif action == lock.UNLOCK_ACTION:
                    unlock_nonce = request[lock.NONCE_KEY]
                    response = self.unlock(action, lockname, pid, unlock_nonce)

                # bad action
                else:
                    log.warning(f'unexpected request: {request}')
                    response = None

                if response:
                    #log('response: {}'.format(response)) # DEBUG
                    data = repr(response).encode()
                    #log('send response: {}'.format(data)) # DEBUG
                    self.request.sendall(data)

            else:
                log('got empty data; did denova.os.lock send it correctly?')

        except Exception as exc:
            # just log it
            log.warning(exc)
            log(exc)

    def lock(self, action, lockname, pid):
        ''' Lock a lockname. '''

        global locks

        #log('lock "{}" {}'.format(lockname, pid))
        response = {lock.ACTION_KEY: action,
                    lock.LOCKNAME_KEY: lockname,
                   }

        if lockname in locks:
            # already locked
            #log.warning('lockname already in locks: {}'.format(lockname))
            __, lock_pid = locks[lockname]
            if is_pid_active(lock_pid):
                ok = False
                msg = f'Already locked lockname: {lockname}, pid: {lock_pid}'
                #log.warning(msg)
                response[lock.MESSAGE_KEY] = msg
            # else release the old lock
            else:
                ok = True
                log.warning(f'lock allowed because locking pid gone: {pid}')
        else:
            # not already locked
            ok = True

        response[lock.OK_KEY] = ok
        if ok:
            nonce = self.nonce()
            response[lock.NONCE_KEY] = nonce
            locks[lockname] = (nonce, pid)
            #log('locked: {}, with nonce: {}'.format(lockname, nonce))

        return response

    def unlock(self, action, lockname, unlock_pid, unlock_nonce):
        ''' Unlock a lockname. '''

        global locks

        #log('unlock "{}" {} {}'.format(lockname, unlock_pid, unlock_nonce))
        response = {lock.ACTION_KEY: action,
                    lock.LOCKNAME_KEY: lockname,
                   }

        # if locked
        if lockname in locks:

            lock_nonce, lock_pid = locks[lockname]
            if lock_nonce == unlock_nonce:

                if unlock_pid == lock_pid:
                    ok = True

                else:
                    ok = False
                    log.warning('tried to unlock lock "{}" from wrong pid: {}, locked by pid: {}'.
                                format(lockname, unlock_pid, lock_pid))
                    response[lock.MESSAGE_KEY] = f'Wrong pid: {lock_pid}'

            else:
                ok = False
                log.warning(f'tried to unlock lock "{lockname}" with wrong nonce: {lock_nonce}')
                response[lock.MESSAGE_KEY] = f'Wrong nonce: {lock_nonce}'

        else:
            ok = False
            log.warning(f'tried to unlock non-existent lock: {lockname}')
            log.debug(f'locks: {locks}')
            response[lock.MESSAGE_KEY] = f'No lock: {lockname}'

        response[lock.OK_KEY] = ok
        if ok:
            response[lock.NONCE_KEY] = lock_nonce
            del locks[lockname]

        return response

    def nonce(self):
        ''' Return a unique nonce.'''

        global count

        count += 1
        return f'{timestamp()} {count}'

def main():
    '''
        Run the safelock.

        >>> try:
        ...    main()
        ...    print('Failure')
        ... except:
        ...    print('This program must be run as root.')
        This program must be run as root.
    '''

    # We require running as root because:
    #   1) safelog is a system-wide server
    #   2) to create log files with the right ownership and permisions
    # This lets users clear out their own logs whenever they want.

    # Of course it would be better to create a separate user with
    # access only to the log dirs, and create a group for users.
    # But that makes installation a lot harder.
    # Until we automate that setup, we're root.
    require_user('root')

    try:
        # Create the server
        BIND_ADDR = (lock.SAFELOCK_HOST, lock.SAFELOCK_PORT)
        server = socketserver.TCPServer(BIND_ADDR, LockServer)

        # Activate the server
        # This will keep running until you interrupt the program with Ctrl-C
        log('start lock server')
        server.serve_forever()

        server.server_close()

    except OSError as ose:
        if 'Address already in use' in str(ose):
            if is_program_running(os.path.basename(__file__)):
                msg = f'safelock {CURRENT_VERSION} is already running'
                log(msg)
            else:
                msg = f'Port {lock.SAFELOCK_PORT} is in use. Did "safelock stop" fail to wait for clients to time out?'
                log(msg)

    except KeyboardInterrupt:
        server.shutdown()
        server.server_close()

    except Exception as exc:
        log.warning(exc)
        raise

    else:
        log(f'safelock {CURRENT_VERSION} started')


if __name__ == "__main__":

    main()
