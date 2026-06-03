from typing import Generator

import pytest
from qm import QuantumMachinesManager
from qm_saas import QmSaas

HOST_IP = "localhost"
DEFAULT_PORT = 9510


def pytest_addoption(parser):
    parser.addoption(
        "--qop-version",
        action="store",
        default="latest",
        help="Cloud simulator QOP version, e.g. v3_6_2. Pass 'latest' for the latest available version or 'local' to use a local simulator.",
    )
    parser.addoption(
        "--cloudsim-host",
        action="store",
        default=None,
        help="Cloud simulator host",
    )
    parser.addoption(
        "--cloudsim-email",
        action="store",
        default=None,
        help="Cloud simulator user email",
    )
    parser.addoption(
        "--cloudsim-pwd",
        action="store",
        default=None,
        help="Cloud simulator password",
    )


@pytest.fixture(scope="session")
def qop_cloud_sim_version(request: pytest.FixtureRequest) -> str:
    return request.config.getoption("--qop-version")


@pytest.fixture(scope="session")
def cloud_sim_host(request: pytest.FixtureRequest) -> str:
    return request.config.getoption("--cloudsim-host")


@pytest.fixture(scope="session")
def cloud_sim_email(request: pytest.FixtureRequest) -> str:
    return request.config.getoption("--cloudsim-email")


@pytest.fixture(scope="session")
def cloud_sim_pwd(request: pytest.FixtureRequest) -> str:
    return request.config.getoption("--cloudsim-pwd")


def _get_local_qmm() -> QuantumMachinesManager:
    return QuantumMachinesManager(host=HOST_IP, port=DEFAULT_PORT)


@pytest.fixture(scope="session")
def qmm(
    qop_cloud_sim_version: str,
    cloud_sim_host: str,
    cloud_sim_email: str,
    cloud_sim_pwd: str,
) -> Generator[QuantumMachinesManager, None, None]:
    if qop_cloud_sim_version == "local":
        yield _get_local_qmm()
    else:
        client = QmSaas(email=cloud_sim_email, password=cloud_sim_pwd, host=cloud_sim_host)
        version = None if qop_cloud_sim_version == "latest" else qop_cloud_sim_version
        with client.simulator(version) as sim_instance:
            qmm = QuantumMachinesManager(
                host=sim_instance.host,
                port=sim_instance.port,
                connection_headers=sim_instance.default_connection_headers,
            )
            yield qmm
