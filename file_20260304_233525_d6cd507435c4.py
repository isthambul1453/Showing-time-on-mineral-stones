RESOURCE DESPAWN TIMER - FULL COPY/PASTE GUIDE

Macro:
- ENABLE_RESOURCE_DESPAWN_TIMER

==================================================
1) DEFINES
==================================================

[SERVER] Source/Server/common/service.h
Add:
#define ENABLE_RESOURCE_DESPAWN_TIMER

[CLIENT] Source/Binary/source/UserInterface/Locale_inc.h
Add:
#define ENABLE_RESOURCE_DESPAWN_TIMER
#define RESOURCE_DESPAWN_MIN_SEC 420
#define RESOURCE_DESPAWN_MAX_SEC 900
#define RESOURCE_DESPAWN_LIFETIME_SEC RESOURCE_DESPAWN_MAX_SEC

==================================================
2) PACKET STRUCT (MUST MATCH ON BOTH SIDES)
==================================================

[SERVER] Source/Server/game/src/packet.h
[CLIENT] Source/Binary/source/UserInterface/Packet.h
Struct: TPacketGCCharacterAdd
Place EXACTLY after dwAffectFlag[2]:

#ifdef ENABLE_RESOURCE_DESPAWN_TIMER
	DWORD dwResourceDespawnRemainSec;
#endif

==================================================
3) SERVER SEND VALUE
==================================================

File: Source/Server/game/src/char.cpp
In character add packet fill area, add:

#ifdef ENABLE_RESOURCE_DESPAWN_TIMER
	pack.dwResourceDespawnRemainSec = 0;
	if (IsMining() && m_pkMiningEvent)
	{
		const long lRemainPulse = event_time(m_pkMiningEvent);
		pack.dwResourceDespawnRemainSec = (lRemainPulse > 0) ? (DWORD)(lRemainPulse / passes_per_sec) : 0;
	}
#endif

==================================================
4) CLIENT READ VALUE
==================================================

File: Source/Binary/source/UserInterface/PythonNetworkStreamPhaseGameActor.cpp

A) In character add packet parser:

#ifdef ENABLE_RESOURCE_DESPAWN_TIMER
	kNetActorData.m_dwResourceDespawnRemainSec = chrAddPacket.dwResourceDespawnRemainSec;
#endif

B) In append/new actor init block:

#ifdef ENABLE_RESOURCE_DESPAWN_TIMER
	kNetActorData.m_dwResourceDespawnRemainSec = 0;
#endif

==================================================
5) NETWORK ACTOR DATA
==================================================

File: Source/Binary/source/UserInterface/NetworkActorManager.h
Inside SNetworkActorData:

#ifdef ENABLE_RESOURCE_DESPAWN_TIMER
	DWORD m_dwResourceDespawnRemainSec;
#endif

File: Source/Binary/source/UserInterface/NetworkActorManager.cpp

A) copy from src:
#ifdef ENABLE_RESOURCE_DESPAWN_TIMER
	m_dwResourceDespawnRemainSec = src.m_dwResourceDespawnRemainSec;
#endif

B) init/reset to zero:
#ifdef ENABLE_RESOURCE_DESPAWN_TIMER
	m_dwResourceDespawnRemainSec = 0;
#endif

C) apply to instance on create:
#ifdef ENABLE_RESOURCE_DESPAWN_TIMER
	if (rkNetActorData.m_dwResourceDespawnRemainSec > 0)
		pNewInstance->SetResourceDespawnRemainSeconds(rkNetActorData.m_dwResourceDespawnRemainSec);
	else
		pNewInstance->ClearResourceDespawnRemainSeconds();
#endif

==================================================
6) INSTANCEBASE.H (DECLARATIONS + MEMBERS)
==================================================

File: Source/Binary/source/UserInterface/InstanceBase.h

Public section add:
#ifdef ENABLE_RESOURCE_DESPAWN_TIMER
	DWORD GetSpawnTimeMSec() const;
	DWORD GetResourceRemainSeconds() const;
	void GetResourceRemainSecondsRange(DWORD& dwMinRemainSec, DWORD& dwMaxRemainSec) const;
	void SetResourceDespawnRemainSeconds(DWORD dwRemainSec);
	void ClearResourceDespawnRemainSeconds();
#endif

