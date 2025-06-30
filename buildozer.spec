[app]
title = Amharic PDF Reader
package.name = amharicpdfreader
package.domain = org.example
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
source.include_patterns = tessdata/**
version = 0.1
requirements = python3,kivy==2.2.1,PyPDF2,gTTS,plyer,pdf2image,pytesseract,urllib3,requests,pillow
orientation = portrait
icon = icon.png

[buildozer]
log_level = 2
android.permissions = READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE,INTERNET
android.api = 33
android.minapi = 21
android.archs = arm64-v8a, armeabi-v7a
android.add_aapt_options = --utf8
