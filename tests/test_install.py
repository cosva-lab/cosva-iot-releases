"""Exercise the public installer without network access or host installation."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
STUB = r'''#!PYTHON
import hashlib, json, os, pathlib, subprocess, sys
name = pathlib.Path(sys.argv[0]).name
args = sys.argv[1:]
scenario = os.environ.get('SCENARIO', '')
version = '1.0.20'
package = f'cosva-setup_{version}_arm64.deb'
payload = b'isolated installer package fixture\n'
with open(os.environ['CALL_LOG'], 'a') as log:
    log.write(json.dumps([name, *args]) + '\n')
if name == 'uname':
    print('Darwin' if scenario == 'wrong-system' else 'Linux')
elif name == 'cat' and args == ['/etc/os-release']:
    print('ID=debian\nVERSION_ID="12"' if scenario == 'wrong-os' else 'ID=ubuntu\nVERSION_ID="24.04"')
elif name == 'cat':
    sys.exit(subprocess.call(['/bin/cat', *args]))
elif name == 'dpkg':
    print('amd64' if scenario == 'wrong-arch' else 'arm64')
elif name == 'id':
    print('0' if scenario == 'root' else '1000')
elif name == 'dpkg-deb':
    value = {'Package': 'cosva-setup', 'Version': version, 'Architecture': 'arm64'}[args[-1]]
    if scenario == 'wrong-package' and args[-1] == 'Package': value = 'other-package'
    if scenario == 'wrong-version' and args[-1] == 'Version': value = '1.0.19'
    if scenario == 'wrong-package-arch' and args[-1] == 'Architecture': value = 'amd64'
    print(value)
elif name == 'curl':
    url = next(arg for arg in args if arg.startswith('https://'))
    dest = pathlib.Path(args[args.index('--output') + 1])
    if 'api.github.com' in url:
        if scenario == 'no-stable' and url.endswith('/latest'): sys.exit(22)
        if scenario == 'missing-release':
            dest.write_text('[]\n')
        elif scenario == 'unsafe-tag':
            dest.write_text('{\n  "tag_name": "../../etc/passwd"\n}\n')
        elif scenario == 'multiple-tags':
            dest.write_text('[\n  {"tag_name": "1.0.19"},\n  {"tag_name": "1.0.20"}\n]\n')
        else:
            dest.write_text(json.dumps({'tag_name': version, 'draft': False, 'prerelease': True}, indent=2))
    elif url.endswith('.sha256'):
        digest = hashlib.sha256(payload).hexdigest()
        if scenario == 'bad-receipt':
            dest.write_text(f'{digest}  /etc/shadow\n')
        else:
            dest.write_text(f'{digest}  {package}\n')
    elif url.endswith('.deb'):
        if scenario == 'failed-download': sys.exit(22)
        dest.write_bytes(b'tampered bytes' if scenario == 'bad-checksum' else payload)
    else:
        sys.exit(90)
elif name == 'sudo':
    sys.exit(subprocess.call(args[1:] if args[0] == '--' else args))
elif name == 'apt-get':
    if sys.stdin.read(): sys.exit(91)
    if scenario == 'apt-failure': sys.exit(100)
else:
    sys.exit(92)
'''


class InstallerTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='cosva-installer-test-')
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        self.bin = self.directory / 'bin'
        self.bin.mkdir()
        self.log = self.directory / 'calls.jsonl'
        for name in ('curl', 'uname', 'cat', 'dpkg', 'dpkg-deb', 'id', 'sudo', 'apt-get'):
            path = self.bin / name
            path.write_text(STUB.replace('PYTHON', os.sys.executable, 1))
            path.chmod(0o755)

    def run_installer(self, *args, scenario='', piped=False):
        env = dict(os.environ, PATH=f'{self.bin}{os.pathsep}{os.environ["PATH"]}',
                   CALL_LOG=str(self.log), SCENARIO=scenario)
        env.pop('BASH_ENV', None)
        if piped:
            command = ['bash', '-s', '--', *args]
            text = (ROOT / 'install.sh').read_text()
        else:
            command = ['bash', str(ROOT / 'install.sh'), *args]
            text = ''
        result = subprocess.run(command, input=text, text=True, env=env,
                                capture_output=True, timeout=20)
        calls = [json.loads(line) for line in self.log.read_text().splitlines()] if self.log.exists() else []
        return result, calls

    def assert_no_install(self, result, calls):
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertFalse(any(call[0] in ('sudo', 'apt-get') for call in calls), calls)

    def test_help_has_no_host_or_network_actions(self):
        result, calls = self.run_installer('--help')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(calls, [['cat']])

    def test_stable_queries_only_certified_channel(self):
        result, calls = self.run_installer()
        self.assertEqual(result.returncode, 0, result.stderr)
        requests = [call for call in calls if call[0] == 'curl']
        self.assertTrue(any(arg.endswith('/releases/latest') for arg in requests[0]))
        self.assertFalse(any('per_page' in arg for call in requests for arg in call))

    def test_candidate_can_run_from_a_pipe_and_preserves_configuration(self):
        result, calls = self.run_installer('--candidate', piped=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(any('?per_page=1' in arg for call in calls for arg in call))
        apt = next(call for call in calls if call[0] == 'apt-get')
        self.assertIn('Dpkg::Options::=--force-confold', apt)
        self.assertIn('Dpkg::Options::=--force-confdef', apt)
        self.assertIn('--yes', apt)
        self.assertTrue(any(call[0] == 'sudo' for call in calls))
        self.assertFalse(Path(apt[-1]).parent.exists(), 'temporary downloads must be cleaned')

    def test_pinned_version_avoids_latest_lookup(self):
        result, calls = self.run_installer('--version', '1.0.20')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(any('api.github.com' in arg for call in calls for arg in call))

    def test_root_does_not_require_sudo(self):
        result, calls = self.run_installer('--version', '1.0.20', scenario='root')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(any(call[0] == 'sudo' for call in calls))

    def test_bad_arguments_do_not_download(self):
        for args in [('--version',), ('--version', ''), ('--unknown',), ('--version', '../other'),
                     ('--candidate', '--version', '1.0.20')]:
            with self.subTest(args=args):
                if self.log.exists(): self.log.unlink()
                result, calls = self.run_installer(*args)
                self.assert_no_install(result, calls)
                self.assertFalse(any(call[0] == 'curl' for call in calls))

    def test_wrong_platform_does_not_download(self):
        for scenario in ('wrong-system', 'wrong-os', 'wrong-arch'):
            with self.subTest(scenario=scenario):
                if self.log.exists(): self.log.unlink()
                result, calls = self.run_installer(scenario=scenario)
                self.assert_no_install(result, calls)
                self.assertFalse(any(call[0] == 'curl' for call in calls))

    def test_no_stable_does_not_fall_back_to_candidate(self):
        result, calls = self.run_installer(scenario='no-stable')
        self.assert_no_install(result, calls)
        self.assertIn('--candidate', result.stderr)
        self.assertEqual(len([call for call in calls if call[0] == 'curl']), 1)

    def test_untrusted_or_incomplete_download_never_reaches_sudo(self):
        for scenario in ('missing-release', 'unsafe-tag', 'multiple-tags', 'failed-download',
                         'bad-checksum', 'bad-receipt', 'wrong-package', 'wrong-version',
                         'wrong-package-arch'):
            with self.subTest(scenario=scenario):
                if self.log.exists(): self.log.unlink()
                result, calls = self.run_installer('--candidate', scenario=scenario)
                self.assert_no_install(result, calls)

    def test_apt_failure_is_not_reported_as_success(self):
        result, calls = self.run_installer('--candidate', scenario='apt-failure')
        self.assertEqual(result.returncode, 100, result.stderr)
        self.assertNotIn('helper instalado', result.stdout)
        apt = next(call for call in calls if call[0] == 'apt-get')
        self.assertFalse(Path(apt[-1]).parent.exists())

    def test_truncated_pipe_does_not_execute_partial_script(self):
        script = (ROOT / 'install.sh').read_text().split('\ncosva_install "$@"')[0]
        env = dict(os.environ, PATH=f'{self.bin}{os.pathsep}{os.environ["PATH"]}',
                   CALL_LOG=str(self.log))
        result = subprocess.run(['bash'], input=script, text=True, env=env,
                                capture_output=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(self.log.exists())


if __name__ == '__main__':
    unittest.main()
