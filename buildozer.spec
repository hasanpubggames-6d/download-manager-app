[app]
title = AI Studio Download Manager
package.name = aistudiodownloadmanager
package.domain = org.aistudio
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json,ttf,txt,yml,yaml
version = 2.0.0
requirements = python3,kivy,kivymd,pyjnius,android,requests,pillow,urllib3,chardet,idna,certifi
orientation = portrait
fullscreen = 0
android.permissions = INTERNET,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE,ACCESS_NETWORK_STATE,ACCESS_WIFI_STATE,FOREGROUND_SERVICE,FOREGROUND_SERVICE_DATA_SYNC,WAKE_LOCK
android.api = 33
android.minapi = 24
android.ndk = 25b
android.archs = arm64-v8a

[buildozer]
log_level = 2
warn_on_root = 0
