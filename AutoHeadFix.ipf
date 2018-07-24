#pragma rtGlobals=3		// Use modern global access method and strict wave access.
#pragma version =1
#include "GUIPDirectoryLoad"
#include "GUIPMath"


// ******************************************************
// Loader for data from AutoHeadFix program running on the raspberry pi
// Last modified 2018/07/24 by Jamie Boyd

// Each line in Text file is tab separated, as follows:
//  mouse num (or 0 for events where mouse is not known);		unix Time;  event;		human formatted time;  
// event can be SeshStart, SeshEnd, entry, exit, check+ or check-, complete. example:
// 0000201608423	1532156724.25	entry	2018-07-21 00:05:24


Menu "Macros"
	"Load Auto Head Fix Data", AHF_Loader ()
End


// Loader makes datetime and event waves for each mouse

// Each file name should contain metadata on cageID: "headFix_" + cageID + "_" + YYYMMDD + (optionally) "_" + other meta-Data
// e.g., headFix_AB_20161108.txt or

CONSTANT kSECSPERDAY = 86400 // number of seconds in one day
CONSTANT kSECSTODAYSTART = 25200 // we bin data by day to mouse-time where a day starts at 7 am, to cleanly divide light and dark phases
CONSTANT kUNIXEPOCHGMOFFSET = 2082816000// the Unix epoch started on jan 01 1970, Igor time is calculated from jan 01 1904. 
// Unix time.time(), used in the acquisition code,  gives seconds in Universal (Greenwich) time, not accounting for timezone.
//  this constant combines both the 66 year and 8 hour offset

#define kDEBUG

// ******************************************************
// Utility functions to  return a  formatted text string representing a given number of seconds since 1970 (UNIX time format)
// Last Modified 2015/12/16 by Jamie Boyd
function/s AHF_DateTime (secs)
	variable secs
	
	secs += kUNIXEPOCHGMOFFSET
	return secs2date (secs, -2) + " " + Secs2Time(secs, 2)
end

// ******************************************************
// Utility functions to  parse a date time string formatted exactly as in the AHF text files and return the corresponding UNIXy number of seconds
// Result may be off by exactly 3600 (one hr) in the Spring/Summer due to daylight savings time differences between local and  Grenwich time (UT)
// Last Modified 2015/12/16 by Jamie Boyd
function AHF_Secs (dtStr)
	string dtStr
	
	// date
	string dateStr = stringfromlist (0, dtStr, " ")
	variable year = str2num (stringfromlist (0, dateStr, "-"))
	variable month = str2num (stringfromlist (1, dateStr, "-"))
	variable day = str2num (stringfromlist (2, dateStr, "-"))
	// time
	string timeStr = stringfromlist (1, dtStr, " ")
	variable hrs = str2num (stringFromList (0, timeStr, ":"))
	variable minutes = str2num (stringFromList (1, timeStr, ":"))
	variable seconds= str2num (stringFromList (2, timeStr, ":"))
	// add them all up
	variable totalSecs = date2secs(year, month, day) +  (hrs * 3600) +  (minutes* 60) + seconds
	// subtract offset for Igor/local to UNIX/UT
	totalSecs -= kUNIXEPOCHGMOFFSET
	return totalSecs
end

// sample usage:
//	print/d AHF_Secs ("2015-08-14 17:31:39.498807")
//	1439602299.49881
//	print AHF_DateTime (1439602299.49881)
//	2015-08-14 17:31
 
 // ******************************************************
// Makes the control panel for loading text files, and makes some global variables
// Last Modified 2015/12/15 by Jamie Boyd
function AHF_Loader ()
	variable panelDirectoryExists = GUIPDirPanel ("Auto Head Fix", ".txt", "AHF_Load",extraVertPix = 140)
	if ((panelDirectoryExists & 1) ==0) // directory did not previously exist, so add globals for options for AHF
		// folder for data
		NewDataFolder/o root:AutoHeadFixData
		SVAR GUIPDataFolderStr = root:packages:GUIP:Auto_Head_Fix:GUIPDataFolderStr
		GUIPDataFolderStr = "root:AutoHeadFixData"
		// list box with IDs and groups
		make/o/t/n = (1,2) root:AutoHeadFixData:GrpList
		WAVE/T grpList = root:AutoHeadFixData:GrpList
		grpList = ""
		SetDimLabel 1,0,TagID,grpList
		SetDimLabel 1,1,Group,grpList
		make/o/n = (1,2) root:packages:GUIP:Auto_Head_Fix:GrpListSel
		WAVE GrpListSel = root:packages:GUIP:Auto_Head_Fix:GrpListSel
		GrpListSel = 3
		// variables for overwriting and loading movies
		Variable/G root:packages:GUIP:Auto_Head_Fix:loadMovies =0
		Variable/G root:packages:GUIP:Auto_Head_Fix:Overwrite = 0
		Variable/G root:packages:GUIP:Auto_Head_Fix:ExistingMiceOnly =0
		SVAR optionStr = root:packages:GUIP:Auto_Head_Fix:GUIPloadOptionStr
		optionStr = "Overwrite=no;LoadMovies=no;"
	endif
	AHF_UpdateGrps ()
end


Function Auto_Head_Fix_drawControls (vTop)
	variable vTop
	
	// variables for overwriting and loading movies
	Variable/G root:packages:GUIP:Auto_Head_Fix:loadMovies =0
	Variable/G root:packages:GUIP:Auto_Head_Fix:Overwrite = 0
	Variable/G root:packages:GUIP:Auto_Head_Fix:ExistingMiceOnly =0
	SVAR optionStr = root:packages:GUIP:Auto_Head_Fix:GUIPloadOptionStr
	optionStr = "Overwrite=no;LoadMovies=no;"
	SVAR GUIPDataFolderStr = root:packages:GUIP:Auto_Head_Fix:GUIPDataFolderStr
	GUIPDataFolderStr = "root:AutoHeadFixData"
	
	// list box with IDs and groups
	WAVE/T/Z grpList = root:AutoHeadFixData:GrpList
	if (!(waveExists (grpList)))
		make/t/n = (1,2) root:AutoHeadFixData:GrpList
		WAVE/T grpList = root:AutoHeadFixData:GrpList
		grpList = ""
		SetDimLabel 1,0,TagID,grpList
		SetDimLabel 1,1,Group,grpList
	endif
	WAVE/Z GrpListSel = root:packages:GUIP:Auto_Head_Fix:GrpListSel
	if (!(waveExists (GrpListSel)))
		make/n = (1,2) root:packages:GUIP:Auto_Head_Fix:GrpListSel
		WAVE grpListSel = root:packages:GUIP:Auto_Head_Fix:GrpListSel
		grpListSel = 3
	endif
	ListBox GroupsList win = Auto_Head_FixLoader,pos={5,vTop + 22},size={285,110}
	ListBox GroupsList win = Auto_Head_FixLoader,listWave=GrpList,selWave=GrpListSel, mode= 1
	ListBox GroupsList win = Auto_Head_FixLoader,widths={106,161},userColumnResize= 1, proc=AHF_GrpListProc
	CheckBox OverwriteCheck win = Auto_Head_FixLoader, pos={4,vTop + 2},size={91,15},title="Overwrite Existing Data"
	CheckBox OverwriteCheck win = Auto_Head_FixLoader, help={"If a file for a particular day was loaded previously, delete existing data and load new data"}
	CheckBox OverwriteCheck win = Auto_Head_FixLoader, variable= root:packages:GUIP:Auto_Head_Fix:Overwrite, proc = AHF_OptionsCheckProc
	CheckBox LoadMoviesCheck win = Auto_Head_FixLoader,pos={136,vTop + 2},size={71,16},proc=AHF_OptionsCheckProc,title="Load Movies"
	CheckBox LoadMoviesCheck win = Auto_Head_FixLoader,help={"Try to load movies for head fixed events, using relative file path from text file folder"}
	CheckBox LoadMoviesCheck win = Auto_Head_FixLoader,variable= root:packages:GUIP:Auto_Head_Fix:loadMovies
	CheckBox ExistingMiceOnlyCheck win = Auto_Head_FixLoader,pos={214,57},size={74,15},proc=AHF_OptionsCheckProc,title="Existing Mice"
	CheckBox ExistingMiceOnlyCheck win = Auto_Head_FixLoader,help={"Load data only for mice for which a TagID has been given a grp ID"}
	CheckBox ExistingMiceOnlyCheck win = Auto_Head_FixLoader,variable= root:packages:GUIP:Auto_Head_Fix:ExistingMiceOnly
	ListBox GroupsList win = Auto_Head_FixLoader,pos={5,vTop + 22},size={285,110}
	ListBox GroupsList win = Auto_Head_FixLoader,listWave=GrpList,selWave=GrpListSel, mode= 1
	ListBox GroupsList win = Auto_Head_FixLoader,widths={106,161},userColumnResize= 1, proc=AHF_GrpListProc
end

// Updates list of groups of mice by their tag IDs by checking waves already made, and ensures that an entry exists in the table for that tag
Function AHF_UpdateGrps ()

	WAVE/T grpList = root:AutoHeadFixData:GrpList
	WAVE grpListSel = root:packages:GUIP:Auto_Head_Fix:GrpListSel
	variable iMouse, nMice = dimSize (grpList, 0)
	string grpWaves = GUIPListObjs ("root:AutoHeadFixData", 1, "*_Date", 0, "")
	variable iWave, nWaves = ItemsInList(grpWaves, ";")
	string  mouseIDStr, grp
	variable mouseID
	for (iWave =0; iWave < nWaves; iWave +=1)
		SplitString /E="([[:alpha:]]*)([[:digit:]]*)" stringFromList (iWave, grpWaves, ";"), grp, mouseIDStr
		mouseID = str2num (mouseIDStr)
		for(iMouse =0; iMouse < nMice; iMouse +=1)
			if (mouseID == str2num (grpList [iMouse] [0])) // ID is present in the list
				// check that the grp from the wave name agrees with grp from the list
				if (cmpStr (grp, grpList [iMouse] [1]) != 0)
					printf "Mouse ID %d is part of group %s in the list, but data for this mouse has already been loaded as group %s\r", mouseID, grpList [iMouse] [1], grp
				endif
				break
			endif
		endfor
		// if we don't have it, add it
		if (iMouse == nMice)
			string nameStr
			insertPoints/M =0 nMice, 1, grpList, grpListSel
			sprintf nameStr, "%04d", mouseID
			grpList [nMice] [0] = nameStr
			grpList [nMice] [1] = grp
			grpListSel [nMice] [0] = 0
			grpListSel [nMice] [1] = 3
			nMice +=1
		endif
	endfor
end


