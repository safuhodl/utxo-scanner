# UTXO Scanner

This is a simple UTXO scanner that takes in a list of Bitcoin addresses via stdin, a starting
block height, scans the blockchain up to a particular height and finds the unspent outputs for
the passed addresses.

The program requires RPC access to a bitcoind instance (configure `scanner.conf` with the correct
parameters).

Usage:

```bash
$ ./scanner.py 509414 -n 50
  1Df6Xd9G1qmfLV1ZGsJRQuobZNjKm3kkvD
  1uCQPHp1Co1pScu95VvyJSDBArJeWLZtd
  1KAqd4skcmUmUJQKYKxuSbU2TDCjaUJJ8M
  ...
```

