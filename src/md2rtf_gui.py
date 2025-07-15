"""
Markdown to RTF Converter with Obsidian Integration

This script converts Obsidian-compatible Markdown notes into RTF format, including:
- Resolving and embedding images from the Obsidian vault (based on `app.json`)
- Modifying image links from Obsidian-style `![[image.png]]` to usable RTF paths
- Automatically resizing images and tables in the generated RTF
- Providing a user-friendly GUI using Gooey

NOTES:
- This script is designed to work with **Obsidian vaults**.
- It looks for the `.obsidian/app.json` file to resolve the configured attachment folder path.
- Logging output is saved to `conversion.log` and printed to the console.

Requirements:
- Python 3.x
- `pypandoc`, `gooey`
- pandoc installed on the system "winget install pandoc"

Author: [B]
Revised Date: [01/07/2025]
"""
import os
import sys
import json
import re
import logging
from pathlib import Path
import pypandoc
from gooey import Gooey, GooeyParser

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s', handlers=[logging.FileHandler("conversion.log"), logging.StreamHandler()])
logger = logging.getLogger()

# Step 1: Find vault and config paths
def get_config_path(path=None):
    logger.info("Finding config path...")
    start_path = Path(path).resolve() if path else Path.cwd()
    
    for parent in [start_path, *start_path.parents]:
        config_path = parent / ".obsidian"
        if config_path.exists() and config_path.is_dir():
            logger.debug(f"Found config path: {config_path}")
            return parent, config_path

    logger.error("Config path not found.")
    return None, None


def get_image_store_path(note_path=None, vault_path=None, config=None):
    note_path = Path(note_path)
    logger.info("Getting image store path...")
    if config:
        app_json_path = config / "app.json"
        if app_json_path.exists():
            try:
                with app_json_path.open("r", encoding="utf-8") as f:
                    app_config = json.load(f)
                    attachment_folder = app_config.get("attachmentFolderPath")
                    logger.debug(f"{note_path}")
                    if "." in attachment_folder:
                        # We are relative
                        image_store_path = (note_path.parent / attachment_folder).resolve()
                        logger.debug(f"Relative attachment path: {image_store_path}")
                        return image_store_path
                    elif attachment_folder:
                        image_store_path = (vault_path / attachment_folder).resolve()
                        logger.debug(f"Image store path: {image_store_path}")
                        return image_store_path
            except (json.JSONDecodeError, FileNotFoundError):
                logger.exception("Error reading app.json.")
    logger.error("Image store path not found.")
    return None

# Step 2: Modify image paths in Markdown
def modify_image_paths(md_content, filestore_path):
    logger.info("Modifying image paths in Markdown...")
    
    def replace_image_path(match):
        image_path = match.group(1)
        absolute_path = os.path.join(filestore_path, os.path.basename(image_path))
        logger.debug(f"Replacing image path: {image_path} with {absolute_path}")
        return f'![{os.path.basename(image_path)}]({absolute_path})'

    modified_content = re.sub(r'!\[\[(.*?)\]\]', replace_image_path, md_content)
    logger.info("Image paths modified.")
    return modified_content

# Step 3: Convert Markdown to RTF
def convert_md_to_rtf(input_file, output_file, filestore_path):
    logger.info(f"Converting Markdown file {input_file} to RTF...")

    with open(input_file, 'r', encoding='utf-8') as f:
        md_content = f.read()

    # Normalize line endings to Unix style
    md_content = md_content.replace('\r\n', '\n').replace('\r', '\n')

    # Remove horizontal rules (--- on their own line)
    md_content = re.sub(r'^\s*---\s*$', '', md_content, flags=re.MULTILINE)

    # Modify image paths
    modified_md_content = modify_image_paths(md_content, filestore_path)

    # Ensure blank lines between blocks EXCEPT between lines that are part of a table
    lines = modified_md_content.split('\n')
    result = []
    prev_nonblank = False
    in_table = False

    for i, line in enumerate(lines):
        stripped = line.strip()

        if '|' in line:
            result.append(line)
            in_table = True
            prev_nonblank = True
        elif stripped == '':
            if not prev_nonblank:
                # Skip multiple blank lines
                continue
            result.append('')
            prev_nonblank = False
            in_table = False
        else:
            if prev_nonblank and not in_table:
                # Add blank line before non-table blocks
                result.append('')
            result.append(line)
            prev_nonblank = True
            in_table = False

    modified_md_content = '\n'.join(result)

    # Write to temp file
    temp_md_file = 'temp.md'
    with open(temp_md_file, 'w', encoding='utf-8') as f:
        f.write(modified_md_content)

    # Convert to RTF using Pandoc
    output = pypandoc.convert_file(temp_md_file, 'rtf', format='markdown')

    # Prepend RTF header
    rtf_header = r'{\rtf1\ansi\deff0\nouicompat{\fonttbl{\f0\fnil\fcharset0 Calibri;}}{\*\generator Riched20 10.0.22621}\viewkind4\uc1 '
    output = rtf_header + output

    with open(output_file, 'wb') as f:
        f.write(output.encode('utf-8'))
        f.write(b'\x00')

    os.remove(temp_md_file)
    logger.info(f"RTF file created: {output_file}")