Function AHF_OptionsCheckProc(cba) : CheckBoxControl
	STRUCT WMCheckboxAction &cba

	switch( cba.eventCode )
		case 2: // mouse up
			SVAR optionStr = root:packages:GUIP:Auto_Head_Fix:GUIPloadOptionStr
			string KeyStr = RemoveEnding(cba.ctrlName, "Check")
			if (cba.checked)
				optionStr = ReplaceStringByKey(KeyStr, optionStr, "yes" , "=", ";")
			else
				optionStr = ReplaceStringByKey(KeyStr, optionStr, "no" , "=", ";")
			endif
			break
		case -1: // control being killed
			break
	endswitch
	return 0
End


Function AHF_GrpListProc(lba) : ListBoxControl
	STRUCT WMListboxAction &lba
	
	variable iRow, nRows
	string alpha, digits, IDStr
	switch( lba.eventCode )
		case -1: // control being killed
			break
		case 1: // mouse down
			nRows =dimsize(lba.listWave,0)
			if ((lba.row == nRows) && ((lba.eventMod & 2)==2))
				if ((nRows > 1) || (cmpstr (lba.listWave [0] [0], "") != 0))
					insertPoints/M=0 nRows, 1, lba.listWave, lba.selWave
					lba.selWave = 3
				endif
			endif
			break
		case 3: // double click
			if (lba.row == -1)  // sort list by selected column
				nRows =dimsize(lba.listWave,0)
				make/T/free/n=(nRows) key
				make/free/n=(nRows) valindex
				key[] = lba.listWave[p][lba.col]
				valindex=p
				sort /a key,key,valindex
				make/t/free/n=((nRows), 2), toBeSorted
				toBeSorted[][] = lba.listWave[valindex[p]][q]
				lba.listWave = toBeSorted
			endif
			break
		case 4: // cell selection
			break
		case 5: // cell selection plus shift key
			if (dimsize(lba.listWave,0) > 1) 
				deletepoints/M=0 lba.row, 1, lba.listWave, lba.selWave
			endif
			break
		case 6: // begin edit
			break
		case 7: // finish edit - either a new mouse or changing grp of existing mouse
			// if adding a new mouse, validate number and check if it is already in the list
			if (((lba.row ==0) && (cmpstr (lba.listWave [0] [0], "") != 0)) && (cmpstr (lba.listWave [0] [1], "") != 0))
				variable newID = mod (str2num (lba.listWave [lba.row] [0]), 10000)
				if (numtype (newID) != 0)
					doalert 0, "The TagID needs to be a number."
					lba.listWave [0] [0] = ""
					return 0
				else
					nRows = dimsize(lba.listWave,0)
					for (iRow =1; iRow < nRows; iRow +=1)
						if (newID == str2num (lba.listWave [iRow] [0]))
							doAlert 0, "The TagID \"" + lba.listWave [iRow] [0] + "\" already exists in the list of mice, in group \"" + lba.listWave [iRow] [1]
							return 0
						endif 
					endfor
					sprintf IDStr, "%04d", newID
					lba.listWave [0] [0]= IDStr
					//grp needs to be letters, whether adding a new mouse or changing grp for existing mouse
					SplitString /E="([[:alpha:]]*)([[:digit:]]*)" lba.listWave [0] [1], alpha, digits
					if ((strlen (alpha) == 0) || (strlen (digits) > 0))
						lba.listWave [0] [1] = alpha
						doalert 0, "Group names must contain only letters"
					endif
					// Insert a new row, Saving position 0 for inserting new IDs
					insertpoints 0,1, lba.listWave, lba.selWave
					lba.listWave [0] = ""
					lba.selWave [0][*] = 3
					lba.selWave [1] [0]= 0
					lba.selWave [1] [1]= 3
				endif
			elseif ((lba.row > 0) && (lba.col == 1))
				//grp needs to be letters, whether adding a new mouse or changing grp for existing mouse
				SplitString /E="([[:alpha:]]*)([[:digit:]]*)" lba.listWave [lba.row] [1], alpha, digits
				if ((strlen (alpha) == 0) || (strlen (digits) > 0))
					lba.listWave [lba.row] [1] = alpha
					doalert 0, "Group names must contain only letters"
				endif
				// change names of existing waves
				string aWaveName, newWaveName, mouseWaves = GUIPListObjs ("root:AutoHeadFixData", 1, "*" + lba.listWave [lba.row] [0] + "_*", 0, "")
				variable iWave, nWaves = itemsInlist (mouseWaves, ";")
				for (iWave = 0; iWave < nWaves; iWave +=1)
					aWaveName = stringFromList (iWave, mouseWaves, ";")
					WAVE aWave = $"root:AutoHeadFixData:" + aWaveName
					SplitString /E="([[:alpha:]]*)([[:digit:]]*)" aWaveName, alpha, digits
					Rename aWave, $ReplaceString(alpha, aWaveName, lba.listWave [lba.row] [1], 0)
				endfor
				if (nWaves > 0)
					doalert 0 ,"Changed names of existing waves for this mouse in AutoHeadFixData to match new group."
				endif
			endif
//			if (lba.col ==0)
//			
//			// if adding a new mouse, validate number and check if it is already in the list
//			if (((lba.row ==0) && (cmpstr (lba.listWave [0] [0], "") != 0)) && (cmpstr (lba.listWave [0] [1], "") != 0))
//				variable newID = mod (str2num (lba.listWave [lba.row] [0]), 10000)
//				if (numtype (newID) != 0)
//					doalert 0, "The TagID needs to be a number."
//					lba.listWave [0] [0] = ""
//					return 0
//				else
//					nRows = dimsize(lba.listWave,0)
//					for (iRow =1; iRow < nRows; iRow +=1)
//						if (newID == str2num (lba.listWave [iRow] [0]))
//							doAlert 0, "The TagID \"" + lba.listWave [iRow] [0] + "\" already exists in the list of mice, in group \"" + lba.listWave [iRow] [1]
//							return 0
//						endif 
//					endfor
//					sprintf IDStr, "%04d", newID
//					lba.listWave [0] [0]= IDStr
//					//grp needs to be letters, whether adding a new mouse or changing grp for existing mouse
//					SplitString /E="([[:alpha:]]*)([[:digit:]]*)" lba.listWave [0] [1], alpha, digits
//					if ((strlen (alpha) == 0) || (strlen (digits) > 0))
//						lba.listWave [0] [1] = alpha
//						doalert 0, "Group names must contain only letters"
//					endif
//					// Insert a new row, Saving position 0 for inserting new IDs
//					insertpoints 0,1, lba.listWave, lba.selWave
//					lba.listWave [0] = ""
//					lba.selWave [0][*] = 3
//					lba.selWave [1] [0]= 0
//					lba.selWave [1] [1]= 3
//				endif
//			elseif ((lba.row > 0) && (lba.col == 1))
//				//grp needs to be letters, whether adding a new mouse or changing grp for existing mouse
//				SplitString /E="([[:alpha:]]*)([[:digit:]]*)" lba.listWave [lba.row] [1], alpha, digits
//				if ((strlen (alpha) == 0) || (strlen (digits) > 0))
//					lba.listWave [lba.row] [1] = alpha
//					doalert 0, "Group names must contain only letters"
//				endif
//				// change names of existing waves
//				string aWaveName, newWaveName, mouseWaves = GUIPListObjs ("root:AutoHeadFixData", 1, "*" + lba.listWave [lba.row] [0] + "_*", 0, "")
//				variable iWave, nWaves = itemsInlist (mouseWaves, ";")
//				for (iWave = 0; iWave < nWaves; iWave +=1)
//					aWaveName = stringFromList (iWave, mouseWaves, ";")
//					WAVE aWave = $"root:AutoHeadFixData:" + aWaveName
//					SplitString /E="([[:alpha:]]*)([[:digit:]]*)" aWaveName, alpha, digits
//					Rename aWave, $ReplaceString(alpha, aWaveName, lba.listWave [lba.row] [1], 0)
//				endfor
//				if (nWaves > 0)
//					doalert 0 ,"Changed names of existing waves for this mouse in AutoHeadFixData to match new group."
//				endif
//			endif
			break
		case 13: // checkbox clicked (Igor 6.2 or later)
			break
	endswitch
	return 0
End