Member section add:
#ifdef ENABLE_RESOURCE_DESPAWN_TIMER
	DWORD m_dwSpawnTimeMSec;
	DWORD m_dwResourceDespawnRemainSec;
	DWORD m_dwResourceDespawnSyncTimeMSec;
	bool m_bUseExactResourceDespawnTime;
#endif

==================================================
7) INSTANCEBASE.CPP (FULL METHOD BODIES)
==================================================

File: Source/Binary/source/UserInterface/InstanceBase.cpp

A) In Create(), after SetVirtualID(...):
#ifdef ENABLE_RESOURCE_DESPAWN_TIMER
	m_dwSpawnTimeMSec = CTimer::Instance().GetCurrentMillisecond();
	ClearResourceDespawnRemainSeconds();
#endif

B) Add these methods (copy exactly):

#ifdef ENABLE_RESOURCE_DESPAWN_TIMER
DWORD CInstanceBase::GetSpawnTimeMSec() const
{
	return m_dwSpawnTimeMSec;
}

void CInstanceBase::SetResourceDespawnRemainSeconds(DWORD dwRemainSec)
{
	m_dwResourceDespawnRemainSec = dwRemainSec;
	m_dwResourceDespawnSyncTimeMSec = CTimer::Instance().GetCurrentMillisecond();
	m_bUseExactResourceDespawnTime = (dwRemainSec > 0);
}

void CInstanceBase::ClearResourceDespawnRemainSeconds()
{
	m_dwResourceDespawnRemainSec = 0;
	m_dwResourceDespawnSyncTimeMSec = 0;
	m_bUseExactResourceDespawnTime = false;
}

DWORD CInstanceBase::GetResourceRemainSeconds() const
{
	DWORD dwMinRemain = 0;
	DWORD dwMaxRemain = 0;
	GetResourceRemainSecondsRange(dwMinRemain, dwMaxRemain);
	return dwMaxRemain;
}

void CInstanceBase::GetResourceRemainSecondsRange(DWORD& dwMinRemainSec, DWORD& dwMaxRemainSec) const
{
	dwMinRemainSec = 0;
	dwMaxRemainSec = 0;

	if (!const_cast<CInstanceBase*>(this)->IsResource())
		return;

	if (m_bUseExactResourceDespawnTime)
	{
		const DWORD dwNow = CTimer::Instance().GetCurrentMillisecond();
		const DWORD dwElapsedSec = (dwNow > m_dwResourceDespawnSyncTimeMSec) ? ((dwNow - m_dwResourceDespawnSyncTimeMSec) / 1000) : 0;
		const DWORD dwRemainSec = (dwElapsedSec >= m_dwResourceDespawnRemainSec) ? 0 : (m_dwResourceDespawnRemainSec - dwElapsedSec);
		dwMinRemainSec = dwRemainSec;
		dwMaxRemainSec = dwRemainSec;
		return;
	}

	if (m_dwSpawnTimeMSec == 0)
	{
		dwMinRemainSec = RESOURCE_DESPAWN_MIN_SEC;
		dwMaxRemainSec = RESOURCE_DESPAWN_MAX_SEC;
		return;
	}

	const DWORD dwNow = CTimer::Instance().GetCurrentMillisecond();
	if (dwNow <= m_dwSpawnTimeMSec)
	{
		dwMinRemainSec = RESOURCE_DESPAWN_MIN_SEC;
		dwMaxRemainSec = RESOURCE_DESPAWN_MAX_SEC;
		return;
	}

	const DWORD dwElapsedSec = (dwNow - m_dwSpawnTimeMSec) / 1000;
	dwMinRemainSec = (dwElapsedSec >= RESOURCE_DESPAWN_MIN_SEC) ? 0 : (RESOURCE_DESPAWN_MIN_SEC - dwElapsedSec);
	dwMaxRemainSec = (dwElapsedSec >= RESOURCE_DESPAWN_MAX_SEC) ? 0 : (RESOURCE_DESPAWN_MAX_SEC - dwElapsedSec);
}
#endif

C) In __Initialize() reset block:
#ifdef ENABLE_RESOURCE_DESPAWN_TIMER
	m_dwSpawnTimeMSec = 0;
	m_dwResourceDespawnRemainSec = 0;
	m_dwResourceDespawnSyncTimeMSec = 0;
	m_bUseExactResourceDespawnTime = false;
#endif

==================================================
8) PYTHONTEXTTAIL.H
==================================================

File: Source/Binary/source/UserInterface/PythonTextTail.h

