import sys
print("exe:", sys.executable)
for m in ["requests","trafilatura","bs4","curl_cffi"]:
    try:
        __import__(m)
        print(m, "OK")
    except Exception as e:
        print(m, "MISSING", e)
