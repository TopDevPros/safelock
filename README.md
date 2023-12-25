Safelock
---------

Mutually exclusive locks are usually the simplest way to get safe concurrent access to a shared resource.
But implementing the locks is a bear to get right. Get simple systemwide multithread, multiprocess, and multiprogram safe locks.


Description
-----------

Multithreading Concurrency in Python Solved

When you first try python multithreading and access a database, it usually works. That's because databases have some concurrency built in. With any other shared resource, your program frequently crashes. Concurrency is hard. Safelock makes it easy.

Start as many threads, subprocesses, or programs as you like. When they try to access a shared resource, Safelock only lets one run at a time.


Install
-------

git clone https://codeberg.org/topdevpros/safelock.git

Also install the "safelog" package from https://codeberg.org/topdevpros/safelog.git.


How it Works
-----------

Safelock includes a small server that must run as root. See Configuration to learn how to start the server.

In any python code that you want locked,

   from solidlibs.os.lock import locked

    with locked():
        ... your locked code ...

It's that easy.

You access the shared resource only in your locked code. No matter how many threads, subprocesses, or separate programs enter your locked code, Safelock only lets one run at a time. So only one job gets the resource at a time.

 Safelock manages python multithreading concurrency

No more crashes caused by resource conflict.

Complex apps frequently require access to the same resources at the same time. This can cause serious contention which slows down an app or crashes it. The python standard library provides some resource sharing, but it's very hard to get it right. Safelock makes it simple.

Safelock retries the lock automatically for you. If the lock times out, your app must decide whether to try again.

If you need to access a shared resource from multiple places in your code, always get the lock for that resource from a single function. Example:

        def my_locked_resource():
            return locked():


Then every time you need access to the shared resource:

        with my_locked_resource():
            ... your locked code ...


Using syncronized locks is usually the simplest way to get safe concurrent access to a shared resource. But implementing the locks is a bear to get right. Get simple systemwide multithread, multiprocess, and multiprogram safe locks.

Safelock automatically creates and manages a separate system-wide lock for every locked context block.


Configuration
-------------

Safelock uses Safelog. Both are installed when you install Safelock regardless which install method you use. Both include small servers to manage system-wide access.

The safelock and safelog commands installed in /usr/bin. The safelock and safelog servers must run as root.

You can start the servers automatically with systemd. Get the service files:

    safelock.service
    safelog.service

Then:

        systemctl enable MYPATH/safelog.service
        systemctl start safelog
        systemctl enable MYPATH/safelock.service
        systemctl start safelock

MYPATH is the directory where you saved the service files.

If you don't use systemd, start both servers by hand:

        safelog &
        safelock &


You're ready to use safelock.

Manage your python multithreading concurrency with simple locks. Get Safelock.
