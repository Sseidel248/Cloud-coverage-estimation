import os.path
import unittest

import _Tests.testConsts as tc
import Lib.Consts.ModelConts as mConst
import Lib.Consts.GeneralConts as gConst
import Lib.Consts.ErrorWarningConsts as ewConst
from datetime import datetime
from unittest.mock import patch
from Lib.CloudCoverageReader import ModelType, CloudCoverData, InvalidCloudCoverages, CloudCoverDatas
from Lib.CloudCoverageReader import _get_info_str, init_cloud_cover_data


class TesCloudCoverData(unittest.TestCase):
    def test__init__(self):
        test_obj: CloudCoverData = CloudCoverData(tc.EXISTING_TESTFILE_D2)
        self.assertEqual(test_obj.model_type, ModelType.ICON_D2)
        self.assertEqual(test_obj.fcst_minutes, 60)

    def test_init__invalid(self):
        test_obj: CloudCoverData = CloudCoverData("")
        self.assertEqual(test_obj.model_type, ModelType.UNKNOWN)

    def test_get_info_str(self):
        test_obj_d2: CloudCoverData = CloudCoverData(tc.EXISTING_TESTFILE_D2)
        self.assertEqual(test_obj_d2.get_info_str(), f"Date [start]: {str(test_obj_d2.org_date_time)}; "
                                                     f"Param: {test_obj_d2.param}; "
                                                     f"Fcst: {test_obj_d2.fcst_minutes:4d} [min]; "
                                                     f"Model: {mConst.MODEL_ICON_D2}; "
                                                     f"File: {test_obj_d2.filename}")

        test_obj_eu: CloudCoverData = CloudCoverData(tc.EXISTING_TESTFILE_EU)
        self.assertEqual(test_obj_eu.get_info_str(), f"Date [start]: {str(test_obj_eu.org_date_time)}; "
                                                     f"Param: {test_obj_eu.param}; "
                                                     f"Fcst: {test_obj_eu.fcst_minutes:4d} [min]; "
                                                     f"Model: {mConst.MODEL_ICON_EU}; "
                                                     f"File: {test_obj_eu.filename}")

    def test_get_info_str_invalid(self):
        test_obj_d2: CloudCoverData = CloudCoverData("")
        self.assertEqual(test_obj_d2.get_info_str(), f"Date [start]: {str(gConst.NONE_DATETIME)}; "
                                                     f"Param: ; "
                                                     f"Fcst: {-1:4d} [min]; "
                                                     f"Model: {mConst.MODEL_UNSTRUCTURED}; "
                                                     f"File: {test_obj_d2.filename}")

    def test_get_value(self):
        test_obj_d2: CloudCoverData = CloudCoverData(tc.EXISTING_TESTFILE_D2)
        self.assertEqual(test_obj_d2.get_value(53, 12), 100)
        self.assertEqual(test_obj_d2.get_value(60, 21), -1)


