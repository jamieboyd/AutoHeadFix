#pragma rtGlobals=3		// Use modern global access method and strict wave access.
#pragma version =1
#include "GUIPDirectoryLoad"
#include "GUIPMath"


// ******************************************************
// Loader for data from AutoHeadFix program running on the raspberry pi
// Last modified 2016/01/14 by Jamie Boyd

Menu "Macros"
	"Load Auto Head Fix Data", AHF_Loader ()
End

// Each line in Text file is tab separated, as follows:
//  mouse num (or 0 for events seshstart and  seshend); unix GM Time;  human formatted time;  event
// event can be SeshStart, seshEnd, entry, exit, check+ or check-, reward0..., n, complete. example:
// 0000000000000	1448722801.83	2015-11-28 07:00:01	SeshStart

// Loader makes the following sets of waves for each mouse
// day waves are made with values for the whole day. Not every calendar day will neccessarily be represented, only test days
	// date in seconds from Igor epoch to start of the testing day
	// total time in cage, in seconds,  for this day from sesh start/end events
	// total entries
	// total entry rewards (based on time to exit or head fix being less than  entrance_reward_delay_time)
	// total head fixes
	// total fix rewards

// entrance times waves are made based on each entry being a dat point
	// entrance date/time in Igor time format
	// entrance duration, in seconds
	// was an entry reward (based on time to exit or head fix being less than  entrance_reward_delay_time) 1 for Yes, 0 for No
	
//	head fix time waves are made with each head fix being a data point
	// date/time of each headFix in Igor time format
	// head fix duration, in secs
	// nRewards delivered during that head fix

// The loader assumes that data between each seshStart and seshEnd pair is ordered in time, but not that files are loaded in chronological order 


// Each file name should contain metadata on cageID: "headFix_" + cageID + "_" + MMDD + (optionally) "_" + other meta-Data
// e.g., headFix_AB_1108.txt or

 CONSTANT kSECSPERDAY =86400 // number of seconds in one day
 CONSTANT kSECSTODAYSTART = 25200 // we bin data by day to mouse-time where a day starts at 7 am, to cleanly divide light and dark phases
 CONSTANT kUNIXEPOCHGMOFFSET = 2082816000// the Unix epoch started on jan 01 1970, Igor time is calculated from jan 01 1904. 
