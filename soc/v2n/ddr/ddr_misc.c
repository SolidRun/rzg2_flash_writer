/*
 * Copyright (c) 2024, Renesas Electronics Corporation. All rights reserved.
 *
 * SPDX-License-Identifier: BSD-3-Clause
 */

#include <stdint.h>
#include <stddef.h>
#include <arch_helpers.h>
#include <common/debug.h>
#include <lib/mmio.h>
#include <drivers/delay_timer.h>

#include "ddr_regs.h"
#include "ddr_private.h"


static void decode_streaming_message(void);


void ddrtop_mc_apb_rmw(uint32_t addr, uint32_t data, uint32_t mask)
{
	uint32_t tmp_data;

	tmp_data = ddrtop_mc_apb_rd(addr);
	data = (data & mask) | (tmp_data & (~mask));

	ddrtop_mc_apb_wr(addr, data);
}

void ddrtop_mc_apb_poll(uint32_t addr, uint32_t data, uint32_t mask)
{
	uint32_t tmp_data;

	tmp_data = ddrtop_mc_apb_rd(addr);
	tmp_data &= mask;

	while (tmp_data != data) {
		udelay(1);
		tmp_data = ddrtop_mc_apb_rd(addr);
		tmp_data &= mask;
	}
}

void ddrtop_mc_param_wr(uint32_t addr, uint32_t offset, uint32_t width, uint32_t data)
{
	uint32_t tmp_data;
	uint32_t tmp_mask;

	tmp_data = data << offset;
	tmp_mask = ((1 << width) - 1) << offset;

	ddrtop_mc_apb_rmw(addr, tmp_data, tmp_mask);
}

uint32_t ddrtop_mc_param_rd(uint32_t addr, uint32_t offset, uint32_t width)
{
	uint32_t tmp_data;
	uint32_t tmp_mask;

	tmp_data = ddrtop_mc_apb_rd(addr);
	tmp_mask = ((1 << width) - 1) << offset;

	return (tmp_data & tmp_mask) >> offset;
}

void ddrtop_mc_param_poll(uint32_t addr, uint32_t offset, uint32_t width, uint32_t data)
{
	uint32_t tmp_data;
	uint32_t tmp_mask;

	tmp_data = data << offset;
	tmp_mask = ((1 << width) - 1) << offset;

	ddrtop_mc_apb_poll(addr, tmp_data, tmp_mask);
}

void dwc_ddrphy_phyinit_userCustom_G_waitDone(uint8_t sel_train)
{
	uint32_t train_done = 0;
	uint32_t mail;

	do {
		/* Wait at least 500 cycles */
		uint32_t data = dwc_ddrphy_apb_rd(0x0d0004);

		if ((data & 0x1) == 0) {
			mail = get_mail(0);
			if (mail == 0xff || mail == 0x07) {
				train_done = 1;
			} else if (mail == 0x08) {
				decode_streaming_message();
			}
		}
	} while (train_done == 0);

	if (mail == 0xff) {
		ERROR("Training failed.\n");
		panic();
	}
}

uint32_t get_mail(uint8_t mode_32bits)
{
	uint32_t mail = 0;
	uint32_t wd_timer = 0;

	while ((dwc_ddrphy_apb_rd(0x0d0004) & 0x1) != 0)
		;

	mail = dwc_ddrphy_apb_rd(0x0d0032);

	if (mode_32bits != 0) {
		mail = (dwc_ddrphy_apb_rd(0x0d0034) << 16) | mail;
	}

	dwc_ddrphy_apb_wr(0x0d0031, 0x0000);

	while ((dwc_ddrphy_apb_rd(0x0d0004) & 0x1) == 0) {
		if (wd_timer++ > 1000) {
			ERROR("Watchdog timer overflow\n");
			panic();
		}
	}
	dwc_ddrphy_apb_wr(0x0d0031, 0x0001);

	VERBOSE("mail = %x\n", mail);
	return mail;
}

static void decode_streaming_message(void)
{
	uint32_t coded_message_hex;
	uint16_t num_args;
	int i;

	coded_message_hex = get_mail(1);
	/* Get the number of argument need to be read from mailbox */
	num_args = (uint16_t)(0xffff & coded_message_hex);
	for (i = 0; i < num_args; i++) {
		(void)get_mail(1);
	}
}

