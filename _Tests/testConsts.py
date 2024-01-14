import os


TEST_DIR_EMPTY: str = f"{os.path.dirname(os.path.abspath(__file__))}\\Empty"  # .\_Tests
TEST_DIR_DWD: str = f"{os.path.dirname(os.path.abspath(__file__))}\\DWD_Testfiles"
TEST_DIR_GRIB2: str = f"{os.path.dirname(os.path.abspath(__file__))}\\Grib2_Testfiles"
TEST_DOWNLOAD_DIR: str = f"{os.path.dirname(os.path.abspath(__file__))}\\TestDownload"  # .\_Tests