// Unix time.time(), used in the acquisition code,  gives seconds in Universal (Greenwich) time, not accounting for timezone.
//  this constant combines both the 66 year and 8 hour offset
 CONSTANT kENTRANCEREWARDDELAY = 2 // As set in the  acquisition code, if a mouse leaves the chamber before this delay is up, no entrance reward

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
	
	WAVE/T grpList = root:AutoHeadFixData:GrpList
	WAVE GrpListSel = root:packages:GUIP:Auto_Head_Fix:GrpListSel
	CheckBox OverwriteCheck win = Auto_Head_FixLoader, pos={4,vTop + 2},size={91,15},title="Overwrite Existing Data"
	CheckBox OverwriteCheck win = Auto_Head_FixLoader, help={"If a file for a particular day was loaded previously, delete existing data and load new data"}
	CheckBox OverwriteCheck win = Auto_Head_FixLoader, variable= root:packages:GUIP:Auto_Head_Fix:Overwrite, proc = AHF_OptionsCheckProc
	CheckBox LoadMoviesCheck win = Auto_Head_FixLoader,pos={136,vTop + 2},size={71,16},proc=AHF_OptionsCheckProc,title="Load Movies"
	CheckBox LoadMoviesCheck win = Auto_Head_FixLoader,help={"Try to load movies for head fixed events, using relative file path from text file folder"}
	CheckBox LoadMoviesCheck win = Auto_Head_FixLoader,variable= root:packages:GUIP:Auto_Head_Fix:loadMovies
	CheckBox ExistingMiceOnlyCheck win = Auto_Head_FixLoader,pos={214,57},size={74,15},proc=AHF_OptionsCheckProc,title="Existing Mice"
	CheckBox ExistingMiceOnlyCheck win = Auto_Head_FixLoader,help={"Load data only for mice for which a TagID has been givrn a grp ID"}
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
			if (lba.row > 0) 
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
	// cage name form file name is used only if group name is not already in the tag ID wave
	string cageName = cleanUpName (StringFromList(1, fileNameStr, "_"), 0)
	if (CmpStr (cageName, "") ==0)
		cageName = "noName"
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
	variable seshStart, seshStarted=0
	variable entryStart
	variable enteredMouse, thisMouse, isCheckedIn
	string waveNameStr
	// find first event - if it is not a session start, start the session at first event
	FReadLine/T="\n"  fileRefNum, aLine
	for (; strlen (aLine) > 1; )
		aLine = removeending (removeending  (aLine, "\n"), "\r")
		thisMouse =  mod (str2num (StringFromList(0, aLIne, "\t")), 10000)
		thisTime = str2Num (StringFromList(1, aLIne, "\t")) + kUNIXEPOCHGMOFFSET
		// skip lines that are not events that may arise from concatenating files together
		if ((numtype (thisTime) == 0) && (numtype (thisMouse) == 0))
			seshStart = thisTime
			seshStarted =1
			thisEvent = StringFromList(3, aLIne, "\t")
			// if first event is seshStart, it is processed and get next line ready for main loop through events
			if (cmpStr (thisEvent, "SeshStart") == 0)
				FReadLine/T="\n"  fileRefNum, aLine
			endif
			break
		endif
		FReadLine/T="\n"  fileRefNum, aLine
	endfor
	// now loop through the rest of events
	for (; strlen (aLine) > 1; )
		aLine = removeending (removeending  (aLine, "\n"), "\r")
		thisMouse =  mod (str2num (StringFromList(0, aLIne, "\t")), 10000) // scrunch carzy long mouseID to 4 digits
		thisTime = str2Num (StringFromList(1, aLIne, "\t")) + kUNIXEPOCHGMOFFSET
		thisEvent =StringFromList(3, aLIne, "\t")
		// skip lines that are not events that may arise from concatenating files together
		if (!((numtype (thisTime) == 0) && (numtype (thisMouse) == 0)))
			continue
		endif
		// process event
		StrSwitch (thisEvent)
			case "SeshStart":  // start of a session; there may be more than 1 start per file
				if (seshStarted)
					print "Session start without corresponding seshEnd: " + fileNameStr + " " + aLine
					AHF_SeshEnd(seshStart, thisTime, cageName, overWrite, existingMiceOnly)
				endif
				seshStart = thisTime 
				seshStarted=1
				break
			case "SeshEnd":
				if (!(seshStarted))
					print "Session end without precedng seshStart: " + fileNameStr + " " + aLine
				endif
				seshStarted = 0
				AHF_SeshEnd(seshStart, thisTime, cageName, overWrite,existingMiceOnly)
				break
			case "entry":
				if (!(seshStarted))
					print "Entry without precedng seshStart: " + fileNameStr + " " + aLine
					seshStart = thisTime 
					seshStarted=1
				endif
				enteredMouse = thisMouse
				// find mouse, or make an entry for it in temp waves
				mousePos = GUIPMathFindNum (mice, thisMouse, 0, nMice-1, 0)
				if (mousePos < 0) // mouse was not found
					// account for the 1 character offset in position used to disambiguate "-0 = not found, aphabetically before pos 0" and
					// "0 = found at position 0"
					mousePos = -(mousePos+1) 
					insertpoints/M=0 mousePos, 1, mice, entries, entryRewards, fixes, fixRewards
					mice [mousePos] = thisMouse
					entries [mousePos] =0; entryRewards[mousePos] =0;fixes[mousePos] =0; fixRewards[mousePos] =0
					nMice +=1
					// make temp waves for this mouse, if not already made
					waveNameStr = "root:packages:m" + num2str (mice [mousePos])
					if (!(WaveExists ($waveNameStr + "_entryTimes")))
						make/o/D/n=(10) $waveNameStr + "_entryTimes"
						make/o/n=(10) $waveNameStr + "_entryDurs"
						make/o/b/u/n=(10) $waveNameStr + "_WasEntryReward"
						make/o/D/n=(10) $waveNameStr + "_HeadFixTimes"
						make/o/n=(10) $waveNameStr+ "_HeadFixDurs"
						make/o/b/u/n=(10) $waveNameStr + "_HeadFixRewards"
					endif
					// reference waves for this mouse
					WAVE entryTimes = $waveNameStr + "_entryTimes"
					WAVE entryDurs = $waveNameStr + "_entryDurs"
					WAVE wasEntryReward = $waveNameStr + "_WasEntryReward"
					WAVE headFixTimes = $waveNameStr + "_HeadFixTimes"
					WAVE headFixDurs =$waveNameStr+ "_HeadFixDurs"
					WAVE headFixRewards= $waveNameStr + "_HeadFixRewards"
				else
					waveNameStr = "root:packages:m" + num2str (mice [mousePos])
				endif
				// add entry for this mouse
				Wave MouseEntries =  $waveNameStr + "_entryTimes"
				MouseEntries [entries [mousePos]] = thisTime
				entryStart = thisTime
				break
			case "exit":
				if (thisMouse !=  enteredMouse)
					print"Entered mouse, " + num2str (enteredMouse) + " is not exited mouse " + num2str (thisMouse)
					print FileNameStr, aline
				else
					Wave MouseEntries =  $waveNameStr + "_entryTimes"
					WAVE MouseDurations = $waveNameStr+ "_entryDurs"
					WAVE mouseWasEntryReward =  $waveNameStr + "_WasEntryReward"
					MouseDurations[entries [mousePos]] = thisTime - MouseEntries [entries [mousePos]]
					if (MouseDurations[entries [mousePos]] > kENTRANCEREWARDDELAY)
						mouseWasEntryReward  [entries [mousePos]]  = 1
						entryrewards [mousePos] +=1
					else
						mouseWasEntryReward  [entries [mousePos]]  = 0
					endif
					entries [mousePos] += 1
					if (entries [mousePos]  >= (numPnts (MouseEntries)))
						redimension/n=(2*entries [mousePos]) MouseEntries, MouseDurations, mouseWasEntryReward
					endif
				endif
				if (isCheckedIn)
					WAVE mouseHeadFixTimes = $waveNameStr + "_HeadFixTimes"
					WAVE mouseHeadFixDurations = $waveNameStr+ "_HeadFixDurs"
					mouseHeadFixDurations  [fixes [mousePos]]  = thisTime -  mouseHeadFixTimes  [fixes [mousePos]] 
					fixes [mousePos] +=1
					if (fixes [mousePos]  >= numPnts (mouseHeadFixTimes))
						WAVE mouseFixRewards = $waveNameStr + "_HeadFixRewards"	
						redimension/n=(2*fixes [mousePos]) mouseHeadFixTimes, mouseHeadFixDurations, mouseFixRewards
					endif
					isCheckedIn = 0
				endif
				break
			case "check+":
			case "check0+":
				isCheckedIn = 1
				WAVE mouseHeadFixTimes = $waveNameStr + "_HeadFixTimes"
				mouseHeadFixTimes  [fixes [mousePos]]   = thisTime
				WAVE mouseWasEntryReward =  $waveNameStr + "_WasEntryReward"
				if (thisTime <  entryStart + kENTRANCEREWARDDELAY) // countermanding an entrance reward with an immediate head fix
					mouseWasEntryReward  [entries [mousePos]]  = 0
					entryrewards [mousePos] -=1
				endif
				if (loadMovie)
					AHF_LoadMovie(ImportPathStr, thisTime -kUNIXEPOCHGMOFFSET)
				endif
				break
			case "complete":
				isCheckedIn = 0
				WAVE mouseHeadFixTimes = $waveNameStr + "_HeadFixTimes"
				WAVE mouseHeadFixDurations = $waveNameStr+ "_HeadFixDurs"
				mouseHeadFixDurations  [fixes [mousePos]]  = thisTime -  mouseHeadFixTimes  [fixes [mousePos]] 
				fixes [mousePos] +=1
				if (fixes [mousePos]  >= numPnts (mouseHeadFixTimes))
					WAVE mouseFixRewards = $waveNameStr + "_HeadFixRewards"	
					redimension/n=(2*fixes [mousePos]) mouseHeadFixTimes, mouseHeadFixDurations, mouseFixRewards
				endif
				break
			case "reward0":
				WAVE mouseFixRewards = $waveNameStr + "_HeadFixRewards"	
				 mouseFixRewards [fixes [mousePos]] = 1
				fixRewards [mousePos]  +=1
				break
			case "reward1":
			case "reward2":
			case "reward3":
			case "reward4":
			case "reward5":
			case "reward6":
			case "reward7":
			case "reward8":
			case "reward9":
			case "reward10":
			case "reward11":
			case "reward12":
				 WAVE mouseFixRewards = $waveNameStr + "_HeadFixRewards"	
				 mouseFixRewards [fixes [mousePos]] += 1
				 fixRewards [mousePos]  +=1
				break
		endSwitch
		FReadLine/T="\n"  fileRefNum, aLine
	endfor
	// do final seshEnd, if needed
	if (seshStarted)
		AHF_SeshEnd(seshStart, thisTime, cageName, overWrite,existingMiceOnly)
	endif
