#include "constants/scrcmd.h"
#include "fielddata/script/scr_seq/event_T20R0301.h"
#include "msgdata/msg/msg_0547_T20R0301.h"
	.include "asm/macros/script.inc"

	.rodata

	ScrDef scr_seq_T20R0301_000
	ScrDefEnd

scr_seq_T20R0301_000:
	Compare VAR_UNK_4160, 0
	GoToIfNe _StefanConfession
	SimpleNPCMsg msg_0547_T20R0301_00000
	End

_StefanConfession:
	SimpleNPCMsg msg_0547_T20R0301_00001
	End
	.balign 4, 0