class TestInvalidCloudCoverage(unittest.TestCase):
    def test__init__(self):
        inval_cc: InvalidCloudCoverages = InvalidCloudCoverages("Hallo Welt")
        self.assertEqual(inval_cc.stdwarn, "Hallo Welt")
        self.assertEqual(inval_cc.invalid_cloud_cover_datas, [])

    def test_show_warning_empty(self):
        inval_cc: InvalidCloudCoverages = InvalidCloudCoverages("")
        # Check if the function has been called
        with patch("Lib.ColoredPrint.show_warning") as mock_show_warning:
            inval_cc.show_warnings()
            mock_show_warning.assert_not_called()

    def test_show_warning(self):
        inval_cc: InvalidCloudCoverages = InvalidCloudCoverages("")
        cc: CloudCoverData = CloudCoverData(tc.EXISTING_TESTFILE_D2)
        inval_cc.add(cc)
        with patch("Lib.ColoredPrint.show_warning") as mock_show_warning:
            inval_cc.show_warnings()
            mock_show_warning.assert_called()

    def test_add(self):
        cc: CloudCoverData = CloudCoverData(tc.EXISTING_TESTFILE_D2)
        inval_cc: InvalidCloudCoverages = InvalidCloudCoverages("")
        self.assertEqual(len(inval_cc.invalid_cloud_cover_datas), 0)
        inval_cc.add(cc)
        self.assertEqual(len(inval_cc.invalid_cloud_cover_datas), 1)

    def test_remove_invalid(self):
        cc: CloudCoverData = CloudCoverData(tc.EXISTING_TESTFILE_D2)
        inval_cc: InvalidCloudCoverages = InvalidCloudCoverages("")
        inval_cc.add(cc)
        self.assertEqual(len(inval_cc.invalid_cloud_cover_datas), 1)
        inval_cc.remove("Not_existing_File")
        self.assertEqual(len(inval_cc.invalid_cloud_cover_datas), 1)

    def test_remove(self):
        cc: CloudCoverData = CloudCoverData(tc.EXISTING_TESTFILE_D2)
        inval_cc: InvalidCloudCoverages = InvalidCloudCoverages("")
        inval_cc.add(cc)
        self.assertEqual(len(inval_cc.invalid_cloud_cover_datas), 1)
        inval_cc.remove(tc.EXISTING_TESTFILE_D2)
        self.assertEqual(len(inval_cc.invalid_cloud_cover_datas), 0)


