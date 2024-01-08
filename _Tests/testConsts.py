import os

TEST_DIR_MODEL_D2: str = f"{os.path.dirname(os.path.abspath(__file__))}\\TestfilesModel_D2"  # .\_Tests
TEST_DIR_MODEL_EU: str = f"{os.path.dirname(os.path.abspath(__file__))}\\TestfilesModel_EU"  # .\_Tests
EMPTY_TEST_DIR: str = f"{os.path.dirname(os.path.abspath(__file__))}\\Empty"  # .\_Tests
DIR_WITH_INVALID_FILES: str = f"{os.path.dirname(os.path.abspath(__file__))}\\InvalidFiles"  # .\_Tests
DOWNLOAD_DIR: str = f"{os.path.dirname(os.path.abspath(__file__))}\\TestDownload"  # .\_Tests
TEST_DIR_DWD: str = f"{os.path.dirname(os.path.abspath(__file__))}\\TestfilesDWD"  # .\_Tests
TEST_DIR_NOT_EXIST: str = f"{os.path.dirname(os.path.abspath(__file__))}\\Blah"  # .\_Tests
TEST_DIR_DWD_ONLY_INIT: str = f"{os.path.dirname(os.path.abspath(__file__))}\\OnlyDWDInitFile"  # .\_Tests
TEST_DIR_MODEL_D2_INVALID_FILES: str = f"{os.path.dirname(os.path.abspath(__file__))}\\InvalidModelFiles"  # .\_Tests
TEST_DIR_MODEL_D2_MIX_FILES: str = f"{os.path.dirname(os.path.abspath(__file__))}\\TestfilesModel_D2_mix"  # .\_Tests

EXISTING_TESTFILE_D2: str = f"{TEST_DIR_MODEL_D2}\\Test001.grib2"
EXISTING_TESTFILE_D2_2: str = f"{TEST_DIR_MODEL_D2}\\Test003.grib2"
EXISTING_TESTFILE_EU: str = f"{TEST_DIR_MODEL_EU}\\Test001.grib2"
NOT_EXISTING_TESTFILE_D2: str = f"{TEST_DIR_MODEL_D2}\\NoExistingFile.grib2"
BZ2_ARCHIVE: str = f"{TEST_DIR_MODEL_D2}\\Test002.grib2.bz2"
EXTRACTED_FILE: str = f"{TEST_DIR_MODEL_D2}\\Test002.grib2"
INVALID_GRIDTYPE_FILE: str = f"{DIR_WITH_INVALID_FILES}\\Invalid_Gridtype.grib2"
DWD_INIT_FILE: str = f"{TEST_DIR_DWD}\\N_Stundenwerte_Beschreibung_Stationen.txt"
DWD_TESTFILE_ID_96: str = f"{TEST_DIR_DWD}\\produkt_n_stunde_20220626_20231227_00096.txt"
DWD_TESTFILE_ID_427: str = f"{TEST_DIR_DWD}\\produkt_n_stunde_20220626_20220801_00427.txt"
DWD_EMPTYFILE: str = f"{TEST_DIR_DWD}\\EmptyFile.txt"
TRASH_DWD_FILE: str = f"{TEST_DIR_DWD}\\produkt_n_stunde_20220626_20220801_99999.txt"
MODEL_FILE_NO_LATLON: str = f"{TEST_DIR_MODEL_D2_INVALID_FILES}\\no_latlon.grib2"
MODEL_FILE_TOO_MUCH_FORECAST: str = f"{TEST_DIR_MODEL_D2_INVALID_FILES}\\too_much_forecast.grib2"
MODEL_FILE_WRONG_MODEL: str = f"{TEST_DIR_MODEL_D2_INVALID_FILES}\\wrong_model.grib2"
MODEL_FILE_WRONG_PARAM: str = f"{TEST_DIR_MODEL_D2_INVALID_FILES}\\wrong_param.grib2"
