import unittest
import gaedeploy as gd

BASE_PATH = "./test"
TEST_FILE_PATH = BASE_PATH + "/test_deploy.yml"
TEST_NOT_EXIST_FILE_PATH = BASE_PATH + "/not_exist.yml"

TEST_APP = "testapp1"
TEST_NOT_EXIST_APP = "notexist"

class TestConfiguration(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_init(self):
        conf = gd.Configuration(TEST_FILE_PATH)
        self.assertIsInstance(conf, gd.Configuration)
        self.assertEqual(conf.deploy_tool, "/usr/local/google-cloud-sdk/bin/gcloud")
        self.assertEqual(conf.temp_folder, "/tmp")
        self.assertEqual(len(conf.conf_apps), 2)

    def test_not_exist_init(self):
        with self.assertRaises(gd.YAMLFormatException):
            gd.Configuration(TEST_NOT_EXIST_FILE_PATH)

    def test_get_app(self):
        conf = gd.Configuration(TEST_FILE_PATH)
        app = conf.get_application(TEST_APP)
        self.assertEqual(app.name, TEST_APP)

    def test_not_exit_app(self):
        conf = gd.Configuration(TEST_FILE_PATH)
        with self.assertRaises(gd.ApplicationNotFoundException):
            conf.get_application(TEST_NOT_EXIST_APP)

class TestApllication(unittest.TestCase):
    def test_init(self):
        conf = gd.Configuration(TEST_FILE_PATH)
        app = conf.get_application(TEST_APP)
        self.assertEqual(app.applicationId, "applicationIdTest")
        self.assertEqual(app.version, 1)
        self.assertEqual(app.source["type"], "local")
        self.assertEqual(app.source["location"], "/Users/nakata/PycharmProjects/gae-python-sample")
        self.assertEqual(app.yaml_file, "app.yaml")
        self.assertEqual(app.deploy_tool, "/usr/local/google-cloud-sdk/bin/gcloud")
        self.assertEqual(app.temp_folder, "/tmp")
        #
        self.assertTrue(app.work_folder)
        self.assertTrue(app.temp_folder)

    def test_deploy(self):
        conf = gd.Configuration(TEST_FILE_PATH)
        app = conf.get_application(TEST_APP)
        with self.assertRaises(gd.DeployFailedException):
            app.deploy()

    """
    def test_create_command(self):
        conf = gd.Configuration(TEST_FILE_PATH)
        app = conf.get_application(TEST_APP)
        command = app._create_deploy_command()
        command_version = "1" in command
        command_application = "--project=applicationIdTest" in command
        self.assertTrue(command_version)
        self.assertTrue(command_application)
    """

