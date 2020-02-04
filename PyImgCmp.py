import os
import cv2

from skimage.measure import compare_ssim

from openpyxl import Workbook
from openpyxl import load_workbook
from openpyxl.worksheet.worksheet import Worksheet

class FileCompareResult(object):
    CODE_ERROR = -1
    CODE_WARN = -2
    CODE_SUCCESS = 0

    def __init__(self, code):
        self.code = code

class ImageCompareResult(FileCompareResult):
    def __init__(self, imagefile, otherfile, diff, dimensions, code = FileCompareResult.CODE_SUCCESS):
        super().__init__(code)
        self.imagefile = imagefile
        self.otherfile = otherfile
        self.dimensions = dimensions
        self.diff = diff

    def __str__(self):
        '''
        if FileCompareResult.CODE_ERROR == self.code:
            return '{},w:{:d},h:{:d},c:{:d}'.format(self.imagefile, self.dimensions[0], self.dimensions[1], self.dimensions[2])
        else:
        '''
        return '{},{},{:.10f},w:{:d},h:{:d},c:{:d}'.format(self.imagefile, self.otherfile, self.diff, self.dimensions[0], self.dimensions[1], self.dimensions[2])

    def iterator(self):
        return str(self).split(',')

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
            #print ('Invalid compare inputs: left={}{}, right={}{}'.format(img1.dtype, img1.shape, img2.dtype, img2.shape))
            return ImageCompareResult(imagefile1, imagefile2, ImageComparater.IGNORE_DIFF_SCORE, img1.shape, FileCompareResult.CODE_WARN)
        
        try:
            bgrScore = compare_ssim(img1, img2, multichannel=True)
        except ValueError:
            print ('Invalid compare inputs: left={}{}{}, right={}{}{}'.format(imagefile1, img1.dtype, img1.shape, imagefile2, img2.dtype, img2.shape))
            return ImageCompareResult(imagefile1, imagefile2, ImageComparater.IGNORE_DIFF_SCORE, img1.shape, FileCompareResult.CODE_ERROR)
        return ImageCompareResult(imagefile1, imagefile2, 1.0 - bgrScore, img1.shape)

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

    def __init__(self, imagefile, folder, comparater: ImageComparater):
        super().__init__(folder)
        self.imagefile = imagefile
        self.comparater = comparater
        self.equal_list = []
        self.similar_list = []
        self.error_list = []

    def insert_result(self, result: ImageCompareResult):
        if FileCompareResult.CODE_ERROR == result.code:
            self.error_list.append(result)
        elif FileCompareResult.CODE_WARN == result.code:
            #dimensions not equal, pass over
            return
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
        self.insert_result(self.comparater.calculate_diff(self.imagefile, imagefile))

    def start(self):
        super().start()
        if not len(self.equal_list) == 0:
            #we only need the equal one
            self.similar_list.clear
            self.error_list.clear
        elif not len(self.similar_list) == 0:
            if len(self.similar_list) == 1:
                #the only one similar, can be treated as equal
                self.equal_list.append(self.similar_list[0])
                self.similar_list.clear
        elif not len(self.error_list) == 0:
            if len(self.error_list) == 1:
                #the only one that dimensions match, can be treated as equal
                self.equal_list.append(self.error_list[0])
                self.error_list.clear

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
        '''
        #add empty row
        ws.append([])
        '''

    def print(self, compare_task: ImageFileCompareTask):
        equal_list = compare_task.equal_list
        similar_list = compare_task.similar_list
        error_list = compare_task.error_list
        len_equal = len(equal_list)
        len_similar = len(similar_list)
        len_error = len(error_list)
        if not len_equal == 0:
            #print equal sheet
            self.print_sheet(ExcelPrinter.EQUAL_SHEET_NAME, equal_list)
        elif not len_similar == 0:
            #print similar sheet
            self.print_sheet(ExcelPrinter.SIMILAR_SHEET_NAME, similar_list)
        elif not len_error == 0:
            #print error sheet
            self.print_sheet(ExcelPrinter.ERROR_SHEET_NAME, error_list)
        self.finish_print()

class ImageFolderCompareTask(ImageFileIterator):
    def __init__(self, folder1, folder2, comparater: ImageComparater, printer: ResultPrinter):
        super().__init__(folder1)
        self.otherfolder = folder2
        self.comparater = comparater
        self.printer = printer

    def process(self, file):
        file_compare_task = ImageFileCompareTask(file, self.otherfolder, self.comparater)
        file_compare_task.start()
        # print results
        self.printer.print(file_compare_task)

if __name__ == '__main__':
    ui_folder = 'launcher'
    proj_folder = 'future-skin-red'
    xlsx_filename = 'launcher.xlsx'

    comparater = ImageFolderCompareTask(proj_folder, ui_folder, ImageSSIMComparater(), ExcelPrinter(xlsx_filename))
    comparater.start()


