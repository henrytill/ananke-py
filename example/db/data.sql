CREATE TABLE IF NOT EXISTS entries (
    id TEXT PRIMARY KEY NOT NULL,
    keyid TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    description TEXT NOT NULL,
    identity TEXT,
    ciphertext TEXT NOT NULL,
    meta TEXT
);

INSERT INTO entries(id, keyid, timestamp, description, identity, ciphertext)
VALUES(
    '88a8b87f-01b1-4965-8362-6572951a0d2d',
    '371C136C',
    '2023-06-12T08:13:45.171872642Z',
    'https://www.foomail.com',
    'quux',
    'hQEMAzc/TVLd4/C8AQf5AWOscf34zklI490vQKnp5tI0xA0ntYuqiof7EEolHGC9V0jOjft1eBs38SMvI4MEskjKuZR+JE/m40g9xl3oSeXYbPLDAdgP0k4P7sBznbzYotRoFxKEi1mnYi/MxBtNrjG+nttxeTWXx3EseKDQfu3lz749XScwyY5aEzO+LbjQHGzqUMcntHRmareC63Do6S3pgMio1bKTuhGl87Ijf4bfw6NARg8GlF8UDUZDLnDpaaJjxJyW17owiV0SS7IC81ETydKM9wz60xUo23ow3fpEmcUhFHUspbXfSNzh2cABIfgRDhLMlZrMyuGQr9UBjw6cxMbwuNWJ5ECCGm3n3tJKAdzBFRyudhcHPwI7fm2nrthdqTJ2l+89EuP09aJsCvo4BpmAJcwSPxkrsCqirAsgctveeu+9F1LOymY9J8JGvnUu/81kYP9HYfA='
);

INSERT INTO entries(id, keyid, timestamp, description, identity, ciphertext)
VALUES(
    'f1e981ac-4d3d-4b1d-8ed5-9dd722ceab6a',
    '371C136C',
    '2023-06-12T08:14:19.928402975Z',
    'https://www.bazbank.com',
    'quux',
    'hQEMAzc/TVLd4/C8AQf/QRz4kazJvOmtlUY/raQIqDMS0raFf6Pc8dfilAHnTilxfEFP4t+/l0bLbo3yncG7iDXnlMltxqJrHxQQKbhRj2M8t214I8t26QOZ55Hw0CYs2iyh2APMZGO+CWkps7hst1WB653CSNCTEyARrhTPSkJRTpzox9I8gNHcd3Fp7QvCKOTeDaSxvmJymlsJc4cNAbC/rX3z9n39QrfZmWgeffZ3DQC72rs+Let8OHrTKUMhpyeBWaA6/Lv1X9DObOseAk9zyxVgiH76hdhE9ssMgUHMURwr0Sspw1XDVagqqQlJjNbXjQI/aQ/aW2WbSMTnzJTTUPah4fn0acmNgTYMYtJQAZeTkdpCzLLrBvhXnzmagPF+bVDJY+YtUHOZclSow3gNxPq60VA4Fpy411fA/WjI+Iwnnxsyr2Ue0/qkZTO2s1p7TWNWBl7BBkhCOUL2CX8='
);

INSERT INTO entries(id, keyid, timestamp, description, identity, ciphertext)
VALUES(
    'ba9d7666-f201-4d78-ae30-300ff236de7f',
    '371C136C',
    '2023-06-12T08:16:30.985240519Z',
    'https://www.barphone.com',
    'quux',
    'hQEMAzc/TVLd4/C8AQgAjAWcRoFoTI6k62fHtArOe6uCyEp6TDlLY5NhGKCRWKxDqggZByPDY59KzX/IqE6UgrQmvRM1yrEGvWVSM8lq43a5m8zDLNLIWVgEv0eUH50oYeB9I2vnL04L6bMPLkCwb19oFD1PUFQ9KqsmTQXyMDHkcXhAXk3mHcki1Ven38edw38Tf6xwrf/ISCSC/wDkgse6E+1+dbsEo5aWy3WWxzAFV+kARu10Mje3U+yGMBSs0Se6E/Z+iRSkCJhwOor//7W//Y0KuKzNrc3S6D4yXXIQ7lQJ33vNPAPCC5FGMwsw/StLRShNH6DHVbAp6Ws42J/9OTexwFitGY08UAX0ENJTAXhUTUGyQ23CIVfDRcWAOdsiikE7Ss37lXjrkJM86PTGrEMmY0psSrfpahkfvnmC2BsLaVTbSqz20t8J3tl5C8nlamu7AoATtDInOJcew+XcqMo='
);

INSERT INTO entries(id, keyid, timestamp, description, identity, ciphertext)
VALUES(
    'ef745ae7-d3ff-4ecd-aa32-0e913f69b030',
    '371C136C',
    '2024-04-29T20:46:16.070012530Z',
    'https://www.foomail.com',
    'altquux',
    'hQEMAzc/TVLd4/C8AQf+OCzAMrtrRm+SSBSyxfzWydSRc33AtVths6VHIW+vOFQglwQM78mXfqe/SSqjhe6DYZbYHttz1pSvOwDyJjOMrMqTID6gvm/VCKnuyGUN/I6K05shf64Ko3dnml1Pxr+P7ctohI/TV6hQQUYoeNbNBqTnVCPL4L0mAkcx71Qv7ktG3q22QeatDDY6AlPpWqMquU0JNE0qg/1bRyosNAGB31nUelSc9XVrgjSU2ni7tZ+7vU8iwc2OOC/NRPEnimwhWmwh+sNoHNsv06HPkcuzYVCURPiRMLshKnEWRKSDYYq1Vv7koG+9FQm57HFM+Vs0jb+AHj5FXjjwCuOl/Sybz9JOARLX6AoFR5Wg5U7+R87tY8pH1upYs5Cu1RnbbjF0OiC7KCNqhQMzmAREjGDk3tFPfhp/46Giwx0ACTsBl6L8Z5+Qik+Hnf4bj4OsnUzQ'
);