end




function AHF_SpanEntries (mouse)
	string mouse
	
	//setdatafolder
	
	
	wave headFixTime = $" root:AutoHeadFixData:" + mouse	 + "_hdFXTIme"
	Wave headFixDur = $" root:AutoHeadFixData:" + mouse + "_hdFxDurs"
	variable iFix, iOut,  nFixes = numpnts (headFixTIme)
	make/d/o/n= (nFixes  * 3) $mouse	 + "_hdFXSpanX"
	make/o/n=(nFixes * 3) ,  $mouse	 + "_hdFXSpanY"
	WAVE spanX =   $mouse	 + "_hdFXSpanX"
	WAVE spanY =   $mouse	 + "_hdFXSpanY"
	Setscale d 0,0, "dat", spanX
	spanY = 0
	for (iFIx =0, iOut =0; iFix < nFixes; iFix +=1, iOut +=3)
		spanX [ iout] = headFixTime [iFix]
		spanX [ iout + 1] = headFixTime [iFix] + headFixDur [iFix]
		spanX [ iout + 2] = NaN
		
	endfor
	
	wave entryTime = $" root:AutoHeadFixData:" + mouse	 + "_EntrTime"
	Wave entryDur = $" root:AutoHeadFixData:" + mouse + "_entryDurs"
	variable iEntr,   nEntries = numpnts (entryTime)
	make/d/o/n= (nEntries  * 3) $mouse	 + "_EntrSpanX"
	make/o/n=(nFixes * 3) ,  $mouse	 + "_EntrSpanY"
	WAVE spanX =   $mouse	 + "_EntrSpanX"
	WAVE spanY =   $mouse	 + "_EntrSpanY"
	Setscale d 0,0, "dat", spanX
	spanY = 0
	for (iFIx =0, iOut =0; iFix < nFixes; iFix +=1, iOut +=3)
		spanX [ iout] = entryTime [iFix]
		spanX [ iout + 1] = entryTime [iFix] + entryDur [iFix]
		spanX [ iout + 2] = NaN
		
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
		printf "Error opening  Auto Head Fix movie file for \"%s\".\r", mfile
