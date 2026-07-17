Include("\\script\\global\\nobitaxd\\vdk\\simcity\\config.lua")
Include("\\script\\global\\nobitaxd\\vdk\\simcity\\libs\\index.lua")
Include("\\script\\global\\nobitaxd\\vdk\\simcity\\components\\sim.movement.lua")
Include("\\script\\global\\nobitaxd\\vdk\\simcity\\components\\sim.fun.lua")
Include("\\script\\global\\nobitaxd\\vdk\\simcity\\components\\sim.entity.lua")
Include("\\script\\global\\nobitaxd\\vdk\\simcity\\components\\sim.fight.lua")
IncludeLib("NPCINFO")
SimCore = {
    fighterList = {},
    counter = 1,
    removedIds = {},
    currentProcessGroup = 1,
    totalFighters = 0
}

function SimCore:Get(nListId)
    return self.fighterList[nListId]
end


function SimCore:initCharConfig(config)
    -- Init stats
    config.isFighting = 0
    config.tick_breath = 0
    config.tick_canWalk = 0
    config.tick_canswitch = 0
    config.tick_canCast = 0
    config.camp = config.camp or random(1, 3)
    config.noRevive = config.noRevive or 0   
    config.fightingScore = 0
    config.rank = 1
    config.ngoaitrang = config.ngoaitrang or 0
    config.capHP = config.capHP or 1
    config.level = config.level or 95
    config.isAttackable = config.isAttackable or 0
    if config.capHP and config.capHP ~= "auto" then
        config.maxHP = random(SIMBOT_HP_MIN or 60000, SIMBOT_HP_MAX or 120000)  
    end
    config.parentAppointPos = {0, 0}
    config.walkMode = config.walkMode or "random"
    config.isAttractionAround = 0
    config.isPlayerEnemyAround = 0

    -- Phai nhan vat?
    if not config.faction and SimCityPhai.id2phai[config.nNpcId] then
        config.faction = SimCityPhai.id2phai[config.nNpcId]

        if (config.faction == "thienvuong" or config.faction == "thieulam") then
            config.series = 0
        end

        if (config.faction == "ngudoc" or config.faction == "duongmon") then
            config.series = 1
        end

        if (config.faction == "ngami" or config.faction == "thuyyen") then
            config.series = 2
        end

        if (config.faction == "caibang" or config.faction == "thiennhan") then
            config.series = 3
        end

        if (config.faction == "vodang" or config.faction == "conlon") then
            config.series = 4
        end
        
        
        
        
    end

    if not config.faction then
        local _phais = {"thienvuong","thieulam","ngudoc","duongmon","ngami","thuyyen","caibang","thiennhan","vodang","conlon"}
        config.faction = _phais[random(1, getn(_phais))]
    end

    if config.series == nil then
        config.series = random(0,4)
    end

    if config.faction then
        if (SimCityPhai[config.faction] and SimCityPhai[config.faction].knownIds[config.nNpcId]) then
       
            config.series = SimCityPhai[config.faction].knownIds[config.nNpcId].series

            if SimCityPhai[config.faction].knownIds[config.nNpcId].gen == 1 then
                config.nSettingsIdx = -1
            elseif SimCityPhai[config.faction].knownIds[config.nNpcId].gen == 2 then
                config.nSettingsIdx = -2
            end

        end   
        if SimCityPhai[config.faction] and SimCityPhai[config.faction].noCast and getn(SimCityPhai[config.faction].noCast) > 0 then
            config.skillHoTro = random(1, getn(SimCityPhai[config.faction].noCast))
        end
       
        if config.nSettingsIdx == nil then config.nSettingsIdx = random(-2, -1) end
        if config.faction == "thienvuong" or config.faction == "thieulam" then config.nSettingsIdx = -1  
        elseif config.faction == "ngami" or config.faction == "thuyyen" then config.nSettingsIdx = -2 end       
        local _tmpl = SimCityNPCInfo and SimCityNPCInfo.ALLNPCs_INFO and SimCityNPCInfo.ALLNPCs_INFO["n"..config.nNpcId]
        if _tmpl and _tmpl.series ~= nil then
            config.series = _tmpl.series
            if _tmpl.series == 0 then config.nSettingsIdx = -1 elseif _tmpl.series == 2 then config.nSettingsIdx = -2 end
        end       
            if not SimBotSW then
                SimBotSW = {
                    thieulam   = {{318,"taykhong"},{319,"con"},{321,"dao"}},
                    thienvuong = {{322,"dao"},{323,"thuong"},{325,"chuy"}},
                    duongmon   = {{339,"taykhong"},{342,"taykhong"},{302,"taykhong"}},  
                    ngudoc     = {{353,"any"},{355,"dao"}},
                    ngami      = {{328,"kiem"},{380,"any"}},
                    thuyyen    = {{336,"dao"},{337,"songdao"}},
                    caibang    = {{357,"any"},{359,"con"}},
                    thiennhan  = {{361,"thuong"},{362,"any"}},
                    vodang     = {{365,"any"},{368,"kiem"}},
                    conlon     = {{372,"dao"},{375,"kiem"}}
                }
                SimBotWID = {
                    taykhong = {0},
                    kiem = {20}, dao = {23}, thuong = {24},
                    con = {26}, songdao = {28}, chuy = {30}
                }
                SimBotDebuff = { ngudoc = {72, 73, 390} } 
                SimBotSkill50 = {  
                    [318]=218,[319]=11,[321]=19, [322]=32,[323]=41,[325]=324, [339]=249,[342]=341,[302]=228,
                    [353]=71,[355]=74, [328]=88,[380]=91, [336]=108,[337]=111, [357]=128,[359]=125,
                    [361]=142,[362]=148, [365]=165,[368]=267, [372]=176,[375]=182 }
                SimBotNpc = {  
                    [1906]={322,"dao"},[1907]={323,"thuong"},[1908]={318,"taykhong"},[1909]={321,"dao"},
                    [1910]={339,"taykhong"},[1911]={342,"taykhong"},[1912]={353,"dao"},[1913]={355,"dao"},
                    [1914]={328,"kiem"},[1915]={380,"kiem"},[1916]={336,"dao"},[1917]={337,"songdao"},
                    [1918]={357,"con"},[1919]={359,"con"},[1920]={361,"thuong"},[1921]={362,"thuong"},
                    [1922]={365,"kiem"},[1923]={368,"kiem"},[1924]={372,"dao"},
                    [2000]={318,"taykhong"},[2001]={319,"con"},[2002]={321,"dao"},[2003]={322,"dao"},[2004]={323,"thuong"},[2005]={325,"chuy"},
                    [2006]={339,"taykhong"},[2007]={342,"taykhong"},[2008]={302,"taykhong"},[2009]={302,"taykhong"},[2010]={353,"any"},[2011]={355,"dao"},  
                    [2012]={328,"kiem"},[2013]={380,"any"},[2014]={336,"dao"},[2015]={337,"songdao"},[2016]={357,"any"},[2017]={359,"con"},
                    [2018]={361,"thuong"},[2019]={362,"any"},[2020]={365,"any"},[2021]={368,"kiem"},[2022]={372,"dao"},[2023]={375,"kiem"}
                }
            end
            local _sw = SimBotSW[config.faction]
            local _np = SimBotNpc[config.nNpcId]   
            local _p = _np or (_sw and _sw[random(1, getn(_sw))])
            if _p then
                config.skillCastBua = {_p[1], 20}
                if config.faction == "duongmon" then config.skill351 = 351 end                  
                if SimBotDebuff[config.faction] then config.skillDebuffList = SimBotDebuff[config.faction] end
                if _p[2] ~= "any" then
                    local _w = SimBotWID[_p[2]]
                    if _w then config.nNewWeaponType = _w[random(1, getn(_w))] end
                end
            end

    end
   
    if config.series == 0 then
        config.nSettingsIdx = -1
    elseif config.series == 2 then
        config.nSettingsIdx = -2
    end
    
    if config.nSettingsIdx ~= -1 and config.nSettingsIdx ~= -2 then
        config.nSettingsIdx = (random(1,2) == 1) and -1 or -2
    end

    -- Setup movement behavior    
    config.movementSys = SimMovementSys(config)
    config.funSys = SimFunSys(config)
    config.entitySys = SimEntitySys(config)
    config.fightSys = SimFightSys(config)


