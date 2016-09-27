# coding=utf-8
"""Verify the `repomd.xml` file generated by a YUM distributor.

.. _repomd.xml: http://createrepo.baseurl.org/
"""
import unittest
from urllib.parse import urljoin

from pulp_smash import api, selectors, utils
from pulp_smash.constants import REPOSITORY_PATH, RPM_NAMESPACES
from pulp_smash.tests.rpm.api_v2.utils import (
    gen_distributor,
    gen_repo,
    xml_handler,
)
from pulp_smash.tests.rpm.utils import set_up_module as setUpModule  # noqa pylint:disable=unused-import


class RepoMDTestCase(utils.BaseAPITestCase):
    """Tests to ensure ``repomd.xml`` can be created and is valid."""

    @classmethod
    def setUpClass(cls):
        """Generate, fetch and parse a ``repomd.xml`` file.

        Do the following:

        1. Create an RPM repository, add a YUM distributor, and publish the
           repository.
        2. Fetch the ``repomd.xml`` file from the distributor, and parse it.
        """
        super(RepoMDTestCase, cls).setUpClass()
        if selectors.bug_is_untestable(2277, cls.cfg.version):
            raise unittest.SkipTest('https://pulp.plan.io/issues/2277')

        # Create a repository. Add a yum distributor and publish it.
        client = api.Client(cls.cfg, api.json_handler)
        repo = client.post(REPOSITORY_PATH, gen_repo())
        cls.resources.add(repo['_href'])
        distributor = client.post(
            urljoin(repo['_href'], 'distributors/'),
            gen_distributor(),
        )
        client.post(
            urljoin(repo['_href'], 'actions/publish/'),
            {'id': distributor['id']},
        )

        # Fetch and parse repomd.xml
        client.response_handler = xml_handler
        path = urljoin('/pulp/repos/', distributor['config']['relative_url'])
        path = urljoin(path, 'repodata/repomd.xml')
        cls.root_element = client.get(path)

    def test_tag(self):
        """Assert the XML tree's root element has the correct tag."""
        xpath = '{{{}}}repomd'.format(RPM_NAMESPACES['metadata/repo'])
        self.assertEqual(self.root_element.tag, xpath)

    def test_data(self):
        """Assert the tree's "data" elements have correct "type" attributes."""
        xpath = '{{{}}}data'.format(RPM_NAMESPACES['metadata/repo'])
        data_elements = self.root_element.findall(xpath)
        data_types = [element.get('type') for element in data_elements]
        data_types.sort()
        self.assertEqual(
            data_types,
            ['filelists', 'group', 'other', 'primary', 'updateinfo'],
        )
