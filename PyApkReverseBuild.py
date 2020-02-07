import os

apk_filename = 'launcher-future-skin-blue'

# Step 1, decode apk package
#os.system('java -jar apktool_2.4.0.jar d {}.apk'.format(apk_filename))


new_packagename = 'com.harman.hmi.launcher_future_skin_red'
new_apkname = 'launcher-future-skin-red.apk'
manifest_filename = 'AndroidManifest.xml'
apktool_yml_filename = 'apktool.yml'
import re

manifest_filepath = '{}\\{}'.format(apk_filename, manifest_filename)
apktool_yml_filepath = '{}\\{}'.format(apk_filename, apktool_yml_filename)

def replace_match(filepath, regex, replacement):
    "Match file content with regex, and replace with replacement"
    pattern = re.compile(regex, re.IGNORECASE)
    try:
        fin = open(filepath, 'rt')
        content = fin.read()
        fin.close()
        match = pattern.search(content)
        print(match)
        if match:
            #replace content
            new_content = pattern.sub(replacement, content)
        else:
            raise AssertionError('{} doesn\'t contains {}'.format(filepath, regex))

        fout = open(filepath, 'wt')
        fout.write(new_content)
        fout.close()
    except OSError as e:
        print (e)
        raise AssertionError('{} not found'.format(filepath))

# Step 2, rename package
replace_match(manifest_filepath, 'package=\"[\w.]+\"', 'package=\"{}\"'.format(new_packagename))

# Step 3, rename apk file
replace_match(apktool_yml_filepath, 'apkFileName: [\w.]+', 'apkFileName: {}'.format(new_apkname))


#os.system('java -jar apktool_2.4.0.jar b {}'.format(apk_filename))
