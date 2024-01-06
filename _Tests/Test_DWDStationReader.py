import os.path
import unittest
import _Tests.testConsts as tc
import Lib.Consts.GeneralConts as gConst
import Lib.Consts.ErrorWarningConsts as ewConst
from datetime import datetime
from unittest.mock import patch
from Lib.DWDStationReader import DWDStation, InvalidStations, DWDStations
from Lib.DWDStationReader import _get_init_file, _read_id, init_dwd_stations


INIT_DATA_ID_00096 = ("00096 20190410 20231227             50     52.9437   12.8518 Neuruppin-Alt Ruppin"
                      "                                                             Brandenburg ")
INIT_DATA_ID_00954 = ("00954 19790101 20220720              0     54.1796    7.4587 UFS Deutsche Bucht"
                      "                                                               Hamburg")


class TestDWDStation(unittest.TestCase):
    def test__init__(self):
        dwd = DWDStation(INIT_DATA_ID_00096)
        self.assertEqual(dwd.filename, "")
        self.assertFalse(dwd.loaded)
        self.assertEqual(dwd.id, 96)
        self.assertEqual(dwd.date_from, datetime(2019, 4, 10, 00, 00))
        self.assertEqual(dwd.date_to, datetime(2023, 12, 27, 00, 00))
        self.assertEqual(dwd.height, 50)
        self.assertEqual(dwd.lat, 52.9437)
        self.assertEqual(dwd.lon, 12.8518)

    def test_invalid__init__(self):
        dwd = DWDStation("")
        self.assertEqual(dwd.filename, "")
        self.assertFalse(dwd.loaded)
        self.assertEqual(dwd.id, -1)
        self.assertEqual(dwd.date_from, gConst.NONE_DATETIME)
        self.assertEqual(dwd.date_to, gConst.NONE_DATETIME)
        self.assertEqual(dwd.height, -1)
        self.assertEqual(dwd.lat, -1)
        self.assertEqual(dwd.lon, -1)

    def test_load_data(self):
        dwd = DWDStation(INIT_DATA_ID_00096)
        self.assertEqual(dwd.date_from, datetime(2019, 4, 10, 00, 00))
        self.assertEqual(dwd.date_to, datetime(2023, 12, 27, 00, 00))
        dwd.load_data(tc.DWD_TESTFILE_ID_96)
        self.assertEqual(dwd.date_from, datetime(2022, 6, 26, 00))
        self.assertEqual(dwd.date_to, datetime(2023, 12, 27, 23))
        self.assertTrue(dwd.loaded)
        self.assertEqual(dwd.filename, tc.DWD_TESTFILE_ID_96)

    def test_get_value(self):
        dwd = DWDStation(INIT_DATA_ID_00096)
        dwd.load_data(tc.DWD_TESTFILE_ID_96)
        excepted_value = 3 / 8 * 100
        self.assertEqual(dwd.get_value(datetime(2022, 6, 26, 1)), excepted_value)
        self.assertEqual(dwd.get_value(datetime(2022, 6, 26, 1, 12)), excepted_value)
        self.assertEqual(dwd.get_value(datetime(2022, 6, 26, 0, 45)), excepted_value)

    def test_invalid_get_value(self):
        dwd = DWDStation(INIT_DATA_ID_00096)
        self.assertEqual(dwd.get_value(datetime(2022, 6, 26, 1)), -1)
        self.assertEqual(dwd.get_value(datetime(1970, 1, 1)), -1)

    def test_get_info_str(self):
        dwd = DWDStation(INIT_DATA_ID_00096)
        self.assertEqual(dwd.get_info_str(), f"Id: {dwd.id} ,Lat: {dwd.lat} ,Lon: {dwd.lon} ,"
                                             f"File: {dwd.filename} ,Loaded: {dwd.loaded}")

    def test_invalid_get_info_str(self):
        dwd = DWDStation("")
        self.assertEqual(dwd.get_info_str(), f"Id: {-1} ,Lat: {-1} ,Lon: {-1} ,File:  ,"
                                             f"Loaded: {dwd.loaded}")

    def test_datetime_in_range_with_loaded_file(self):
        dwd = DWDStation(INIT_DATA_ID_00096)
        dwd.load_data(tc.DWD_TESTFILE_ID_96)
        self.assertFalse(dwd.datetime_in_range(datetime(2019, 4, 10, 0)))
        self.assertTrue(dwd.datetime_in_range(datetime(2022, 6, 26, 0)))
        self.assertTrue(dwd.datetime_in_range(datetime(2023, 12, 27, 0)))
        self.assertTrue(dwd.datetime_in_range(datetime(2023, 12, 27, 23)))

    def test_datetime_in_range_only_init_file(self):
        dwd = DWDStation(INIT_DATA_ID_00096)
        self.assertTrue(dwd.datetime_in_range(datetime(2019, 4, 10, 0)))
        self.assertTrue(dwd.datetime_in_range(datetime(2022, 6, 26, 0)))
        self.assertTrue(dwd.datetime_in_range(datetime(2023, 12, 27, 0)))
        self.assertFalse(dwd.datetime_in_range(datetime(2023, 12, 27, 23)))