// copies data for this sesh from temp waves to data waves
Function AHF_SeshEnd(seshStart, seshEnd, cageName, doOverWrite, existingMiceOnly)
	variable seshStart, seshEnd
	string cageName
	variable doOverWrite
	variable existingMiceOnly
	
	// reference text wave containing tagIDs and grp assignments
	WAVE/T grpWave = root:AutoHeadFixData:GrpList
	WAVE grpSelWave = root:packages:GUIP:Auto_Head_Fix:GrpListSel
	// and make sure it is sorted by mouseID
	if (DimSize (grpWave, 0) > 2)
		STRUCT WMListboxAction lba
		lba.eventCode = 3
		lba.row = -1
		lba.col = 0
		WAVE/T lba.listWave = grpWave
		AHF_GrpListProc(lba)
	endif
	// reference temp waves for mice and event numbers
	WAVE mice = root:packages:mice
	WAVE entries= root:packages:entries
	WAVE entryRewards = root:packages:entryRewards
	WAVE fixes = root:packages:fixes
	WAVE fixRewards = root:packages:fixRewards
	// number of seconds from epoch to start of day when this session started
	variable startDay =floor((seshStart - kSECSTODAYSTART)/ kSECSPERDAY) * kSECSPERDAY
	// number of seconds in this session
	// yes, we could have slightly more than 24 hr in a daily session, but in the end it will average out
	variable cageDuration = seshEnd - seshStart 
	// get data for each mouse in temp mice wave
	variable iMouse, mouseDayPos, nMice = numPnts (mice)
	variable aMouse, mousePos, grpPos
	string tempNameStr, dataNameStr, mouseIDstr, grp
	for (iMouse =0; iMouse < nMice; iMouse +=1)
		aMouse = mice [iMouse]
		// Reference temp data waves for this mouse
		tempNameStr = "root:packages:m" + num2str (aMouse)
		WAVE entryTimesTemp = $tempNameStr + "_entryTimes"
		WAVE entryDursTemp = $tempNameStr + "_entryDurs"
		WAVE wasEntryRewardTemp = $tempNameStr + "_WasEntryReward"
		WAVE headFixTimesTemp = $tempNameStr + "_HeadFixTimes"
		WAVE headFixDursTemp =$tempNameStr+ "_HeadFixDurs"
		WAVE headFixRewardsTemp= $tempNameStr + "_HeadFixRewards"
		// do we have a grp for this mouse? If not, use cageName as grp
		sprintf mouseIDstr, "%04d", aMouse
		grpPos = GUIPMathFindText2D (grpWave, mouseIDstr, 1, INF, 0, 0, 0)
		if (grpPos < 0)
			if (existingMiceOnly)
				continue
			else
				grp = CleanupName(cageName, 0) 
				grpPos = -(grpPos + 1) 
				insertpoints/M=0 grpPos, 1, grpWave,grpSelWave
				grpWave [grpPos] [0] = mouseIDstr
				grpWave [grpPos] [1] = cageName
				grpSelWave [grpPos] [0] = 0
				grpSelWave [grpPos] [1] = 3
			else
				grp = grpWave [grpPos] [1]
			endif
			if (cmpStr (grp, "test") ==0)
				continue
			endif
		else
			grp = grpWave [grpPos] [1]
		endif
		dataNameStr = "root:AutoHeadFixData:" + grp + mouseIDstr
		// Copy individual entry/exits/wasEntryReward into waves for this mouse
		variable nEntries = entries [iMouse]
		if (nEntries > 0)
			WAVE/Z EntryTimes = $dataNameStr +  "_EntrTime"
			if (!(WaveExists (EntryTimes)))
				Make/D/n = (nEntries) $dataNameStr + "_EntrTime"
				Make/n = (nEntries) $dataNameStr  + "_entryDurs"
				make/b/u/n=(nEntries)  $dataNameStr + "_WasEntryReward"
				WAVE EntryTimes = $dataNameStr +  "_EntrTime"
				WAVE entryDurs = $dataNameStr  + "_entryDurs"
				WAVE wasRewarded = $dataNameStr + "_WasEntryReward"
				EntryTimes = entryTimesTemp [p]
				entryDurs = entryDursTemp [p]
				wasRewarded = wasEntryRewardTemp [p]
			else
				WAVE entryDurs = $dataNameStr  + "_entryDurs"
				WAVE wasRewarded = $dataNameStr + "_WasEntryReward"
				variable entryPos =  GUIPMathFindNum (EntryTimes, entryTimesTemp [0], 0, INF, 0)
				if (entryPos < 0)
					entryPos = -(entryPos + 1) 
				endif
				insertpoints entryPos, (nEntries), EntryTimes, entryDurs//, wasRewarded
				EntryTimes [entryPos, entryPos + nEntries -1] = entryTimesTemp [p - entryPos]
				entryDurs [entryPos, entryPos + nEntries -1] = entryDursTemp [p - entryPos]
				//wasRewarded [entryPos, entryPos + nEntries -1] = wasEntryRewardTemp [p - entryPos]
			endif
			//				else // first entry was found in data
			//					
			//					if (doOverWrite)
			//						// find position of last entry from temp waves in existing data 
			//						variable entryEnd =  GUIPMathFindNum (EntryTimes, entryTimesTemp [nEntries -1], entryPos, INF, 0)
			//						if (entryEnd < 0)
			//							entryEnd = -(entryEnd + 1)
			//						endif
			//						DeletePoints entryPos, (entryEnd - entryPos), EntryTimes, entryDurs, wasRewarded
			//						insertpoints entryPos, (nEntries), EntryTimes, entryDurs, wasRewarded
			//						EntryTimes [entryPos, entryPos + nEntries -1] = entryTimesTemp [p - entryPos]
			//						entryDurs [entryPos, entryPos + nEntries -1] = entryDursTemp [p - entryPos]
			//						wasRewarded [entryPos, entryPos + nEntries -1] = wasEntryRewardTemp [p - entryPos]
			//					else
			//						doAlert 0, "Entries for that session were already loaded."
			//						continue
			//					endif
			//				endif
		endif
		// Copy individual headFixes/headfix rewards for this mouse
		variable nheadFixes= fixes [iMouse]
		if (nHeadFixes > 0)
			WAVE/Z headFixes = $dataNameStr +  "_HdFxTime"
			if (!(WaveExists (headFixes)))
				Make/D/n = (nheadFixes) $dataNameStr + "_HdFxTime"
				Make/n = (nheadFixes) $dataNameStr  + "_HdFxDurs"
				Make/n = (nheadFixes) $dataNameStr  + "_HdFxRews"
				WAVE headFixes = $dataNameStr +  "_HdFxTime"
				WAVE headFixDurs = $dataNameStr +  "_HdFxDurs"
				WAVE headFixRews=$dataNameStr  + "_HdFxRews"
				headFixes = headFixTimesTemp [p]
				headFixDurs = headFixDursTemp [p]
				headFixRews = headFixRewardsTemp [p]
			else
				WAVE headFixDurs = $dataNameStr +  "_HdFxDurs"
				WAVE headFixRews=$dataNameStr  + "_HdFxRews"
				variable hfPos =  GUIPMathFindNum (headFixes, headFixTimesTemp [0], 0, INF, 0)
				if (hfPos < 0)
					hfPos = -(hfPos + 1) 
					print "errm"
				//else
					
				endif
				insertpoints hfPos, (nheadFixes), headFixes, headFixDurs//, headFixRews
				headFixes [hfPos, hfPos + nheadFixes -1] = headFixTimesTemp [p-hfPos]
				headFixDurs [hfPos, hfPos + nheadFixes -1] = headFixDursTemp [p -hfPos]
				//headFixRews  [hfPos, hfPos + nheadFixes -1]  = headFixRewardsTemp  [p -hfPos]
				//				else
				//					variable hfEnd = GUIPMathFindNum (headFixes, headFixTimesTemp [nHeadFixes -1], hfPos, INF, 0)
				//					if (hfEnd < 0)
				//						hfEnd = -(hfEnd + 1)
				//					endif
				//					DeletePoints hfPos, (hfEnd - hfPos), headFixes, headFixDurs, headFixRews
				//					insertpoints hfPos, (nEntries), headFixes, headFixDurs, headFixRews
				//					headFixes [hfPos, hfPos + nheadFixes -1] = headFixTimesTemp [p - hfPos]
				//					headFixDurs  [hfPos, hfPos + nheadFixes -1] = headFixTimesTemp [p - hfPos]
				//					headFixRews  [hfPos, hfPos + nheadFixes -1] = headFixRewardsTemp [p - hfPos]
				//				endif
			endif
		endif
		// copy day and duration data into wave for this mouse
		WAVE/Z mouseDayWave = $dataNameStr + "_Date"
		if (!(WaveExists (mouseDayWave)))
			make/D/n = (1) $dataNameStr + "_Date"
			make/n = (1) $dataNameStr+ "_DayCageDur"
			make/n = (1) $dataNameStr + "_DayEntries"
			make/n = (1) $dataNameStr + "_DayEntRews"
			make/n = (1) $dataNameStr + "_DayHeadFixes"
			make/n = (1) $dataNameStr + "_DayHFixRewds"
			WAVE mouseDayWave = $dataNameStr + "_Date"
			WAVE mouseCageDurWave = $dataNameStr + "_DayCageDur"
			WAVE mouseDayEntries=$dataNameStr + "_DayEntries"
			WAVE mouseDayEntryRewards = $dataNameStr + "_DayEntRews"
			WAVE mouseDayHeadFixes = $dataNameStr + "_DayHeadFixes"
			WAVE mouseDayHeadFixRewards =  $dataNameStr + "_DayHFixRewds"
			mouseDayPos=0
			mouseCageDurWave [0] = 0
			mouseDayEntries [0] =0
			mouseDayEntryRewards [0] = 0
			mouseDayHeadFixes [0]=0
			mouseDayHeadFixRewards [0] =0
		else
			WAVE mouseCageDurWave = $dataNameStr + "_DayCageDur"
			WAVE mouseDayEntries=$dataNameStr + "_DayEntries"
			WAVE mouseDayEntryRewards = $dataNameStr + "_DayEntRews"
			WAVE mouseDayHeadFixes = $dataNameStr + "_DayHeadFixes"
			WAVE mouseDayHeadFixRewards =  $dataNameStr + "_DayHFixRewds"
			mouseDayPos = GUIPMathFindNum (mouseDayWave, startDay, 0, INF, 0)
			if (mouseDayPos < 0)
				mouseDayPos = -(mouseDayPos+1) 
				insertpoints mouseDayPos, 1, mouseDayWave, mouseCageDurWave, mouseDayEntries, mouseDayEntryRewards,mouseDayHeadFixes,mouseDayHeadFixRewards
			endif
		endif
		mouseDayWave[mouseDayPos]=startDay
		mouseCageDurWave [mouseDayPos] += cageDuration
		mouseDayEntries [mouseDayPos] += entries [iMouse]
		mouseDayEntryRewards [mouseDayPos] += entryRewards [iMouse]
		mouseDayHeadFixes [mouseDayPos]+=fixes [iMouse]
		mouseDayHeadFixRewards [mouseDayPos] += fixRewards [imouse]
	endfor
	entries[*]=0;entryRewards[*]=0; fixes[*]=0;fixRewards[*]=0
end



Function AHF_Load (ImportPathStr, FileNameStr, OptionsStr, FileDescStr)
	string ImportPathStr, FileNameStr, OptionsStr, FileDescStr
	
	variable overWrite = 0
	if (cmpStr (StringByKey("Overwrite", OptionsStr, "=", ";"), "yes") ==0)
		overwrite = 1
	endif
	variable loadMovie =0
	if (cmpStr (StringByKey("LoadMovies", OptionsStr, "=", ";"), "yes") ==0)
		loadMovie = 1
	endif
	variable existingMiceOnly =0
	if (cmpStr (StringByKey("existingMiceOnly", OptionsStr, "=", ";"), "yes") ==0)
		existingMiceOnly = 1
	endif
	variable fileRefNum
	// Set flag for number of files to 0, we will deal with the moving and renaming in this function
	// This will prevent GUIPDirectoryLoad from complaining about no waves loaded
	Variable/G :V_Flag = -1 
	String/G :S_waveNames = ""
	Open/R/P=$ImportPathStr/Z fileRefNum as FileNameStr
	if (V_flag != 0)
#ifdef kDEBUG
		printf "Error opening  Auto Head Fix text file for \"%s\".\r", FileNameStr