#endif
		return 1
	endif
	FStatus mref 
	make/o/b/u/n = (V_logEOF)  root:testMovie
	WAVE testMovie = root:testMovie
	FBinRead  mref, testMovie
	variable iFrame, nFrames  = V_logEOF/(3 * kMOVIEFRAMESIZE)
	testMovie [0, V_logEOF/3 -1] = testMovie [1 + p * 3]
	redimension/n = (kMOVIEX,kMOVIEY, nFrames)testMovie
end



function Dirk_removeDups ()
	
	WAVE animalNum = root:tagW
	WAVE dateSecs = root:timeW
	WAVE/T event = root:Action
	sort {animalNum, dateSecs, event} animalNum, dateSecs, event;doupdate
	
	
	variable iPt, nPts = numpnts (animalNum)
	for (iPt =nPts -1; iPt > 0; iPt -=1)
		if (((dateSecs [iPt] == dateSecs [iPt-1]) &&  (animalNum [iPt] == animalNum [iPt-1])) && (cmpStr (event [iPt], event  [iPt -1]) ==0))
			DeletePoints iPt, 1, animalNum, dateSecs, event
		endif
	endfor
end



function DIrk_toMice ()
	
	WAVE animalNum = root:tagW
	WAVE dateSecs = root:timeW
	WAVE/T event = root:Action

	WAVE/T grpList =root:AutoHeadFixData:GrpList
		
	variable iPt, nPts = numpnts (animalNum)
	
	
	variable imouse, nMice = dimsize (grpList, 0)
	variable mouseStartPt, mouseEndPt, mouseNum
	string mouseNumStr, aMouse, thisEvent
	variable nEntries =0, nHeadFixes=0
	variable entered, fixed, tempEnterTime, tempFixTime
	for (iMouse =1; iMouse < nMice; iMouse +=1)
		mouseNumStr = grpList [iMouse] [0]
		aMouse =  grpList [iMouse] [1] +  grpList [iMouse] [0]
		mouseNum = str2num (mouseNumStr)
		make/o/d/n=0 $"root:AutoHeadFixData_DIrk:" + aMouse + "_EntrTime"
		make/o/n=0 $"root:AutoHeadFixData_DIrk:" + aMouse +"_entryDurs"
		make/o/d/n=0 $"root:AutoHeadFixData_DIrk:" + aMouse +"_HdFxTime"
		make/o/n=0 $"root:AutoHeadFixData_DIrk:" + aMouse +"_HdFxDurs"
		WAVE entrTime = $"root:AutoHeadFixData_DIrk:" + aMouse + "_EntrTime"
		WAVE entryDurs =  $"root:AutoHeadFixData_DIrk:" + aMouse +"_entryDurs"
		WAVE HdFxTime = $"root:AutoHeadFixData_DIrk:" + aMouse +"_HdFxTime"
		WAVE HdFxDurs = $"root:AutoHeadFixData_DIrk:" + aMouse +"_HdFxDurs"
		mouseStartPt = GUIPMathFindNum (animalNum, mouseNum, 0,nPts -1, 0)
		if (mouseStartPt < 0)
			continue
		endif
		mouseEndPt =  GUIPMathFindNum (animalNum, mouseNum, mouseStartPt,nPts-1, 1)
		entered = 0; fixed =0
		nEntries =0; nHeadFixes=0
		for (iPt = mouseStartPt; iPt <= mouseEndPt; iPt +=1)
			thisEvent = event [iPt]
			StrSwitch (thisEvent)
				case "entry":
					//if (!(entered))
						tempEnterTime = dateSecs [iPt]
						entered =1
					//endif
					break
				case "exit":
					if (entered)
						InsertPoints nEntries, 1, entrTime, entryDurs
						entrTime [nEntries] = tempEnterTime
						entryDurs [nEntries] =  dateSecs [iPt] - tempEnterTime
						nEntries +=1
						entered =0
					endif
					break
			case "check+":
			case "check0+":
				if (!(fixed))
					tempFixTime =  dateSecs [iPt]
					fixed = 1
				endif
				break
			case "complete":
				if (fixed)
					InsertPoints nHeadFixes, 1, HdFxTime, HdFxDurs
					HdFxTime [nHeadFixes] =  tempFixTime
					HdFxDurs [nHeadFixes] =  dateSecs [iPt] -tempFixTime
					nHeadFixes +=1
					fixed =0
				endif
			EndSwitch
					
		endFor
	endfor
	