end


function SimCore:Remove(nListId)
    local tbNpc = self.fighterList[nListId]
    if tbNpc then
        DelNpcSafe(tbNpc.finalIndex)

        if tbNpc.children then
            for i = 1, getn(tbNpc.children) do
                self:Remove(tbNpc.children[i])
            end
        end

        self.fighterList[nListId] = nil
        tinsert(self.removedIds, nListId)
        
        -- Decrement total fighters
        self.totalFighters = self.totalFighters - 1
    end
end

function SimCore:OnDeath(nListId, nNpcIndex, attackerIndex)
    local tbNpc = self.fighterList[nListId]
    if tbNpc == nil then
        return 0
    end
  
    if tbNpc.duelPlayerId then SimDuelEnd(tbNpc); tbNpc.resetPosWhenRevive = 1 end
    if tbNpc.partyPlayerId then PartyEnd(tbNpc); tbNpc.resetPosWhenRevive = 1 end   

    tbNpc.entitySys:OnDeath(self, tbNpc, nNpcIndex, attackerIndex)    
end


SIMBOT_MELEE_SKILLS = {[318]=1,[319]=1,[322]=1,[323]=1,[325]=1,[361]=1,[368]=1}
SIMBOT_DISMOUNT_SKILLS = {[318]=1,[319]=1,[323]=1,[325]=1,[328]=1,[380]=1,[336]=1,[337]=1,[339]=1,[342]=1,[351]=1,[353]=1,[357]=1,[359]=1,[362]=1,[365]=1,[368]=1,[372]=1,[375]=1}
SIM_DIR8X = {1, 1, 0, -1, -1, -1, 0, 1}   
SIM_DIR8Y = {0, 1, 1, 1, 0, -1, -1, -1}
SIMBOT_RANGED_DIST = 12  
SIMBOT_MELEE_DIST  = 2  
SIMBOT_SKILL_RANGE = {  
    [318]=2,[319]=2,[321]=12,                  -- thieulam
    [322]=2,[323]=2,[325]=2,                   -- thienvuong (3 melee)
    [339]=11,[342]=11,[302]=14,[351]=1,        -- duongmon (351 bom dat phu tro)
    [353]=13,[355]=5,[72]=13,[73]=13,[390]=13, -- ngudoc (chinh + debuff)
    [328]=11,[380]=12,                         -- ngami
    [336]=11,[337]=7,                          -- thuyyen
    [357]=12,[359]=12,                         -- caibang
    [361]=1,[362]=13,                          -- thiennhan
    [365]=14,[368]=2,                          -- vodang
    [372]=12,[375]=14,                         -- conlon
}
function SimBotCastDist(tbNpc)
    local s = tbNpc.skillCastBua and tbNpc.skillCastBua[1]
    if s and SIMBOT_SKILL_RANGE[s] then return SIMBOT_SKILL_RANGE[s] end   
    if s and SIMBOT_MELEE_SKILLS[s] then return SIMBOT_MELEE_DIST end
    return SIMBOT_RANGED_DIST
end

function SimPickSkill(tbNpc, noDebuff)   
    if not noDebuff and tbNpc.skillDebuffList and getn(tbNpc.skillDebuffList) > 0 then
        if not tbNpc.debuffResetTick or tbNpc.debuffResetTick <= tbNpc.tick_breath then
            tbNpc.debuffIdx = 1
            tbNpc.debuffResetTick = tbNpc.tick_breath + 60*18/REFRESH_RATE   
        end
        tbNpc.debuffIdx = tbNpc.debuffIdx or 1
        if tbNpc.debuffIdx <= getn(tbNpc.skillDebuffList) then
            local id = tbNpc.skillDebuffList[tbNpc.debuffIdx]
            tbNpc.debuffIdx = tbNpc.debuffIdx + 1
            return {id, 20}
        end
    end
   
    if tbNpc.skill351 and random(1, 100) <= 40 then
        return {tbNpc.skill351, 20}
    end
    local sk = tbNpc.skillCastBua  
    if tbNpc.skillCastBua2 then   
        if tbNpc.bua2Toggle then sk = tbNpc.skillCastBua2 end   
        tbNpc.bua2Toggle = not tbNpc.bua2Toggle                
    end
    if not sk and tbNpc.faction and SimCityPhai[tbNpc.faction] and SimCityPhai[tbNpc.faction].normalCast and getn(SimCityPhai[tbNpc.faction].normalCast) > 0 then
        sk = SimCityPhai[tbNpc.faction].normalCast[random(1, getn(SimCityPhai[tbNpc.faction].normalCast))]
    end
    return sk
end

function SimDuelEnd(tbNpc)
    if BotDuelDisarm and tbNpc.finalIndex then BotDuelDisarm(tbNpc.finalIndex) end   
    if SetNpcDuelEnd and tbNpc.finalIndex and tbNpc.finalIndex > 0 then
        SetNpcDuelEnd(tbNpc.finalIndex, (tbNpc.duelPlayerId and PIdx2NpcIdx and PIdx2NpcIdx(tbNpc.duelPlayerId)) or 0)
    end
    tbNpc.duelPlayerId = nil
    tbNpc.duelCombatSet = nil
    tbNpc.selfDefDuel = nil  
    tbNpc.selfDefTick = nil
    tbNpc.isPlayerEnemyAround = 0 
    tbNpc.isFighting = 0
    if SetNpcCombat and tbNpc.finalIndex and tbNpc.finalIndex > 0 then SetNpcCombat(tbNpc.finalIndex, 0, 0) end   
    tbNpc.plLastTX = nil; tbNpc.plLastTY = nil   
    if tbNpc.duelOldCamp ~= nil then
        tbNpc.camp = tbNpc.duelOldCamp
        if SetNpcCurCamp and tbNpc.finalIndex and tbNpc.finalIndex > 0 then SetNpcCurCamp(tbNpc.finalIndex, tbNpc.duelOldCamp) end
        tbNpc.duelOldCamp = nil
    end
    return 0
end

SIMBOT_TAUNT_Q = SIMBOT_TAUNT_Q or {}
SIMBOT_TAUNT_NEXT = SIMBOT_TAUNT_NEXT or 0

function SimBotTaunt(tbNpc)  
    if not tbNpc.finalIndex or tbNpc.finalIndex <= 0 then return end
    if not SimCityChat or not SimCityChat["rep_chui"] or getn(SimCityChat["rep_chui"]) <= 0 then return end
    local _qn = getn(SIMBOT_TAUNT_Q)
    if _qn >= 12 then return end   
    SIMBOT_TAUNT_Q[_qn + 1] = tbNpc.finalIndex
end

function SimBotTauntDrain(gclock)
    if getn(SIMBOT_TAUNT_Q) <= 0 then return end
    if gclock < SIMBOT_TAUNT_NEXT then return end
    local _idx = SIMBOT_TAUNT_Q[1]
    local _qn = getn(SIMBOT_TAUNT_Q)
    for _qi = 1, _qn - 1 do SIMBOT_TAUNT_Q[_qi] = SIMBOT_TAUNT_Q[_qi + 1] end
    SIMBOT_TAUNT_Q[_qn] = nil
    SIMBOT_TAUNT_NEXT = gclock + (1 + random(0, 1)) / REFRESH_RATE  
    if _idx and _idx > 0 and NpcChat and SimCityChat and SimCityChat["rep_chui"] and getn(SimCityChat["rep_chui"]) > 0 then
        local _gx = GetNpcPos and GetNpcPos(_idx)  
        if _gx then NpcChat(_idx, SimCityChat["rep_chui"][random(1, getn(SimCityChat["rep_chui"]))]) end
    end
