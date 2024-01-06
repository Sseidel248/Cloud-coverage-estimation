import os

TEST_DIR_MODEL_D2 = f"{os.path.dirname(os.path.abspath(__file__))}\\TestfilesModel_D2"  # .\_Tests
TEST_DIR_MODEL_EU = f"{os.path.dirname(os.path.abspath(__file__))}\\TestfilesModel_EU"  # .\_Tests
EMPTY_TEST_DIR = f"{os.path.dirname(os.path.abspath(__file__))}\\Empty"  # .\_Tests
DIR_WITH_INVALID_FILES = f"{os.path.dirname(os.path.abspath(__file__))}\\InvalidFiles"  # .\_Tests
DOWNLOAD_DIR = f"{os.path.dirname(os.path.abspath(__file__))}\\TestDownload"  # .\_Tests
TEST_DIR_DWD = f"{os.path.dirname(os.path.abspath(__file__))}\\TestfilesDWD"  # .\_Tests
TEST_DIR_NOT_EXIST = f"{os.path.dirname(os.path.abspath(__file__))}\\Blah"  # .\_Tests
TEST_DIR_DWD_ONLY_INIT = f"{os.path.dirname(os.path.abspath(__file__))}\\OnlyDWDInitFile"  # .\_Tests
TEST_DIR_MODEL_D2_INVALID_FILES = f"{os.path.dirname(os.path.abspath(__file__))}\\InvalidModelFiles"  # .\_Tests
TEST_DIR_MODEL_D2_MIX_FILES = f"{os.path.dirname(os.path.abspath(__file__))}\\TestfilesModel_D2_mix"  # .\_Tests


EXISTING_TESTFILE_D2 = f"{TEST_DIR_MODEL_D2}\\Test001.grib2"
EXISTING_TESTFILE_D2_2 = f"{TEST_DIR_MODEL_D2}\\Test003.grib2"
EXISTING_TESTFILE_EU = f"{TEST_DIR_MODEL_EU}\\Test001.grib2"
NOT_EXISTING_TESTFILE_D2 = f"{TEST_DIR_MODEL_D2}\\NoExistingFile.grib2"
BZ2_ARCHIVE = f"{TEST_DIR_MODEL_D2}\\Test002.grib2.bz2"
EXTRACTED_FILE = f"{TEST_DIR_MODEL_D2}\\Test002.grib2"
INVALID_GRIDTYPE_FILE = f"{DIR_WITH_INVALID_FILES}\\Invalid_Gridtype.grib2"
DWD_INIT_FILE = f"{TEST_DIR_DWD}\\N_Stundenwerte_Beschreibung_Stationen.txt"
DWD_TESTFILE_ID_96 = f"{TEST_DIR_DWD}\\produkt_n_stunde_20220626_20231227_00096.txt"
DWD_TESTFILE_ID_427 = f"{TEST_DIR_DWD}\\produkt_n_stunde_20220626_20220801_00427.txt"
DWD_EMPTYFILE = f"{TEST_DIR_DWD}\\EmptyFile.txt"
TRASH_DWD_FILE = f"{TEST_DIR_DWD}\\produkt_n_stunde_20220626_20220801_99999.txt"
MODEL_FILE_NO_LATLON = f"{TEST_DIR_MODEL_D2_INVALID_FILES}\\no_latlon.grib2"
MODEL_FILE_TOO_MUCH_FORECAST = f"{TEST_DIR_MODEL_D2_INVALID_FILES}\\too_much_forecast.grib2"
MODEL_FILE_WRONG_MODEL = f"{TEST_DIR_MODEL_D2_INVALID_FILES}\\wrong_model.grib2"
MODEL_FILE_WRONG_PARAM = f"{TEST_DIR_MODEL_D2_INVALID_FILES}\\wrong_param.grib2"
