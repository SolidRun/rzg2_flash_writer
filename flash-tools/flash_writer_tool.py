#!/usr/bin/env python3

import serial
import argparse
import time
import sys
from tqdm import tqdm
import os

# RZ/V2N SPI NOR flash address map
SPI_ADDRESSES = {
    'bl2': {'ram': '8101E00', 'flash': '0'},
    'fip': {'ram': '0', 'flash': '60000'},
}

# RZ/V2N eMMC address map
EMMC_ADDRESSES = {
    'bl2': {'partition': '1', 'sector': 0x1},
    'fip': {'partition': '1', 'sector': 0x300},
    'overlays': {'partition': '1', 'sector': 0x1800},
}


def parse_args():
    parser = argparse.ArgumentParser(
        description='RZ/V2N Flash Writer Tool - Program SPI NOR or eMMC over serial',
        epilog='''Examples:
  SPI NOR:  %(prog)s --target spi --fw Flash_Writer.mot --bl2 bl2_bp_spi.srec --fip fip.srec
  eMMC:     %(prog)s --target emmc --fw Flash_Writer.mot --bl2 bl2_bp_mmc.bin --fip fip.bin
''',
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--port', default='/dev/ttyUSB0', help='Serial port device (default: /dev/ttyUSB0)')
    parser.add_argument('--speed', default=921600, type=int, help='Baudrate for data transfer (default: 921600)')
    parser.add_argument('--target', choices=['spi', 'emmc'], required=True, help='Flash target: spi or emmc')
    parser.add_argument('--fw', required=True, help='Path to flash writer .mot file')
    parser.add_argument('--bl2', help='Path to BL2 image (.srec for SPI, .bin for eMMC)')
    parser.add_argument('--fip', help='Path to FIP image (.srec for SPI, .bin for eMMC)')
    parser.add_argument('--overlays', help='Path to FIT image with DT overlays (eMMC only)')

    args = parser.parse_args()

    if not (args.bl2 or args.fip or args.overlays):
        parser.error('At least one of --bl2, --fip, or --overlays must be specified')

    if args.target == 'spi' and args.overlays:
        parser.error('--overlays is only supported with --target emmc')

    return args


def open_serial(port, baudrate, timeout=1):
    ser = serial.Serial(port, baudrate=baudrate, timeout=timeout)
    return ser


def send_command(ser, command, expect=None, timeout=5):
    ser.write((command + '\r').encode())
    if expect:
        return wait_for_prompt(ser, expect, timeout)
    else:
        return True


def wait_for_prompt(ser, expect, timeout=5):
    end_time = time.time() + timeout
    buffer = ''
    while time.time() < end_time:
        data = ser.read(ser.in_waiting or 1)
        if data:
            decoded = data.decode(errors='ignore')
            buffer += decoded
            sys.stdout.write(decoded)
            sys.stdout.flush()
            clean_buffer = buffer.replace('\r', '').replace('\n', '')
            if expect in clean_buffer:
                return True
        else:
            time.sleep(0.1)
    print(f"\nBuffer received: {repr(buffer)}")
    raise Exception(f"Timeout waiting for '{expect}'")


def send_file(ser, file_path):
    file_size = os.path.getsize(file_path)
    with open(file_path, 'rb') as f:
        with tqdm(total=file_size, unit='B', unit_scale=True, desc='Sending') as pbar:
            while True:
                chunk = f.read(1024)
                if not chunk:
                    break
                ser.write(chunk)
                ser.flush()
                pbar.update(len(chunk))
    print("File transfer complete.")


def is_srec(file_path):
    """Check if file is S-record format based on extension."""
    return file_path.lower().endswith('.srec')


def spi_write_srec(ser, name, ram_addr, flash_addr, file_path):
    """Write S-record file to SPI NOR flash using XLS2 command.

    Protocol: XLS2 -> RAM address -> SPI flash address -> send file -> confirm 'y'
    """
    print(f"\nWriting {name} to SPI NOR flash (XLS2)")
    print(f"  RAM address:   0x{ram_addr}")
    print(f"  Flash address: 0x{flash_addr}")
    print(f"  File: {file_path}")

    send_command(ser, "XLS2")
    time.sleep(0.5)
    send_command(ser, ram_addr)
    time.sleep(0.5)
    send_command(ser, flash_addr)
    time.sleep(0.5)

    print("Sending file...")
    send_file(ser, file_path)
    time.sleep(0.5)

    # Confirm erase if flash is not blank
    send_command(ser, "y")
    time.sleep(0.5)
    print(f"{name} written to SPI NOR flash.")


def spi_write_bin(ser, name, flash_addr, file_path):
    """Write binary file to SPI NOR flash using XLS3 command.

    Protocol: XLS3 -> file size (hex) -> SPI flash address -> send file -> confirm 'y'
    """
    file_size = os.path.getsize(file_path)
    size_hex = format(file_size, 'X')

    print(f"\nWriting {name} to SPI NOR flash (XLS3)")
    print(f"  Flash address: 0x{flash_addr}")
    print(f"  File size:     0x{size_hex} ({file_size} bytes)")
    print(f"  File: {file_path}")

    send_command(ser, "XLS3")
    time.sleep(0.5)
    send_command(ser, size_hex)
    time.sleep(0.5)
    send_command(ser, flash_addr)
    time.sleep(0.5)

    print("Sending file...")
    send_file(ser, file_path)
    time.sleep(0.5)

    # Confirm erase if flash is not blank
    send_command(ser, "y")
    time.sleep(0.5)
    print(f"{name} written to SPI NOR flash.")


def spi_write(ser, name, ram_addr, flash_addr, file_path):
    """Write file to SPI NOR flash, auto-selecting XLS2 or XLS3 based on file type."""
    if is_srec(file_path):
        spi_write_srec(ser, name, ram_addr, flash_addr, file_path)
    else:
        spi_write_bin(ser, name, flash_addr, file_path)


def emmc_write(ser, name, file_path, sector_number):
    """Write binary file to eMMC using EM_WB command."""
    print(f"\nWriting {name} to eMMC")
    print(f"  Sector: 0x{format(sector_number, 'X')}")
    print(f"  File: {file_path}")

    send_command(ser, "EM_WB", expect="Select area(0-2)>")
    send_command(ser, "1", expect="Please Input Start Address in sector :")
    sector_hex = format(sector_number, 'X')
    send_command(ser, sector_hex, expect="Please Input File size(byte) : ")
    file_size = os.path.getsize(file_path)
    file_size_hex = format(file_size, 'X')
    send_command(ser, file_size_hex, expect="please send binary file!")

    print("Sending file...")
    send_file(ser, file_path)
    wait_for_prompt(ser, ">", timeout=10)
    print(f"{name} written to eMMC.")


def emmc_configure(ser):
    """Configure eMMC boot partition settings via EM_SECSD."""
    print("\nConfiguring eMMC boot settings...")

    # Set EXT_CSD register 177 (0xB1) BOOT_BUS_CONDITIONS
    print("  Setting EXT_CSD register 0xB1 (BOOT_BUS_CONDITIONS)...")
    send_command(ser, "EM_SECSD", expect="Please Input EXT_CSD Index(H'00 - H'1FF) :")
    send_command(ser, "b1", expect="Please Input Value(H'00 - H'FF) :")
    send_command(ser, "02", expect=">")

    # Set EXT_CSD register 179 (0xB3) PARTITION_CONFIG
    print("  Setting EXT_CSD register 0xB3 (PARTITION_CONFIG)...")
    send_command(ser, "EM_SECSD", expect="Please Input EXT_CSD Index(H'00 - H'1FF) :")
    send_command(ser, "b3", expect="Please Input Value(H'00 - H'FF) :")
    send_command(ser, "08", expect=">")

    print("eMMC boot configuration complete.")


def main():
    args = parse_args()

    # Step 1: Download flash writer at 115200
    ser = open_serial(args.port, 115200)

    print("=== RZ/V2N Flash Writer Tool ===")
    print(f"Target: {'SPI NOR Flash' if args.target == 'spi' else 'eMMC'}")
    print(f"Port:   {args.port}")
    print("")
    print("Please reset the board into SCIF download mode...")
    # RZ/V2N outputs "-- Load Program to SRAM" when ready for download
    # Older RZ/G2L boards output "please send !"
    wait_for_prompt(ser, "Load Program to SRAM", timeout=30)

    start_time = time.time()
    print(f"\nDownloading flash writer: {args.fw}")
    send_file(ser, args.fw)
    send_command(ser, "", ">")

    # Step 2: Increase baudrate
    if args.speed > 115200:
        print(f"\nIncreasing baudrate to {args.speed}...")
        send_command(ser, "SUP")
        ser.close()
        time.sleep(0.1)
        ser = open_serial(args.port, args.speed)
        send_command(ser, "", ">")

    # Step 3: Flash images
    if args.target == 'spi':
        # SPI NOR flash programming
        if args.bl2:
            addr = SPI_ADDRESSES['bl2']
            spi_write(ser, "BL2", addr['ram'], addr['flash'], args.bl2)
            time.sleep(1)

        if args.fip:
            addr = SPI_ADDRESSES['fip']
            spi_write(ser, "FIP", addr['ram'], addr['flash'], args.fip)

    else:
        # eMMC programming
        if args.bl2:
            emmc_write(ser, "BL2", args.bl2, EMMC_ADDRESSES['bl2']['sector'])
            time.sleep(1)

        if args.fip:
            emmc_write(ser, "FIP", args.fip, EMMC_ADDRESSES['fip']['sector'])
            time.sleep(1)

        if args.overlays:
            emmc_write(ser, "DT Overlays", args.overlays, EMMC_ADDRESSES['overlays']['sector'])

        # Configure eMMC boot partition
        emmc_configure(ser)

    ser.close()
    elapsed = int(time.time() - start_time)
    print(f"\n=== Flashing complete in {elapsed} seconds ===")


if __name__ == "__main__":
    main()