# Step 4: Resize tables and images in RTF
def resize_tables_and_images(rtf_content, table_width_target, image_width_target):
    logger.info("Resizing tables and images in RTF content...")
    
    def resize_image(match):
        image_data = match.group(0)
        current_width_match = re.search(r"\\picwgoal(\d+)", image_data)
        current_height_match = re.search(r"\\pichgoal(\d+)", image_data)
        
        if current_width_match and current_height_match:
            current_width = int(current_width_match.group(1))
            current_height = int(current_height_match.group(1))
            logger.debug(f"Current image dimensions: {current_width}x{current_height}")
            
            new_height = int(current_height * (image_width_target / current_width))
            logger.debug(f"Resized image dimensions: {image_width_target}x{new_height}")
            
            image_data = re.sub(r"\\picwgoal\d+", rf"\\picwgoal{image_width_target}", image_data)
            image_data = re.sub(r"\\pichgoal\d+", rf"\\pichgoal{new_height}", image_data)
        
        return image_data
    
    rtf_content = re.sub(r"{\\pict.*?}", resize_image, rtf_content, flags=re.DOTALL)
    
    def resize_table(match):
        table = match.group(0)
        cell_matches = re.findall(r"\\cellx\d+", table)
        num_columns = len(cell_matches)
        
        new_widths = [int(table_width_target / num_columns) * (i + 1) for i in range(num_columns)]
        for i, cell in enumerate(cell_matches):
            table = table.replace(cell, f"\\cellx{new_widths[i]}")
        return table
    
    rtf_content = re.sub(r"\\trowd.*?\\row", resize_table, rtf_content, flags=re.DOTALL)
    
    logger.info("Resizing completed.")
    return rtf_content

@Gooey(program_name="Markdown to RTF Converter")
def main():
    parser = GooeyParser(description="Convert Markdown files to RTF format with image path adjustments.")
    parser.add_argument("input_md_file", help="Select the Markdown file to convert", widget="FileChooser")
    args = parser.parse_args()
    
    input_file = args.input_md_file
    vault_path, config_path = get_config_path(input_file)
    image_store_path = get_image_store_path(input_file, vault_path, config_path)
    
    if not image_store_path:
        logger.error("Error: Could not locate image store path.")
        return
    
    output_file = "output.rtf"
    convert_md_to_rtf(input_file, output_file, image_store_path)
    
    with open(output_file, "r", encoding="utf-8") as file:
        rtf_content = file.read()
    
    resized_rtf_content = resize_tables_and_images(rtf_content, 1000 * 20, 380 * 20)
    
    with open("size_output.rtf", "w", encoding="utf-8") as file:
        file.write(resized_rtf_content)
    
    logger.info("Processing complete. Output file: size_output.rtf")
    os.system('start wordpad.exe "size_output.rtf"')

if __name__ == "__main__":
    # Handle PyInstaller bundle path for pandoc
    if hasattr(sys, '_MEIPASS'):
        pandoc_path = os.path.join(sys._MEIPASS, 'pandoc', 'pandoc.exe')
        pypandoc.download_pandoc = lambda: None  # prevent auto-download
        pypandoc.pandoc_path = pandoc_path
    else:
        try:
            pypandoc.get_pandoc_version()
        except OSError:
            raise RuntimeError("Pandoc is not installed or not in PATH.")
        
    # Launch application
    main()