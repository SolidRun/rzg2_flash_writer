# RZ/V2N Flash Writer

Flash Writer is a firmware programming utility for the Renesas RZ/V2N SoC. It provides an interactive command-line interface over SCIF (serial) for writing to eMMC and SPI NOR flash memory.

## Supported Boards

| BOARD | DDR | Output |
|-------|-----|--------|
| `RZV2N_EVK` | LPDDR4X | `Flash_Writer_SCIF_RZV2N_EVK_LPDDR4X.mot` |
| `RZV2N_DEV` | LPDDR4X | `Flash_Writer_SCIF_RZV2N_DEV_LPDDR4X.mot` |
| `RZV2N_SR_SOM_8GB` | LPDDR4X | `Flash_Writer_SCIF_RZV2N_SR_SOM_8GB_LPDDR4X.mot` |
| `RZV2N_UNIVERSAL` | Internal memory only | `Flash_Writer_SCIF_RZV2N_COMMON_INTERNAL_MEMORY.mot` |

## Prerequisites

Download and extract the ARM GCC cross-compiler (aarch64-none-elf):

```bash
cd ~
wget https://developer.arm.com/-/media/Files/downloads/gnu-a/10.3-2021.07/binrel/gcc-arm-10.3-2021.07-x86_64-aarch64-none-elf.tar.xz
tar xvf gcc-arm-10.3-2021.07-x86_64-aarch64-none-elf.tar.xz
```

## Building

```bash
CROSS_COMPILE=/home/root/gcc/gcc-arm-10.3-2021.07-x86_64-aarch64-none-elf/bin/aarch64-none-elf- \
    make -f makefile-v2n.gcc-arm BOARD=RZV2N_EVK
```

Replace `BOARD=RZV2N_EVK` with the target board from the table above.

### Build Options

| Option | Values | Default | Description |
|--------|--------|---------|-------------|
| `SERIAL_FLASH` | `ENABLE`, `DISABLE` | `ENABLE` | Include SPI NOR flash support |
| `EMMC` | `ENABLE`, `DISABLE` | `ENABLE` | Include eMMC support |
| `QSPI_IOV` | `1_8V`, `3_3V` | `1_8V` | QSPI I/O voltage |
| `EMMC_IOV` | `1_8V`, `3_3V` | `1_8V` | eMMC I/O voltage |

Example with options:

```bash
CROSS_COMPILE=/home/root/gcc/gcc-arm-10.3-2021.07-x86_64-aarch64-none-elf/bin/aarch64-none-elf- \
    make -f makefile-v2n.gcc-arm BOARD=RZV2N_EVK SERIAL_FLASH=ENABLE EMMC=DISABLE
```

### Clean

```bash
make -f makefile-v2n.gcc-arm clean
```

## Programming

The `flash-tools/flash_writer_tool.py` script automates firmware programming over the serial downloader (SCIF). It loads the flash writer onto the board, then writes BL2 and FIP images to the target flash device.

### Prerequisites

- Python 3 with `pyserial` and `tqdm` packages
- USB serial connection to the board (default: `/dev/ttyUSB0`)
- Board set to serial download boot mode

### SPI NOR

```bash
python3 flash-tools/flash_writer_tool.py --target spi \
    --fw Flash_Writer_SCIF_RZV2N_SR_SOM_8GB_LPDDR4X.mot \
    --bl2 bl2_bp_spi-rzv2n-sr-som.srec \
    --fip fip-rzv2n-sr-som.srec
```

### eMMC

```bash
python3 flash-tools/flash_writer_tool.py --target emmc \
    --fw Flash_Writer_SCIF_RZV2N_SR_SOM_8GB_LPDDR4X.mot \
    --bl2 bl2_bp_mmc-rzv2n-sr-som.bin \
    --fip fip-rzv2n-sr-som.bin
```

### Options

| Option | Default | Description |
|--------|---------|-------------|
| `--port` | `/dev/ttyUSB0` | Serial port device |
| `--speed` | `921600` | Baudrate for data transfer |
| `--target` | *(required)* | Flash target: `spi` or `emmc` |
| `--fw` | *(required)* | Path to flash writer `.mot` file |
| `--bl2` | | BL2 image (`.srec` for SPI, `.bin` for eMMC) |
| `--fip` | | FIP image (`.srec` for SPI, `.bin` for eMMC) |
| `--overlays` | | FIT image with DT overlays (eMMC only) |

## Output

Build artifacts are placed in `AArch64_output/`:

- `.mot` — Motorola S-record (used for flashing)
- `.bin` — Raw binary
- `.axf` — ARM executable

## License

BSD 3-Clause — see [LICENSE.md](LICENSE.md) for details.
