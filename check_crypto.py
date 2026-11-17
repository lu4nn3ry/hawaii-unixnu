try:
    import cryptography
    print("cryptography OK")
except ImportError:
    print("cryptography NÃO disponível")

try:
    import Crypto
    print("pycryptodome OK")
except ImportError:
    print("pycryptodome NÃO disponível")

try:
    import rsa
    print("rsa OK")
except ImportError:
    print("rsa NÃO disponível")