A) In STextTail fields:
#ifdef ENABLE_RESOURCE_DESPAWN_TIMER
	std::string stOriginalText;
	DWORD dwLastResourceRemainSec;
	bool bHasResourceTimerText;
#endif

B) In class declarations:
#ifdef ENABLE_RESOURCE_DESPAWN_TIMER
	void RefreshResourceTimerText(TTextTail* pTextTail);
#endif

==================================================
9) PYTHONTEXTTAIL.CPP
==================================================

File: Source/Binary/source/UserInterface/PythonTextTail.cpp

A) In character text-tail update loop:
#ifdef ENABLE_RESOURCE_DESPAWN_TIMER
	RefreshResourceTimerText(pTextTail);
#endif

B) In RegisterTextTail(...) initialize timer state:
#ifdef ENABLE_RESOURCE_DESPAWN_TIMER
	pTextTail->stOriginalText = c_szText;
	pTextTail->dwLastResourceRemainSec = 0xFFFFFFFF;
	pTextTail->bHasResourceTimerText = false;
#endif

C) Add method body:

#ifdef ENABLE_RESOURCE_DESPAWN_TIMER
void CPythonTextTail::RefreshResourceTimerText(TTextTail* pTextTail)
{
	if (!pTextTail)
		return;

	CInstanceBase* pCharacterInstance = CPythonCharacterManager::Instance().GetInstancePtr(pTextTail->dwVirtualID);
	if (!pCharacterInstance)
		return;

	if (!pCharacterInstance->IsResource())
	{
		if (pTextTail->bHasResourceTimerText)
		{
			pTextTail->pTextInstance->SetValue(pTextTail->stOriginalText.c_str());
			pTextTail->pTextInstance->Update();
			pTextTail->bHasResourceTimerText = false;
			pTextTail->dwLastResourceRemainSec = 0xFFFFFFFF;
		}
		return;
	}

	DWORD dwMinRemainSec = 0;
	DWORD dwMaxRemainSec = 0;
	pCharacterInstance->GetResourceRemainSecondsRange(dwMinRemainSec, dwMaxRemainSec);

	if (dwMaxRemainSec == 0)
	{
		if (pTextTail->bHasResourceTimerText)
		{
			pTextTail->pTextInstance->SetValue(pTextTail->stOriginalText.c_str());
			pTextTail->pTextInstance->Update();
			pTextTail->bHasResourceTimerText = false;
			pTextTail->dwLastResourceRemainSec = 0xFFFFFFFF;
		}
		return;
	}

	if (pTextTail->bHasResourceTimerText && pTextTail->dwLastResourceRemainSec == dwMaxRemainSec)
		return;

	const DWORD dwMinMin = dwMinRemainSec / 60;
	const DWORD dwMinSec = dwMinRemainSec % 60;
	const DWORD dwMaxMin = dwMaxRemainSec / 60;
	const DWORD dwMaxSec = dwMaxRemainSec % 60;

	char szTimerText[256];
	if (dwMinRemainSec == dwMaxRemainSec)
		snprintf(szTimerText, sizeof(szTimerText), "%s [%u dk %u sn]", pTextTail->stOriginalText.c_str(), dwMaxMin, dwMaxSec);
	else
		snprintf(szTimerText, sizeof(szTimerText), "%s [%u dk %u sn - %u dk %u sn]", pTextTail->stOriginalText.c_str(), dwMinMin, dwMinSec, dwMaxMin, dwMaxSec);

	pTextTail->pTextInstance->SetValue(szTimerText);
	pTextTail->pTextInstance->Update();
	pTextTail->bHasResourceTimerText = true;
	pTextTail->dwLastResourceRemainSec = dwMaxRemainSec;
}
#endif

==================================================
10) BUILD / TEST
==================================================

- Packet changed => build BOTH server and client.
- Test:
  1) spawn mineral
  2) timer visible
  3) exact timer mode shows single value
  4) fallback mode shows range
  5) mineral disappears near expected timeout

==================================================
11) HARD FAIL CHECKLIST (BEFORE RUN)
==================================================

- ENABLE_RESOURCE_DESPAWN_TIMER defined on both sides.
- packet_add_char field position identical server/client.
- RESOURCE_DESPAWN_MIN_SEC/MAX_SEC exists.
- RegisterTextTail init block exists.
- No duplicate method definitions in InstanceBase.cpp.
