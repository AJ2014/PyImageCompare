import subprocess
from PyImgCmp import *
import shutil

def decode_apk(apk_filepath, output_folder):
    splits = apk_filepath.split('\\')
    apk_filename = splits[len(splits) - 1]
    splits = apk_filename.split('.')
    decode_folder = splits[0]
    decode_folder = '{}\\{}'.format(output_folder, decode_folder)
    batcmd = 'java -jar apktool_2.4.0.jar d -f {} -o {}'.format(apk_filepath, decode_folder)
    result = subprocess.check_output(batcmd, shell=True)
    return decode_folder

def build_apk(decode_folder, output_folder):
    splits = decode_folder.split('\\')
    apk_filename = '{}.apk'.format(splits[len(splits) - 1])
    build_filepath = '{}\\{}'.format(output_folder, apk_filename)
    batcmd = 'java -jar apktool_2.4.0.jar b {} -o {}'.format(decode_folder, build_filepath)
    result = subprocess.check_output(batcmd, shell=True)
    return build_filepath

class ImageReplaceTask(ImageFolderCompareTask):
    def __init__(self, folders1, folders2, printer: ResultPrinter):
        super().__init__(folders1)
        self.otherfolders = folders2
        self.printer = printer

    def start_file_compare_task(self, file):
        file_compare_task = super().start_file_compare_task(file)
        equal_results = file_compare_task.equal_list
        if not len(equal_results) == 0:
            old_file = equal_results[0].imagefile
            new_file = equal_results[0].otherfile
            print('replace {} with {}'.format(old_file, new_file))
            shutil.move(new_file, old_file)

if __name__ == '__main__':

    skin_template_apk = '..\\launcher-future-skin-blue.apk'
    ui_folder = '..\\launcher'
    output_folder = '..\\output'
    excel_filename = 'launcher.xlsx'

    # Step1, decode apk package
    decode_folder = decode_apk(skin_template_apk, output_folder)
    print('decode folder: ', decode_folder)

    # Step2, replace matched resources
    drawable_folder = '{}\\res\\drawable'.format(decode_folder)
    mipmap_mdpi_v4_folder = '{}\\res\\mipmap-mdpi-v4'.format(decode_folder)
    excel_filepath = '{}\\{}'.format(output_folder, excel_filename)

    proj_folders = [drawable_folder, mipmap_mdpi_v4_folder]
    ui_folders = [ui_folder]
    comparater = ImageFolderCompareTask(proj_folders, ui_folders, ExcelPrinter(excel_filepath))
    comparater.start()

    # Step3, build apk package
    build_filepath = build_apk(decode_folder, output_folder)
    print('build apk: ', build_filepath)