#endif
		return 1
	endif
	// cage name from file name is used only if group name is not already in the tag ID wave
	string cageName = StringFromList(1, fileNameStr, "_")
	if (CmpStr (cageName, "") ==0)
		cageName = "noName"
	else
		if (numtype(str2num (cageName [0])) ==0)
			cageName = "c" + cageName
		endif
		cageName = cleanUpName (cageName, 0)
	endif

	// make temp waves for mice names and numbers of events in packages folder
	make/o/n=0 root:packages:mice, root:packages:entries, root:packages:entryRewards
	make/o/n =0 root:packages:fixes, root:packages:fixRewards
	WAVE mice = root:packages:mice
	WAVE entries= root:packages:entries
	WAVE entryRewards = root:packages:entryRewards
	WAVE fixes = root:packages:fixes
	WAVE fixRewards = root:packages:fixRewards
	variable mousePos, nMice =0
	variable thisTime
	string thisEvent
	string aLine
	variable nData = 1000
	make/d/FREE/n = (nData) eventTime
	make/t/FREE/n=(nData) eventData
	make/i/u/FREE/n=(nData) eventMouse
	variable thisMouse =0
	string mouseNumStr
	// read data line at a time
	variable iData
	FReadLine/T="\n" fileRefNum, aLine
	aLine = removeending (removeending  (aLine, "\n"), "\r")
	for (iData =0; strlen (aLine) > 1; )
		if (!((CmpStr (StringFromList(2, aLine, "\t"), "SeshStart") ==0) || (CmpStr (StringFromList(2, aLine, "\t"), "SeshEnd") ==0)))
			eventMouse [iData] =  mod (str2num (StringFromList(0, aLIne, "\t")), 10000)
			if (eventMouse [iData] == 0)
				eventMouse [iData] = thisMouse
			else
				thisMouse = eventMouse [iData]
			endif
			eventTime [iData] = str2Num (StringFromList(1, aLIne, "\t")) + kUNIXEPOCHGMOFFSET
			eventData [iData] = StringFromList(2, aLine, "\t")
			iData +=1
			if (iData == nData)
				insertPoints nData, nData, eventTime, eventData, eventMouse
				nData *=2
			endif
		endif
		FReadLine/T="\n" fileRefNum, aLine
		aLine = removeending (removeending  (aLine, "\n"), "\r")
	endfor
	nData = iData
	redimension/n = (nData) eventTime, eventData, eventMouse
	// sort data by mouse and by time then copy into existing waves for each mouse
	sort {eventMouse, eventTime} eventTime, eventData, eventMouse
	WAVE/T GrpList = root:AutoHeadFixData:GrpList
	WAVE GrpListSel = root:packages:GUIP:Auto_Head_Fix:GrpListSel
	variable im, nm = dimsize (GrpList, 0), hasMouse
	variable firstPos, lastPos, aMouse
	variable insertStart, insertEnd, dataPts, insertPnts
	
	for (firstPos =0;firstPos < nData; firstPos = lastPos + 1)
		// get mouse name and find end of data for this mouse
		aMouse = eventMouse [firstPos]
		lastPos = GUIPMathFindNum (eventMouse, eventMouse [firstPos], firstPos, nData, 1)
		// Do we want to even bother with this mouse? or Add to existing Mice?
		sprintf mouseNumStr "%04d", aMouse
		//mouseNumStr = num2str (aMouse)
		for (im =0, hasMouse = -1; im < nm; im +=1)
			if (cmpstr (mouseNumStr, GrpList [im] [0]) ==0)
				hasMouse = im
				break
			endif
		endfor
		if (existingMiceOnly)
			if ((hasMouse == -1) || (cmpStr (GrpList [hasMouse] [1], "") == 0))
				continue
			endif
		else // perhaps add mouse to list
			if (hasMouse == -1)
				InsertPoints /M=0 0, 1, GrpList, GrpListSel
				GrpList [0] [0] = mouseNumStr
				GrpList [0] [1] = cageName
				GrpListSel [0,1] [1] = 3 
			endif
		endif
		// reference waves for this mouse
		sprintf mouseNumStr "%04d", aMouse
		WAVE/D/Z timeWave = $"root:AutoHeadFixData:m" + mouseNumStr + "_time"
		WAVE/T/Z eventWave = $"root:AutoHeadFixData:m" + mouseNumStr + "_event"
		if (!((WaveExists (timeWave)) && waveExists (eventWave)))
			duplicate/o/r= [firstPos, lastPos] eventTime $"root:AutoHeadFixData:m" + mouseNumStr + "_time"
			duplicate/o/r= [firstPos, lastPos] eventData $"root:AutoHeadFixData:m" + mouseNumStr + "_event"
			WAVE/D/Z timeWave = $"root:AutoHeadFixData:m" + mouseNumStr + "_time"
			setscale d 0,0, "dat" timeWave
			WAVE/T/Z eventWave = $"root:AutoHeadFixData:m" + mouseNumStr + "_event"
			Note timeWave,"grp=" + cageName + "\r" 
			Note eventWave,"grp=" + cageName + "\r"
		else
			dataPts = numpnts (timeWave)
			insertStart = GUIPMathFindNum (timeWave, eventTime [firstPos], 0, dataPts, 0)
			if (insertStart < 0)
				insertStart *= -1;insertStart -=1
			endif
			insertEnd=GUIPMathFindNum (timeWave, eventTime [lastPos], 0, dataPts, 0)
			if (insertEnd < 0)
				insertEnd *= -1;insertEnd -=1
			endif
			if (insertStart != insertEnd) // data has been inserted before, so overwriting
				if (overWrite == 0)
					printf "Data for file %s was already loaded and will NOT be overwritten.\r", fileNameStr
					continue
				endif
				DeletePoints insertStart, (insertEnd-InsertStart + 1), timeWave , eventWave
			endif
			insertPnts =(lastPos - firstPos +1)
			InsertPoints insertStart, insertPnts, timeWave, eventWave
			timeWave [insertStart, insertStart + insertPnts-1] = eventTime [p - insertStart + firstPos]
			eventWave [insertStart, insertStart + insertPnts-1] = eventData [p - insertStart + firstPos]
		endif
		
	endfor
end


// moivie size = 256 x 256, variable number of frames, r,g,b
STATIC CONSTANT kMOVIEX = 256
STATIC CONSTANT kMOVIEY = 256
STATIC CONSTANT kMOVIEFRAMESIZE = 65536

function AHF_LoadMovie(ImportPathStr, thisTime)
	string ImportPathStr
	variable thisTime
	
	pathinfo $ImportPathStr
	print S_Path
	string mPath = ReplaceString("textFiles", S_Path, "Videos")
	NewPath  /O videoPath, mPath
	string nameMatchStr = "*" + num2istr (floor (thisTime)) + "*"
	print nameMatchStr
	string mfile = stringfromlist (0, GUIPListFiles ("videoPath",  ".raw", nameMatchStr, 0, ""), ";")
	variable mref
	Open/R/P=videoPath/Z mref as mfile
	if (V_flag != 0)
#ifdef kDEBUG 
		printf "Error opening  Auto Head Fix movie file for \"%s\".\r", mPath
#endif
		return 1
	endif
	string mWaveName = RemoveEnding (StringFromList(ItemsInList(mPath, ":")-1, mPath, ":"), ".raw")
	FStatus mref 
	make/o/b/u/n = (V_logEOF)  root:testMovie
	WAVE testMovie = root:testMovie
	FBinRead  mref, testMovie
	variable iFrame, nFrames  = V_logEOF/(3 * kMOVIEFRAMESIZE)
	testMovie [0, V_logEOF/3 -1] = testMovie [1 + p * 3]
	redimension/n = (kMOVIEX,kMOVIEY, nFrames)testMovie
end


// makes better daily tally of entries and headfixes
function AHF_dailyHist (theGrp, isClipped)
	string theGrp
	variable isClipped
		
	WAVE/T grpList = root:AutoheadFixData:grpList
	string grpMice = ""
	variable iMouse, nMice = dimsize (grpList, 0)
	for (iMouse =1; iMouse < nMice; iMouse+=1)
		if (cmpstr (theGrp, grplist [iMouse] [1]) ==0)
			grpMice += grplist [iMouse] [1] +  grplist [iMouse] [0] + ";"
		endif
	endfor
	nMice= itemsinlist (grpMice, ";")
	// find first and last time looking at entries for all the mice
	variable startTime =INF, endTime = -INF
	string aMouse
	for (iMouse =0; iMouse < nMice; iMouse+=1)
		aMouse = stringFromList (iMouse, grpMice, ";")
		WAVE/Z entryWave = $"root:AutoheadFixData:"  + aMouse + "_entrTime"
		if (WaveExists (entryWave))
			startTime = Min (startTime, entryWave [0])
			endTime = max (endTime,  entryWave [numpnts (entryWave)-1])
		else
			grpMice = RemoveFromList(aMouse,grpMice, ";")
			nMice -=1
			iMouse -=1
		endif
	endfor
	
	string  pathStr = "root:AutoheadFixData:" 
	if (isClipped)
		pathStr =  "root:HeadFixesClipped:"
	endif
	// start bins at 7 AM, to synch to  dark/light schedule
	startTime =((floor (startTime / kSecsPerDay)) * kSecsPerDay) + kSECSTODAYSTART
	endTime =((ceil (endTime / kSecsPerDay)) * kSecsPerDay) + kSECSTODAYSTART
	variable iDay, nDays = (endTime - startTime)/kSECSPERDAY
	for (iMouse =0; iMouse < nMice; iMouse +=1)
		aMouse = stringFromList (iMouse, grpMice, ";")
		make/o/n = (nDays) $aMouse + "_entriesCalc", $aMouse + "_fixesCalc"
		WAVE entries = $aMouse + "_entriesCalc"
		WAVE fixes = $aMouse + "_fixesCalc"
		fixes = NaN
		entries = nan
		SetScale/p x startTime,  kSECSPERDAY, "dat" , entries, fixes
		//SetScale/p x 0,  1, "day" , entries, fixes
	endfor
	variable iTime, startP, endP=0, nPnts
	string notTodayList
	variable , iNotToday, nNotToday, iNotTodayVal
	variable grpWasTested
	for (iDay =0, iTime = startTime; iDay < nDays; iDay +=1, iTime += kSECSPERDAY)
		for (iMouse =0; iMouse < nMice; iMouse +=1)
			aMouse = stringFromList (iMouse, grpMice, ";")
			WAVE entryWave = $pathStr +  aMouse + "_entrTime"
			WAVE perDay =  $aMouse + "_entriesCalc"
			nPnts = numPnts (entryWave)
			startP = GUIPMathFindNum (entryWave, iTime, 0, nPnts-1, 0)
			if (startP < 0)
				startP = -(startP + 1) // startP is the first point for the day, unless 0 or nPnts, in which case check
			endif
			if (((startP == 0) && (entryWave [0] < iTime)) || (startP == nPnts))// start of day is outside data range of this animals 
				perDay [iDay]  =0
			else
				endP = GUIPMathFindNum (entryWave, iTime + kSecsPerDay, startP,nPnts -1, 0)  // endP is first point in next day
				if (endP < 0)
					endP = -(endP + 2) 
				endif
				perDay [iDay] = endP - startP + 1
			endif
			
			WAVE HeadFixWave = $pathStr+  aMouse +"_HdFxTime"
			WAVE perDay =  $aMouse +"_fixesCalc"
			nPnts = numPnts (HeadFixWave)
			startP =GUIPMathFindNum (HeadFixWave, iTime, 0, nPnts-1, 0)
			if (startP < 0)
				startP = -(startP + 1)
			endif
			if (((startP == 0) && (HeadFixWave [0] < iTime)) || (startP == nPnts))// start of day is outside data range of this animals 
				perDay [iDay] = 0
			else
				endP = GUIPMathFindNum (HeadFixWave, iTime + kSecsPerDay, startP,nPnts -1, 0)  // endP is first point in next day
				if (endP < 0)
					endP = -(endP + 2) 
				endif
				perDay [iDay] = endP - startP + 1
			endif
			//perDay [iDay] = endP - startP
		endfor

	endfor
