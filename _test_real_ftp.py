# Copyright (C) 2003, Stefan Schwarzer
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
#
# - Redistributions of source code must retain the above copyright
#   notice, this list of conditions and the following disclaimer.
#
# - Redistributions in binary form must reproduce the above copyright
#   notice, this list of conditions and the following disclaimer in the
#   documentation and/or other materials provided with the distribution.
#
# - Neither the name of the above author nor the names of the
#   contributors to the software may be used to endorse or promote
#   products derived from this software without specific prior written
#   permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# ``AS IS'' AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE AUTHOR OR
# CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
# PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

# $Id: _test_real_ftp.py,v 1.1 2003/12/28 19:18:28 schwa Exp $

# Execute a test on a real FTP server (other tests use a mock server)

import getpass
import os
import time
import unittest

import ftputil
from ftputil import ftp_error


# difference between local times of server and client; if 0.0, server
#  and client are in the same timezone
EXPECTED_TIME_SHIFT = 0.0

def get_login_data():
    """
    Return a three-element tuple consisting of server name, user id
    and password. The data is requested interactively.
    """
    server = raw_input("Server: ")
    user = raw_input("User: ")
    password = getpass.getpass()
    return server, user, password


class RealFTPTest(unittest.TestCase):
    def setUp(self):
        self.host = ftputil.FTPHost(server, user, password)

    def tearDown(self):
        self.host.close()

    def test_time_shift(self):
        self.host.synchronize_times()
        self.assertEqual(self.host.time_shift(), EXPECTED_TIME_SHIFT)

    def test_mkdir_rmdir(self):
        host = self.host
        dir_name = "_testdir_"
        file_name = host.path.join(dir_name, "_nonempty_")
        # make dir and check if it's there
        host.mkdir(dir_name)
        files = host.listdir(host.curdir)
        self.failIf(dir_name not in files)
        # try to remove non-empty directory
        non_empty = host.file(file_name, "w")
        non_empty.close()
        self.assertRaises(ftp_error.PermanentError, host.rmdir, dir_name)
        # remove file and delete empty directory
        host.unlink(file_name)
        host.rmdir(dir_name)
        files = host.listdir(host.curdir)
        self.failIf(dir_name in files)

    def test_stat(self):
        host = self.host
        dir_name = "_testdir_"
        file_name = host.path.join(dir_name, "_nonempty_")
        # make a directory and a file in it
        host.mkdir(dir_name)
        fobj = host.file(file_name, "wb")
        fobj.write("abc\x12\x34def\t")
        fobj.close()
        # do some stats
        # - dir
        self.assertEqual(host.listdir(dir_name), ["_nonempty_"])
        self.assertEqual(bool(host.path.isdir(dir_name)), True)
        self.assertEqual(bool(host.path.isfile(dir_name)), False)
        self.assertEqual(bool(host.path.islink(dir_name)), False)
        # - file
        self.assertEqual(bool(host.path.isdir(file_name)), False)
        self.assertEqual(bool(host.path.isfile(file_name)), True)
        self.assertEqual(bool(host.path.islink(file_name)), False)
        self.assertEqual(host.path.getsize(file_name), 9)
        # - file's modification time; allow up to two minutes difference
        host.synchronize_times()
        server_mtime = host.path.getmtime(file_name)
        client_mtime = time.mktime(time.localtime())
        calculated_time_shift = server_mtime - client_mtime
        self.failIf(abs(calculated_time_shift-host.time_shift()) > 120)
        # clean up
        host.unlink(file_name)
        host.rmdir(dir_name)

    def make_local_file(self):
        fobj = file("_localfile_", "wb")
        fobj.write("abc\x12\x34def\t")
        fobj.close()

    def test_upload(self):
        host = self.host
        # make local file and upload it
        self.make_local_file()
        # wait; else small time differences between client and server
        #  actually could trigger the update
        time.sleep(60)
        host.upload("_localfile_", "_remotefile_", "b")
        # retry; shouldn't be uploaded
        uploaded = host.upload_if_newer("_localfile_", "_remotefile_", "b")
        self.assertEqual(uploaded, False)
        # rewrite the local file
        self.make_local_file()
        time.sleep(60)
        # retry; should be uploaded
        uploaded = host.upload_if_newer("_localfile_", "_remotefile_", "b")
        self.assertEqual(uploaded, True)
        # clean up
        os.unlink("_localfile_")
        host.unlink("_remotefile_")


if __name__ == '__main__':
    print """\
Test for real FTP access.

This test writes some files and directories on the local client and the
remote server. Thus, you may want to skip this test by pressing Ctrl-C. If
the test should run, enter the login data for the remote server. You need
write access in the login directory. This test can take a few minutes.
"""
    # get login data only once, not for each test
    server, user, password = get_login_data()
    unittest.main()