class TestCloudCoverDatas(unittest.TestCase):
    def test__init__(self):
        ccs: CloudCoverDatas = CloudCoverDatas(mConst.MODEL_ICON_D2)
        self.assertEqual(ccs.model, mConst.MODEL_ICON_D2.lower())
        self.assertEqual(ccs.model_type, ModelType.ICON_D2)
        self.assertEqual(len(ccs.cloud_cover_files), 0)
        self.assertEqual(ccs.min_datetime, gConst.NONE_DATETIME)
        self.assertEqual(ccs.max_datetime, gConst.NONE_DATETIME)
        self.assertEqual(ccs.stderr, "")
        self.assertEqual(ccs.wrong_model_files.stdwarn, "Wrong model")
        self.assertEqual(ccs.wrong_param_files.stdwarn, "Wrong param in file")
        self.assertEqual(ccs.no_latlon_files.stdwarn, "Unstructured grid")
        self.assertEqual(ccs.none_datetime_files.stdwarn, "File has no datetime")
        self.assertEqual(ccs.too_far_forecast_files.stdwarn, "Forecast is longer then 120 min")

    def test__init__invalid(self):
        ccs: CloudCoverDatas = CloudCoverDatas("")
        self.assertEqual(ccs.model, "")
        self.assertEqual(ccs.model_type, ModelType.UNKNOWN)
        self.assertEqual(len(ccs.cloud_cover_files), 0)
        self.assertEqual(ccs.min_datetime, gConst.NONE_DATETIME)
        self.assertEqual(ccs.max_datetime, gConst.NONE_DATETIME)
        self.assertEqual(ccs.stderr, "")
        self.assertEqual(ccs.wrong_model_files.stdwarn, "Wrong model")
        self.assertEqual(ccs.wrong_param_files.stdwarn, "Wrong param in file")
        self.assertEqual(ccs.no_latlon_files.stdwarn, "Unstructured grid")
        self.assertEqual(ccs.none_datetime_files.stdwarn, "File has no datetime")
        self.assertEqual(ccs.too_far_forecast_files.stdwarn, "Forecast is longer then 120 min")

    def test_add_invalid(self):
        ccs: CloudCoverDatas = CloudCoverDatas(mConst.MODEL_ICON_D2)
        self.assertFalse(ccs.add(""))
        self.assertFalse(ccs.add("", data=None))

        self.assertFalse(ccs.add(tc.MODEL_FILE_WRONG_MODEL))
        self.assertEqual(len(ccs.wrong_model_files.invalid_cloud_cover_datas), 1)

        self.assertFalse(ccs.add(tc.MODEL_FILE_WRONG_PARAM))
        self.assertEqual(len(ccs.wrong_param_files.invalid_cloud_cover_datas), 1)

        self.assertFalse(ccs.add(tc.MODEL_FILE_NO_LATLON))
        self.assertEqual(len(ccs.no_latlon_files.invalid_cloud_cover_datas), 1)

        self.assertFalse(ccs.add(tc.MODEL_FILE_TOO_MUCH_FORECAST))
        self.assertEqual(len(ccs.too_far_forecast_files.invalid_cloud_cover_datas), 1)

        cc_none_datetime: CloudCoverData = CloudCoverData(tc.MODEL_FILE_WRONG_MODEL)
        cc_none_datetime.org_date_time = gConst.NONE_DATETIME
        self.assertFalse(ccs.add("", cc_none_datetime))
        self.assertEqual(len(ccs.none_datetime_files.invalid_cloud_cover_datas), 1)

    def test_add(self):
        ccs: CloudCoverDatas = CloudCoverDatas(mConst.MODEL_ICON_D2)  # forecast 60min -> 1h
        self.assertTrue(ccs.add(tc.EXISTING_TESTFILE_D2))
        self.assertEqual(len(ccs.cloud_cover_files), 1)
        self.assertEqual(len(ccs.wrong_model_files.invalid_cloud_cover_datas), 0)
        self.assertEqual(len(ccs.wrong_param_files.invalid_cloud_cover_datas), 0)
        self.assertEqual(len(ccs.no_latlon_files.invalid_cloud_cover_datas), 0)
        self.assertEqual(len(ccs.too_far_forecast_files.invalid_cloud_cover_datas), 0)
        self.assertEqual(len(ccs.none_datetime_files.invalid_cloud_cover_datas), 0)
        self.assertEqual(ccs.min_datetime, datetime(2023, 11, 29, 13))  # plus forecast hours
        self.assertEqual(ccs.max_datetime, datetime(2023, 11, 29, 13))  # plus forecast hours

    def test_add_via_obj(self):
        ccs: CloudCoverDatas = CloudCoverDatas(mConst.MODEL_ICON_D2)  # forecast 60min -> 1h
        cc: CloudCoverData = CloudCoverData(tc.EXISTING_TESTFILE_D2)
        self.assertTrue(ccs.add("", data=cc))
        self.assertEqual(len(ccs.cloud_cover_files), 1)

    def test_show_all_invalid_files(self):
        ccs: CloudCoverDatas = CloudCoverDatas(mConst.MODEL_ICON_D2)
        self.assertFalse(ccs.add(tc.MODEL_FILE_WRONG_MODEL))
        self.assertEqual(len(ccs.wrong_model_files.invalid_cloud_cover_datas), 1)
        with patch("Lib.ColoredPrint.show_warning") as mock_show_warning:
            ccs.show_all_invalid_files()
            mock_show_warning.assert_called()

    def test_datetime_in_range(self):
        ccs: CloudCoverDatas = CloudCoverDatas(mConst.MODEL_ICON_D2)
        ccs.add(tc.EXISTING_TESTFILE_D2)
        self.assertFalse(ccs.datetime_in_range(datetime(2023, 11, 29, 14)))
        self.assertTrue(ccs.datetime_in_range(datetime(2023, 11, 29, 13)))

    def test_lat_in_range(self):
        ccs_d2: CloudCoverDatas = CloudCoverDatas(mConst.MODEL_ICON_D2)
        ccs_d2.add(tc.EXISTING_TESTFILE_D2)
        self.assertFalse(ccs_d2.lat_in_range(60))  # lat max = 58.08
        self.assertTrue(ccs_d2.lat_in_range(53))

        ccs_eu: CloudCoverDatas = CloudCoverDatas(mConst.MODEL_ICON_EU)
        ccs_eu.add(tc.EXISTING_TESTFILE_EU)
        self.assertFalse(ccs_eu.lat_in_range(72))  # lat max = 70.5
        self.assertTrue(ccs_eu.lat_in_range(53))

    def test_lat_in_range_invalid(self):
        ccs_d2: CloudCoverDatas = CloudCoverDatas("")
        self.assertFalse(ccs_d2.lat_in_range(53))

    def test_lon_in_range(self):
        ccs_d2: CloudCoverDatas = CloudCoverDatas(mConst.MODEL_ICON_D2)
        ccs_d2.add(tc.EXISTING_TESTFILE_D2)
        self.assertFalse(ccs_d2.lon_in_range(25))  # lat max = 20.34
        self.assertTrue(ccs_d2.lon_in_range(13))

        ccs_eu: CloudCoverDatas = CloudCoverDatas(mConst.MODEL_ICON_EU)
        ccs_eu.add(tc.EXISTING_TESTFILE_EU)
        self.assertFalse(ccs_eu.lon_in_range(64))  # lat max = 62.5
        self.assertTrue(ccs_eu.lon_in_range(13))

    def test_lon_in_range_invalid(self):
        ccs_d2: CloudCoverDatas = CloudCoverDatas("")
        self.assertFalse(ccs_d2.lon_in_range(13))

    def test_get_cloud_cover(self):
        ccs_d2: CloudCoverDatas = CloudCoverDatas(mConst.MODEL_ICON_D2)
        ccs_d2.add(tc.EXISTING_TESTFILE_D2)
        self.assertEqual(ccs_d2.get_cloud_cover(datetime(2023, 11, 29, 13), 53, 13), 100)

    def test_get_cloud_cover_invalid(self):
        ccs_d2: CloudCoverDatas = CloudCoverDatas(mConst.MODEL_ICON_D2)
        self.assertEqual(ccs_d2.get_cloud_cover(datetime(2023, 11, 29, 13), 53, 13), -1)

        ccs_d2.add(tc.EXISTING_TESTFILE_D2)
        ccs_d2.add(tc.EXISTING_TESTFILE_D2_2)
        self.assertEqual(ccs_d2.get_cloud_cover(datetime(2023, 11, 29, 15), 53, 13), -1)

        ccs_d2.add(tc.EXISTING_TESTFILE_D2)
        with patch("Lib.ColoredPrint.show_error") as mock_show_error:
            self.assertEqual(ccs_d2.get_cloud_cover(datetime(2023, 11, 30, 13), 53, 13), -1)
            mock_show_error.assert_called()
        with patch("Lib.ColoredPrint.show_error") as mock_show_error:
            self.assertEqual(ccs_d2.get_cloud_cover(datetime(2023, 11, 29, 13), 70, 13), -1)
            mock_show_error.assert_called()
        with patch("Lib.ColoredPrint.show_error") as mock_show_error:
            self.assertEqual(ccs_d2.get_cloud_cover(datetime(2023, 11, 29, 13), 53, 25), -1)
            mock_show_error.assert_called()

    def test_get_used_datetime(self):
        ccs_d2: CloudCoverDatas = CloudCoverDatas(mConst.MODEL_ICON_D2)
        ccs_d2.add(tc.EXISTING_TESTFILE_D2)
        ccs_d2.add(tc.MODEL_FILE_TOO_MUCH_FORECAST)
        ccs_d2.add(tc.MODEL_FILE_NO_LATLON)
        ccs_d2.add(tc.EXISTING_TESTFILE_D2_2)
        self.assertEqual(len(ccs_d2.get_used_datetimes()), 2)
        self.assertTrue(isinstance(ccs_d2.get_used_datetimes()[0], datetime))
        self.assertTrue(isinstance(ccs_d2.get_used_datetimes()[1], datetime))

    def test_num_invalid_files(self):
        ccs_d2: CloudCoverDatas = CloudCoverDatas(mConst.MODEL_ICON_D2)
        ccs_d2.add(tc.EXISTING_TESTFILE_D2)
        ccs_d2.add(tc.MODEL_FILE_TOO_MUCH_FORECAST)
        ccs_d2.add(tc.MODEL_FILE_NO_LATLON)
        ccs_d2.add(tc.MODEL_FILE_WRONG_MODEL)
        ccs_d2.add(tc.MODEL_FILE_WRONG_PARAM)
        cc_none_datetime: CloudCoverData = CloudCoverData(tc.MODEL_FILE_WRONG_MODEL)
        cc_none_datetime.org_date_time = gConst.NONE_DATETIME
        ccs_d2.add("", cc_none_datetime)

        ccs_d2.add(tc.EXISTING_TESTFILE_D2_2)
        self.assertEqual(ccs_d2.get_num_invalid_files(), 4)


