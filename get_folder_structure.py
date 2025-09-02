import os

def save_folder_structure(root_folder, output_file):
    with open(output_file, "w", encoding="utf-8") as f:
        for foldername, subfolders, filenames in os.walk(root_folder):
            # Get relative path depth for indentation
            level = foldername.replace(root_folder, "").count(os.sep)
            indent = "    " * level
            f.write(f"{indent}{os.path.basename(foldername)}/\n")

            # Write files with extra indentation
            sub_indent = "    " * (level + 1)
            for filename in filenames:
                f.write(f"{sub_indent}{filename}\n")

    print(f"✅ Folder structure saved to {output_file}")


# Example usage
save_folder_structure(
    r"C:\Users\prana\Desktop\PROJECTS\tubetalk.ai",   # Root folder
    "folder_structure.txt"                            # Output file
)
