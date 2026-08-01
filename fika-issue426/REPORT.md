# Fika Bug Report — Large containers can't be looted in 3-player+ squads

**GitHub Issue:** https://github.com/project-fika/Fika-Plugin/issues/426

## Description

When playing in a Fika co-op raid with **3 or more players**, interacting with large containers
(weapon boxes, technical crates, etc.) plays the search animation but the search UI never opens —
the player gets stuck in the search loop until the animation finishes, and the container cannot be looted.

This happened consistently to the **client** (not the host) in a 3-player squad on 2026-07-30.

### Reproduction steps
1. Host starts a Fika co-op raid (3 players total in the squad)
2. Client walks up to a large container (e.g. weapon box)
3. Client presses the interaction key to search the container
4. Search animation plays, but the search window never appears; container cannot be looted

### Expected Result
The search UI should open normally and the client should be able to loot the container.

### Affected side
- [x] Client
- [ ] Host
- [ ] Both

## Key error found in Client Player.log

```
InvalidOperationException: Collection was modified; enumeration operation may not execute.
  at System.Collections.Generic.Dictionary`2+Enumerator[TKey,TValue].MoveNext ()
  at EFT.UI.DragAndDrop.GridView.PrepareItems ()
  at EFT.UI.DragAndDrop.GridView.method_2 ()
  at EFT.UI.DragAndDrop.GridView.Show (StashGridClass grid, ...)
  at EFT.UI.DragAndDrop.ContainedGridsView.Show (...)
  at EFT.UI.DragAndDrop.GeneratedGridsView.Show (...)
  at EFT.UI.DragAndDrop.SearchableItemView.method_0 ()     <-- searchable item view
  at EFT.UI.DragAndDrop.SearchableView.method_2 ()          <-- search UI
  ...
Rethrow as AggregateException: One or more errors occurred.
```

The search UI crashes while enumerating the container's item grid (`GridView.PrepareItems` → `Collection was modified`),
which matches the "animation plays but search never starts" symptom.

Additionally, the client's Fika log (extracted) shows inventory-packet sync errors in the same session:

```
[Fika.Client] HandleInventoryPacket: You're trying to transfer 9 when you can only transfer 1
[Fika.Client] HandleInventoryPacket: Result cannot hold as much
[Fika.Client] HandleInventoryPacket: Cloned item ID desync. Expected ID: ...0017, real ID: ...0016
[Fika.Client] HandleInventoryPacket: (x:1,y:3) in grid main in backpack_Raid_6SH118 ... is taken by another item when trying to add item weapon_grenade_f1
[Fika.Core] WorldInteractionPacket: Could not find item: 6a6b4ec07ed847bb66000000
```

## Attached files

| File | Side | Source |
|------|------|--------|
| `CLIENT_player_2026-07-30.log` | Client | `%AppData%\..\LocalLow\Battlestate Games\EscapeFromTarkov\Player-prev.log` (351 KB, session ended 07/30 22:58) |
| `CLIENT_bepinex_errors_2026-07-30.txt` | Client | Extracted Fika errors from `BepInEx\LogOutput.log` (original overwritten by next session on 07/31) |
| `HOST_spt-server_2026-07-30.log` | Host | SPT server log (spt20260730.log) |
| `HOST_client-backend_2026-07-30.log` | Host | EFT client backend log (0.16.9.0.40087) |

## Environment

- SPT: 4.0.13
- Fika: Server 2.3.5 / Client 2.3.9
- Game version: 0.16.9.0.40087
- Windows 10/11
- Note: multiple other mods were installed on the client at the time (SAIN, QuestingBots, LootingBots, AmandsGraphics, SearchOpenContainers, etc.). The bug may need verification in a Fika-only environment, but the SearchableView exception is a vanilla EFT UI crash triggered while the Fika inventory sync was updating the same grid.