end

function PartyEnd(tbNpc)
    if BotDuelDisarm and tbNpc.finalIndex and tbNpc.finalIndex > 0 then BotDuelDisarm(tbNpc.finalIndex) end   
    tbNpc.partyArmTick = nil
    if PartyClear and tbNpc.finalIndex and tbNpc.finalIndex > 0 then PartyClear(tbNpc.finalIndex) end
    if tbNpc.partyOldCamp ~= nil then
        tbNpc.camp = tbNpc.partyOldCamp
        if SetNpcCurCamp and tbNpc.finalIndex and tbNpc.finalIndex > 0 then SetNpcCurCamp(tbNpc.finalIndex, tbNpc.partyOldCamp) end
        tbNpc.partyOldCamp = nil
    end
    if SetBotSpeed and tbNpc.finalIndex and tbNpc.finalIndex > 0 then SetBotSpeed(tbNpc.finalIndex, SIMBOT_WALK_SPEED or 15, SIMBOT_RUN_SPEED or 24) end  
    tbNpc.partyPlayerId = nil
    tbNpc.partyFarTicks = nil
    tbNpc.partyTarget = nil
    tbNpc.partyHuntCamp = nil
    return 0
end

function SimPartyFollow(simInstance, tbNpc)
    if not tbNpc.finalIndex or tbNpc.finalIndex == 0 then return PartyEnd(tbNpc) end
    local pID = tbNpc.partyPlayerId
    if not pID or pID <= 0 then return PartyEnd(tbNpc) end
    if PollParty and PollParty(tbNpc.finalIndex) <= 0 then return PartyEnd(tbNpc) end 
    if PartyRebind and (not tbNpc.partyIconFixN or tbNpc.partyIconFixN < 2) then   
        if not tbNpc.partyIconFixTick then tbNpc.partyIconFixTick = tbNpc.tick_breath + 4*18/REFRESH_RATE end
        if tbNpc.tick_breath >= tbNpc.partyIconFixTick then
            PartyRebind(tbNpc.finalIndex, tbNpc.finalIndex, pID)
            tbNpc.partyIconFixN = (tbNpc.partyIconFixN or 0) + 1
            tbNpc.partyIconFixTick = tbNpc.tick_breath + 4*18/REFRESH_RATE   
        end
    end
    if PIdx2NpcIdx and NPCINFO_GetNpcCurrentLife then   
        local _pnpc = PIdx2NpcIdx(pID)
        if _pnpc and _pnpc > 0 then
            local _plife = NPCINFO_GetNpcCurrentLife(_pnpc)
            if _plife and _plife <= 0 then
                tbNpc.partyDead = (tbNpc.partyDead or 0) + 1
                if tbNpc.partyDead >= 2 then return PartyEnd(tbNpc) end  
            else tbNpc.partyDead = 0 end
        end
    end
    local pW, pX, pY = CallPlayerFunction(pID, GetWorldPos)
    if not pX or not pY then   
        tbNpc.partyMiss = (tbNpc.partyMiss or 0) + 1
        if tbNpc.partyMiss > 90 then return PartyEnd(tbNpc) end   
        return 0
    end
    tbNpc.partyMiss = 0
    local nX32, nY32, nW32 = GetNpcPos(tbNpc.finalIndex)
    if not nX32 then
        tbNpc.partyMiss = (tbNpc.partyMiss or 0) + 1
        if tbNpc.partyMiss > 90 then return PartyEnd(tbNpc) end
        return 0
    end
    if SubWorldIdx2ID(nW32) ~= pW then        
        local _oldIdx = tbNpc.finalIndex
        tbNpc.nMapId = pW
        tbNpc.isFighting = 0
        tbNpc.partyTarget = nil
        tbNpc.lastPos = nil
        DelNpcSafe(_oldIdx)
        tbNpc.finalIndex = nil
        tbNpc.entitySys:CreateChar(simInstance, tbNpc, 0, pX*32, pY*32)
        if not tbNpc.finalIndex or tbNpc.finalIndex <= 0 then return PartyEnd(tbNpc) end   
        tbNpc.botLvSet = nil   
        if SetBotSpeed then SetBotSpeed(tbNpc.finalIndex, SIMBOT_WALK_SPEED or 15, SIMBOT_RUN_SPEED or 24) end  
        if PartyRebind then PartyRebind(_oldIdx, tbNpc.finalIndex, pID) end   
        return 1
    end
    local myX = floor(nX32 / 32)
    local myY = floor(nY32 / 32)    
    local _tgt = tbNpc.partyTarget
    if BotDoSkill then
        if not tbNpc.partyScanTick or tbNpc.partyScanTick <= tbNpc.tick_breath then
            tbNpc.partyScanTick = tbNpc.tick_breath + 4*18/REFRESH_RATE
            local _e = 0       
            if SimEnemyAround and (not SimCityIsPeaceZone or SimCityIsPeaceZone(tbNpc) ~= 1) then
                _e = SimEnemyAround(tbNpc.finalIndex, 12) or 0
            end            
            if (not _e or _e <= 0) and GetAroundNpcList and pID and GetNpcKind then
                local _list, _n = CallPlayerFunction(pID, GetAroundNpcList, 16)
                if _list and _n then
                    for _i = 1, _n do
                        local _cand = _list[_i]
                        if _cand and _cand ~= tbNpc.finalIndex and GetNpcKind(_cand) == 0 and (not GetNpcParam or GetNpcParam(_cand, 4) ~= 1) then
                            _e = _cand; break
                        end
                    end
                end
            end
            if _e and _e > 0 then tbNpc.partyTarget = _e; tbNpc.partyTargetTick = tbNpc.tick_breath + 10*18/REFRESH_RATE
            elseif tbNpc.partyTargetTick and tbNpc.partyTargetTick <= tbNpc.tick_breath then tbNpc.partyTarget = nil end
            _tgt = tbNpc.partyTarget
        end
    else
        tbNpc.partyTarget = nil; _tgt = nil
    end

    if SimBotTranPhai then SimBotTranPhai(simInstance, tbNpc) end
    if _tgt and _tgt > 0 then
        local tx32, ty32, tw32 = GetNpcPos(_tgt)
        if not tx32 or nW32 ~= tw32 then tbNpc.partyTarget = nil
        else
            local tX = floor(tx32 / 32)
            local tY = floor(ty32 / 32)
            if GetDistanceRadius(tX, tY, pX, pY) > 20 then tbNpc.partyTarget = nil  
            else
                local _cd = SimBotCastDist(tbNpc)
                local _td = GetDistanceRadius(myX, myY, tX, tY)
                if SetNpcLevel and not tbNpc.botLvSet then tbNpc.botLvSet = 1; SetNpcLevel(tbNpc.finalIndex, SIMBOT_LEVEL) end
                
                if IsAttackableCamp and GetNpcCurCamp and SetNpcCurCamp then
                    local _tc = GetNpcCurCamp(_tgt) or 0
                    if IsAttackableCamp(tbNpc.camp or 0, _tc) ~= 1 then
                        local _ac = (_tc == 0) and 5 or (((tbNpc.camp or 0) == _tc) and (_tc == 1 and 2 or 1) or 5)
                        if GetNpcCurCamp(tbNpc.finalIndex) ~= _ac then SetNpcCurCamp(tbNpc.finalIndex, _ac); tbNpc.partyHuntCamp = 1 end
                    elseif tbNpc.partyHuntCamp and GetNpcCurCamp(tbNpc.finalIndex) ~= (tbNpc.camp or 0) then
                        SetNpcCurCamp(tbNpc.finalIndex, tbNpc.camp or 0); tbNpc.partyHuntCamp = nil
                    end
                end
                tbNpc.isFighting = 1; tbNpc.botFighting = 1
                if SetNpcCombat and (not tbNpc.botCombatTick or tbNpc.botCombatTick <= tbNpc.tick_breath) then
                    SetNpcCombat(tbNpc.finalIndex, 1, tbNpc.skillCastBua and tbNpc.skillCastBua[1] or 0)
                    tbNpc.botCombatTick = tbNpc.tick_breath + 2
                end
                SimBotTranPhai(simInstance, tbNpc)                 
                if _td > _cd and _td < 40 then
                    if BotDuelDisarm and tbNpc.partyArmTick then BotDuelDisarm(tbNpc.finalIndex); tbNpc.partyArmTick = nil end
                    if NpcRun then NpcRun(tbNpc.finalIndex, tX, tY) end
                elseif _td <= _cd and SimPickSkill and (BotDuelArm or BotDoSkill) and (not tbNpc.partyArmTick or tbNpc.partyArmTick <= tbNpc.tick_breath) then
                    local sk = SimPickSkill(tbNpc)  
                    if sk and sk[1] and sk[1] > 0 then
                        if SetNpcLevel then SetNpcLevel(tbNpc.finalIndex, SIMBOT_LEVEL) end
                        if SetNpcAtkSpeed then SetNpcAtkSpeed(tbNpc.finalIndex, SIMBOT_ATKSPEED) end
                        tbNpc.partyArmTick = tbNpc.tick_breath + 1
                        if BotDuelArm then
                            BotDuelArm(tbNpc.finalIndex, _tgt, sk[1], sk[2] or 20) 
                        else
                            local _gd = GetNpcDoing and GetNpcDoing(tbNpc.finalIndex) or 1   
                            if _gd ~= 6 and _gd ~= 7 then BotDoSkill(tbNpc.finalIndex, sk[1], sk[2] or 20, _tgt) end
                        end
                    end
                end
                return 1
            end
        end
    end
    if tbNpc.botFighting == 1 then tbNpc.isFighting = 0; tbNpc.botFighting = nil end  
    if BotDuelDisarm and tbNpc.partyArmTick then BotDuelDisarm(tbNpc.finalIndex); tbNpc.partyArmTick = nil end   
    if tbNpc.partyHuntCamp and SetNpcCurCamp then SetNpcCurCamp(tbNpc.finalIndex, tbNpc.camp or 0); tbNpc.partyHuntCamp = nil end   
    local _oct = mod(tbNpc.finalIndex, 8) + 1   
    local _tx = pX + SIM_DIR8X[_oct] * 2
    local _ty = pY + SIM_DIR8Y[_oct] * 2
    if GetDistanceRadius(myX, myY, _tx, _ty) > 1 and NpcRun then
        NpcRun(tbNpc.finalIndex, _tx, _ty)
    end
    return 0
