from lib.packages.Package import Package
from lib.utils.constants import SEPARATOR
from lib.utils.enums import PackageType
from lib.packages.AckPackage import AckPackage
from lib.packages.DataPackage import DataPackage
from lib.packages.FinPackage import FinPackage
from lib.packages.InitPackage import InitPackage
from lib.utils.package_error import PackageErr

class FactoryPackage:
    @staticmethod
    def recover_package(raw_data: bytes) -> Package:
        package_type = int(raw_data.split(SEPARATOR.encode())[0])

        if package_type == PackageType.INIT.value:
            package = InitPackage.from_bytes(raw_data)
        elif package_type == PackageType.ACK.value:
            package = AckPackage.from_bytes(raw_data)
        elif package_type == PackageType.DATA.value:
            package = DataPackage.from_bytes(raw_data)
        elif package_type == PackageType.FIN.value:
            package = FinPackage.from_bytes(raw_data)
        elif package_type == PackageType.NACK.value:
            package = Package.from_bytes(raw_data)
        else:
            raise ValueError(f"Unknown package type: {package_type}")
        
        if not package.valid:
            raise PackageErr("Invalid package received")
        return package