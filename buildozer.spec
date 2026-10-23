[app]
title = Sarpele padurii
package.name = sarpelepadurii
package.domain = ro.emma.games
source.dir = .
source.include_exts = py,png
source.exclude_dirs = .git,.github,bin,.buildozer
version = 1.0.0
requirements = python3,kivy==2.3.1
orientation = portrait
fullscreen = 1
android.api = 35
android.minapi = 23
android.ndk = 28c
android.archs = arm64-v8a, armeabi-v7a
android.accept_sdk_license = True
android.debug_artifact = apk
p4a.bootstrap = sdl2

[buildozer]
log_level = 2
warn_on_root = 1