end	



//We need all the times beteeen headfixes for [115,377,159,245,300,592,573,090,139,202,238]
//Between the dates
//2015-06-25 and 2015-08-16

STATIC CONSTANT kIFIBINSIZE = 33
STATIC CONSTANT kIFInBINS = 20

function headFix_IFI (themouse, startTime, endTime)
	string themouse
	variable startTime, endTime
	
	make/o/n = (kIFInBINS) $theMouse + "_IFIHist"
	WAVE ifiHist = $theMouse + "_IFIHist"
	setscale/p x 0, (kIFIBINSIZE), "s", ifiHist
	ifiHist = 0
	
	WAVE hfxWave = $"root:HeadFixesClipped:" +theMouse + "_HdFxTime"
	variable iPt, nPts = numpnts (hfxWave)
	variable startPt, endPt
	startPt = abs ( GUIPMathFindNum (hfxWave, startTime, 0,nPts, 0))
	endPt =  abs ( GUIPMathFindNum (hfxWave, endTime, 0,nPts, 0))
	for (iPt =startPt; iPt < endPt; iPt +=1)
		ifiHist [x2pnt(ifiHist, (hfxWave [iPt] - hfxWave [iPt-1]) )] += 1
		//ifiHist (hfxWave [iPt] - hfxWave [iPt-1]) += 1
	endfor
	appendtograph ifiHist
end


Function HeadFixHist (theMouse, startTime, endTime, binSize)
	string theMouse
	variable startTime
	variable endTime
	variable binSize
	
	variable nBins = ceil (( endTime -startTime)/binSize)
	make/o/n = (nBins)  $theMouse + "_HeadFixHist"
	WAVE theHist =  $theMouse + "_HeadFixHist"
	SetScale/p x (startTime), binSize, "dat", theHist
	theHist =0
	display theHist
	
	WAVE hfxWave = $"root:HeadFixesClipped:" +theMouse + "_HdFxTime"
	variable nPts = numpnts (hfxWave)
	variable startPt, endPt, iTime
	
	
	variable iBin
	for (iBin =0, iTime = startTime; iBin < nBins; iBin +=1, iTime += binSize)
		startPt = abs (GUIPMathFindNum (hfxWave, iTime, 0, Inf, 0)) -1
		endPt = abs (GUIPMathFindNum (hfxWave, iTime + binSize, startPt, INF, 0))
		theHist [iBin] = endPt - startPt
	endfor
end


Function EntryHist (theMouse, startTime, endTime, binSize)
	string theMouse
	variable startTime
	variable endTime
	variable binSize
	
	variable nBins = ceil (( endTime -startTime)/binSize)
	make/o/n = (nBins)  $theMouse + "_EntryHist"
	WAVE theHist =  $theMouse + "_EntryHist"
	SetScale/p x (startTime), binSize, "dat", theHist
	theHist =0
	
	WAVE hfxWave = $"root:HeadFixesClipped:" +theMouse + "_EntrTime"
	variable nPts = numpnts (hfxWave)
	variable startPt, endPt, iTime
	
	//appendtograph theHist
	variable iBin
	for (iBin =0, iTime = startTime; iBin < nBins; iBin +=1, iTime += binSize)
		startPt = abs (GUIPMathFindNum (hfxWave, iTime, 0, Inf, 0)) -1
		endPt = abs (GUIPMathFindNum (hfxWave, iTime + binSize, startPt, INF, 0))
		theHist [iBin] = endPt - startPt
	endfor
end



//STRCONSTANT kMiceList = "m2016080026;m201608298;m201608315;m201608466;m201608468;m201608481;m201609114;m201609124;m201609136;m201609336;m5855691;"
STRCONSTANT kPerformMiceList = "m2016080026;m201608298;m201608466;m201608468;m201608481;m201609336;m201609136"
STRCONSTANT kMiceList = "m0026;m8298;m8466;m8468;m8481;m9336;m9136;"

// histogram of licks from start of buzz
CONSTANT kMinus = 2.0
CONSTANT kPlus = 2.0 
CONSTANT kBinSize = 0.1
function periBuzzHist (string mouse, string dateStr)
	
	WAVE/T eventWave = $"root:AutoHeadFixData:" + mouse + "_" + dateStr + "_event"
	WAVE timeWave = $"root:AutoHeadFixData:" + mouse + "_" + dateStr + "_time"
	variable iPnt, nPnts = numpnts (timeWave)
	make/o/n= ((kPlus + kMinus)/kBinSize) $mouse + "_" + dateStr + "_pbHist"
	WAVE histWave = $mouse + "_" + dateStr + "_pbHist"
	setscale/p x -kMinus, kBinSize, "s", histWave
	histWave =0
	display histWave
	ModifyGraph mode=5, hbFill=4
		variable startPnt, endPnt, histStartPnt, histEndPnt, histPnt
	variable startTime, endTime, buzzTime, histStartTime, histEndTime, histTime
	string event
	variable nBuzzes = 0
	for (iPnt =0; iPnt < nPnts; iPnt += 1)
		// look for check+ for start of trial
		for (; (iPnt < nPnts) && cmpStr (eventWave [iPnt], "check+") != 0; iPnt += 1)
		endfor
		startPnt = iPnt
		startTime = timeWave [iPnt]
		// look for next complete, exit, or SeshEnd
		for (; (iPnt < nPnts) && (!((cmpStr (eventWave [iPnt], "complete") == 0) || (cmpStr (eventWave [iPnt], "exit") == 0) || (cmpStr (eventWave [iPnt], "SeshEnd") == 0))); iPnt +=1)
		endfor
		endPnt = iPnt
		endTime = timeWave [iPnt]
		// look for buzzes within this trial
		for (iPnt = startPnt; iPnt < endPnt; iPnt +=1)
			if (cmpStr (StringFromList(0, eventWave [iPnt], ":"), "Buzz") == 0) // add buzz times to histogram
				nBuzzes +=1
				buzzTime = timeWave [iPnt]
				histStartTime = Max (timeWave [iPnt] - kMinus, startTime)
				histEndTime = Min (timeWave [iPnt] + kPlus, endTime)
				histStartPnt =  GUIPMathFindNum (timeWave, histStartTime, startPnt, endPnt, 0)
				if (histStartPnt < 0)
					histStartPnt = -histStartPnt -1
				endif
				histEndPnt =  GUIPMathFindNum (timeWave, histEndTime, startPnt, endPnt, 0)
				if (histEndPnt < 0)
					histEndPnt = -histEndPnt - 1
				endif
				for (histPnt = histStartPnt; histPnt < histEndPnt; histPnt +=1)
					if (cmpstr (StringFromList (0, eventWave [histPnt], ":"), "lick") ==0)
						histWave [x2pnt(histWave, timeWave [histPnt] - buzzTime)] += 1
					endif
				endfor
			endif
		endfor
	endfor
	histWave /= (nBuzzes * kBinSize)
	string labelStr = "\\Z14" + mouse + "\r" + dateStr + "\r" + num2str (nBuzzes) + " buzzes"
	TextBox/C/N=text0/F=0/A=MT labelStr
	label left "Licks/Second"
	label bottom  "Time relative to buzz start (\\U)"
end


function periBuzzHist_Disc_BUP (string mouse, string dateStr)
	
	WAVE/T eventWave = $"root:AutoHeadFixData:" + mouse + "_" + dateStr + "_event"
	WAVE timeWave = $"root:AutoHeadFixData:" + mouse + "_" + dateStr + "_time"
	variable iPnt, nPnts = numpnts (timeWave)
	make/o/n= ((kPlus + kMinus)/kBinSize) $mouse + "_" + dateStr + "_pbHist_RC", $mouse + "_" + dateStr + "_pbHist_RI"
	make/o/n= ((kPlus + kMinus)/kBinSize) $mouse + "_" + dateStr + "_pbHist_NC", $mouse + "_" + dateStr + "_pbHist_NI"
	WAVE histWaveRC = $mouse + "_" + dateStr + "_pbHist_RC"
	WAVE histWaveRI = $mouse + "_" + dateStr + "_pbHist_RI"
	WAVE histWaveNC = $mouse + "_" + dateStr + "_pbHist_NC"
	WAVE histWaveNI = $mouse + "_" + dateStr + "_pbHist_NI"
	setscale/p x -kMinus, kBinSize, "s", histWaveRC, histWaveRI, histWaveNC, histWaveNI
	histWaveRC =0;histWaveRI =0; histWaveNC =0; histWaveNI =0
	variable startPnt, endPnt, histStartPnt, histEndPnt, histPnt
	variable startTime, endTime, buzzTime, histStartTime, histEndTime, histTime
	string event
	variable goCode
	variable nBuzzesRC = 0, nBuzzesRI =0, nBuzzesNC =0, nBuzzesNI =0
	for (iPnt =0; iPnt < nPnts; iPnt += 1)
		// look for check+ for start of trial
		for (; (iPnt < nPnts) && cmpStr (eventWave [iPnt], "check+") != 0; iPnt += 1)
		endfor
		startPnt = iPnt
		startTime = timeWave [iPnt]
		// look for next complete, exit, or SeshEnd
		for (; (iPnt < nPnts) && (!((cmpStr (eventWave [iPnt], "complete") == 0) || (cmpStr (eventWave [iPnt], "exit") == 0) || (cmpStr (eventWave [iPnt], "SeshEnd") == 0))); iPnt +=1)
		endfor
		endPnt = iPnt
		endTime = timeWave [iPnt]
		// look for buzzes within this trial
		for (iPnt = startPnt; iPnt < endPnt; iPnt +=1)
			if (cmpStr (StringFromList(0, eventWave [iPnt], ":"), "Buzz") == 0) // add buzz times to histogram for trial type
				goCode = NumberByKey("GO", StringFromList(1, eventWave [iPnt], ":"), "=", ",")
				switch (goCode)
					case 2:
						WAVE histWave = histWaveRC
						nBuzzesRC +=1
						break
					case -2:
						WAVE histWave = histWaveRI
						nBuzzesRI +=1
						break
					case 1:
						WAVE histWave = histWaveNC
						nBuzzesNC +=1
						break
					case -1:
						WAVE histWave = histWaveNI
						nBuzzesNI +=1
						break
					default:
						print "Bad data at point " + num2istr (iPnt)
				endSwitch
				buzzTime = timeWave [iPnt]
				histStartTime = Max (timeWave [iPnt] - kMinus, startTime)
				histEndTime = Min (timeWave [iPnt] + kPlus, endTime)
				histStartPnt =  GUIPMathFindNum (timeWave, histStartTime, startPnt, endPnt, 0)
				if (histStartPnt < 0)
					histStartPnt = -histStartPnt -1
				endif
				histEndPnt =  GUIPMathFindNum (timeWave, histEndTime, startPnt, endPnt, 0)
				if (histEndPnt < 0)
					histEndPnt = -histEndPnt - 1
				endif
				for (histPnt = histStartPnt; histPnt < histEndPnt; histPnt +=1)
					if (cmpstr (StringFromList (0, eventWave [histPnt], ":"), "lick") ==0)
						histWave [x2pnt(histWave, timeWave [histPnt] - buzzTime)] += 1
					endif
				endfor
			endif
		endfor
	endfor
	
	histWaveRC /= (nBuzzesRC* kBinSize)
	histWaveRI /= (nBuzzesRI* kBinSize)
	histWaveNC /= (nBuzzesNC* kBinSize)
	histWaveNI /= (nBuzzesNI* kBinSize)
	
	display histWaveRC, histWaveRI, histWaveNC, histWaveNI
	string labelStr = "\\Z14" + mouse + "\r" + dateStr + "\rRC=" + num2str (nBuzzesRC) + ", RI=" + num2str (nBuzzesRI) + ", NC=" + num2str (nBuzzesNC) + ", NI=" + num2str (nBuzzesNI)
	TextBox/C/N=text0/F=0/A=MT labelStr
		label left "Licks/Second"
	label bottom  "Time relative to buzz start (\\U)"
