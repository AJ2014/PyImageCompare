import os
import cv2
import sys
if not sys.warnoptions:
    import warnings
    warnings.simplefilter("ignore")

from skimage.measure import compare_ssim

from openpyxl import Workbook
from openpyxl import load_workbook
from openpyxl.worksheet.worksheet import Worksheet

from openpyxl.styles import Color, PatternFill

class FileCompareResult(object):
    CODE_ERROR = -1
    CODE_WARN = -2
    CODE_SUCCESS = 0

    def __init__(self, code):
        self.code = code

class ImageCompareResult(FileCompareResult):
    def __init__(self, imagefile, otherfile, diff, dimensions, code = FileCompareResult.CODE_SUCCESS, reason = ''):
        super().__init__(code)
        self.imagefile = imagefile
        self.otherfile = otherfile
        self.dimensions = dimensions
        self.diff = diff
        self.reason = reason

    def __eq__(self, other) -> bool:
        return self.imagefile == other.imagefile and self.otherfile == other.otherfile

    def __str__(self):
        return '{},{},{:.10f},w:{:d},h:{:d},c:{:d}, {}'.format(self.imagefile, self.otherfile, self.diff, self.dimensions[0], self.dimensions[1], self.dimensions[2], self.reason)

    def iterator(self):
        return str(self).split(',')

    def correct(self) -> bool:
        split = self.imagefile.split('\\')
        imagefile_name = split[len(split) - 1]
        split = self.otherfile.split('\\')
        otherfile_name = split[len(split) - 1]
        return imagefile_name == otherfile_name

class ImageComparater(object):
    IGNORE_DIFF_SCORE = -1
    EQUAL_DIFF_SCORE = 0

    def calculate_diff(self, imagefile1, imagefile2) -> ImageCompareResult:
        return ImageCompareResult('', '', ImageComparater.EQUAL_DIFF_SCORE, [], FileCompareResult.CODE_SUCCESS)

class ImageSSIMComparater(ImageComparater):
    def calculate_diff(self, imagefile1, imagefile2):
        img1 = cv2.imread(imagefile1, cv2.IMREAD_UNCHANGED)
        img2 = cv2.imread(imagefile2, cv2.IMREAD_UNCHANGED)
        if not img1.dtype == img2.dtype or not img1.shape == img2.shape:
            return ImageCompareResult(imagefile1, imagefile2, ImageComparater.IGNORE_DIFF_SCORE, img1.shape, FileCompareResult.CODE_WARN, 'dimensions not match')
        shape1 = img1.shape
        shape2 = img2.shape
        try:
            bgrScore = compare_ssim(img1, img2, multichannel=True)
        except ValueError as e:
            print ('Invalid compare inputs: left={}{}{}, right={}{}{}'.format(imagefile1, img1.dtype, shape1, imagefile2, img2.dtype, shape2))
            return ImageCompareResult(imagefile1, imagefile2, ImageComparater.IGNORE_DIFF_SCORE, shape1, FileCompareResult.CODE_ERROR, str(e))
        return ImageCompareResult(imagefile1, imagefile2, 1.0 - bgrScore, shape1)

class ImageFileIterator(object):
    def __init__(self, folder):
        if not os.path.isdir(folder):
            raise ValueError('Invalid input folder {} when init'.format(folder))
        self.folder = folder

    def is_imagefile(self, imagepath):
        if not os.path.isfile(imagepath):
            return False
        split = imagepath.split('.')
        if 'png' == split[len(split) - 1] or 'jpg' == split[len(split) - 1]:
            return True
        return False

    def process(self, file):
        pass

    def iterator(self, folder):
        if not os.path.isdir(folder):
            raise ValueError('Invalid input folder {} when iterator'.format(folder))
        for file in os.listdir(folder):
            file = os.path.join(folder, file)
            if os.path.isdir(file):
                self.iterator(file)
            elif self.is_imagefile(file):
                self.process(file)

    def start(self):
        self.iterator(self.folder)