class TestCloudCoverageReaderFunctions(unittest.TestCase):
    def test_get_warn_str(self):
        cc_invalid: CloudCoverData = CloudCoverData("")
        self.assertEqual(_get_info_str(cc_invalid),
                         (f"Date [start]: {str(gConst.NONE_DATETIME)}; Param: ; "
                          f"Fcst: {-1:4d} [min]; Model: {mConst.MODEL_UNSTRUCTURED}; "
                          f"File: {os.path.abspath('')}"))

        cc_d2: CloudCoverData = CloudCoverData(tc.EXISTING_TESTFILE_D2)
        self.assertEqual(_get_info_str(cc_d2),
                         (f"Date [start]: {str(cc_d2.org_date_time)}; Param: TCDC; "
                          f"Fcst: {60:4d} [min]; Model: {mConst.MODEL_ICON_D2}; "
                          f"File: {tc.EXISTING_TESTFILE_D2}"))

        cc_eu: CloudCoverData = CloudCoverData(tc.EXISTING_TESTFILE_EU)
        self.assertEqual(_get_info_str(cc_eu),
                         (f"Date [start]: {str(cc_eu.org_date_time)}; Param: TCDC; "
                          f"Fcst: {60:4d} [min]; Model: {mConst.MODEL_ICON_EU}; "
                          f"File: {tc.EXISTING_TESTFILE_EU}"))

    def test_init_cloud_cover_data(self):
        ccs: CloudCoverDatas = init_cloud_cover_data(tc.TEST_DIR_MODEL_D2, mConst.MODEL_ICON_D2)
        self.assertEqual(ccs.stderr, "")
        self.assertEqual(len(ccs.cloud_cover_files), 3)
        self.assertEqual(ccs.get_num_invalid_files(), 0)

    def test_init_cloud_cover_data_invalid(self):
        ccs_path_not_exist: CloudCoverDatas = init_cloud_cover_data(tc.TEST_DIR_NOT_EXIST, "Hans Wurst")
        self.assertEqual(ccs_path_not_exist.stderr, f"{ewConst.ERROR_WRONG_MODEL}: Wrong model")

        ccs_wrong_param: CloudCoverDatas = init_cloud_cover_data(tc.TEST_DIR_NOT_EXIST, mConst.MODEL_ICON_D2)
        self.assertEqual(ccs_wrong_param.stderr, f"{ewConst.ERROR_PATH_NOT_EXIST}: Path does not exist")

        ccs_empty: CloudCoverDatas = init_cloud_cover_data(tc.EMPTY_TEST_DIR, mConst.MODEL_ICON_D2)
        self.assertEqual(ccs_empty.stderr, f"{ewConst.ERROR_NO_FILES_FOUND}: No grib2 files found")

        ccs_invalid: CloudCoverDatas = init_cloud_cover_data(tc.TEST_DIR_MODEL_D2_INVALID_FILES, mConst.MODEL_ICON_D2)
        self.assertEqual(ccs_invalid.stderr, f"{ewConst.ERROR_GRIB2_FILES_INCOMPLETE}: "
                                             f"There are no files with correct data")

        ccs_mix: CloudCoverDatas = init_cloud_cover_data(tc.TEST_DIR_MODEL_D2_MIX_FILES, mConst.MODEL_ICON_D2)
        self.assertEqual(ccs_mix.stderr, (f"{ewConst.WARNING_SOME_FILES_ARE_INVALID}: Some files are invalid "
                                          f", please check here: [wrong_model_files, wrong_param_files, "
                                          f"no_latlon_files, none_datetime_files, too_far_forecast_files]."))
