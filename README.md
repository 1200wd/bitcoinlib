# bitcoinlib
Compact Bitcoin library to work with Private and Public Keys

Usage Example:

#### Generate random Private Key
```python
k = PrivateKey()
print k.get_hex()
```

#### Import Private Key (WIF format)
```python
privatekey_wif = 'L3RyKcjp8kzdJ6rhGhTC5bXWEYnC2eL3b1vrZoduXMht6m9MQeHy'
k = PrivateKey(privatekey_wif)
print k.get_hex()
```
 
#### Show public key and bitcoin address
```python
public_key_hex = k.get_public()
print public_key_hex
K = PublicKey(public_key_hex)
print K.get_address()
```

# ToDo
- Add P2SH addresses
- Add Wallet functions
- Add HD functions
 