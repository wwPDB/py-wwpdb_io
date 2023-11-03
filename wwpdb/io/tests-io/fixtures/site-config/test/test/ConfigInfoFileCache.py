
import os
import sys
import json
import traceback


class ConfigInfoFileCache(object):
    _configD={'TEST': {'SITE_TYPE': 'test', 'SITE_NAME': 'test', 'WWPDB_SITE_LOC': 'test', 'SITE_PREFIX': 'TEST', 'SITE_PREFIX_LC': 'test', 'SITE_SUFFIX': 'test', 'LANGUAGE_CODE': 'en-us', 'TIME_ZONE': 'Europe/London', 'SITE_DEPOSIT_UI_HOST_NAME': 'test.localhost', 'FTP_HOST_NAME': 'test.localhost', 'TOP_SOFTWARE_DIR': '/tmp/onedep-test', 'TOOLS_NAME': 'tools-test', 'TOP_DATA_DIR': '/tmp/onedep-test', 'SITE_ARCHIVE_STORAGE_PATH': '/tmp/onedep-test', 'SITE_DB_HOST_NAME': 'test.localhost', 'SITE_DB_PORT_NUMBER': '3306', 'SITE_DB_ADMIN_USER': 'test', 'SITE_DB_ADMIN_PASS': 'test', 'SITE_DB_RO_USER': 'test', 'SITE_DB_RO_PASS': 'test', 'SITE_DA_INTERNAL_COMBINE_DB_NAME': 'da_internal_combine', 'SITE_DA_INTERNAL_COMBINE_DB_HOST_NAME': 'test.localhost', 'SITE_DA_INTERNAL_COMBINE_DB_PORT_NUMBER': '3306', 'SITE_DA_INTERNAL_COMBINE_DB_USER_NAME': 'test', 'SITE_DA_INTERNAL_COMBINE_DB_PASSWORD': 'test', 'SITE_RBMQ_SERVER_HOST': 'test.localhost', 'SITE_RBMQ_VIRTUAL_HOST': 'test.localhost', 'SITE_RBMQ_CLIENT_PROTOCOL': 'STANDARD', 'SITE_RBMQ_SSL_SERVER_PORT': '5673', 'SITE_RBMQ_SERVER_PORT': '5672', 'SITE_RBMQ_USER_NAME': 'test', 'SITE_RBMQ_PASSWORD': 'test', 'LOCAL_SERVICE_OWNER': 'test', 'LOCAL_SERVICE_GROUP': 'test', 'LOCAL_INSTALL_OWNER': 'test', 'LOCAL_INSTALL_GROUP': 'test', 'BMRB_EXCHANGE_USER': 'test', 'SITE_REFDATA_CVS_USER': 'test', 'SITE_REFDATA_CVS_PASSWORD': 'test', 'SITE_REFDATA_CVS_HOST': 'test.edu', 'CS_USER': 'test', 'CS_PASS': 'test', 'CS_PW': 'test', 'CS_HOST_BASE': 'test.org', 'SVN_USER': 'test', 'SVN_PASS': 'test', 'RCSB_RSYNC_SERVER_USER': 'test', 'RCSB_RSYNC_SERVER_PWD': 'test', 'RCSB_RSYNC_SERVER_HOST': 'test.localhost', 'RCSB_RSYNC_SERVER_PORT': '8730', 'ANNOTATOR_USER_NAME_DICT': '{}', 'NCBI_API_KEY': 'test', 'ANNOTATION_EMAIL': 'test.localhost', 'USE_COMPUTE_CLUSTER': '', 'PDBE_CLUSTER_QUEUE': 'test', 'BSUB_COMMAND': 'test', 'BSUB_LOGIN_NODE': 'test', 'BSUB_TIMEOUT': '10800', 'BSUB_RETRY_DELAY': '4', 'SITE_DA_INTERNAL_DB_ALL_NAME': 'test'}}

    def __init__(self) -> None:
        print("INIT TEST")

    @classmethod
    def getConfigDictionary(cls, siteId):
        try:
            return cls._configD[siteId]
        except:
            return cls.getJsonConfigDictionary(siteId)

    @classmethod
    def getJsonConfigDictionary(cls, siteId):
        try:
            p = os.getenv("TOP_WWPDB_SITE_CONFIG_DIR")
            for l in ["rcsb-east", "rcsb-west", "pdbj", "pdbe", "pdbc"]:
                jsonPath = os.path.join(p,l,siteId.lower(),"ConfigInfoFileCache.json")
                if os.access(jsonPath, os.R_OK):
                    with open(jsonPath, "r") as infile:
                        cD = json.load(infile)
                    return cD[siteId]
        except:
            pass
            # traceback.print_exc(file=sys.stderr)

        return {}

    @classmethod
    def getJsonConfigDictionaryPrev(cls, siteId):
        try:
            id = os.getenv("WWPDB_SITE_ID")
            if siteId != id:
                p = os.getenv("TOP_WWPDB_SITE_CONFIG_DIR")
                l = str(os.getenv("WWPDB_SITE_LOC")).lower()
                jsonPath = os.path.join(p,l,siteId.lower(),"ConfigInfoFileCache.json")
                with open(jsonPath, "r") as infile:
                    cD = json.load(infile)
                return cD[siteId]
        except:
            pass
            # traceback.print_exc(file=sys.stderr)

        return {}

        