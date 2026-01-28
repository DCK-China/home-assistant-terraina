"""Constants for Terraina integration."""

DOMAIN = "terraina"
NAME = "TERRAINA"
VERSION = "1.0.0"

GLOBAL_DOMAIN = "https://iot-platform-global-prod.dongcheng.ink"

SERVER_DOMAIN_NAME = {
    "cn": "https://iot-platform-cn-prod.dongcheng.ink",
    "eu": "https://iot-platform-eu-prod.dongcheng.ink",
    "us": "https://iot-platform-us-prod.dongcheng.ink",
}
CLIENT_ID = "AfAsyMwEMPDf1I5CTfIc9G2a7LT5YnQCAxLm5rVlx992mNh7B9spEVpK"

CLIENT_SECRET = ""

LOCKED = ["locked", "unlocked"]
EMERGENCY_STOP = ["no emergency stop", "emergency stop"]
CHARGING = ["not in basestation", "charging", "fully charged"]
RAINED = ["not rained", "being rained", "being rained and delayed"]
WORKING_STATUS = [
    "",  # 00
    "hanging",  # 01 待机
    "buidling graph",
    "mowing",
    "backing",
    "backing with low power",
    "locating",
    "resting",
    "error",
    "offline",
    "",
    "leaving basestation",
    "",
]
OTA = ["available", "upgrading"]
LOG = ["available", "uploading"]
TASK = ["available", "assigned"]
WORKING_MODE = ["auto", "manual"]
BINDING = ["not binding", "binding"]
