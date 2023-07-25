"""
Arju Reza
COMP 6350 Project #2
"""

# imports
import sys
import os
from hashlib import sha256

# variables
FileHeader = dict()
FileFooter = dict()
FoundFiles = dict()
FilesOutput = dict()
num_of_files = 0

# File signatures
# How to format hex using b"": https://stackoverflow.com/questions/6269765/what-does-the-b-character-do-in-front-of-a-string-literal and https://stackoverflow.com/questions/2672326/what-does-a-leading-x-mean-in-a-python-string-xaa
# File signature table: https://www.garykessler.net/library/file_sigs.html
# Slicing: https://www.tutorialspoint.com/What-does-colon-operator-do-in-Python

FileHeader[".mpg"] = b"\x00\x00\x01\xB3\x14"
FileFooter[".mpg"] = b"\x00\x00\x01\xB7"
FileHeader[".pdf"] = b"\x25\x50\x44\x46"
FileFooter[".pdf"] = b"\x25\x25\x45\x4F\x46"
FileHeader[".bmp"] = b"\x42\x4D\x76\x30\x01"
FileHeader[".gif"] = b"\x47\x49\x46\x38\x39\x61"
FileFooter[".gif"] = b"\x00\x3B"
FileHeader[".jpg"] = b"\xFF\xD8\xFF\xE0"
FileFooter[".jpg"] = b"\xFF\xD9"
FileHeader[".docx"] = b"\x50\x4B\x03\x04\x14\x00\x06\x00"
FileFooter[".docx"] = b"\x50\x4B\x05\x06"
FileHeader[".avi"] = b"\x52\x49\x46\x46"
FileHeader[".png"] = b"\x89\x50\x4E\x47\x0D\x0A\x1A\x0A"
FileFooter[".png"] = b"\x49\x45\x4E\x44\xAE\x42\x60\x82"

# Command line arguments
# https://www.tutorialspoint.com/python/python_command_line_arguments.htm
cmd_arguments = sys.argv

# Should only be 2 arguments (script name and disk drive name)
if (len(cmd_arguments) != 2):
    print("Format: FileRecovery.py File.dd")
    exit(1)

ddName = cmd_arguments[1]

# Reading binary file
# https://stackoverflow.com/questions/8710456/reading-a-binary-file-with-python
with open(ddName, mode="rb") as file:
    data = file.read()

num_of_files = 0

# main function to find files
for file_type in FileHeader:

    data_string = data
    start = 0
    offset = 0
    file_header = FileHeader[file_type]

    while (offset != -1):

        # find matching file signatures of type file_type
        # https://www.geeksforgeeks.org/python-string-find/gy
        offset = data_string.find(file_header)

        if (offset != -1):
            # false positive check variable
            false_signature = False

            # Generate file name
            file_name = f"File{num_of_files}{file_type}"

            # where the file starts
            start_of_file = start + offset

            # where to file ends
            # PDF
            if (file_type == ".pdf"):
                # next PDF
                temp_string = data_string[offset + len(file_header) + 1:]
                next_pdf_start = temp_string.find(file_header)

                if (next_pdf_start != -1):
                    pdf_string = data_string[offset + len(file_header):next_pdf_start]
                else:
                    pdf_string = data_string
                
                offset_footer = 0
                size = 0
                while offset_footer != -1:
                    offset_footer = pdf_string.find(FileFooter[file_type])
                    
                    if (offset_footer != -1):
                        size = size + offset_footer + len(FileFooter[file_type])
                        pdf_string = pdf_string[offset_footer + len(FileFooter[file_type]):]
                
                eof = start_of_file + size
            
            # BMP
            # Bytes 2-5 contain the file size in little-endian order
            # https://www.file-recovery.com/bmp-signature-format.htm
            elif (file_type == ".bmp"):

                # Check to see if bytes 6-9 are reserved (0s)
                reserved_bytes = data_string[offset + 6: offset + 10]
                if (reserved_bytes == b"\x00\x00\x00\x00"):
                    # https://www.geeksforgeeks.org/how-to-convert-bytes-to-int-in-python/
                    size = int.from_bytes(data_string[offset + 2: offset + 6], "little", signed=False)
                    eof = start_of_file + size
                else:
                    false_signature = True
            
            # AVI
            # Bytes 4-7 contain the file size in little endian
            elif (file_type == ".avi"):
                # https://www.geeksforgeeks.org/how-to-convert-bytes-to-int-in-python/
                size = int.from_bytes(data_string[offset + 4: offset + 8], "little", signed=False)
                eof = start_of_file + size
            
            # every other file type
            else:
                footer_string = data_string[offset:]
                offset_footer = footer_string.find(FileFooter[file_type])
                eof = start_of_file + offset_footer + len(FileFooter[file_type])
                # DOCX
                if (file_type == ".docx"):
                    eof += 18
                size = eof - start_of_file
            
            # Valid file is found
            if (not false_signature):
                # sha256 hash
                # https://docs.python.org/3/library/hashlib.html
                file_data = data[start_of_file:eof]
                file_sha = sha256(file_data).hexdigest()

                # https://www.w3schools.com/python/python_tuples.asp
                file_info = (file_name, start_of_file, eof, file_sha, size)

                if (start_of_file != eof):
                    FoundFiles[file_name] = file_info
                    num_of_files += 1
                
            else:
                size = 10000
                
            # next loop setup
            data_string = data_string[offset + size:]
            start = start + offset + size

os.system("mkdir -p RecoveredFiles")

# recover files and generate output
for file in FoundFiles:
    # create output string for each file
    output = f"{FoundFiles[file][0]} Start Offset: {FoundFiles[file][1]} End Offset: {FoundFiles[file][2]} SHA-256: {FoundFiles[file][3]}"
    FilesOutput[file] = output

    # file recovery
    of = FoundFiles[file][0]
    skip = FoundFiles[file][1]
    count = FoundFiles[file][4]

    recover_cmd = f"dd if=Project2.dd of={of} bs=1 skip={skip} count={count}"
    os.system(recover_cmd)
    os.system(f"mv {of} RecoveredFiles/")

# output
print(f"The disk image contains {num_of_files} files \n")
for i in FilesOutput:
    print(FilesOutput[i])

print("Recovered files are located in ~/RecoveredFiles")