end
function SimDuelMove(simInstance, tbNpc)
    if not tbNpc.finalIndex or tbNpc.finalIndex == 0 then return SimDuelEnd(tbNpc) end
    local pID = tbNpc.duelPlayerId
    if not pID or pID <= 0 then return SimDuelEnd(tbNpc) end   
    if tbNpc.selfDefDuel == 1 and tbNpc.mode == "train" then
        local _rnx, _rny = GetNpcPos(tbNpc.finalIndex)
        local _far = tbNpc.goX32 and tbNpc.goY32 and _rnx and (GetDistanceRadius(floor(_rnx / 32), floor(_rny / 32), floor(tbNpc.goX32 / 32), floor(tbNpc.goY32 / 32)) > 20)
        if _far or (SimCityIsPeaceZone and SimCityIsPeaceZone(tbNpc) == 1) then
            SimBotTaunt(tbNpc)
            if NpcRun and tbNpc.goX32 and tbNpc.goY32 then NpcRun(tbNpc.finalIndex, floor(tbNpc.goX32 / 32), floor(tbNpc.goY32 / 32)) end
            return SimDuelEnd(tbNpc)
        end
    end
   
    if tbNpc.selfDefDuel ~= 1 and tbNpc.worldInfo and tbNpc.worldInfo.cityPeace == 1
       and SimCityIsInCity and SimCityIsPeaceZone and SimCityIsPeaceZone(tbNpc) ~= 1 then
        local _dpW, _dpX, _dpY = CallPlayerFunction(pID, GetWorldPos)
        if _dpX and _dpY and SimCityIsInCity(tbNpc.worldInfo, _dpX, _dpY) == 1 then
            SimBotTaunt(tbNpc)
            return SimDuelEnd(tbNpc)
        end
    end    
    if tbNpc.selfDefDuel == 1 and SimCityIsPeaceZone and SimCityIsPeaceZone(tbNpc) == 1 then SimBotTaunt(tbNpc); return SimDuelEnd(tbNpc) end    
    if tbNpc.selfDefDuel == 1 and GetPlayerPkMode and PIdx2NpcIdx then   
        local _ppk = PIdx2NpcIdx(pID)
        if _ppk and _ppk > 0 and GetPlayerPkMode(_ppk) == 0 then return SimDuelEnd(tbNpc) end
    end
    tbNpc.duelTicks = (tbNpc.duelTicks or 0) - 1
    if tbNpc.duelTicks <= 0 then return SimDuelEnd(tbNpc) end   
    if nil and tbNpc.selfDefDuel == 1 and (not tbNpc.selfDefTick or tbNpc.selfDefTick <= tbNpc.tick_breath) then        
        local _fw, _fx, _fy = CallPlayerFunction(pID, GetWorldPos)
        if _fx and _fy then
            local _fnx, _fny = GetNpcPos(tbNpc.finalIndex)
            if GetDistanceRadius(floor(_fnx / 32), floor(_fny / 32), _fx, _fy) >= 6 then SimBotTaunt(tbNpc) end
        end
        return SimDuelEnd(tbNpc)
    end
    local pW, pX, pY = CallPlayerFunction(pID, GetWorldPos)
    if not pX or not pY then return SimDuelEnd(tbNpc) end 
    local nX32, nY32, nW32 = GetNpcPos(tbNpc.finalIndex)
    if SubWorldIdx2ID(nW32) ~= pW then return SimDuelEnd(tbNpc) end
    local myX = floor(nX32 / 32)
    local myY = floor(nY32 / 32)
    local dist = GetDistanceRadius(myX, myY, pX, pY)
    local _castDist = SimBotCastDist(tbNpc)     
    local _melee = (tbNpc.skillCastBua and SIMBOT_MELEE_SKILLS[tbNpc.skillCastBua[1]]) and true or false
    local _hold = _melee and 1 or (_castDist - 2)
    if _hold < 1 then _hold = 1 end
    local _holdMin = _melee and 0 or (_hold - 2)
    if _holdMin < 0 then _holdMin = 0 end
    local _inBand = (dist <= _castDist) and (dist >= _holdMin)
    local _bandX, _bandY = myX, myY
    if dist > 0 then
        _bandX = pX + floor((myX - pX) * _hold / dist)
        _bandY = pY + floor((myY - pY) * _hold / dist)
    end

    local _canFight = (SimCityCanFight and SimCityCanFight(tbNpc) == 1)
    tbNpc.isPlayerEnemyAround = _canFight and pID or 0
   
    if SetNpcCombat and _canFight and (not tbNpc.duelCombatTick or tbNpc.duelCombatTick <= tbNpc.tick_breath) then
        SetNpcCombat(tbNpc.finalIndex, 1, tbNpc.skillCastBua and tbNpc.skillCastBua[1] or 0)
        tbNpc.duelCombatTick = tbNpc.tick_breath + 2
    end
    if tbNpc.selfDefDuel == 1 and _canFight and BotMountSync and BotPlayerMove then
        if not tbNpc.plProto75Tick or tbNpc.plProto75Tick <= tbNpc.tick_breath then
            BotMountSync(tbNpc.finalIndex, 0)   
            tbNpc.plProto75Tick = tbNpc.tick_breath + 6
        end
        if (not _inBand) and (tbNpc.plLastTX ~= _bandX or tbNpc.plLastTY ~= _bandY) then
            BotPlayerMove(tbNpc.finalIndex, _bandX*32, _bandY*32)   
            tbNpc.plLastTX = _bandX; tbNpc.plLastTY = _bandY
        end
    end
    if tbNpc.isFighting == 1 then
        if _canFight then      
            local _notCasting = true
            if GetNpcDoing then local _gd = GetNpcDoing(tbNpc.finalIndex); _notCasting = (_gd ~= 6 and _gd ~= 7) end   
            if (BotDuelArm or BotDoSkill) and PIdx2NpcIdx and _inBand and (not tbNpc.duelArmTick or tbNpc.duelArmTick <= tbNpc.tick_breath) then   
                
                local sk = SimPickSkill(tbNpc)  
                if sk and sk[1] and sk[1] > 0 then
                    local _tn = PIdx2NpcIdx(pID)
                    if _tn and _tn > 0 then
                        if SetNpcAtkSpeed then SetNpcAtkSpeed(tbNpc.finalIndex, SIMBOT_ATKSPEED) end  
                        if SetNpcLevel then SetNpcLevel(tbNpc.finalIndex, SIMBOT_LEVEL) end 
                        tbNpc.duelArmTick = tbNpc.tick_breath + 1  
                        if BotDuelArm then   
                            BotDuelArm(tbNpc.finalIndex, _tn, sk[1], sk[2] or 20)   
                        else
                            local _gd = GetNpcDoing and GetNpcDoing(tbNpc.finalIndex) or 1  
                            if _gd ~= 6 and _gd ~= 7 then BotDoSkill(tbNpc.finalIndex, sk[1], sk[2] or 20, _tn) end
                        end
                    end
                end
            end
     
            if SetNpcCombat and (not tbNpc.duelCombatTick or tbNpc.duelCombatTick <= tbNpc.tick_breath) then
                SetNpcCombat(tbNpc.finalIndex, 1, tbNpc.skillCastBua and tbNpc.skillCastBua[1] or 0)
                tbNpc.duelCombatTick = tbNpc.tick_breath + 2
            end
    
            if SIMBOT_TRANPHAI == 1 and (not tbNpc.duelBuffTick or tbNpc.duelBuffTick <= tbNpc.tick_breath) then
                tbNpc.duelBuffTick = tbNpc.tick_breath + 60*18/REFRESH_RATE
                local _bc = tbNpc.faction and SimCityPhai[tbNpc.faction] and SimCityPhai[tbNpc.faction].needCast
                if not _bc or getn(_bc) == 0 then
                    local _fb = {ngami = {{92,20}}, ngudoc = {{69,20}}}
                    _bc = _fb[tbNpc.faction]
                end
                if _bc and getn(_bc) > 0 then
                    for _bi = 1, getn(_bc) do
                        if _bc[_bi][1] and _bc[_bi][1] > 0 then NpcCastSkill(tbNpc.finalIndex, _bc[_bi][1], _bc[_bi][2] or 20) end
                    end
                end
            end

            if not _inBand then
                if BotDuelDisarm then BotDuelDisarm(tbNpc.finalIndex) end  
                NpcRun(tbNpc.finalIndex, _bandX, _bandY)  
            end
        else
            if BotDuelDisarm then BotDuelDisarm(tbNpc.finalIndex) end   
            if dist > (DISTANCE_DUEL_FOLLOW or 2) then
                NpcRun(tbNpc.finalIndex, pX, pY)  
            end
        end
        return 1
    end
    if dist > 2 then
        local fx = pX + floor((myX - pX) * 2 / dist)
        local fy = pY + floor((myY - pY) * 2 / dist)
        NpcRun(tbNpc.finalIndex, fx, fy)  
    end

    if dist <= (DISTANCE_SUPPORT_PLAYER or 10) and _canFight and tbNpc.isFighting ~= 1 then
        tbNpc.isFighting = 1
        if SetNpcCombat then SetNpcCombat(tbNpc.finalIndex, 1, tbNpc.skillCastBua and tbNpc.skillCastBua[1] or 0) end
        tbNpc.tick_canswitch = tbNpc.tick_breath + random(tbNpc.TIME_FIGHTING_minTs or TIME_FIGHTING.minTs, tbNpc.TIME_FIGHTING_maxTs or TIME_FIGHTING.maxTs)
    end
    return 1
