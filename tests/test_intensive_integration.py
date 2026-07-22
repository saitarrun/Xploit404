import contextlib
import io
import os
import unittest
from unittest import mock

import menu
from modules.tools import gau, httpx, nmap_scan, nuclei, profiles, subfinder


class IntensiveCommandTests(unittest.TestCase):
    def _command_from(self, module, target, **kwargs):
        with mock.patch.object(module, 'binary', return_value='/tool'), \
                mock.patch.object(module.subprocess, 'call', return_value=0) as call:
            module.run(target, profile='intensive', **kwargs)
        return call.call_args.args[0]

    def test_subfinder_expands_sources_with_rate_limit(self):
        command = self._command_from(subfinder, 'example.com')
        self.assertIn('-all', command)
        self.assertEqual(command[command.index('-rl') + 1], '15')

    def test_httpx_adds_rich_probes_and_bounded_rate(self):
        command = self._command_from(httpx, 'https://example.com')
        self.assertIn('-tech-detect', command)
        self.assertIn('-tls-grab', command)
        self.assertEqual(command[command.index('-threads') + 1], '60')
        self.assertEqual(command[command.index('-rate-limit') + 1], '175')

    def test_httpx_rejects_overrides_of_intensive_bounds(self):
        with mock.patch.object(httpx, 'binary', return_value='/tool'):
            with self.assertRaisesRegex(ValueError, 'cannot override'):
                httpx.run('https://example.com', '-threads 10000',
                          profile='intensive')

    def test_nuclei_broadens_severity_without_disruptive_templates(self):
        command = self._command_from(
            nuclei, 'https://example.com',
            severity='info,low,medium,high,critical')
        self.assertIn('info,low,medium,high,critical', command)
        self.assertEqual(command[command.index('-exclude-tags') + 1], 'dos,fuzz')
        self.assertEqual(command[command.index('-concurrency') + 1], '30')
        self.assertEqual(command[command.index('-rate-limit') + 1], '175')

    def test_gau_includes_subdomains_with_bounded_workers(self):
        command = self._command_from(gau, 'example.com')
        self.assertIn('--subs', command)
        self.assertEqual(command[command.index('--threads') + 1], '5')

    def test_nmap_has_explicit_intensive_profile(self):
        _, args = nmap_scan.PROFILES[nmap_scan.INTENSIVE_PROFILE]
        self.assertIn('-p-', args)
        self.assertIn('--version-all', args)
        self.assertNotIn('-T5', args)


class ProfileActivationTests(unittest.TestCase):
    def setUp(self):
        menu.activate_profile('standard')

    def tearDown(self):
        menu.activate_profile('standard')

    def test_intensive_profile_requires_authorization(self):
        with self.assertRaises(PermissionError):
            menu.activate_profile('intensive')

    def test_interactive_confirmation_is_exact(self):
        answers = iter(['intensive', 'AUTHORIZED'])
        with contextlib.redirect_stdout(io.StringIO()):
            changed = menu.set_profile(lambda _: next(answers))
        self.assertTrue(changed)
        self.assertEqual(menu.SESSION['profile'], 'intensive')

    def test_cli_intensive_mode_requires_environment_confirmation(self):
        with mock.patch.dict(os.environ, {}, clear=True), \
                contextlib.redirect_stdout(io.StringIO()):
            result = menu.main(['--intensive', 'help'])
        self.assertEqual(result, 2)
        self.assertEqual(menu.SESSION['profile'], 'standard')

    def test_cli_intensive_mode_accepts_environment_confirmation(self):
        with mock.patch.dict(os.environ, {'STRIKER_AUTHORIZED': '1'}, clear=True), \
                contextlib.redirect_stdout(io.StringIO()):
            result = menu.main(['--intensive', 'help'])
        self.assertEqual(result, 0)
        self.assertEqual(menu.SESSION['profile'], 'intensive')

    def test_intensive_wayback_raises_bounded_result_limit(self):
        menu.activate_profile('intensive', authorized=True)
        with mock.patch.object(menu, 'session_prompt', return_value='example.com'), \
                mock.patch('modules.tools.wayback.run') as run:
            menu.run_wayback()
        run.assert_called_once_with(
            'example.com', menu.OUTPUT_DIR,
            limit=profiles.setting('wayback_limit', 'intensive'))


if __name__ == '__main__':
    unittest.main()
