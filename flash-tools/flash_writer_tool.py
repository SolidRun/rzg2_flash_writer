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
    'bl2': {'partition': '1', 'sector': 0x1, 'ram': '8101E00'},
    'fip': {'partition': '1', 'sector': 0x300, 'ram': '0'},
    'overlays': {'partition': '1', 'sector': 0x1800, 'ram': '0'},
}


def parse_args():
    parser = argparse.ArgumentParser(
        description='RZ/V2N Flash Writer Tool - Program SPI NOR or eMMC over serial',
        epilog='''Examples:
  SPI NOR:  %(prog)s --target spi --fw Flash_Writer.mot --bl2 bl2_bp_spi.srec --fip fip.srec
  eMMC:     %(prog)s --target emmc --fw Flash_Writer.mot --bl2 bl2_bp_mmc.bin --fip fip.bin
  eMMC:     %(prog)s --target emmc --fw Flash_Writer.mot --bl2 bl2_bp_mmc.srec --fip fip.srec
''',
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--port', default='/dev/ttyUSB0', help='Serial port device (default: /dev/ttyUSB0)')
    parser.add_argument('--speed', default=921600, type=int, help='Baudrate for data transfer (default: 921600)')
    parser.add_argument('--target', choices=['spi', 'emmc'], required=True, help='Flash target: spi or emmc')
    parser.add_argument('--fw', required=True, help='Path to flash writer .mot file')
    parser.add_argument('--bl2', help='Path to BL2 image (.srec or .bin)')
    parser.add_argument('--fip', help='Path to FIP image (.srec or .bin)')
    parser.add_argument('--overlays', help='Path to FIT image with DT overlays (eMMC only)')

    args = parser.parse_args()

    if not (args.bl2 or args.fip or args.overlays):
        parser.error('At least one of --bl2, --fip, or --overlays must be specified')

    if args.target == 'spi' and args.overlays:
        parser.error('--overlays is only supported with --target emmc')

    return args


def open_serial(port, baudrate, timeout=1):
    ser = serial.Serial(port, baudrate=baudrate, timeout=timeout,
                        xonxoff=False, rtscts=False, dsrdtr=False)
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


def emmc_write_srec(ser, name, file_path, partition, sector_number, ram_addr):
    """Write S-record file to eMMC using EM_W command.

    Protocol: EM_W -> partition -> sector -> RAM address -> send srec file
    Uses blind delays (1s) between commands like the shell script.
    """
    emmc_delay = 1.0

    print(f"\nWriting {name} to eMMC (EM_W, S-record)")
    print(f"  Partition: {partition}")
    print(f"  Sector:    0x{format(sector_number, 'X')}")
    print(f"  RAM addr:  0x{ram_addr}")
    print(f"  File: {file_path}")

    ser.write(b"EM_W\r")
    time.sleep(emmc_delay)
    ser.write((partition + '\r').encode())
    time.sleep(emmc_delay)
    sector_hex = format(sector_number, 'X')
    ser.write((sector_hex + '\r').encode())
    time.sleep(emmc_delay)
    ser.write((ram_addr + '\r').encode())
    time.sleep(emmc_delay)

    print("Sending file...")
    send_file(ser, file_path)
    time.sleep(emmc_delay)
    # Drain any remaining output from flash writer
    time.sleep(1.0)
    remaining = ser.read(ser.in_waiting or 0)
    if remaining:
        sys.stdout.write(remaining.decode(errors='ignore'))
        sys.stdout.flush()
    print(f"{name} written to eMMC.")


def emmc_write_bin(ser, name, file_path, partition, sector_number):
    """Write binary file to eMMC using EM_WB command.

    Protocol: EM_WB -> partition -> sector -> file size (hex) -> send binary file
    Uses blind delays (1s) between commands like the shell script.
    """
    emmc_delay = 1.0

    print(f"\nWriting {name} to eMMC (EM_WB, binary)")
    print(f"  Partition: {partition}")
    print(f"  Sector:    0x{format(sector_number, 'X')}")
    print(f"  File: {file_path}")

    ser.write(b"EM_WB\r")
    time.sleep(emmc_delay)
    ser.write((partition + '\r').encode())
    time.sleep(emmc_delay)
    sector_hex = format(sector_number, 'X')
    ser.write((sector_hex + '\r').encode())
    time.sleep(emmc_delay)
    file_size = os.path.getsize(file_path)
    file_size_hex = format(file_size, 'X')
    ser.write((file_size_hex + '\r').encode())
    time.sleep(emmc_delay)

    print("Sending file...")
    send_file(ser, file_path)
    time.sleep(emmc_delay)
    # Drain any remaining output from flash writer
    time.sleep(1.0)
    remaining = ser.read(ser.in_waiting or 0)
    if remaining:
        sys.stdout.write(remaining.decode(errors='ignore'))
        sys.stdout.flush()
    print(f"{name} written to eMMC.")


def emmc_write(ser, name, file_path, addr):
    """Write file to eMMC, auto-selecting EM_W or EM_WB based on file type."""
    if is_srec(file_path):
        emmc_write_srec(ser, name, file_path, addr['partition'],
                        addr['sector'], addr['ram'])
    else:
        emmc_write_bin(ser, name, file_path, addr['partition'],
                       addr['sector'])


def emmc_configure(ser):
    """Configure eMMC boot partition settings via EM_SECSD.

    Uses blind delays (1s) between commands like the shell script.
    """
    emmc_delay = 1.0

    print("\nConfiguring eMMC boot settings...")

    # Set EXT_CSD register 177 (0xB1) BOOT_BUS_CONDITIONS:
    #   BOOT_MODE bit[4:3] = 0x1 (SDR + High Speed timings)
    #   BOOT_BUS_WIDTH bit[1:0] = 0x2 (x8 bus width)
    #   Value = 0x0a
    print("  Setting EXT_CSD register 0xB1 (BOOT_BUS_CONDITIONS) = 0x0a...")
    ser.write(b"EM_SECSD\r")
    time.sleep(emmc_delay)
    ser.write(b"b1\r")
    time.sleep(emmc_delay)
    ser.write(b"0a\r")
    time.sleep(emmc_delay)

    # Set EXT_CSD register 179 (0xB3) PARTITION_CONFIG:
    #   BOOT_ACK bit[6] = 0x0 (No boot acknowledge)
    #   BOOT_PARTITION_ENABLE bit[5:3] = 0x1 (Boot partition 1 enabled)
    #   Value = 0x08
    print("  Setting EXT_CSD register 0xB3 (PARTITION_CONFIG) = 0x08...")
    ser.write(b"EM_SECSD\r")
    time.sleep(emmc_delay)
    ser.write(b"b3\r")
    time.sleep(emmc_delay)
    ser.write(b"08\r")
    time.sleep(emmc_delay)

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
        time.sleep(1.0)
        ser.close()
        ser = open_serial(args.port, args.speed)
        time.sleep(0.5)
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
            emmc_write(ser, "BL2", args.bl2, EMMC_ADDRESSES['bl2'])
            time.sleep(3)

        if args.fip:
            emmc_write(ser, "FIP", args.fip, EMMC_ADDRESSES['fip'])
            time.sleep(3)

        if args.overlays:
            emmc_write(ser, "DT Overlays", args.overlays, EMMC_ADDRESSES['overlays'])

        # Configure eMMC boot partition
        emmc_configure(ser)

    ser.close()
    elapsed = int(time.time() - start_time)
    print(f"\n=== Flashing complete in {elapsed} seconds ===")


if __name__ == "__main__":
    main()