end
	


function periBuzzHist_Disc_ALL(string grp, string startDateTime, string endDateTime)
	
	string miceList = GUIPListObjs ("root:AutoHeadFixData:", 1, "*_event", 0, ""), aMouse
	variable iMouse, nMice = itemsinlist (miceList, ";")
	for (iMouse =0;iMouse < nMice;iMouse +=1)
		aMouse = stringfromlist (iMouse, micelist, ";")
		WAVE aWave = $"root:AutoHeadFixData:" + aMouse
		if (cmpstr (StringByKey("grp", note (aWave) , "=" , "\r"), grp) == 0)
			periBuzzHist_Disc (removeending (aMouse, "_event"), startDateTime, endDateTime)
		endif
	endfor
end

function periBuzzHist_ALL(string dateStr)
	
	variable iMouse, nMice = itemsinlist (kMiceList, ";")
	for (iMouse =0;iMouse < nMice;iMouse +=1)
		periBuzzHist (stringfromlist (iMouse, kMiceList, ";"), dateStr)
	endfor
end


// startStr and endStr in date/tme format : "2017-06-30 13:40:44.11"
// makes histogram of numbers of entries and headfixes
function AHF_EntryFixHists (theGrp, startStr, endStr, binSize)
	string theGrp,startStr, endStr 
	variable binSize
	
	string dateStr =  stringfromlist (0, startStr, " ")
	string timeStr = stringfromlist (1, startStr, " ")
	variable timeEls = itemsinlist (timeStr, ":")
	variable startTIme = date2secs (str2num (stringfromlist (0, dateStr, "-")), str2num (stringfromlist (1, dateStr, "-")), str2num (stringfromlist (2, dateStr, "-")))
	if (timeEls > 0)
		startTime += str2num (stringfromlist (0, timeStr, ":")) * 3600
		if (timeEls > 1)
			startTime += str2num (stringfromlist (1, timeStr, ":")) * 60
			if (timeEls > 2)
				startTime += str2num (stringfromlist (2, timeStr, ":"))
			endif
		endif
	endif
	// now end time
	dateStr =  stringfromlist (0, endStr, " ")
	timeStr = stringfromlist (1, endStr, " ")
	timeEls = itemsinlist (timeStr, ":")
	variable endTime = date2secs (str2num (stringfromlist (0, dateStr, "-")), str2num (stringfromlist (1, dateStr, "-")), str2num (stringfromlist (2, dateStr, "-")))
	if (timeEls > 0)
		endTime += str2num (stringfromlist (0, timeStr, ":")) * 3600
		if (timeEls > 1)
			endTime += str2num (stringfromlist (1, timeStr, ":")) * 60
			if (timeEls > 2)
				endTime += str2num (stringfromlist (2, timeStr, ":"))
			endif
		endif
	endif
	variable nBins = floor ((endTime - startTime)/binSize)
	
	//string grpList = GUIPListWavesByNoteKey ("root:AutoHeadFixData", "grp", theGrp,  0, "",keySepStr="=", listSepStr="\r")
//	variable iWave, nWaves = itemsinlist (grpList, ";")
//	for (iWave =0;iWave < nWaves;iWave +=1)
//		aWaveName = StringFromList(iWave, grpList)
//		if (cmpStr (stringFromlist (1, aWaveName, "_"), "time") ==0)
//			miceList += stringFromlist (0, aWaveName, "_") + ";"
//		endif
//	endfor
//	string miceList = "", aWaveName
//variable iMouse, nMice= itemsinList (miceList)
	
	WAVE/T grpList = root:AutoHeadFixData:GrpList
	variable iMouse, nMice = dimsize (grpList, 0)	
	variable iPnt, endPnt, nPnts, iBin
	variable entryStart, fixStart, isEntered, isFixed
	string anEvent, mouseName
	for (iMouse =0; iMouse < nMice; iMouse +=1)
		//mouseName = stringfromlist (iMouse, miceList) 
		mouseName = "m" + grpList [iMouse] [0]
		WAVE timeWave = $"root:AutoHeadFixData:" + mouseName + "_time"
		WAVE/T eventWave = $"root:AutoHeadFIxData:" + mouseName + "_event"
		make/o/n = (nBins) $mouseName + "_entries", $mouseName + "_fixes", $mouseName + "_entryDur",  $mouseName + "_fixDur"
		WAVE entryHist = $mouseName + "_entries"
		WAVE fixHist = $mouseName + "_fixes"
		WAVE entryDurs = $mouseName + "_entryDur"
		WAVE fixDurs = $mouseName + "_fixDur"
		setscale/p x startTime, binSize, "dat", entryHist, fixHist, entryDurs, fixDurs
		setscale d 0,0, "s", entryDurs, fixDurs
		entryHist = 0;fixHist=0;entryDurs=0;fixDurs=0
		// find start and end pnts
		nPnts = numPnts (timeWave)
		iPnt = GUIPMathFindNum(timeWave, startTime, 0, nPnts, 0)
		if (iPnt < 0)
			iPnt *=-1; iPnt -=1
		endif
		endPnt = GUIPMathFindNum(timeWave, endTime, iPnt, nPnts, 0)
		if (endPnt < 0)
			endPnt *=-1; endPnt -=1
		endif
		// iterate through data points assigning to corrct bin
		for (iBin =0, entryStart=0, fixStart=0, isEntered=0, isFixed=0;iPnt < endPnt; iPnt +=1)
			anEvent = eventWave [iPnt]
			strSwitch (anEvent)
				case "entry":
					if (isEntered)
						printf "Error for %s: entered twice without exiting at point %d.\r", mouseName, iPnt
						isEntered =0
					else
						isEntered=1
						entryStart = timeWave [iPnt]
					endif
					break
				case "exit":
					if (isEntered==0)
						printf "Error for %s: exited before entering at point %d.\r", mouseName, iPnt
						isEntered =0
					else
						iBin = floor((timeWave [iPnt] - startTime)/binSize)
						entryDurs [iBin] += (timeWave [iPnt] - entryStart)
						entryHist [iBin] +=1
						isEntered=0
					endif
					break
				case "check No Fix Trial":
					isFixed = 2
					break
				case "check+":
					if (isFixed ==1)
						printf "Error for %s: fixed twice without completion at point %d.\r", mouseName, iPnt
						isFixed =0
						break
					else
						isFixed=1
						fixStart = timeWave [iPnt]
					endif
					break
				case "complete":
					if (isFixed ==0)
						printf "Error for %s: Completed head fix trial twice without starting at point %d.\r", mouseName, iPnt
					elseif (isFixed ==1)
						iBin = floor((timeWave [iPnt] - startTime)/binSize)
						fixDurs [iBin] += (timeWave [iPnt] - fixStart)
						fixHist [iBin] +=1
					endif
					isFixed=0
					break
			endSwitch
		endfor
	endfor
	// now make some plots
	display /N=$theGrp + "_EntryHist" as theGrp + "_Number of Entries per " + num2str (binSize/3600) + " hrs"
	string entryHistName = S_name
	display /N=$theGrp + "_EntryDurations" as theGrp + "_Total Time in Chamber per " + num2str (binSize/3600) + " hrs"
	string entryDurName = S_name
	display /N=$theGrp + "_headFixHist" as theGrp + "_Number of Head Fixes per " + num2str (binSize/3600) + " hrs"
	string headFixHistName = S_name
	display /N=$theGrp + "_headFixDurations" as theGrp + "_Total Time headFixed per " + num2str (binSize/3600) + " hrs"
	string headFixDurName = S_name
	
	variable rVal, gVal, bVal
	
	for (iMouse =0; iMouse < nMice; iMouse +=1)
		//mouseName = stringfromlist (iMouse, miceList)
		mouseName = "m" + grpList [iMouse] [0]
		GUIPcolorRamp ("rainbow256", iMouse, nMice, rVal, gVal, bVal)
		WAVE entryHist = $mouseName + "_entries"
		WAVE fixHist = $mouseName + "_fixes"
		WAVE entryDurs = $mouseName + "_entryDur"
		WAVE fixDurs = $mouseName + "_fixDur"
		appendtograph/w=$entryHistName /c=(rval, gval, bval) entryHist
		appendtograph/w=$entryDurName /c=(rval, gval, bval) entryDurs
		appendtograph/w=$headFixHistName /c=(rval, gval, bval) fixHist
		appendtograph/w=$headFixDurName /c=(rval, gval, bval) fixDurs
	endfor
	ModifyGraph/w=$entryHistName mode=5,toMode=3, hbFill=5
	ModifyGraph/w=$entryDurName mode=5,toMode=3, hbFill=5
	ModifyGraph/w=$headFixHistName mode=5,toMode=3, hbFill=5
	ModifyGraph/w=$headFixDurName mode=5,toMode=3, hbFill=5
end


