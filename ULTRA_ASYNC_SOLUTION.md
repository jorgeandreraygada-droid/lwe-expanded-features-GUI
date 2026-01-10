# Ultra-Async Window Manipulation Solution

## Problem

When running in Flatpak, attempts to manipulate window flags (`--above`, `--random`, `--delay`) were potentially **blocking** the entire application or causing it to freeze. This happened because:

1. **wmctrl blocking**: Calls to `wmctrl` to detect or manipulate windows could hang indefinitely if Flatpak was blocking X11 access
2. **flatpak-enter blocking**: Accessing the sandbox via `flatpak-enter` could also block if the PID namespace access was slow or restricted
3. **Sequential attempts**: The old approach tried one method, waited for it, then tried another - multiplying the blocking time

## Solution: Ultra-Async Non-Blocking Approach

The `window-monitor.sh` and `async-window-fixer.sh` scripts now use a **completely non-blocking async-first strategy**:

### Key Features

#### 1. **Background Job Spawning**
- All window manipulation attempts are spawned as background jobs (`&`)
- Script returns immediately without waiting
- Work happens in parallel in separate subprocesses

#### 2. **Aggressive Timeouts**
Each operation is wrapped in `timeout`:
- 2-second timeout for wmctrl detection (finding windows)
- 1-second timeout for each individual flag manipulation
- 3-second timeout for flatpak-enter operations
- **If timeout is exceeded, the operation dies** and doesn't block anything

#### 3. **Dual-Strategy Parallelism**
Both methods run **simultaneously in parallel**:
```bash
# Try direct wmctrl in background
try_direct_wmctrl &

# Try flatpak-enter in background  
try_flatpak_enter &

# Return immediately, both methods run in parallel
```

#### 4. **Window-Level Parallelism**
When multiple wallpaper windows are found, each window gets multiple flag operations **all in parallel**:
```bash
timeout 0.5 wmctrl -i -r "$win" -b remove,above &
timeout 0.5 wmctrl -i -r "$win" -b add,skip_pager &
timeout 0.5 wmctrl -i -r "$win" -b add,below &
```

### How It Works

**Before (Blocking):**
```
main.sh launches engine
-> waits for window monitor to find and apply flags (COULD BLOCK)
-> monitor tries wmctrl (waits up to 30s)
-> if wmctrl hangs, ENTIRE APP FREEZES
```

**After (Ultra-Async):**
```
main.sh launches engine
-> window-monitor.sh starts in background with "sleep 0.5" loop
-> every 0.5s, monitor spawns async window manipulation subprocess
-> subprocess tries wmctrl + flatpak-enter IN PARALLEL, both with timeouts
-> subprocess dies if any timeout exceeded
-> monitor continues, tries again in 0.5s
-> main.sh NEVER BLOCKED, continues normally
```

### Implementation Details

#### window-monitor.sh
- **Loop interval**: 0.5 seconds (tries every half-second)
- **Duration**: 5 minutes or until engine dies
- **All operations**: Wrapped in `timeout` + background job spawning
- **Returns immediately**: Never waits for any wmctrl/flatpak-enter operation

#### async-window-fixer.sh  
- **Purpose**: Can be called for on-demand window manipulation
- **Strategy**: Same ultra-async approach as monitor
- **Methods**: `direct`, `flatpak-enter`, or `both` (default)
- **Never blocks**: Returns exit code 0 immediately, work happens in background

### Benefits

1. **No blocking**: Application remains responsive at all times
2. **Guaranteed timeouts**: Each operation has hard timeout, can't hang indefinitely
3. **Parallel attempts**: Multiple methods try simultaneously, increases success chance
4. **Resilience**: If one method fails/times out, others still attempt
5. **Continuous retry**: Monitor runs for full 5 minutes, keeps trying
6. **CPU efficient**: Only uses CPU when making attempts, sleeps between tries

### Timeout Strategy

| Operation | Timeout | Reason |
|-----------|---------|--------|
| wmctrl list windows | 2s | Detection should be fast |
| wmctrl flag operation | 1s | Each flag operation is simple |
| flatpak-enter detect | 3s | Namespace entry can be slower |
| flatpak-enter flag op | 1s | Once inside, operation is fast |
| Monitor loop interval | 0.5s | Balance responsiveness vs CPU |

### Log Messages

The monitor logs indicate what's happening:

```bash
[2024-01-15 10:30:45] [MONITOR-12345] Starting ultra-async window monitor for PID 5678
[2024-01-15 10:30:46] [MONITOR-12345] Launched async window fix attempt (bg PID: 6789, attempt 1)
[2024-01-15 10:30:47] [MONITOR-12345] Launched async window fix attempt (bg PID: 6790, attempt 2)
# ... continues every 0.5s
[2024-01-15 10:35:45] [MONITOR-12345] Engine PID 5678 died, exiting monitor
```

### When is This Used?

The ultra-async window monitor is automatically launched when:
1. User specifies `--above` flag on command line
2. `main.sh` detects this and sets `REMOVE_ABOVE=true`
3. `apply_wallpaper()` launches `window-monitor.sh` in background
4. Monitor runs for entire lifetime of wallpaper engine (max 5 minutes)

### Fallback Layers

If wmctrl/flatpak-enter don't work, the system has multiple fallbacks:

1. **Async attempts**: Monitor keeps trying with different methods
2. **State file**: Previous window state saved for reference
3. **Process tracking**: Even if window detection fails, engine process runs
4. **Manual intervention**: User can always use `wmctrl` manually if needed

## Testing

To verify ultra-async is working:

```bash
# With debug logging
flatpak run --filesystem=home com.github.mauefrod.LWEExpandedFeaturesGUI --above --dir ~/wallpapers

# Check logs for monitor activity
tail -f ~/.local/share/linux-wallpaper-engine-features/logs.txt

# Look for "async window fix attempt" messages
# These indicate the monitor is actively trying in background
```

## Conclusion

This ultra-async approach ensures that window manipulation attempts **never block the application**, while still aggressively trying to apply flags through multiple methods in parallel. The application remains responsive even if wmctrl or flatpak-enter are slow or temporarily unavailable.