class TestInvalidStations(unittest.TestCase):
    def test__init__(self):
        inval_dwd = InvalidStations("Hallo Welt")
        self.assertEqual(inval_dwd.stdwarn, "Hallo Welt")
        self.assertEqual(inval_dwd.unloaded_dwdstations, [])

    def test_show_warning_empty(self):
        inval_dwd = InvalidStations("")
        # Check if the function has been called
        with patch("Lib.ColoredPrint.show_warning") as mock_show_warning:
            inval_dwd.show_warnings()
            mock_show_warning.assert_not_called()

    def test_show_warning(self):
        inval_dwd = InvalidStations("")
        dwd = DWDStation(INIT_DATA_ID_00096)
        inval_dwd.add(dwd)
        with patch("Lib.ColoredPrint.show_warning") as mock_show_warning:
            inval_dwd.show_warnings()
            mock_show_warning.assert_called()

    def test_add(self):
        dwd = DWDStation(INIT_DATA_ID_00096)
        inval_dwd = InvalidStations("")
        self.assertEqual(len(inval_dwd.unloaded_dwdstations), 0)
        inval_dwd.add(dwd)
        self.assertEqual(len(inval_dwd.unloaded_dwdstations), 1)

    def test_remove_invalid(self):
        dwd = DWDStation(INIT_DATA_ID_00096)  # Id 96
        inval_dwd = InvalidStations("")
        inval_dwd.add(dwd)
        self.assertEqual(len(inval_dwd.unloaded_dwdstations), 1)
        inval_dwd.remove(1)
        self.assertEqual(len(inval_dwd.unloaded_dwdstations), 1)

    def test_remove(self):
        dwd = DWDStation(INIT_DATA_ID_00096)  # Id 96
        inval_dwd = InvalidStations("")
        inval_dwd.add(dwd)
        self.assertEqual(len(inval_dwd.unloaded_dwdstations), 1)
        inval_dwd.remove(96)
        self.assertEqual(len(inval_dwd.unloaded_dwdstations), 0)


class TestDWDStations(unittest.TestCase):
    def test__init__(self):
        stations = DWDStations()
        self.assertEqual(stations.stations, {})
        self.assertEqual(stations.id_latlon, {})
        self.assertEqual(stations.stderr, "")
        self.assertEqual(len(stations.unloaded_files.unloaded_dwdstations), 0)

    def test_add_invalid(self):
        stations = DWDStations()
        self.assertFalse(stations.add(""))
        self.assertEqual(len(stations.stations), 0)

    def test_add(self):
        stations = DWDStations()
        self.assertTrue(stations.add(INIT_DATA_ID_00096))
        self.assertEqual(len(stations.stations), 1)
        self.assertEqual(len(stations.unloaded_files.unloaded_dwdstations), 1)
        self.assertFalse(stations.add(INIT_DATA_ID_00096))
        self.assertEqual(len(stations.stations), 1)

    def test_load_station_invalid(self):
        stations = DWDStations()
        stations.add(INIT_DATA_ID_00096)
        self.assertFalse(stations.load_station(tc.DWD_TESTFILE_ID_427))
        self.assertEqual(len(stations.stations), 1)
        self.assertEqual(len(stations.unloaded_files.unloaded_dwdstations), 1)

    def test_load_station(self):
        stations = DWDStations()
        stations.add(INIT_DATA_ID_00096)
        self.assertTrue(stations.load_station(tc.DWD_TESTFILE_ID_96))
        self.assertEqual(len(stations.stations), 1)
        self.assertEqual(len(stations.unloaded_files.unloaded_dwdstations), 0)

    def test_get_value_invalid(self):
        stations = DWDStations()
        stations.add(INIT_DATA_ID_00096)
        stations.load_station(tc.DWD_TESTFILE_ID_96)
        date = datetime(2023, 12, 27, 23)
        self.assertEqual(stations.get_value(date, 53, 12), -1)

    def test_get_value(self):
        stations = DWDStations()
        stations.add(INIT_DATA_ID_00096)
        stations.load_station(tc.DWD_TESTFILE_ID_96)
        date = datetime(2023, 12, 27, 23)
        self.assertEqual(stations.get_value(date, 52.9437, 12.8518), 100)

    def test_get_unloaded_stations(self):
        stations = DWDStations()
        stations.add(INIT_DATA_ID_00096)
        unloaded = stations.get_unloaded_stations()
        self.assertEqual(len(unloaded), 1)
        self.assertEqual(unloaded[0].id, 96)

    def test_show_unloaded_files(self):
        stations = DWDStations()
        stations.add(INIT_DATA_ID_00096)
        with patch("Lib.ColoredPrint.show_warning") as mock_show_warning:
            stations.show_unloaded_files()
            mock_show_warning.assert_called()

    def test_datetime_in_range(self):
        stations = DWDStations()
        stations.add(INIT_DATA_ID_00096)
        stations.load_station(tc.DWD_TESTFILE_ID_96)
        invalid_date = datetime(1970, 1, 1)
        valid_date = datetime(2023, 12, 27, 23)
        self.assertFalse(stations.datetime_in_range(invalid_date, 52.9437, 12.8518))
        self.assertFalse(stations.datetime_in_range(valid_date, 52, 12))
        self.assertTrue(stations.datetime_in_range(valid_date, 52.9437, 12.8518))

    def test_get_station(self):
        stations = DWDStations()
        stations.add(INIT_DATA_ID_00096)
        stations.load_station(tc.DWD_TESTFILE_ID_96)
        get_dwd = stations.get_station(52.9437, 12.8518)
        self.assertEqual(get_dwd.id, 96)

    def test_get_stations(self):
        stations = DWDStations()
        self.assertEqual(len(stations.get_stations()), 0)
        stations.add(INIT_DATA_ID_00096)
        self.assertEqual(len(stations.get_stations()), 1)
        self.assertEqual(stations.get_stations()[0].id, 96)

    def test_get_station_invalid(self):
        stations = DWDStations()
        stations.add(INIT_DATA_ID_00096)
        stations.load_station(tc.DWD_TESTFILE_ID_96)
        get_dwd = stations.get_station(52, 12)
        self.assertIsNone(get_dwd)

    def test_get_station_locations(self):
        stations = DWDStations()
        stations.add(INIT_DATA_ID_00096)
        stations.load_station(tc.DWD_TESTFILE_ID_96)
        dwd_loc = stations.get_station_locations()
        self.assertEqual(len(stations.stations), len(dwd_loc))
        self.assertEqual(dwd_loc[0][0], 52.9437)
        self.assertEqual(dwd_loc[0][1], 12.8518)


