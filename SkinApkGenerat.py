import os
import subprocess
from PyImgCmp import *
import shutil
import re

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def get_proj_drawable_folders(proj_folder):
    proj_res_folder = '{}\\res'.format(proj_folder)
    proj_drawable_folders = []
    drawable_pattern = re.compile('^.*drawable$')
    mipmap_pattern = re.compile('^.*mipmap.*$')
    for file in os.listdir(proj_res_folder):
        file = os.path.join(proj_res_folder, file)
        if os.path.isdir(file):
            if drawable_pattern.match(str(file)) or mipmap_pattern.match(str(file)):
                proj_drawable_folders.append(file)
    return proj_drawable_folders

APKTOOL_EXE = 'apktool.exe'
apktool_filepath = resource_path(APKTOOL_EXE)

def decode_apk(apk_filepath, output_folder):
    splits = apk_filepath.split('\\')
    apk_filename = splits[len(splits) - 1]
    splits = apk_filename.split('.')
    decode_folder = splits[0]
    decode_folder = '{}\\{}'.format(output_folder, decode_folder)

    batcmd = '{} d -f {} -o {}'.format(apktool_filepath, apk_filepath, decode_folder)
    result = subprocess.check_output(batcmd, shell=True)
    return decode_folder

def build_apk(decode_folder, output_folder):
    splits = decode_folder.split('\\')
    apk_filename = '{}.apk'.format(splits[len(splits) - 1])
    build_filepath = '{}\\{}'.format(output_folder, apk_filename)
    #aapt1 won't do png file improving, which may cause apk file too large or even failure
    #solution 1, use -nc, won't do png file compress
    #solution 2, use -use-aapt2, will do png file compress if needed

    batcmd = '{} b -use-aapt2 {} -o {}'.format(apktool_filepath, decode_folder, build_filepath)
    result = subprocess.check_output(batcmd, shell=True)
    return build_filepath

class ImageReplaceTask(ImageFolderCompareTask):
    def start_file_compare_task(self, file):
        file_compare_task = super().start_file_compare_task(file)
        equal_results = file_compare_task.equal_list
        if not len(equal_results) == 0:
            old_file = equal_results[0].imagefile
            new_file = equal_results[0].otherfile
            print('replace {} with {}'.format(old_file, new_file))
            if os.path.isfile(old_file):
                # 1. Remove old file
                try:
                    os.remove(old_file)
                except OSError as e:
                    print ("Error: %s - %s." % (e.filename, e.strerror))
            # 2. copy new file
            shutil.copy(new_file, old_file)
        return file_compare_task

def main(skin_template_apk, ui_folders, output_folder, excel_filename):
    """
    Do image file compare between ui folders and project folders.
    Output report excel file and new skin apk package
    Args:
        skin_template_apk: old skin apk package file path
        ui_folders: new skin ui resource folders, must be a list
        output_folder: report file and new apk file output folder
        excel_filename: report file name
    """
    # Step1, decode apk package
    decode_folder = decode_apk(skin_template_apk, output_folder)
    print('decode folder: ', decode_folder)

    # Step2, replace matched resources
    proj_drawable_folders = get_proj_drawable_folders(decode_folder)
    print('project drawable folders: ', proj_drawable_folders)

    excel_filepath = '{}\\{}'.format(output_folder, excel_filename)
    comparater = ImageReplaceTask(proj_drawable_folders, ui_folders, ExcelPrinter(excel_filepath))
    comparater.start()
    print('Report excel file: ', excel_filepath)

    # Step3, build apk package
    build_filepath = build_apk(decode_folder, output_folder)
    print('build apk: ', build_filepath)

if __name__ == '__main__':

    skin_template_apk = 'D:\\Projects\\GWM_V2\\SkinSwitchTool\\PyProj\\launcher-future-skin-blue.apk'
    ui_folders = ['D:\\Projects\\GWM_V2\\SkinSwitchTool\\PyProj\\common', 'D:\\Projects\\GWM_V2\\SkinSwitchTool\\PyProj\\launcher']
    output_folder = 'D:\\Projects\\GWM_V2\\SkinSwitchTool\\PyProj\\output'
    excel_filename = 'launcher.xlsx'

    main(skin_template_apk, ui_folders, output_folder, excel_filename)