function periBuzzHist_Disc (string mouse, string startStr, string endStr)
	
	WAVE/T eventWave = $"root:AutoHeadFixData:" + mouse + "_event"
	WAVE timeWave = $"root:AutoHeadFixData:" + mouse + "_time"
	
	string dateStr =  stringfromlist (0, startStr, " ")
	string timeStr = stringfromlist (1, startStr, " ")
	variable timeEls = itemsinlist (timeStr, ":")
	variable startTIme = date2secs (str2num (stringfromlist (0, dateStr, "-")), str2num (stringfromlist (1, dateStr, "-")), str2num (stringfromlist (2, dateStr, "-")))
	if (timeEls > 0)
		startTime += str2num (stringfromlist (0, timeStr, ":")) * 3600
		if (timeEls > 1)
			startTime += str2num (stringfromlist (1, timeStr, ":")) * 60
			if (timeEls > 2)
				startTime += str2num (stringfromlist (2, timeStr, ":"))
			endif
		endif
	endif
	// now end time
	dateStr =  stringfromlist (0, endStr, " ")
	timeStr = stringfromlist (1, endStr, " ")
	timeEls = itemsinlist (timeStr, ":")
	variable endTime = date2secs (str2num (stringfromlist (0, dateStr, "-")), str2num (stringfromlist (1, dateStr, "-")), str2num (stringfromlist (2, dateStr, "-")))
	if (timeEls > 0)
		endTime += str2num (stringfromlist (0, timeStr, ":")) * 3600
		if (timeEls > 1)
			endTime += str2num (stringfromlist (1, timeStr, ":")) * 60
			if (timeEls > 2)
				endTime += str2num (stringfromlist (2, timeStr, ":"))
			endif
		endif
	endif
	// find start and end pnts
	variable startPntG, endPntG, nPnts = numPnts (timeWave)
	startPntG = GUIPMathFindNum(timeWave, startTime, 0, nPnts, 0)
	if (startPntG < 0)
		startPntG *=-1; startPntG -=1
	endif
	endPntG = GUIPMathFindNum(timeWave, endTime, startPntG, nPnts, 0)
	if (endPntG < 0)
		endPntG *=-1; endPntG -=1
	endif
	//Make output waves
	make/o/n= ((kPlus + kMinus)/kBinSize) $mouse + "_pbHist_RC", $mouse + "_pbHist_RI"
	make/o/n= ((kPlus + kMinus)/kBinSize) $mouse   + "_pbHist_NC", $mouse   + "_pbHist_NI"
	make/o/n= ((kPlus + kMinus)/kBinSize) $mouse   + "_pbHist_GO"
	WAVE histWaveRC = $mouse + "_pbHist_RC"
	WAVE histWaveRI = $mouse + "_pbHist_RI"
	WAVE histWaveNC = $mouse +  "_pbHist_NC"
	WAVE histWaveNI = $mouse +  "_pbHist_NI"
	WAVE histWaveGO = $mouse   + "_pbHist_GO"
	setscale/p x -kMinus, kBinSize, "s", histWaveRC, histWaveRI, histWaveNC, histWaveNI, histWaveGO
	histWaveRC = 0;histWaveRI =0; histWaveNC =0; histWaveNI =0
	histWaveGO = 0
	
	variable iPnt, startPnt, endPnt, histStartPnt, histEndPnt, histPnt
	variable buzzTime, histStartTime, histEndTime, histTime
	string event
	variable goCode
	variable nBuzzesRC = 0, nBuzzesRI =0, nBuzzesNC =0, nBuzzesNI =0, nBuzzesGO = 0
	for (iPnt =startPntG; iPnt < endPntG; iPnt += 1)
		// look for check+ for start of trial
		for (; (iPnt < endPnt) && cmpStr (eventWave [iPnt], "check+") != 0; iPnt += 1)
		endfor
		startPnt = iPnt
		startTime = timeWave [iPnt]
		// look for next complete, exit, or SeshEnd
		for (; (iPnt < nPnts) && (!((cmpStr (eventWave [iPnt], "complete") == 0) || (cmpStr (eventWave [iPnt], "exit") == 0))); iPnt +=1)
		endfor
		endPnt = iPnt
		endTime = timeWave [iPnt]
		// look for buzzes within this trial
		for (iPnt = startPnt; iPnt < endPnt; iPnt +=1)
			if (stringMatch (eventWave [iPnt], "*Buzz*") == 1)
			//if (cmpStr (StringFromList(1, eventWave [iPnt], ":"), "Buzz") == 0) // add buzz times to histogram for trial type
				goCode = NumberByKey("GO", eventWave [iPnt], "=", ",")
				switch (goCode)
					case 2:
						WAVE histWave = histWaveRC
						nBuzzesRC +=1
						break
					case -2:
						WAVE histWave = histWaveRI
						nBuzzesRI +=1
						break
					case 1:
						WAVE histWave = histWaveNC
						nBuzzesNC +=1
						break
					case -1:
						WAVE histWave = histWaveNI
						nBuzzesNI +=1
						break
					default:
						//printf "Bad data at point %d\r", iPnt
						WAVE histWave =histWaveGO
						nBuzzesGO +=1
				endSwitch
				//if (!(WaveExists (histwave)))
				//	continue
				//endif
				buzzTime = timeWave [iPnt]
				histStartTime = Max (timeWave [iPnt] - kMinus, startTime)
				histEndTime = Min (timeWave [iPnt] + kPlus, endTime)
				histStartPnt =  GUIPMathFindNum (timeWave, histStartTime, startPnt, endPnt, 0)
				if (histStartPnt < 0)
					histStartPnt = -histStartPnt -1
				endif
				histEndPnt =  GUIPMathFindNum (timeWave, histEndTime, startPnt, endPnt, 0)
				if (histEndPnt < 0)
					histEndPnt = -histEndPnt - 1
				endif
				for (histPnt = histStartPnt; histPnt < histEndPnt; histPnt +=1)
					if (cmpstr (StringFromList (0, eventWave [histPnt], ":"), "lick") ==0)
						histWave [x2pnt(histWave, timeWave [histPnt] - buzzTime)] += 1
					endif
				endfor
			endif
		endfor
	endfor
	
	histWaveRC /= (nBuzzesRC* kBinSize)
	histWaveRI /= (nBuzzesRI* kBinSize)
	histWaveNC /= (nBuzzesNC* kBinSize)
	histWaveNI /= (nBuzzesNI* kBinSize)
	histWaveGO /= (nBuzzesGO* kBinSize)
	display histWaveRC, histWaveRI, histWaveNC, histWaveNI, histWaveGO
	ModifyGraph lstyle($nameofWave(histWaveRI))=1,rgb($nameofWave(histWaveNC))=(1,16019,65535),lstyle($nameofWave(histWaveNI))=1,rgb($nameofWave(histWaveNI))=(1,16019,65535)
	
	
	string labelStr = "\\Z14" + mouse + "\r" + dateStr + "\rRC=" + num2str (nBuzzesRC) + ", RI=" + num2str (nBuzzesRI) + ", NC=" + num2str (nBuzzesNC) + ", NI=" + num2str (nBuzzesNI) + ",GO=" + num2str (nBuzzesGO)
	TextBox/C/N=text0/F=0/A=MT labelStr
		label left "Licks/Second"
	label bottom  "Time relative to buzz start (\\U)"
end


function periBuzzHist_NOT_Disc (string mouse, string startStr, string endStr)
	
	WAVE/T eventWave = $"root:AutoHeadFixData:" + mouse + "_event"
	WAVE timeWave = $"root:AutoHeadFixData:" + mouse + "_time"
	
	string dateStr =  stringfromlist (0, startStr, " ")
	string timeStr = stringfromlist (1, startStr, " ")
	variable timeEls = itemsinlist (timeStr, ":")
	variable startTIme = date2secs (str2num (stringfromlist (0, dateStr, "-")), str2num (stringfromlist (1, dateStr, "-")), str2num (stringfromlist (2, dateStr, "-")))
	if (timeEls > 0)
		startTime += str2num (stringfromlist (0, timeStr, ":")) * 3600
		if (timeEls > 1)
			startTime += str2num (stringfromlist (1, timeStr, ":")) * 60
			if (timeEls > 2)
				startTime += str2num (stringfromlist (2, timeStr, ":"))
			endif
		endif
	endif
	// now end time
	dateStr =  stringfromlist (0, endStr, " ")
	timeStr = stringfromlist (1, endStr, " ")
	timeEls = itemsinlist (timeStr, ":")
	variable endTime = date2secs (str2num (stringfromlist (0, dateStr, "-")), str2num (stringfromlist (1, dateStr, "-")), str2num (stringfromlist (2, dateStr, "-")))
	if (timeEls > 0)
		endTime += str2num (stringfromlist (0, timeStr, ":")) * 3600
		if (timeEls > 1)
			endTime += str2num (stringfromlist (1, timeStr, ":")) * 60
			if (timeEls > 2)
				endTime += str2num (stringfromlist (2, timeStr, ":"))
			endif
		endif
	endif
	// find start and end pnts
	variable startPntG, endPntG, nPnts = numPnts (timeWave)
	startPntG = GUIPMathFindNum(timeWave, startTime, 0, nPnts, 0)
	if (startPntG < 0)
		startPntG *=-1; startPntG -=1
	endif
	endPntG = GUIPMathFindNum(timeWave, endTime, startPntG, nPnts, 0)
	if (endPntG < 0)
		endPntG *=-1; endPntG -=1
	endif
	//Make output waves
	make/o/n= ((kPlus + kMinus)/kBinSize) $mouse + "_pbHist_Go", $mouse + "_pbHist_NoGo"
	WAVE histWaveGo = $mouse + "_pbHist_Go"
	WAVE histWaveNoGo = $mouse + "_pbHist_NoGo"

	setscale/p x -kMinus, kBinSize, "s", histWaveGo, histWaveNoGo
	histWaveGo = 0;histWaveNoGo =0
	
	variable iPnt, startPnt, endPnt, histStartPnt, histEndPnt, histPnt
	variable buzzTime, histStartTime, histEndTime, histTime
	string event
	variable goCode
	variable nBuzzesRC = 0, nBuzzesRI =0, nBuzzesNC =0, nBuzzesNI =0
	for (iPnt =startPntG; iPnt < endPntG; iPnt += 1)
		// look for check+ for start of trial
		for (; (iPnt < endPnt) && cmpStr (eventWave [iPnt], "check+") != 0 && cmpStr (eventWave [iPnt], "check No Fix Trial") != 0; iPnt += 1)
		endfor
		startPnt = iPnt
		startTime = timeWave [iPnt]
		// look for next complete, exit, or SeshEnd
		for (; (iPnt < nPnts) && (!((cmpStr (eventWave [iPnt], "complete") == 0) || (cmpStr (eventWave [iPnt], "exit") == 0))); iPnt +=1)
		endfor
		endPnt = iPnt
		endTime = timeWave [iPnt]
		// look for buzzes within this trial
		for (iPnt = startPnt; iPnt < endPnt; iPnt +=1)
			if (stringMatch (eventWave [iPnt], "*Buzz*") == 1)
			//if (cmpStr (StringFromList(1, eventWave [iPnt], ":"), "Buzz") == 0) // add buzz times to histogram for trial type
				goCode = NumberByKey("GO", eventWave [iPnt], "=", ",")
				switch (goCode)
					case 2:
						WAVE histWave = histWaveGo
						nBuzzesRC +=1
						break
					case -2:
						WAVE histWave = histWaveGo
						nBuzzesRI +=1
						break
					case 1:
						WAVE histWave = histWaveNoGo
						nBuzzesNC +=1
						break
					case -1:
						WAVE histWave = histWaveNoGo
						nBuzzesNI +=1
						break
					default:
						printf "Bad data at point %d\r", iPnt
				endSwitch
				buzzTime = timeWave [iPnt]
				histStartTime = Max (timeWave [iPnt] - kMinus, startTime)
				histEndTime = Min (timeWave [iPnt] + kPlus, endTime)
				histStartPnt =  GUIPMathFindNum (timeWave, histStartTime, startPnt, endPnt, 0)
				if (histStartPnt < 0)
					histStartPnt = -histStartPnt -1
				endif
				histEndPnt =  GUIPMathFindNum (timeWave, histEndTime, startPnt, endPnt, 0)
				if (histEndPnt < 0)
					histEndPnt = -histEndPnt - 1
				endif
				for (histPnt = histStartPnt; histPnt < histEndPnt; histPnt +=1)
					if (cmpstr (StringFromList (0, eventWave [histPnt], ":"), "lick") ==0)
						histWave [x2pnt(histWave, timeWave [histPnt] - buzzTime)] += 1
					endif
				endfor
			endif
		endfor
	endfor
	
	histWaveGo /= ((nBuzzesRC + nBuzzesRI) * kBinSize)
	histWaveNoGo /= ((nBuzzesNC + nBuzzesNI) * kBinSize)
	//histWaveNC /= (nBuzzesNC* kBinSize)
	//histWaveNI /= (nBuzzesNI* kBinSize)
	
	display histWaveGo, histWaveNoGo
	ModifyGraph rgb($nameofWave(histWaveNoGo))=(1,16019,65535),lstyle($nameofWave(histWaveNoGo))=1
	
	
	string labelStr = "\\Z14" + mouse + "\r" + dateStr + "\rRC=" + num2str (nBuzzesRC) + ", RI=" + num2str (nBuzzesRI) + ", NC=" + num2str (nBuzzesNC) + ", NI=" + num2str (nBuzzesNI)
	TextBox/C/N=text0/F=0/A=MT labelStr
		label left "Licks/Second"
	label bottom  "Time relative to buzz start (\\U)"
