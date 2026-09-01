[app]

title = JARVIS TITAN
package.name = jarvistitan
package.domain = org.jarvistitan

source.dir = .
source.include_exts = py,png,jpg,jpeg,kv,atlas,json,txt

version = 1.0

requirements = python3==3.11.9,hostpython3==3.11.9,kivy

orientation = portrait
fullscreen = 0

# Android
android.api = 35
android.minapi = 24
android.ndk_api = 24
android.accept_sdk_license = True

# Android permissions
android.permissions = INTERNET

# Build settings
android.archs = arm64-v8a

# Python-for-Android
p4a.bootstrap = sdl2

# Android activity
android.presplash_color = #000000
android.entrypoint = org.kivy.android.PythonActivity

[buildozer]

log_level = 2
warn_on_root = 0