void ddrtop_prog_all0 (uint64_t start_addr, uint32_t addr_space)
{
	uint32_t bak_lp_auto_entry_en;

	ddrtop_mc_param_wr(ECC_DISABLE_W_UC_ERR_ADDR, ECC_DISABLE_W_UC_ERR_OFFSET, ECC_DISABLE_W_UC_ERR_WIDTH, 1); //ecc_disable_w_uc_err=1
	bak_lp_auto_entry_en = ddrtop_mc_param_rd(LP_AUTO_ENTRY_EN_ADDR, LP_AUTO_ENTRY_EN_OFFSET, LP_AUTO_ENTRY_EN_WIDTH); //Backup lp_auto_entry_en
	ddrtop_mc_param_wr(LP_AUTO_ENTRY_EN_ADDR, LP_AUTO_ENTRY_EN_OFFSET, LP_AUTO_ENTRY_EN_WIDTH, 0x0); //lp_auto_entry_en = 0x0

	ddrtop_mc_param_wr(BIST_START_ADDRESS_ADDR+0, 0, 32, (start_addr&0xffffffff)); //bist_start_address[31:0]
	ddrtop_mc_param_wr(BIST_START_ADDRESS_ADDR+1, 0, BIST_START_ADDRESS_WIDTH-32, ((start_addr>>32)&0x0ffffffff)); //bist_start_address[32:32]
	ddrtop_mc_param_wr(ADDR_SPACE_ADDR, ADDR_SPACE_OFFSET, ADDR_SPACE_WIDTH, addr_space); //2**addr_space
	ddrtop_mc_param_wr(BIST_DATA_CHECK_ADDR, BIST_DATA_CHECK_OFFSET, BIST_DATA_CHECK_WIDTH, 1);
	ddrtop_mc_param_wr(BIST_TEST_MODE_ADDR, BIST_TEST_MODE_OFFSET, BIST_TEST_MODE_WIDTH, 0b100);
	ddrtop_mc_param_wr(BIST_DATA_PATTERN_ADDR+0, 0, 32, 0x00000000); //bist_data_pattern[ 31:  0]
	ddrtop_mc_param_wr(BIST_DATA_PATTERN_ADDR+1, 0, 32, 0x00000000); //bist_data_pattern[ 63: 32]
	ddrtop_mc_param_wr(BIST_DATA_PATTERN_ADDR+2, 0, 32, 0x00000000); //bist_data_pattern[ 95: 64]
	ddrtop_mc_param_wr(BIST_DATA_PATTERN_ADDR+3, 0, 32, 0x00000000); //bist_data_pattern[127: 96]
	udelay(1);

	ddrtop_mc_param_wr(BIST_GO_ADDR, BIST_GO_OFFSET, BIST_GO_WIDTH, 1); //bist_go=1
	ddrtop_mc_param_poll(INT_STATUS_BIST_ADDR, INT_STATUS_BIST_OFFSET+0, 1, 1); //while(int_status_bist[0]!=1)
	ddrtop_mc_param_wr(BIST_GO_ADDR, BIST_GO_OFFSET, BIST_GO_WIDTH, 0); //bist_go=0
	ddrtop_mc_param_wr(INT_ACK_BIST_ADDR, INT_ACK_BIST_OFFSET+0, 1, 1); //int_ack_bist[0]=1
	ddrtop_mc_param_wr(INT_ACK_ECC_ADDR, INT_ACK_ECC_OFFSET, INT_ACK_ECC_WIDTH, 0x000001cf); //int_ack_ecc[8,7:6,3:0]=All-1
	ddrtop_mc_param_poll(INT_STATUS_BIST_ADDR, INT_STATUS_BIST_OFFSET+0, 1, 0); //while(int_status_bist[0]!=0)
	ddrtop_mc_param_poll(INT_STATUS_ECC_ADDR, INT_STATUS_ECC_OFFSET, INT_STATUS_ECC_WIDTH, 0); //while(int_status_ecc[31:0]!=0)

	ddrtop_mc_param_wr(LP_AUTO_ENTRY_EN_ADDR, LP_AUTO_ENTRY_EN_OFFSET, LP_AUTO_ENTRY_EN_WIDTH, bak_lp_auto_entry_en); //lp_auto_entry_en = bak_lp_auto_entry_en
	ddrtop_mc_param_wr(ECC_DISABLE_W_UC_ERR_ADDR, ECC_DISABLE_W_UC_ERR_OFFSET, ECC_DISABLE_W_UC_ERR_WIDTH, 0); //ecc_disable_w_uc_err=0
	udelay(1);
}