end

function SimBotTranPhai(simInstance, tbNpc)
    if not tbNpc.finalIndex or tbNpc.finalIndex <= 0 then return end  
    if tbNpc.fightSys and tbNpc.fightSys.BuffChar then tbNpc.fightSys:BuffChar(simInstance, tbNpc) end
    if SIMBOT_TRANPHAI == 1 and NpcCastSkill and (not tbNpc.tpBuffTick or tbNpc.tpBuffTick <= tbNpc.tick_breath) then
        tbNpc.tpBuffTick = tbNpc.tick_breath + 60*18/REFRESH_RATE
        local _bc = tbNpc.faction and SimCityPhai[tbNpc.faction] and SimCityPhai[tbNpc.faction].needCast
        if not _bc or getn(_bc) == 0 then
            local _fb = {ngami = {{92,20}}, ngudoc = {{69,20}}}
            _bc = _fb[tbNpc.faction]
        end
        if _bc and getn(_bc) > 0 then
            for _bi = 1, getn(_bc) do
                if _bc[_bi][1] and _bc[_bi][1] > 0 then NpcCastSkill(tbNpc.finalIndex, _bc[_bi][1], _bc[_bi][2] or 20) end
            end
        end
    end
end
function SimBotDuelMove(simInstance, tbNpc)
    local tIdx = tbNpc.botDuelTarget
    if not tIdx or tIdx <= 0 or not tbNpc.finalIndex or tbNpc.finalIndex == 0 then
        tbNpc.botDuelTarget = nil
        return tbNpc.movementSys:Move(simInstance, tbNpc)
    end
    if SimCityIsPeaceZone and SimCityIsPeaceZone(tbNpc) == 1 then   
        tbNpc.botDuelTarget = nil
        return tbNpc.movementSys:Move(simInstance, tbNpc)
    end
    local tx32, ty32, tw32 = GetNpcPos(tIdx)
    if not tx32 then tbNpc.botDuelTarget = nil; return tbNpc.movementSys:Move(simInstance, tbNpc) end
    local nx32, ny32, nw32 = GetNpcPos(tbNpc.finalIndex)
    if not nx32 then return 0 end
    if nw32 ~= tw32 then tbNpc.botDuelTarget = nil; return tbNpc.movementSys:Move(simInstance, tbNpc) end
    local tX = floor(tx32 / 32)
    local tY = floor(ty32 / 32)
    local myX = floor(nx32 / 32)
    local myY = floor(ny32 / 32)
    local dist = GetDistanceRadius(myX, myY, tX, tY)
    local _castDist = SimBotCastDist(tbNpc)
    if SetNpcLevel and not tbNpc.botLvSet then tbNpc.botLvSet = 1; SetNpcLevel(tbNpc.finalIndex, SIMBOT_LEVEL) end  
    tbNpc.isFighting = 1; tbNpc.botFighting = 1   
    if SetNpcCombat and (not tbNpc.botCombatTick or tbNpc.botCombatTick <= tbNpc.tick_breath) then
        SetNpcCombat(tbNpc.finalIndex, 1, tbNpc.skillCastBua and tbNpc.skillCastBua[1] or 0)   
        tbNpc.botCombatTick = tbNpc.tick_breath + 2
    end
    SimBotTranPhai(simInstance, tbNpc)       
    if tbNpc.faction == "ngudoc" and SetNpcAuraSkill and tbNpc.skillHoTro and SimCityPhai["ngudoc"] and SimCityPhai["ngudoc"].noCast[tbNpc.skillHoTro]
       and (not tbNpc.bvAuraTick or tbNpc.bvAuraTick <= tbNpc.tick_breath) then
        tbNpc.bvAuraTick = tbNpc.tick_breath + 5*18/REFRESH_RATE
        SetNpcAuraSkill(tbNpc.finalIndex, SimCityPhai["ngudoc"].noCast[tbNpc.skillHoTro][1], 1)
    end
    
    local _meleeBV = (tbNpc.skillCastBua and SIMBOT_MELEE_SKILLS and SIMBOT_MELEE_SKILLS[tbNpc.skillCastBua[1]]) and true or false
    local _holdBV = _meleeBV and 1 or (_castDist - 2)
    if _holdBV < 1 then _holdBV = 1 end
    local _holdMinBV = _meleeBV and 0 or (_holdBV - 2)
    if _holdMinBV < 0 then _holdMinBV = 0 end
    local _inBandBV = (dist <= _castDist) and (dist >= _holdMinBV)
    if (not _inBandBV) and dist > 0 and dist < 60 then
        local _bx = tX + floor((myX - tX) * _holdBV / dist)   
        local _by = tY + floor((myY - tY) * _holdBV / dist)
        if BotDuelDisarm then BotDuelDisarm(tbNpc.finalIndex) end   
        if tbNpc.bvRunTX ~= _bx or tbNpc.bvRunTY ~= _by then  
            tbNpc.bvRunTX = _bx; tbNpc.bvRunTY = _by
            NpcRun(tbNpc.finalIndex, _bx, _by)
        end
    end    
    if _inBandBV and NpcCastSkill and SimPickSkill and (not tbNpc.botCastTick or tbNpc.botCastTick <= tbNpc.tick_breath) then
        local sk = SimPickSkill(tbNpc, 1)  
        if sk and sk[1] and sk[1] > 0 then
            if SetNpcLevel then SetNpcLevel(tbNpc.finalIndex, SIMBOT_LEVEL) end   
            if SetNpcAtkSpeed then SetNpcAtkSpeed(tbNpc.finalIndex, SIMBOT_ATKSPEED) end
            local _gd = GetNpcDoing and GetNpcDoing(tbNpc.finalIndex) or 1   
            if _gd ~= 6 and _gd ~= 7 and BotDoSkill then BotDoSkill(tbNpc.finalIndex, sk[1], sk[2] or 20, tIdx) end  
            tbNpc.botCastTick = tbNpc.tick_breath + 1   
        end
    end
    return 1
