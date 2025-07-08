import xlwings as xw
from PIL import ImageGrab

class ExcelHandler:
    def __init__(self, file_path):
        self.file_path = file_path
        self.app = xw.App(visible=False)
        self.workbook = self.app.books.open(file_path)

    def save_chart_as_image(self, sheet_name, chart_name, image_path):
        """
        Saves a chart from an Excel sheet as an image file.
        """
        try:
            sheet = self.workbook.sheets[sheet_name]
            chart = sheet.charts[chart_name]
            chart.to_png(path=image_path)
            print(f"Successfully saved chart '{chart_name}' to '{image_path}'")
        except Exception as e:
            print(f"Error saving chart '{chart_name}': {e}")

    def save_range_as_image(self, sheet_name, range_name, image_path):
        """
        Saves a named range from an Excel sheet as an image file.
        """
        try:
            sheet = self.workbook.sheets[sheet_name]
            named_range = sheet.range(range_name)
            named_range.copy(picture=True)
            img = ImageGrab.grabclipboard()
            if img:
                img.save(image_path)
                print(f"Successfully saved range '{range_name}' to '{image_path}'")
            else:
                print(f"Error: No image found on clipboard for range '{range_name}'")
        except Exception as e:
            print(f"Error saving range '{range_name}': {e}")

    def __del__(self):
        self.workbook.close()
        self.app.quit()