end


STRCONSTANT kstartTIme = "2017-06-30 0:0:0"
STRCONSTANT kEndTime = "2017-11-10 0:0:0"
function MovieLists ()
	variable iMouse, nMice = itemsinList (kMiceList, ";")
	string aMouse
	for (iMouse =0; iMouse < nMice; iMouse +=1)
		aMouse = StringFromList(iMouse, kMiceList, ";")
		AHF_movieList (aMouse, kstartTIme, kEndTime)
	endfor
end

// Print a list of movie names and events
function AHF_movieList (string mouse, string startStr, string endStr)
	
	WAVE/T eventWave = $"root:AutoHeadFixData:" + mouse + "_event"
	WAVE timeWave = $"root:AutoHeadFixData:" + mouse + "_time"
	
	variable movieRefNum
	open /P=Auto_Head_fixLoadPath movieRefNum as mouse + "_movieEvents.txt"
	string dateStr =  stringfromlist (0, startStr, " ")
	string timeStr = stringfromlist (1, startStr, " ")
	variable timeEls = itemsinlist (timeStr, ":")
	variable startTIme = date2secs (str2num (stringfromlist (0, dateStr, "-")), str2num (stringfromlist (1, dateStr, "-")), str2num (stringfromlist (2, dateStr, "-")))
	if (timeEls > 0)
		startTime += str2num (stringfromlist (0, timeStr, ":")) * 3600
		if (timeEls > 1)
			startTime += str2num (stringfromlist (1, timeStr, ":")) * 60
			if (timeEls > 2)
				startTime += str2num (stringfromlist (2, timeStr, ":"))
			endif
		endif
	endif
	// now end time
	dateStr =  stringfromlist (0, endStr, " ")
	timeStr = stringfromlist (1, endStr, " ")
	timeEls = itemsinlist (timeStr, ":")
	variable endTime = date2secs (str2num (stringfromlist (0, dateStr, "-")), str2num (stringfromlist (1, dateStr, "-")), str2num (stringfromlist (2, dateStr, "-")))
	if (timeEls > 0)
		endTime += str2num (stringfromlist (0, timeStr, ":")) * 3600
		if (timeEls > 1)
			endTime += str2num (stringfromlist (1, timeStr, ":")) * 60
			if (timeEls > 2)
				endTime += str2num (stringfromlist (2, timeStr, ":"))
			endif
		endif
	endif
	// find start and end pnts
	variable startPntG, endPntG, nPnts = numPnts (timeWave)
	startPntG = GUIPMathFindNum(timeWave, startTime, 0, nPnts, 0)
	if (startPntG < 0)
		startPntG *=-1; startPntG -=1
	endif
	endPntG = GUIPMathFindNum(timeWave, endTime, startPntG, nPnts, 0)
	if (endPntG < 0)
		endPntG *=-1; endPntG -=1
	endif
	
	variable iPt
	string videoName, fullPath
	variable videoStartTime, lwt, go
	for (iPt = startPntG; iPt < endPntG; iPt +=1)
		if (cmpstr ("",stringbykey ("video", eventWave [iPt], ":",";")) !=0)
			videoName = "M" + StringByKey("video", eventWave [iPt] , ":" , ";")
//			fullPath =  removeending (GUIPListFiles ("Auto_head_fixLoadPath",  ".raw", videoName, 3, "NOTFOUND"), ";")
//			if (cmpStr (fullPath, "NOTFOUND") != 0)
//				fullPath = removeListItem (0,fullPath, ":")
//				fullPath = removeListItem (0,fullPath, ":")
//				fullPath = removeListItem (0,fullPath, ":")
//				fullPath = removeListItem (0,fullPath, ":")
				fprintf movieRefNum, "Movie\t0\t%s\r", videoName
				//printf "Movie\t0\t%s\r", videoName
				videoStartTime = timeWave [iPt]
				// look for rewards and buzzes till conplete
				for (iPt +=1;cmpstr (eventWave [iPt],"complete") != 0; iPt +=1)
					if (cmpStr (eventWave [iPt], "reward") == 0)
						fprintf movieRefNum, "reward\t%.2f\t\r",(timeWave [iPt] - videoStartTime)
					elseif (cmpStr (StringByKey("Buzz", eventWave [iPt] ,":", ","), "") != 0)
						lwt = NumberByKey("lickWitholdTime", eventWave [iPt], "=", ",")
						go = NumberByKey("GO", eventWave [iPt], "=", ",")
						fprintf movieRefNum, "stim\t%.2f\tGO=%d,witholdtime=%.2f\r", (timeWave [iPt] - videoStartTime), go, lwt
					elseif (cmpStr (eventWave [iPt], "lick:2") == 0)	
						fprintf movieRefNum, "lick\t%.2f\t\r",(timeWave [iPt] - videoStartTime)
					elseif (((cmpStr (eventWave [iPt],"BrainLEDON") ==0)) || ((cmpStr (eventWave [iPt],"BrainLEDOFF") ==0)))
						fprintf movieRefNum, "%s\t%.2f\t\r",eventWave [iPt],(timeWave [iPt] - videoStartTime)
					endif
				endfor
			endif
//		endif
	endfor
	close movieRefNum
end
		
		
		
function AFH_LoadVideos (string mouse, string startStr, string endStr)
	
	WAVE/T eventWave = $"root:AutoHeadFixData:" + mouse + "_event"
	WAVE timeWave = $"root:AutoHeadFixData:" + mouse + "_time"
	
	string dateStr =  stringfromlist (0, startStr, " ")
	string timeStr = stringfromlist (1, startStr, " ")
	variable timeEls = itemsinlist (timeStr, ":")
	variable startTIme = date2secs (str2num (stringfromlist (0, dateStr, "-")), str2num (stringfromlist (1, dateStr, "-")), str2num (stringfromlist (2, dateStr, "-")))
	if (timeEls > 0)
		startTime += str2num (stringfromlist (0, timeStr, ":")) * 3600
		if (timeEls > 1)
			startTime += str2num (stringfromlist (1, timeStr, ":")) * 60
			if (timeEls > 2)
				startTime += str2num (stringfromlist (2, timeStr, ":"))
			endif
		endif
	endif
	// now end time
	dateStr =  stringfromlist (0, endStr, " ")
	timeStr = stringfromlist (1, endStr, " ")
	timeEls = itemsinlist (timeStr, ":")
	variable endTime = date2secs (str2num (stringfromlist (0, dateStr, "-")), str2num (stringfromlist (1, dateStr, "-")), str2num (stringfromlist (2, dateStr, "-")))
	if (timeEls > 0)
		endTime += str2num (stringfromlist (0, timeStr, ":")) * 3600
		if (timeEls > 1)
			endTime += str2num (stringfromlist (1, timeStr, ":")) * 60
			if (timeEls > 2)
				endTime += str2num (stringfromlist (2, timeStr, ":"))
			endif
		endif
	endif
	// find start and end pnts
	variable startPntG, endPntG, nPnts = numPnts (timeWave)
	startPntG = GUIPMathFindNum(timeWave, startTime, 0, nPnts, 0)
	if (startPntG < 0)
		startPntG *=-1; startPntG -=1
	endif
	endPntG = GUIPMathFindNum(timeWave, endTime, startPntG, nPnts, 0)
	if (endPntG < 0)
		endPntG *=-1; endPntG -=1
	endif
	
	variable iPt
	string videoName, fullPath
	variable videoStartTime
	for (iPt = startPntG; iPt < endPntG; iPt +=1)
		if (cmpstr (eventWave [iPt], "check+") ==0)
			iPt +=1
			videoName = "M" + StringByKey("video", eventWave [iPt] , ":" , ";")
			fullPath =  removeending (GUIPListFiles ("Auto_head_fixLoadPath",  ".raw", videoName, 3, "NOTFOUND"), ";")
			if (cmpStr (fullPath, "NOTFOUND") != 0)
				AHF_LoadMovie(fullPath, 0)
			endif
		endif
	endfor
end
