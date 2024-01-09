import unittest
import os
import Lib.Consts.GeneralConts as gConst
import Lib.Consts.ErrorWarningConsts as ewConst
import Lib.wgrib2.Grib2Reader as g2r
import Lib.GeneralFunctions as gFunc
import _Tests.testConsts as tc
from Lib.wgrib2.Grib2Reader import LatLonData, Grib2Data, GridType, Grib2Result
from datetime import datetime, timedelta
from unittest.mock import patch


class TestLatLonData(unittest.TestCase):
    def test__init__(self):
        datastr: str = ("1:0:grid_template=0:winds(N/S):"
                        "lat-lon grid:(1215 x 746) units 1e-06 input WE:SN output WE:SN res 48)"
                        "lat 43.180000 to 58.080000 by 0.020000"
                        "lon 356.060000 to 20.340000 by 0.020000 #points=906390")
        test_obj: LatLonData = LatLonData(datastr)
        self.assertEqual(test_obj.lat_max, 58.08)
        self.assertEqual(test_obj.lat_min, 43.18)
        self.assertEqual(test_obj.lon_min, 356.06)
        self.assertEqual(test_obj.lon_max, 20.34)
        self.assertEqual(test_obj.delta_by, 0.02)

    def test_invalid__init__(self):
        datastr: str = ""
        test_obj: LatLonData = LatLonData(datastr)
        self.assertEqual(test_obj.lat_max, -1)
        self.assertEqual(test_obj.lat_min, -1)
        self.assertEqual(test_obj.lon_min, -1)
        self.assertEqual(test_obj.lon_max, -1)
        self.assertEqual(test_obj.delta_by, -1)


class TestGrib2Data(unittest.TestCase):
    def setUp(self):
        self.assertTrue(os.path.exists(tc.EXISTING_TESTFILE_D2))
        self.assertFalse(os.path.exists(tc.NOT_EXISTING_TESTFILE_D2))

    def test__init__(self):
        test_obj: Grib2Data = Grib2Data(tc.EXISTING_TESTFILE_D2)
        self.assertEqual(test_obj.filename, os.path.abspath(tc.EXISTING_TESTFILE_D2))
        self.assertEqual(test_obj.fcst_date_time, datetime(2023, 11, 29, 13, 00))
        self.assertEqual(test_obj.org_date_time, datetime(2023, 11, 29, 12, 00))
        self.assertEqual(test_obj.param, "TCDC")
        self.assertEqual(test_obj.fcst_minutes, 60)
        self.assertEqual(test_obj.grid_type, GridType.LAT_LON_REGULAR)
        self.assertNotEqual(test_obj.latlon_data, None)

    def test_invalid__init__(self):
        test_obj: Grib2Data = Grib2Data(tc.NOT_EXISTING_TESTFILE_D2)
        self.assertEqual(test_obj.filename, os.path.abspath(tc.NOT_EXISTING_TESTFILE_D2))
        self.assertEqual(test_obj.fcst_date_time, gConst.NONE_DATETIME)
        self.assertEqual(test_obj.org_date_time, gConst.NONE_DATETIME)
        self.assertEqual(test_obj.param, "")
        self.assertEqual(test_obj.fcst_minutes, -1)
        self.assertEqual(test_obj.grid_type, GridType.UNSTRUCTURED)
        self.assertNotEqual(test_obj.latlon_data, None)

    def test_exist_latlon(self):
        test_obj: Grib2Data = Grib2Data(tc.EXISTING_TESTFILE_D2)
        self.assertTrue(test_obj.exist_latlon())

    def test_exist_latlon_invalid(self):
        test_obj: Grib2Data = Grib2Data(tc.NOT_EXISTING_TESTFILE_D2)
        self.assertFalse(test_obj.exist_latlon())

    def test_lat_in_range(self):
        test_obj: Grib2Data = Grib2Data(tc.EXISTING_TESTFILE_D2)
        self.assertTrue(test_obj.lat_in_range(58.08))
        self.assertTrue(test_obj.lat_in_range(43.18))
        self.assertFalse(test_obj.lat_in_range(58.09))
        self.assertFalse(test_obj.lat_in_range(43.17))

    def test_lon_in_range(self):
        test_obj: Grib2Data = Grib2Data(tc.EXISTING_TESTFILE_D2)
        self.assertTrue(test_obj.lon_in_range(356.06))
        self.assertTrue(test_obj.lon_in_range(20.34))
        self.assertFalse(test_obj.lon_in_range(356.05))
        self.assertFalse(test_obj.lon_in_range(20.35))


