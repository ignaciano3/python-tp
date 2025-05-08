from lib.packages.Package import Package
from lib.utils.constants import SEPARATOR
from lib.utils.enums import PackageType
from lib.packages.AckPackage import AckPackage
from lib.packages.DataPackage import DataPackage
from lib.packages.FinPackage import FinPackage
from lib.packages.InitPackage import InitPackage
from lib.packages.NackPackage import NackPackage


class FactoryPackage:
    @staticmethod
    def recover_package(raw_data: bytes) -> Package:
        package_type = int(raw_data.split(SEPARATOR.encode())[0])

        if package_type == PackageType.INIT.value:
            return InitPackage.from_bytes(raw_data)
        elif package_type == PackageType.ACK.value:
            return AckPackage.from_bytes(raw_data)
        elif package_type == PackageType.DATA.value:
            return DataPackage.from_bytes(raw_data)
        elif package_type == PackageType.FIN.value:
            return FinPackage.from_bytes(raw_data)
        elif package_type == PackageType.NACK.value:
            return NackPackage.from_bytes(raw_data)
        else:
            raise ValueError(f"Unknown package type: {package_type}")