end


function combineData (inFolder, outFolder)
	string inFolder, outFolder
	
	WAVE/T grpList =root:AutoHeadFixData:GrpList
	variable imouse, nMice = dimsize ( grpList, 0)
	variable nPin, nPout
	string aMouse
	
	string dataStr, dataList = "EntrTime;entryDurs;HdfxTime;HdfxDurs;"
	variable iDatum, nData = itemsinlist (dataList, ";")
	for (iMouse =1; iMouse < nMice; iMouse +=1)
		aMouse = grpList [iMouse] [1] +  grpList [iMouse] [0]
		for (iDatum = 0; iDatum < nData; iDatum +=1)
			dataStr = stringFromlist (iDatum, dataList)
			WAVE inWave = $inFolder +  aMouse + "_" + dataStr
			wave outWave = $outFolder +  aMouse + "_" + dataStr
			nPin = numpnts (inWave)
			nPout =  numpnts (outWave)
			if (nPout > 0)
				InsertPoints nPout, npin, outWave
				outWave [nPout, (nPout + nPin)] = inWave [p-nPout]
			endif
		endfor
	endfor
end



function AHF_removeDupes ()
	
	WAVE/T grpList =root:AutoHeadFixData:GrpList
	variable imouse, nMice = dimsize ( grpList, 0)
	variable iPt, nPts
	string aMouse
	for (iMouse =1; iMouse < nMice; iMouse +=1)
		aMouse = grpList [iMouse] [1] +  grpList [iMouse] [0]
		WAVE entrTIme = $"root:AutoHeadFixData:" + aMouse + "_EntrTIme"
		WAVE entryDurs = $"root:AutoHeadFixData:" + aMouse + "_entryDurs"
		if (!((WaveExists (entrTIme)  && (WaveExists (entryDurs)))))
			printf "Entry waves do not exist for %s\t", aMouse + "_entryDurs"
			continue
		endif
		sort entrTIme entrTIme, entryDurs
		nPts = numPnts (entrTIme)
		for (iPt =nPts -1; iPt > 0; iPt -= 1)
			if (entrTIme [iPt] == entrTIme [iPt-1])
				deletePoints iPt, 1, entrTIme, entryDurs
			endif
		endfor
		
		WAVE headFixTIme = $"root:AutoHeadFixData:" + aMouse + "_HdfxTIme"
		WAVE headFixDurs = $"root:AutoHeadFixData:" + aMouse + "_HdFxDurs"
		if (!((WaveExists (headFixTIme)  && (WaveExists (headFixDurs)))))
			printf "Head fix waves do not exist for %s\t", aMouse + "_HdFxDurs"
			continue
		endif
		sort headFixTIme headFixTIme, headFixDurs
		nPts = numPnts (headFixTIme)
		for (iPt =nPts -1; iPt > 0; iPt -= 1)
			if (headFixTIme [iPt] == headFixTIme [iPt-1])
				deletePoints iPt, 1, headFixTIme, headFixDurs
			endif
		endfor
		
	endfor
	
