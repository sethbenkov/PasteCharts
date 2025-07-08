import json
import os
from src.excel_handler import ExcelHandler
from src.slides_handler import SlidesHandler

def main():
    with open('config.json', 'r') as f:
        config = json.load(f)

    excel = ExcelHandler(config['excel_file'])
    slides = SlidesHandler(config['slides_id'], config['client_secret_file'])

    if not os.path.exists(config['image_dir']):
        os.makedirs(config['image_dir'])

    for i, mapping in enumerate(config['mappings']):
        image_name = f"{mapping['type']}_{i}.png"
        image_path = os.path.join(config['image_dir'], image_name)

        if mapping['type'] == 'chart':
            excel.save_chart_as_image(mapping['sheet_name'], mapping['source_name'], image_path)
        elif mapping['type'] == 'range':
            excel.save_range_as_image(mapping['sheet_name'], mapping['source_name'], image_path)

        if os.path.exists(image_path):
            slides.paste_image(image_path, mapping['slide_page_number'], mapping['position'], mapping['size'])

if __name__ == '__main__':
    main()