end

function SimCore:OnTimer(tbNpc, rate)
  
    if (tbNpc.bangKeoxe and SetNpcBang and tbNpc.isDead ~= 1 and tbNpc.finalIndex and tbNpc.finalIndex > 0) then
        tbNpc.bangBcN = (tbNpc.bangBcN or 0) + 1
        if (tbNpc.bangBcN == 1 or tbNpc.bangBcN >= 12) then
            if (tbNpc.bangBcN >= 12) then tbNpc.bangBcN = 0 end
            SetNpcBang(tbNpc.finalIndex, tbNpc.bangKeoxe)
        end
    end
    
    if (tbNpc.finalIndex and tbNpc.finalIndex > 0 and tbNpc.isDead ~= 1) then
        
        if SetNpcPeace then
            if (not tbNpc.peaceTick or tbNpc.peaceTick <= tbNpc.tick_breath) then
                tbNpc.peaceTick = (tbNpc.tick_breath or 0) + 2   
                local _raw = (SimCityIsPeaceZone and SimCityIsPeaceZone(tbNpc) == 1) and 1 or 0   
                if tbNpc.peaceState == nil then
                    tbNpc.peaceState = _raw   
                elseif _raw == tbNpc.peaceState then
                    tbNpc.peaceFlip = 0
                else
                    tbNpc.peaceFlip = (tbNpc.peaceFlip or 0) + 1
                    if tbNpc.peaceFlip >= 3 then tbNpc.peaceState = _raw; tbNpc.peaceFlip = 0 end   
                end
            end
            SetNpcPeace(tbNpc.finalIndex, tbNpc.peaceState or 1)   
        end
        if tbNpc.tongkim == 1 and tbNpc.worldInfo then
            if tbNpc.worldInfo.tkWarStarted ~= 1 then  
                tbNpc.tick_canWalk = (tbNpc.tick_breath or 0) + 30
            elseif tbNpc.tick_canWalk and tbNpc.tick_canWalk > (tbNpc.tick_breath or 0) then
                tbNpc.tick_canWalk = tbNpc.tick_breath or 0  
            end
        end
        
        if NPCINFO_GetNpcCurrentLife then
            local _cur = NPCINFO_GetNpcCurrentLife(tbNpc.finalIndex)
            if _cur then
                if tbNpc.prevHP and _cur < tbNpc.prevHP then
                    tbNpc.selfDefTick = tbNpc.tick_breath + 20*18/REFRESH_RATE                       
                    if not tbNpc.duelPlayerId and not tbNpc.partyPlayerId and GetNpcLastAttacker and NpcIdx2PIdx then                        
                        local _atk = GetNpcLastAttacker(tbNpc.finalIndex)
                        if _atk and _atk > 0 then
                            local _ap = NpcIdx2PIdx(_atk)
                            if _ap and _ap > 0 and CallPlayerFunction(_ap, GetCurCamp) ~= tbNpc.camp
                               and (not GetPlayerPkMode or GetPlayerPkMode(_atk) ~= 0) then  
                                tbNpc.duelPlayerId = _ap; tbNpc.selfDefDuel = 1
                            end
                        end
                    end
                    if tbNpc.selfDefDuel == 1 and tbNpc.duelPlayerId then tbNpc.duelTicks = 120 end                       
                    if BotDashTo and tbNpc.tongkim ~= 1
                       and (tbNpc.selfDefDuel == 1 or tbNpc.duelPlayerId or tbNpc.botDuelTarget)
                       and SimCityCanFight and SimCityCanFight(tbNpc) == 1
                       and tbNpc.dmFootSince and (tbNpc.tick_breath - tbNpc.dmFootSince) >= 4*18/REFRESH_RATE   
                       and (not GetNpcRideHorse or GetNpcRideHorse(tbNpc.finalIndex) == 0)  
                       and (not tbNpc.dashTick or tbNpc.dashTick <= tbNpc.tick_breath)
                       and GetNpcLastAttacker and GetNpcPos then
                        local _dka = GetNpcLastAttacker(tbNpc.finalIndex)
                        if _dka and _dka > 0 then
                            local _bnx, _bny = GetNpcPos(tbNpc.finalIndex)
                            local _anx, _any = GetNpcPos(_dka)
                            if _bnx and _anx and _bny and _any then
                                tbNpc.dashTick = tbNpc.tick_breath + 16*18/REFRESH_RATE   
                                local _bx, _by = floor(_bnx/32), floor(_bny/32)
                                local _ax, _ay = floor(_anx/32), floor(_any/32)
                                local _dx, _dy = _bx - _ax, _by - _ay
                                local _dd = sqrt(_dx*_dx + _dy*_dy)
                                if _dd < 1 then _dx = 1; _dy = 0; _dd = 1 end
                                local _dn = 12  
                                local _destX = _bx + floor(_dx * _dn / _dd)
                                local _destY = _by + floor(_dy * _dn / _dd)
                                if SetNpcLevel then SetNpcLevel(tbNpc.finalIndex, SIMBOT_LEVEL) end          
                                local _dr = BotDashTo(tbNpc.finalIndex, _destX, _destY, 20)
                                if _dr and _dr > 0 then tbNpc.dashUntil = tbNpc.tick_breath + 2*18/REFRESH_RATE end   
                            end
                        end
                    end
                end
                tbNpc.prevHP = _cur
            end
        end
        if (EnforceBotHp) then            
            EnforceBotHp(tbNpc.finalIndex, 1)          
            if tbNpc.tongkim ~= 1
               and NPCINFO_GetNpcCurrentLife and NPCINFO_GetNpcCurrentMaxLife
               and (not tbNpc.potionTick or tbNpc.potionTick <= tbNpc.tick_breath) then
                tbNpc.potionTick = tbNpc.tick_breath + 1.5*18/REFRESH_RATE  
                local _cl = NPCINFO_GetNpcCurrentLife(tbNpc.finalIndex)
                local _ml = NPCINFO_GetNpcCurrentMaxLife(tbNpc.finalIndex)
                if _cl and _ml and _ml > 0 then
                    if _cl >= _ml * 0.99 then
                        tbNpc.healStartTick = nil   
                    elseif _cl < _ml * 0.9 then
                        if not tbNpc.healStartTick then tbNpc.healStartTick = tbNpc.tick_breath end  
                        if tbNpc.tick_breath < tbNpc.healStartTick + 40*18/REFRESH_RATE then   
                            EnforceBotHp(tbNpc.finalIndex, 350)   
                        end
                        
                    end
                end
            end
        end
       
        if (tbNpc.tongkim ~= 1 and not tbNpc.rankCleared and SetNpcTitle) then
            tbNpc.rankCleared = 1
            SetNpcTitle(tbNpc.finalIndex, 0)
        end
       
        if (SetBotSpeed) then
            SetBotSpeed(tbNpc.finalIndex, SIMBOT_WALK_SPEED or 15, SIMBOT_RUN_SPEED or 24)  
        end
       
        if (BotMountSync) then
            BotMountSync(tbNpc.finalIndex, tbNpc.isFighting or 0)
        end
    
        if SetNpcRideHorse and tbNpc.tongkim ~= 1 then
            local _dmSk = tbNpc.skillCastBua and tbNpc.skillCastBua[1]
            local _isDm = _dmSk and SIMBOT_DISMOUNT_SKILLS[_dmSk]
            local _inCbt = (tbNpc.isFighting or 0) == 1 or tbNpc.duelPlayerId or tbNpc.botDuelTarget
            local _wantRide = (_inCbt and _isDm) and 0 or 1  
           
            if _isDm and _inCbt then
                if not tbNpc.dmFootSince then tbNpc.dmFootSince = tbNpc.tick_breath end
            else
                tbNpc.dmFootSince = nil
            end
            if tbNpc.lastRideWant ~= _wantRide or not tbNpc.remountTick or tbNpc.remountTick <= tbNpc.tick_breath then
                tbNpc.remountTick = tbNpc.tick_breath + 5*18/REFRESH_RATE   
                tbNpc.lastRideWant = _wantRide
                SetNpcRideHorse(tbNpc.finalIndex, _wantRide)
                if SetBotSpeed then SetBotSpeed(tbNpc.finalIndex, SIMBOT_WALK_SPEED or 15, SIMBOT_RUN_SPEED or 24) end   
            end
        end
    end
    local tickRate = rate or 1
    if tbNpc.isDead == 1 or (tbNpc.isStanding and tbNpc.isStanding == 1) then
        return 0
    end

    if BOT_VS_BOT == 1 and SimEnemyAround and BotDoSkill and not tbNpc.duelPlayerId and not tbNpc.partyPlayerId
       and tbNpc.tongkim ~= 1 and tbNpc.finalIndex and tbNpc.finalIndex > 0 and (tbNpc.camp or 0) > 0
       and (not SimCityIsPeaceZone or SimCityIsPeaceZone(tbNpc) ~= 1) then
        
        if tbNpc.botDuelTarget or (not tbNpc.botScanTick or tbNpc.botScanTick <= tbNpc.tick_breath) then
            local _cpn = 0
            if GetNpcAroundPlayerList and GetPlayerPkMode and PIdx2NpcIdx then
                local _pl, _pc = GetNpcAroundPlayerList(tbNpc.finalIndex, 32)
                for _i = 1, _pc do
                    if _cpn == 0 and GetPlayerPkMode(PIdx2NpcIdx(_pl[_i])) ~= 0 then _cpn = 1 end
                end
            end
            if _cpn == 0 then
                if tbNpc.botDuelTarget then
                    tbNpc.botDuelTarget = nil
                    if tbNpc.faction == "ngudoc" and SetNpcAuraSkill then SetNpcAuraSkill(tbNpc.finalIndex, 1, 1) end   
                end
                tbNpc.botScanTick = tbNpc.tick_breath + 4*18/REFRESH_RATE
            elseif not tbNpc.botScanTick or tbNpc.botScanTick <= tbNpc.tick_breath then
                tbNpc.botScanTick = tbNpc.tick_breath + 4*18/REFRESH_RATE
                local _e = SimEnemyAround(tbNpc.finalIndex, BOT_COMBAT_RADIUS or 20)
                if _e and _e > 0 then
                    tbNpc.botDuelTarget = _e
                    tbNpc.botDuelTick = tbNpc.tick_breath + 12*18/REFRESH_RATE
                elseif tbNpc.botDuelTick and tbNpc.botDuelTick <= tbNpc.tick_breath then
                    tbNpc.botDuelTarget = nil
                end
            end
        end
    else
        tbNpc.botDuelTarget = nil
    end
    if not tbNpc.botDuelTarget and tbNpc.botFighting == 1 then tbNpc.isFighting = 0; tbNpc.botFighting = nil end   
   
    local _ts = (PollTradeStay and tbNpc.finalIndex and tbNpc.finalIndex > 0 and not tbNpc.duelPlayerId and not tbNpc.botDuelTarget and not tbNpc.partyPlayerId) and PollTradeStay(tbNpc.finalIndex) or 0
    if _ts == 2 then
        tbNpc.tradeStayDeadline = nil; tbNpc.tradeStayBye = nil; tbNpc.tradeStayByeUntil = nil; tbNpc.tradePostUntil = nil
        if not tbNpc.tradeItemSent then
            if not tbNpc.tradeItemAt then tbNpc.tradeItemAt = tbNpc.tick_breath + 8*18/REFRESH_RATE end
            if tbNpc.tick_breath >= tbNpc.tradeItemAt then
                if SendTradeItem then SendTradeItem(tbNpc.finalIndex) end
                tbNpc.tradeItemSent = 1
            end
        end
        tbNpc.tick_breath = tbNpc.tick_breath + 1*tickRate
        return 0
    elseif _ts == 3 then
        tbNpc.tradeItemSent = nil; tbNpc.tradeItemAt = nil
        if not tbNpc.tradePostUntil then tbNpc.tradePostUntil = tbNpc.tick_breath + 27*18/REFRESH_RATE end
        if tbNpc.tick_breath < tbNpc.tradePostUntil then
            tbNpc.tick_breath = tbNpc.tick_breath + 1*tickRate
            return 0
        end
        tbNpc.tradePostUntil = nil
        if TradeStayClear then TradeStayClear(tbNpc.finalIndex) end
    elseif _ts == 1 then
        tbNpc.tradeItemSent = nil; tbNpc.tradeItemAt = nil; tbNpc.tradePostUntil = nil; tbNpc.greetStayDeadline = nil
        if tbNpc.tradeStayBye then
            if tbNpc.tick_breath < tbNpc.tradeStayByeUntil then
                tbNpc.tick_breath = tbNpc.tick_breath + 1*tickRate
                return 0
            end
            tbNpc.tradeStayBye = nil; tbNpc.tradeStayByeUntil = nil; tbNpc.tradeStayDeadline = nil
            if TradeStayClear then TradeStayClear(tbNpc.finalIndex) end
        else
            if not tbNpc.tradeStayDeadline then tbNpc.tradeStayDeadline = tbNpc.tick_breath + 38*18/REFRESH_RATE end
            if tbNpc.tick_breath < tbNpc.tradeStayDeadline then
                tbNpc.tick_breath = tbNpc.tick_breath + 1*tickRate
                return 0
            end
            if NpcChat then local _bm = { "ua ban ko chon giao dich, thoi t di nha :)", "chac ban ban roi, luc khac t cho nha :)", "ko thay mo giao dich, t di truoc nha :)", "thoi ban ko mo trade, t di day nha :)", "doi hoai ko thay, thoi t di nha :)", "ban chua chon giao dich kia, t di truoc :)", "chac ban dang ban, hom khac t cho :)", "t cho ma ban ko lay, thoi t di nha :)", "ko mo giao dich ha, thoi t di nha :)", "ban oi mo giao dich di chu, thoi t di :)" }; NpcChat(tbNpc.finalIndex, _bm[mod(tbNpc.tick_breath + tbNpc.finalIndex*7, 10) + 1]) end
            tbNpc.tradeStayBye = 1; tbNpc.tradeStayByeUntil = tbNpc.tick_breath + 10*18/REFRESH_RATE
            tbNpc.tick_breath = tbNpc.tick_breath + 1*tickRate
            return 0
        end
    elseif _ts == 4 then
        
        tbNpc.tradeItemSent = nil; tbNpc.tradeItemAt = nil; tbNpc.tradePostUntil = nil
        tbNpc.tradeStayBye = nil; tbNpc.tradeStayByeUntil = nil; tbNpc.tradeStayDeadline = nil
        if not tbNpc.greetStayDeadline then tbNpc.greetStayDeadline = tbNpc.tick_breath + 54*18/REFRESH_RATE end
        if tbNpc.tick_breath < tbNpc.greetStayDeadline then
            tbNpc.tick_breath = tbNpc.tick_breath + 1*tickRate
            return 0
        end
        tbNpc.greetStayDeadline = nil
        if TradeStayClear then TradeStayClear(tbNpc.finalIndex) end
    else
        tbNpc.tradeStayDeadline = nil; tbNpc.tradeStayBye = nil; tbNpc.tradeStayByeUntil = nil; tbNpc.greetStayDeadline = nil
        tbNpc.tradeItemSent = nil; tbNpc.tradeItemAt = nil; tbNpc.tradePostUntil = nil
    end
    
    if not tbNpc.duelPlayerId and not tbNpc.botDuelTarget and not tbNpc.partyPlayerId and tbNpc.movementSys:IsActive(self, tbNpc) == 0 then  
        if (not tbNpc.tongkim or tbNpc.tongkim ~= 1) then
            tbNpc.movementSys:MoveInactive(self, tbNpc)
            return 0
        end
    end

    tbNpc.tick_breath = tbNpc.tick_breath + 1*tickRate

    if tbNpc.tick_breath > 1800*18/REFRESH_RATE then
        tbNpc.tick_breath = 0
        tbNpc.tick_canswitch = 0
        tbNpc.tick_checklag = nil
        tbNpc.tick_canWalk = 0
        tbNpc.tick_canCast = 0        
        tbNpc.partyScanTick = 0; tbNpc.partyTargetTick = 0
        tbNpc.botCastTick = 0; tbNpc.botCombatTick = 0
        tbNpc.botScanTick = 0; tbNpc.botDuelTick = 0
        tbNpc.duelCastTick = 0; tbNpc.duelCombatTick = 0
        tbNpc.peaceTick = 0; tbNpc.remountTick = 0
    end
    
    if PollDuel and tbNpc.finalIndex and tbNpc.finalIndex > 0 and not tbNpc.duelPlayerId then
        local dp = PollDuel(tbNpc.finalIndex)
        if dp and dp > 0 then
            tbNpc.duelPlayerId = dp
            tbNpc.duelTicks = 300
            local pcamp = CallPlayerFunction(dp, GetCurCamp)
            local botcamp = tbNpc.camp or 0         
            if botcamp == 0 or botcamp == pcamp then
                local bc = 1
                if pcamp == 0 then bc = 5 elseif pcamp == 1 then bc = 2 else bc = 1 end
                tbNpc.duelOldCamp = botcamp  
                tbNpc.camp = bc
                if SetNpcCurCamp then SetNpcCurCamp(tbNpc.finalIndex, bc) end
            end            
        end
    end   
    if PollParty and tbNpc.finalIndex and tbNpc.finalIndex > 0 and not tbNpc.partyPlayerId and not tbNpc.duelPlayerId and not tbNpc.botDuelTarget then
        local pp = PollParty(tbNpc.finalIndex)
        if pp and pp > 0 then
            tbNpc.partyPlayerId = pp
            tbNpc.partyFarTicks = 0
            if SetBotSpeed then SetBotSpeed(tbNpc.finalIndex, SIMBOT_WALK_SPEED or 15, SIMBOT_RUN_SPEED or 24) end   
            local pcamp = CallPlayerFunction(pp, GetCurCamp)
            if pcamp ~= nil then
                tbNpc.partyOldCamp = tbNpc.camp or 0
                tbNpc.camp = pcamp
                if SetNpcCurCamp then SetNpcCurCamp(tbNpc.finalIndex, pcamp) end
            end
        end
    end   
    if tbNpc.dashUntil and tbNpc.tick_breath < tbNpc.dashUntil then        
    elseif tbNpc.duelPlayerId then
        SimDuelMove(self, tbNpc)
    elseif tbNpc.botDuelTarget then
        SimBotDuelMove(self, tbNpc)   
    elseif tbNpc.partyPlayerId then
        SimPartyFollow(self, tbNpc)   
    else
        tbNpc.movementSys:Move(self, tbNpc)
    end
   
    if mod(tbNpc.tick_breath, 10*18/REFRESH_RATE) == 0 then       
        
        if tbNpc.faction and SimCityPhai[tbNpc.faction].normalCast and not tbNpc.botDuelTarget then  
            tbNpc.fightSys:Update(self, tbNpc)
        end
            
        if tbNpc.isFighting == 1 then
            tbNpc.fightingScore = tbNpc.fightingScore + 100
        end
    end

    if not tbNpc.duelPlayerId and tbNpc.isPlayerEnemyAround and tbNpc.isPlayerEnemyAround > 0
        and tbNpc.faction and SimCityPhai[tbNpc.faction] and SimCityPhai[tbNpc.faction].normalCast then     
        if SetNpcCombat and (not tbNpc.aggroCombatTick or tbNpc.aggroCombatTick <= tbNpc.tick_breath) then
            SetNpcCombat(tbNpc.finalIndex, 1, tbNpc.skillCastBua and tbNpc.skillCastBua[1] or 0)
            tbNpc.aggroCombatTick = tbNpc.tick_breath + 2
        end
        tbNpc.fightSys:Update(self, tbNpc)
    end

end

function SimCore:ATick(rate)       
    if self.totalFighters <= 2000 then
        for _, fighter in self.fighterList do
            self:OnTimer(fighter, rate)
        end
        return
    end 
    for _, fighter in self.fighterList do
        if fighter.processGroup == self.currentProcessGroup then
            self:OnTimer(fighter, rate)
        end
    end 
    self.currentProcessGroup = self.currentProcessGroup == 1 and 2 or 1
end 