class TestGrib2Result(unittest.TestCase):
    def test__init__(self):
        test_obj: Grib2Result = Grib2Result()
        self.assertIsNotNone(test_obj)
        self.assertEqual(test_obj.stderr, "")
        self.assertEqual(test_obj.val, -1)
        self.assertEqual(test_obj.val_lat, -1)
        self.assertEqual(test_obj.val_lon, -1)

    def test_read_values(self):
        test_output: str = "1:0:lon=13.000000,lat=53.000000,val=100"
        test_obj: Grib2Result = Grib2Result()
        test_obj.read_values(test_output)
        self.assertEqual(test_obj.stderr, "")
        self.assertEqual(test_obj.val, 100)
        self.assertEqual(test_obj.val_lat, 53)
        self.assertEqual(test_obj.val_lon, 13)

    def test_read_values_invalid(self):
        test_output: str = "1:0:"
        test_obj: Grib2Result = Grib2Result()
        test_obj.read_values(test_output)
        err_msg = f"{ewConst.ERROR_PARAM_NOT_EXIST}: Param not exist"
        self.assertEqual(test_obj.stderr, err_msg)
        self.assertEqual(test_obj.val, -1)
        self.assertEqual(test_obj.val_lat, -1)
        self.assertEqual(test_obj.val_lon, -1)