class ImageFileCompareTask(ImageFileIterator):
    MAX_DIFF_RECORD = 10

    def __init__(self, imagefile, folder):
        super().__init__(folder)
        self.imagefile = imagefile
        self.comparater = ImageSSIMComparater()
        self.equal_list = []
        self.similar_list = []
        self.warn_list = []
        self.error_list = []

    def insert_result(self, result: ImageCompareResult):
        if FileCompareResult.CODE_ERROR == result.code:
            self.error_list.append(result)
        elif FileCompareResult.CODE_WARN == result.code:
            if len(self.warn_list) == 0:
                self.warn_list.append(result)
        elif FileCompareResult.CODE_SUCCESS == result.code:
            if ImageComparater.EQUAL_DIFF_SCORE == result.diff:
                self.equal_list.append(result)
            else:
                length = len(self.similar_list)
                position = -1
                for i in range(length):
                    record = self.similar_list[i]
                    if record.diff > result.diff:
                        position = i
                        break
                if length < ImageFileCompareTask.MAX_DIFF_RECORD:
                    self.similar_list.append(0)
                    if -1 == position:
                        self.similar_list[length] = result
                        return
                    length += 1
                else:
                    if -1 == position:
                        return
                for i in range(length - 1, position, -1):
                    self.similar_list[i] = self.similar_list[i - 1]
                self.similar_list[position] = result

    def process(self, imagefile):
        result = self.comparater.calculate_diff(self.imagefile, imagefile)
        self.insert_result(result)

    def start(self):
        super().start()
        len_equal = len(self.equal_list)
        len_similar = len(self.similar_list)
        len_error = len(self.error_list)
        len_warn = len(self.warn_list)
        #print('{}: equal {:d}, similar {:d}, error {:d}'.format(self.imagefile, len_equal, len_similar, len_error))
        if not len_equal == 0:
            #we only need the equal one
            self.similar_list.clear
            self.error_list.clear
        elif not len_similar == 0:
            if len_similar == 1:
                #the only one similar, can be treated as equal
                self.equal_list.append(self.similar_list[0])
                self.similar_list.clear
        elif not len_error == 0:
            if len_error == 1:
                #the only one that dimensions match, can be treated as equal
                self.equal_list.append(self.error_list[0])
                self.error_list.clear

        len_equal = len(self.equal_list)
        len_similar = len(self.similar_list)
        len_error = len(self.error_list)
        #no record
        if len_equal == 0 and len_similar == 0 and len_error == 0:
            if len_warn > 0:
                self.error_list.append(self.warn_list[0])
        #maintain one record for similar and error list
        if len_similar > 1:
            del self.similar_list[1:len(self.similar_list)]
        if len_error > 1:
            del self.error_list[1:len(self.error_list)]

class ResultPrinter(object):
    def print(self, compare_task: ImageFileCompareTask):
        pass

class ExcelPrinter(ResultPrinter):
    EQUAL_SHEET_NAME = 'equal'
    SIMILAR_SHEET_NAME = 'similar'
    ERROR_SHEET_NAME = 'error'

    def openxlsx(self, filename) -> Workbook:
        for file in os.listdir('.'):
            if os.path.isfile(file):
                if filename == file:
                    return load_workbook(filename)
        wbk = Workbook()
        wbk.save(filename)
        return load_workbook(filename)

    def __init__(self, filename, default_sheet_name = EQUAL_SHEET_NAME):
        self.filename = filename
        self.xlsxfile = self.openxlsx(filename)
        ws = self.xlsxfile.active
        ws.title = default_sheet_name
        self.xlsxfile.save(filename)
        self.sheet_dict = dict()
        self.sheet_dict[default_sheet_name] = 0
        self.fill = PatternFill(patternType='solid', fill_type='solid', fgColor=Color('C4C4C4'))

    def finish_print(self):
        for ws in self.xlsxfile.worksheets:
	        #format column width
            dims = {}
            for row in ws.rows:
                for cell in row:
                    if cell.value:
                        dims[cell.column_letter] = max(dims.get(cell.column_letter, 0), len(str(cell.value)))
            for col, value in dims.items():
                ws.column_dimensions[col].width = value
        self.xlsxfile.save(self.filename)

    def print_sheet(self, sheet_name, results_list):
        if not sheet_name in self.xlsxfile:
            self.xlsxfile.create_sheet(sheet_name)
        ws = self.xlsxfile[sheet_name]
        for result in results_list:
            ws.append(result.iterator())
            if not result.correct():
                self.sheet_dict[sheet_name] = self.sheet_dict.get(sheet_name, 0) + 1
                for row in ws.iter_rows(min_row=ws.max_row):
                    for cell in row:
                        cell.fill = self.fill
                ws.cell(row = 1, column = 8, value = int(self.sheet_dict[sheet_name]))

    def print(self, compare_task: ImageFileCompareTask):
        equal_list = compare_task.equal_list
        similar_list = compare_task.similar_list
        error_list = compare_task.error_list
        len_equal = len(equal_list)
        len_similar = len(similar_list)
        len_error = len(error_list)
        if not len_equal == 0:
            #print equal sheet
            #print('{} equal record {}'.format(compare_task.imagefile, len_equal))
            self.print_sheet(ExcelPrinter.EQUAL_SHEET_NAME, equal_list)
        elif not len_similar == 0:
            #print similar sheet
            #print('{} similar record {}'.format(compare_task.imagefile, len_similar))
            self.print_sheet(ExcelPrinter.SIMILAR_SHEET_NAME, similar_list)
        elif not len_error == 0:
            #print error sheet
            #print('{} error record {}'.format(compare_task.imagefile, len_error))
            self.print_sheet(ExcelPrinter.ERROR_SHEET_NAME, error_list)
        else:
            #no result
            print('{} no record !!!'.format(compare_task.imagefile))
        self.finish_print()

class ImageFolderCompareTask(ImageFileIterator):
    def __init__(self, folder1, folder2, printer: ResultPrinter):
        super().__init__(folder1)
        self.otherfolder = folder2
        self.printer = printer

    def process(self, file):
        file_compare_task = ImageFileCompareTask(file, self.otherfolder)
        file_compare_task.start()
        # print results
        self.printer.print(file_compare_task)

if __name__ == '__main__':
    ui_folder = 'launcher'
    proj_folder = 'future-skin-red'
    xlsx_filename = 'launcher.xlsx'

    comparater = ImageFolderCompareTask(proj_folder, ui_folder, ExcelPrinter(xlsx_filename))
    comparater.start()


