#!/usr/bin/env python
# -*- coding: utf-8 -*-
# nds-rom-patch.py by theracermaster
# Patcher for OpenPatcher/DS Scene ROM Tool-style patches, like these:
# 5584 - Pokemon White Version [B552501C]
# 00004600: B0 68 8A 00 79 AA 19 72 13 9A B6 9F E1 CC 8B 10 → 3C 00 9F E5 00 10 90 E5 38 20 9F E5 02 00 51 E1
# 00004610: 6F 5B 4F A0 96 42 86 94 76 C3 26 C3 A8 DE 0F A0 → 34 10 9F 05 08 10 80 05 48 11 80 05 2C 10 9F 05
# 00004620: 67 61 FE DF 5A F9 45 41 DA 64 3C B1 23 5C 8A F6 → A8 10 80 05 E8 11 80 05 24 00 9F E5 00 10 90 E5
# 00004630: A4 4F EC 86 C5 A7 9C B9 41 BB E4 30 F4 FF 67 5D → 20 20 9F E5 02 00 51 E1 01 10 A0 03 0A 10 C0 05
# 00004640: 26 8E B1 79 8B 29 02 64 C9 D7 AA 3E 9A A4 83 EA → 1E FF 2F E1 84 7F 18 02 4F 03 5F E1 37 B3 AA 36
# 00004650: 70 FB D7 39 32 C6 6D 3A D2 6F 6F 7B → 6A E0 AA 36 00 0A 18 02 1F FF AA 28
# 00004EA4: 1E FF 2F E1 → D5 FD FF EA
# ...

import argparse, binascii, os, re, shutil, sys

def binpatch(input_file, output_file, offset, find, replace):
	# Remove the output ROM if it already exists
	if not os.path.exists(output_file):
		# Replace it with a copy of the input ROM
		shutil.copy(input_file, output_file)

	offset_int = int(offset, 16)
	find_bytes = find.decode("hex")
	replace_bytes = replace.decode("hex")

	with open(output_file, "r+b") as rom:
		# Seek to offset
		rom.seek(offset_int, os.SEEK_SET)
		# Read bytes at offset
		found = binascii.hexlify(rom.read(len(find) / 2)).upper()
		# Do the bytes read match the find pattern in the patch?
		if found == find:
			# Yes. Patch the ROM
			print("Found @ 0x{0}:\t{1}".format(offset, found))
			rom.seek(offset_int, os.SEEK_SET)
			rom.write(replace_bytes)
			rom.seek(offset_int, os.SEEK_SET)
			replaced = binascii.hexlify(rom.read(len(find) / 2)).upper()
			print("Replaced with:\t\t{0}".format(replaced))
		else:
			# No. The ROM or patch is invalid, so exit
			print("ERROR: {0} not found, patching failed!".format(find))
			exit(2)
	rom.close()

def open_patch(input_rom, patch_file, output_rom):
	rom = open(input_rom, "rb")
	crc32 = format(binascii.crc32(rom.read()) & 0xFFFFFFFF, 'X')
	print("Input ROM: {0} (CRC32: {1})".format(input_rom, crc32))
	rom.close()

	with open(patch_file) as patch:
		patch_line_num = 0
		# Read the patch file line-by-line
		for line_num, line in enumerate(patch, 1):
			# Is there a matching CRC32 in the line?
			if crc32 in line:
				# Yes. Next lines (until newline) are the patch data (offset: find → replace)
				patch_line_num = line_num
				print("Patch for {0} found on line {1}".format(crc32, patch_line_num))
			# Is there patch data in the line?
			if "→" in line and patch_line_num:
				# Yes. Split the data by : and → to get the offset, find pattern, and replace pattern
				patch_data = re.split(":|→", line.rstrip().replace(" ", ""))
				# print(patch_data)
				# Patch the ROM using the patch data
				binpatch(input_rom, output_rom, patch_data[0], patch_data[1], patch_data[2])
		patch.close()
		if not patch_line_num:
			print("No matching patch found for {0}!".format(crc32))
			exit(2)

	rom = open(output_rom, "rb")
	crc32 = format(binascii.crc32(rom.read()) & 0xFFFFFFFF, 'X')
	print("Output ROM: {0} (CRC32: {1})".format(input_rom, crc32))

def main():
	input_rom = ""
	output_drv = ""

	parser = argparse.ArgumentParser()
	parser.add_argument("input", help="Input ROM")
	parser.add_argument("patch", help="Patch file")
	parser.add_argument("output", help="Output ROM")
	args = parser.parse_args()
	if not os.path.exists(args.input):
		raise OSError(2, "No such file or directory", args.input)
	elif not os.path.exists(args.patch):
		raise OSError(2, "No such file or directory", args.patch)
	if os.path.exists(args.output):
		os.remove(args.output)

	input_rom = os.path.normpath(args.input)
	patch_file = os.path.normpath(args.patch)
	output_rom = os.path.normpath(args.output)

	open_patch(input_rom, patch_file, output_rom)

if __name__ == "__main__":
    main()