class TestGrid2ReaderFunctions(unittest.TestCase):
    def setUp(self):
        self.assertTrue(os.path.exists(tc.EXISTING_TESTFILE_D2))
        self.assertTrue(os.path.exists(tc.EMPTY_TEST_DIR))
        self.assertFalse(os.path.exists(tc.NOT_EXISTING_TESTFILE_D2))

    def tearDown(self):
        self.assertFalse(os.path.exists(tc.NOT_EXISTING_TESTFILE_D2))
        if os.path.exists(tc.EXTRACTED_FILE):
            os.remove(tc.EXTRACTED_FILE)

    def test_get_latlon_details_valid_file(self):
        test_latlondata, test_gridtype = g2r._get_latlon_details(tc.EXISTING_TESTFILE_D2)
        self.assertEqual(test_latlondata.delta_by, 0.02)
        self.assertEqual(test_gridtype, GridType.LAT_LON_REGULAR)

    def test_get_latlon_details_invalid_file(self):
        test_latlondata, test_gridtype = g2r._get_latlon_details(tc.NOT_EXISTING_TESTFILE_D2)
        self.assertEqual(test_latlondata.delta_by, -1)
        self.assertEqual(test_gridtype, GridType.UNSTRUCTURED)

    def test_get_files(self):
        num_files: int = len(gFunc.get_files(tc.TEST_DIR_MODEL_D2, ".*"))
        self.assertEqual(num_files, 3)
        num_files: int = len(gFunc.get_files(tc.TEST_DIR_MODEL_D2, ".grib2"))
        self.assertEqual(num_files, 2)

    def test_extract_bz2_archives(self):
        test_files: list[str] = gFunc.get_files(tc.TEST_DIR_MODEL_D2, ".bz2")
        self.assertEqual(len(test_files), 1)
        g2r._extract_bz2_archives(test_files)
        self.assertTrue(os.path.exists(tc.EXTRACTED_FILE))

    def test_extract_bz2_archives_empty_dir(self):
        test_files: list[str] = gFunc.get_files(tc.EMPTY_TEST_DIR, ".bz2")
        self.assertEqual(len(test_files), 0)
        g2r._extract_bz2_archives(test_files)
        no_files: list[str] = gFunc.get_files(tc.EMPTY_TEST_DIR, ".grib2")
        self.assertEqual(len(no_files), 0)

    def test_get_datetime_param_fcst_invalid(self):
        test_date, test_param, test_fcst = g2r._get_datetime_param_fcst(tc.NOT_EXISTING_TESTFILE_D2)
        self.assertEqual(test_date, gConst.NONE_DATETIME)
        self.assertEqual(test_param, "")
        self.assertEqual(test_fcst, -1)

    def test_in_range(self):
        self.assertTrue(gFunc.in_range(0, -999, 999))
        self.assertFalse(gFunc.in_range(1000, -999, 999))
        self.assertFalse(gFunc.in_range(1000, 999, -999))

        min_date: datetime = datetime(1970, 1, 1, 0, 0)
        max_date: datetime = datetime.now()
        self.assertTrue(gFunc.in_range(datetime(1991, 8, 24, 9, 30), min_date, max_date))
        self.assertFalse(gFunc.in_range(max_date + timedelta(days=1), min_date, max_date))
        self.assertFalse(gFunc.in_range(datetime(1991, 8, 24, 9, 30), max_date, min_date))

    def test_convert_in_0_360(self):
        self.assertEqual(gFunc.convert_in_0_360(0), 0)
        self.assertEqual(gFunc.convert_in_0_360(360), 0)
        self.assertEqual(gFunc.convert_in_0_360(-360), 0)
        self.assertEqual(gFunc.convert_in_0_360(-120), 240)
        self.assertEqual(gFunc.convert_in_0_360(120), 120)
        self.assertEqual(gFunc.convert_in_0_360(-480), 240)
        self.assertEqual(gFunc.convert_in_0_360(480), 120)

    def test_convert_in_180_180(self):
        self.assertEqual(gFunc.convert_in_180_180(0), 0)
        self.assertEqual(gFunc.convert_in_180_180(360), 0)
        self.assertEqual(gFunc.convert_in_180_180(-360), 0)
        self.assertEqual(gFunc.convert_in_180_180(-120), -120)
        self.assertEqual(gFunc.convert_in_180_180(120), 120)
        self.assertEqual(gFunc.convert_in_180_180(-480), -120)
        self.assertEqual(gFunc.convert_in_180_180(480), 120)

    def test_load_folder_valid(self):
        grib2pathes: list[str] = g2r.load_folder(tc.TEST_DIR_MODEL_D2)
        self.assertEqual(len(grib2pathes), 3)

    def test_load_folder_invalid(self):
        grib2datas: list[str] = g2r.load_folder("")
        self.assertEqual(len(grib2datas), 0)

    def test_get_value_from_file_valid(self):
        self.assertTrue(os.path.exists(tc.EXISTING_TESTFILE_D2))
        res: Grib2Result = g2r.get_value_from_file(tc.EXISTING_TESTFILE_D2, 53, 13)
        self.assertEqual(res.val, 100)
        self.assertEqual(res.stderr, "")

    def test_get_value_from_file_invalid(self):
        res: Grib2Result = g2r.get_value_from_file(tc.NOT_EXISTING_TESTFILE_D2, 53, 13)
        self.assertEqual(res.val, -1)
        self.assertEqual(res.stderr, f"{ewConst.ERROR_FILE_NOT_EXIST}: File not exist")

    def test_get_value_valid(self):
        test_obj: Grib2Data = Grib2Data(tc.EXISTING_TESTFILE_D2)
        res: Grib2Result = g2r.get_value(test_obj, 53, 13)
        self.assertEqual(res.val, 100)
        self.assertEqual(res.stderr, "")

    def test_get_value_invalid(self):
        test_obj: Grib2Data = Grib2Data(tc.NOT_EXISTING_TESTFILE_D2)
        res: Grib2Result = g2r.get_value(test_obj, 53, 13)
        self.assertEqual(res.val, -1)
        self.assertEqual(res.stderr, f"{ewConst.ERROR_FILE_NOT_EXIST}: File not exist")

        test_obj: Grib2Data = Grib2Data(tc.INVALID_GRIDTYPE_FILE)
        res: Grib2Result = g2r.get_value(test_obj, 53, 13)
        self.assertEqual(res.val, -1)
        self.assertEqual(res.stderr, f"{ewConst.ERROR_UNSTRUCTURED_GRID}: Unstructured Grid")

        test_obj: Grib2Data = Grib2Data(tc.EXISTING_TESTFILE_D2)
        res: Grib2Result = g2r.get_value(test_obj, 0, 13)
        self.assertEqual(res.val, -1)
        self.assertEqual(res.stderr, f"{ewConst.ERROR_LAT_OUT_OF_RANGE}: Lat out of Range")

        test_obj: Grib2Data = Grib2Data(tc.EXISTING_TESTFILE_D2)
        res: Grib2Result = g2r.get_value(test_obj, 53, 30)
        self.assertEqual(res.val, -1)
        self.assertEqual(res.stderr, f"{ewConst.ERROR_LON_OUT_OF_RANGE}: Lon out of Range")

    def test_get_multiple_values(self):
        coords: list[tuple[float, float]] = [(53, 13), (54, 14), (55, 15)]
        test_obj: Grib2Data = Grib2Data(tc.EXISTING_TESTFILE_D2)
        g2rs: list[Grib2Result] = g2r.get_multiple_values(test_obj, coords)
        self.assertEqual(len(g2rs), 3)

        self.assertEqual(g2rs[0].val, 100)
        self.assertEqual(g2rs[0].val_lat, 53)
        self.assertEqual(g2rs[0].val_lon, 13)

        self.assertEqual(g2rs[1].val, 97.375)
        self.assertEqual(g2rs[1].val_lat, 54)
        self.assertEqual(g2rs[1].val_lon, 14)

        self.assertEqual(g2rs[2].val, 100)
        self.assertEqual(g2rs[2].val_lat, 55)
        self.assertEqual(g2rs[2].val_lon, 15)

    def test_get_multiple_values_invalid(self):
        coords: list[tuple[float, float]] = [(70, 14), (55, 70)]
        test_obj: Grib2Data = Grib2Data(tc.NOT_EXISTING_TESTFILE_D2)
        with patch("Lib.ColoredPrint.show_error") as mock_show_error:
            g2rs_file_not_exist = g2r.get_multiple_values(test_obj, coords)
            mock_show_error.assert_called()
        self.assertEqual(len(g2rs_file_not_exist), 0)

        test_obj = Grib2Data(tc.INVALID_GRIDTYPE_FILE)
        with patch("Lib.ColoredPrint.show_error") as mock_show_error:
            g2rs_invalid_grid_type = g2r.get_multiple_values(test_obj, coords)
            mock_show_error.assert_called()
        self.assertEqual(len(g2rs_invalid_grid_type), 0)

        test_obj = Grib2Data(tc.EXISTING_TESTFILE_D2)
        with patch("Lib.ColoredPrint.show_error") as mock_show_error:
            g2rs_invalid_grid_type = g2r.get_multiple_values(test_obj, coords)
            mock_show_error.assert_called()
        self.assertEqual(len(g2rs_invalid_grid_type), 0)
