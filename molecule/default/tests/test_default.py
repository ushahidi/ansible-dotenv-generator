import os

import testinfra.utils.ansible_runner

testinfra_hosts = testinfra.utils.ansible_runner.AnsibleRunner(
    os.environ['MOLECULE_INVENTORY_FILE']).get_hosts('all')


def test_sample_files(host):
    for test_file in host.ansible.get_variables()['test_files']:
        print(test_file)
        out_f = host.file(test_file["dest"])
        result = open(test_file["result"], "r").read()

        assert out_f.exists
        assert out_f.content == result
