import secrets
import random
from datetime import datetime, timedelta
import ipaddress
import typing
import ssl


from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
import certifi
import requests
import requests.adapters

def selfSignedCert(ip: str) -> typing.Tuple[str, str, str]:
    key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=4096,
        backend=default_backend(),
    )
    # Create a random password for private key
    password = secrets.token_urlsafe(32)

    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, ip)])
    san = x509.SubjectAlternativeName([x509.IPAddress(ipaddress.ip_address(ip))])

    basic_contraints = x509.BasicConstraints(ca=True, path_length=0)
    now = datetime.utcnow()
    cert = (
        x509.CertificateBuilder()
        .subject_name(name)
        .issuer_name(name)  # self signed, its Issuer DN must match its Subject DN.
        .public_key(key.public_key())
        .serial_number(random.SystemRandom().randint(0, 1 << 64))
        .not_valid_before(now)
        .not_valid_after(now + timedelta(days=10 * 365))
        .add_extension(basic_contraints, False)
        .add_extension(san, False)
        .sign(key, hashes.SHA256(), default_backend())
    )

    return (
        key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.BestAvailableEncryption(
                password.encode()
            ),
        ).decode(),
        cert.public_bytes(encoding=serialization.Encoding.PEM).decode(),
        password,
    )


def createClientSslContext(verify: bool = True) -> ssl.SSLContext:
    if verify:
        sslContext = ssl.create_default_context(purpose=ssl.Purpose.SERVER_AUTH, cafile=certifi.where())
    else:
        sslContext = (
            ssl._create_unverified_context()
        )  # pylint: disable=protected-access

    # Disable TLS1.0 and TLS1.1
    sslContext.options |= ssl.OP_NO_TLSv1 | ssl.OP_NO_TLSv1_1
    sslContext.minimum_version = ssl.TLSVersion.TLSv1_2
    return sslContext


def checkCertificateMatchPrivateKey(*, cert: str, key: str) -> bool:
    """
    Checks if a certificate and a private key match.
    Borh must be in PEM format.
    """
    try:
        public_cert = (
            x509.load_pem_x509_certificate(cert.encode(), default_backend())
            .public_key()
            .public_bytes(
                format=serialization.PublicFormat.PKCS1,
                encoding=serialization.Encoding.PEM,
            )
        )
        public_key = (
            serialization.load_pem_private_key(
                key.encode(), password=None, backend=default_backend()
            )
            .public_key()
            .public_bytes(
                format=serialization.PublicFormat.PKCS1,
                encoding=serialization.Encoding.PEM,
            )
        )
        return public_cert == public_key
    except Exception:
        return False

def secureRequestsSession(verify: bool = True) -> 'requests.Session':
    class UDSHTTPAdapter(requests.adapters.HTTPAdapter):
        def init_poolmanager(self, *args, **kwargs) -> None:
            sslContext = createClientSslContext(verify=verify)
            
            ssl.create_default_context(purpose=ssl.Purpose.SERVER_AUTH)

            # See urllib3.poolmanager.SSL_KEYWORDS for all available keys.
            kwargs["ssl_context"] = sslContext

            return super().init_poolmanager(*args, **kwargs)

    session = requests.Session()
    session.mount("https://", UDSHTTPAdapter())

    return session