end


// if a head fix strats this soon after another finishes, must be trapped
STATIC CONSTANT kHEADFIXMinDIff = 3.1
// if entry lasts longer than this many seconds, must be trapped, these head fixes do not count
STATIC CONSTANT kMAXENTRTIME = 600

Function  AHF_ClipFixesGrp(theGrp)
	string theGrp
	
	WAVE/T grpList = root:AutoheadFixData:grpList
	variable iMouse, nMice = dimsize (grpList, 0)
	for (iMouse =1; iMouse < nMice; iMouse+=1)
		if (cmpstr (theGrp, grplist [iMouse] [1]) ==0)
			 AHF_ClipFixes( grplist [iMouse] [1] +  grplist [iMouse] [0] )
		endif
	endfor
end
	

function AHF_ClipFixes(mouse)
	string mouse
	
	if (!(DataFolderExists ("root:HeadFixesClipped:")))
		newDataFolder root:HeadFixesClipped
	endif
	WAVE entrytimeIn = $" root:AutoHeadFixData:" + mouse +"_EntrTime"
	Wave entryDurIn = $" root:AutoHeadFixData:" + mouse + "_entryDurs"
	Duplicate/o entrytimeIn $"root:HeadFixesClipped:" + mouse + "_EntrTime"
	Duplicate/o entryDurIn  $"root:HeadFixesClipped:" + mouse + "_entryDurs"
	WAVE entryTime =  $"root:HeadFixesClipped:" + mouse + "_EntrTime"
	WAVE entryDur = $"root:HeadFixesClipped:" + mouse + "_entryDurs"
	
	WAVE headFixTimeIn = $"root:AutoHeadFixData:" + mouse + "_HdFxTime"
	WAVE headFixDurIn = $"root:AutoHeadFixData:" + mouse + "_HdFxDurs"
	Duplicate/o headFixTimeIn $"root:HeadFixesClipped:" + mouse + "_HdFxTime"
	Duplicate/o  headFixDurIn $"root:HeadFixesClipped:" + mouse + "_HdFxDurs"
	WAVE headFixTime =  $"root:HeadFixesClipped:" + mouse + "_HdFxTime"
	WAVE headFixDur =  $"root:HeadFixesClipped:" + mouse + "_HdFxDurs"
	
	variable iEntry, nEntries = numPnts (entryTime)
	variable iFix, nFIxes = numpnts (headFixTime)
	
	for (iFix = nFIxes -1; iFix > 0; iFix -=1)
		if ( headFixDur [iFIx - 1] > 100) // dunno where these come from, but some values are off by orders of magnitude
			continue
		endif
		if (headFixTime [iFix] < headFixTime [iFIx-1 ] +  headFixDur [iFIx - 1] + kHEADFIXMinDIff)
			printf "Head fix interval at point %d for %s was too short  on %s\r",iFix,  mouse, secs2date ( headFixTime [iFix], 2)
			deletepoints iFix, 1, headFixTime,headFixDur
			continue
		endif
	endfor
	
//	variable endTime, nBads
//	for (iEntry =0, iFix =0; iEntry < nEntries; iEntry +=1)
//		if (entryDur [iEntry] > kMAXENTRTIME)
//			printf "Entry Time at point %d for %s was too long at %f", iEntry, mouse, entryDur [iEntry]
//			iFix =abs (GUIPMathFindNum (headFixTime, entryTime [iEntry] , iFix, nFIxes, 0)) 
//			for (endTime  =entryTime [iEntry]  + entryDur [iEntry], nBads=0; ( (iFix < nFIxes) && (headFixTime [iFix] < endTime)); nFIxes -=1, nBads +=1)
//				deletepoints iFix, 1, headFixTime,headFixDur
//			endfor
//			printf ": %d  head fixes were removed\r", nBads
//		endif
//	endfor
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