class TestDWDStationReaderFunctions(unittest.TestCase):
    def tearDown(self):
        if os.path.exists(tc.TRASH_DWD_FILE):
            os.remove(tc.TRASH_DWD_FILE)

    def test_get_init_file(self):
        self.assertEqual(_get_init_file(tc.EMPTY_TEST_DIR), ewConst.ERROR_INIT_FILE_NOT_EXIST)
        self.assertEqual(_get_init_file(tc.TEST_DIR_DWD), tc.DWD_INIT_FILE)

    def test_read_id(self):
        self.assertEqual(_read_id(""), -1)
        self.assertEqual(_read_id(tc.DWD_EMPTYFILE), -1)
        self.assertEqual(_read_id(tc.DWD_TESTFILE_ID_96), 96)

    def test_init_dwd_stations_invalid(self):
        stations = init_dwd_stations(tc.TEST_DIR_NOT_EXIST)
        self.assertEqual(len(stations.stations), 0)
        self.assertEqual(stations.stderr, f"{ewConst.ERROR_PATH_NOT_EXIST}: Path not exist")

        stations = init_dwd_stations(tc.EMPTY_TEST_DIR)
        self.assertEqual(len(stations.stations), 0)
        self.assertEqual(stations.stderr, f"{ewConst.ERROR_INIT_FILE_NOT_EXIST}: Init File not exist")

        stations = init_dwd_stations(tc.DIR_WITH_INVALID_FILES)
        self.assertEqual(len(stations.stations), 0)
        self.assertEqual(stations.stderr, f"{ewConst.ERROR_CORRUPT_INIT_FILES}: Init File is corrupt or empty")

        stations = init_dwd_stations(tc.TEST_DIR_DWD_ONLY_INIT)
        self.assertNotEqual(len(stations.stations), 0)
        self.assertEqual(len(stations.stations), len(stations.unloaded_files.unloaded_dwdstations))
        self.assertEqual(stations.stderr, f"{ewConst.ERROR_NO_DWD_STATIONDATA_FOUND}: "
                                          f"No DWD station files could be found")

    def test_init_dwd_stations(self):
        stations = init_dwd_stations(tc.TEST_DIR_DWD)
        self.assertNotEqual(len(stations.stations), 0)
        # ID 96 and ID 427 was loaded
        self.assertEqual(len(stations.stations)-2, len(stations.unloaded_files.unloaded_dwdstations))
        self.assertEqual(stations.stderr, (f"{ewConst.WARNING_SOME_STATIONS_UNLOADED}: Some stations are unloaded "
                                           f", please check here: [unloaded_files]"))

