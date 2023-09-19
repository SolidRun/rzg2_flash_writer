/*
 * Copyright (c) 2015-2018, Renesas Electronics Corporation
 * All rights reserved.
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions are met:
 *
 *   - Redistributions of source code must retain the above copyright notice,
 *     this list of conditions and the following disclaimer.
 *
 *   - Redistributions in binary form must reproduce the above copyright
 *     notice, this list of conditions and the following disclaimer in the
 *     documentation and/or other materials provided with the distribution.
 *
 *   - Neither the name of Renesas nor the names of its contributors may be
 *     used to endorse or promote products derived from this software without
 *     specific prior written permission.
 *
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
 * AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
 * IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
 * ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
 * LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
 * CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
 * SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
 * INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
 * CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
 * ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
 * POSSIBILITY OF SUCH DAMAGE.
 */

#include "common.h"
#include "dgtable.h"
#include "dgmodul1.h"
#include "ddrcheck.h"
#include "secprv.h"
#if SERIAL_FLASH == 1
#include "dgmodul4.h"
#endif /* SERIAL_FLASH == 1 */
#if EMMC == 1
#include "dgemmc.h"
#endif /* EMMC == 1 */

/********************************************************/
/*        ROM TABLE                                     */
/********************************************************/
const com_menu MonCom[COMMAND_UNIT] = {
/*--------------------- Basic command ------------------------------*/
	"H"		, dgHelp			,  0	,
#if SERIAL_FLASH == 1
	"XCS"		, dgClearSpiflash0		,  0	,
	"XLS"		, dgG2LoadSpiflash0		,  0	,
	"XLS2"		, dgG2LoadSpiflash0_2		,  0	,
	"XLS3"		, dgG2LoadSpiflash0_3		,  0	,
#if SECPROV == 1
	"XLS2S"		, dgG2LoadSpiflash0_2s	, 0	,
	"XLS3S"		, dgG2LoadSpiflash0_3s	, 0	,
#endif /* SECPROV == 1 */
	"XINFO_SA0"	, dgG2InfoSpiflash0_SA0		,  0	,
	"XINFO_SA0_S"	, dgG2InfoSetSpiflash0_SA0	,  0	,
	"XINFO"		, dgG2InfoSpiflash0		,  0	,
	"XINFO_S"	, dgG2InfoSetSpiflash0		,  0	,
#endif /* SERIAL_FLASH == 1 */
#if EMMC == 1
	"EM_DCID"	, &dg_emmc_disp_cid		,  0	,
	"EM_DCSD"	, &dg_emmc_disp_csd		,  0	,
	"EM_DECSD"	, &dg_emmc_disp_ext_csd		,  0	,
	"EM_SECSD"	, &dg_emmc_set_ext_csd		,  0	,
	"EM_W"		, &dg_emmc_write_mot		,  0	,
	"EM_WB"		, &dg_emmc_write_bin		,  0	,
	"EM_E"		, &dg_emmc_erase		,  0	,
#if SECPROV == 1
	"EM_WS"		, dg_emmc_write_mots	, 0	,
	"EM_WBS"	, dg_emmc_write_bins	, 0	,
#endif /* SECPROV == 1 */
#endif /* EMMC == 1 */
	"SUP"		, dgScifSpeedUp			,  0	,
	"DDRCK"		, dgDdrTest			,  0	,
	"RAMCK"		, dgRamTest			,  0	,
	"RESET"		, dgReset			,  0	,
	TBL_END		, 0				,  0
};
