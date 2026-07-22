import unittest

from modules.tools import profiles


class ProfileTests(unittest.TestCase):
    def test_standard_profile_adds_no_extra_arguments(self):
        self.assertEqual(profiles.args_for('httpx', 'standard'), [])

    def test_intensive_profile_is_bounded(self):
        for tool in ('sublist3r', 'sherlock', 'subfinder', 'httpx',
                     'nuclei', 'gau'):
            args = profiles.args_for(tool, 'intensive')
            self.assertTrue(args, tool)
            rendered = ' '.join(args)
            self.assertNotIn('dast', rendered)
            self.assertNotIn('fuzz-aggression', rendered)
            self.assertNotIn('unsafe', rendered)

    def test_nuclei_profile_excludes_disruptive_templates(self):
        args = profiles.args_for('nuclei', 'intensive')
        self.assertIn('-exclude-tags', args)
        self.assertIn('dos,fuzz', args)

    def test_intensive_rates_are_higher_but_bounded(self):
        httpx = profiles.args_for('httpx', 'intensive')
        nuclei = profiles.args_for('nuclei', 'intensive')
        self.assertEqual(httpx[httpx.index('-threads') + 1], '60')
        self.assertEqual(httpx[httpx.index('-rate-limit') + 1], '175')
        self.assertEqual(nuclei[nuclei.index('-concurrency') + 1], '30')
        self.assertEqual(nuclei[nuclei.index('-rate-limit') + 1], '175')

    def test_intensive_profile_rejects_bound_overrides(self):
        for flag in (
                '-threads', '--threads', '--threads=10000', '-rate-limit',
                '--rate-limit=0', '-unsafe', '--unsafe', '--config'):
            with self.subTest(flag=flag):
                with self.assertRaises(ValueError):
                    profiles.validate_user_args('httpx', [flag], 'intensive')

    def test_returned_arguments_are_not_shared(self):
        first = profiles.args_for('gau', 'intensive')
        first.append('--changed')
        self.assertNotIn('--changed', profiles.args_for('gau', 'intensive'))

    def test_unknown_profile_is_rejected(self):
        with self.assertRaises(ValueError):
            profiles.normalize('unbounded')


if __name__ == '__main__':
    unittest.main()
