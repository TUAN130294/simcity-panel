"""SSH/SFTP wrapper over paramiko for browsing and editing SimCity files on the VM.

Byte-faithful editing: files are read/written with a chosen encoding (default
latin-1, which maps bytes 1:1). Editing only ASCII constants therefore never
corrupts the surrounding non-ASCII (GBK/TCVN3) bytes.
"""
import io
import stat
import posixpath
import paramiko


class SSHService:
    def __init__(self, host, port, user, password):
        self.host = host
        self.port = int(port or 22)
        self.user = user
        self.password = password

    def _connect(self):
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(
            self.host, self.port, self.user, self.password,
            timeout=12, banner_timeout=15, auth_timeout=15,
            look_for_keys=False, allow_agent=False,
        )
        return client

    def test(self):
        client = self._connect()
        try:
            _in, out, _err = client.exec_command("echo ok && uname -a", timeout=15)
            return out.read().decode("utf-8", "replace").strip()
        finally:
            client.close()

    def run(self, cmd, timeout=60):
        client = self._connect()
        try:
            _in, out, err = client.exec_command(cmd, timeout=timeout)
            o = out.read().decode("utf-8", "replace")
            e = err.read().decode("utf-8", "replace")
            return o, e
        finally:
            client.close()

    def list_dir(self, path):
        client = self._connect()
        try:
            sftp = client.open_sftp()
            entries = []
            for attr in sftp.listdir_attr(path):
                is_dir = stat.S_ISDIR(attr.st_mode)
                entries.append({
                    "name": attr.filename,
                    "path": posixpath.join(path, attr.filename),
                    "is_dir": is_dir,
                    "size": attr.st_size,
                })
            entries.sort(key=lambda e: (not e["is_dir"], e["name"].lower()))
            return entries
        finally:
            client.close()

    def read_file(self, path, encoding="latin-1"):
        client = self._connect()
        try:
            sftp = client.open_sftp()
            with sftp.open(path, "rb") as f:
                raw = f.read()
            return raw.decode(encoding, "replace")
        finally:
            client.close()

    def write_file(self, path, content, encoding="latin-1", make_backup=True):
        """Write content to path. Creates a timestamp-free .bak (single rolling backup)
        by copying the current remote file to <path>.bak before overwriting."""
        client = self._connect()
        try:
            sftp = client.open_sftp()
            if make_backup:
                try:
                    with sftp.open(path, "rb") as f:
                        old = f.read()
                    with sftp.open(path + ".bak", "wb") as b:
                        b.write(old)
                except IOError:
                    pass  # file may not exist yet
            data = content.encode(encoding, "replace")
            with sftp.open(path, "wb") as f:
                f.write(data)
            return len(data)
        finally:
            client.close()
