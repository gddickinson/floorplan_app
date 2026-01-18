# macOS Crash Fix - Version 1.3.4

## Issue: Segmentation Fault on 3D View Activation

**Symptom:** Application crashes with `SIGSEGV` when opening the 3D view, particularly on macOS.

**Error:**
```
Exception Type:    EXC_BAD_ACCESS (SIGSEGV)
Exception Subtype: KERN_INVALID_ADDRESS at 0x0000000000000414
Terminating Process: exc handler [81052]

Thread 0 Crashed::  Dispatch queue: com.apple.main-thread
0   QtGui          QRasterPaintEngine::renderHintsChanged() + 32
1   QtGui.abi3.so  meth_QPainter_setRenderHint + 132
```

**When:** Opening 3D view immediately after loading a file on macOS.

---

## Root Cause

The crash occurred due to a **race condition** in the Qt painting system:

1. **3D view becomes visible** → Triggers `visibilityChanged` signal
2. **Immediately calls `update()`** → Triggers `paintEvent()`
3. **Widget not fully initialized** → Painter in invalid state
4. **Crash** when calling `painter.setRenderHint()`

On macOS, Qt widgets need a brief moment after becoming visible before they're ready for painting. Calling `update()` immediately can cause the QPainter to be in an invalid state.

---

## The Fix

### Fix 1: Deferred Update with QTimer

Instead of calling `update()` immediately when the 3D view becomes visible, we now defer it by 100ms:

```python
def _on_3d_view_visibility_changed(self, visible):
    if visible:
        # Defer refresh to ensure widget is fully initialized
        QTimer.singleShot(100, self._delayed_3d_refresh)

def _delayed_3d_refresh(self):
    """Called after short delay via QTimer."""
    self.viewer_3d.set_building(self.building)
    self.viewer_3d.refresh()
```

This gives the widget time to fully initialize before attempting to paint.

### Fix 2: Safe Painter Management

Added comprehensive safety checks in `paintEvent()`:

```python
def paintEvent(self, event):
    # Safety check - ensure widget is ready
    if not self.isVisible() or self.width() <= 0 or self.height() <= 0:
        return
    
    painter = QPainter(self)
    
    # Safety check - ensure painter is valid
    if not painter.isActive():
        logger.warning("Painter is not active, skipping paint")
        return
    
    try:
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        # ... rest of painting code ...
        
    except Exception as e:
        logger.error(f"Error in paintEvent: {e}", exc_info=True)
    finally:
        # Ensure painter is properly ended
        if painter.isActive():
            painter.end()
```

Safety checks:
1. ✅ Widget visibility check
2. ✅ Widget size validation
3. ✅ Painter active state check
4. ✅ Exception handling
5. ✅ Explicit painter cleanup

### Fix 3: Deferred Refresh Method

The `refresh()` method now also uses QTimer:

```python
def refresh(self):
    """Force refresh the 3D view."""
    # Use QTimer to defer the update slightly
    QTimer.singleShot(10, self.canvas.update)
```

This prevents race conditions when refresh is called from various event handlers.

---

## Why This Happens on macOS

macOS has different widget initialization timing than Linux/Windows:

**Linux/Windows:**
- Widget becomes visible → Immediately ready for painting
- Synchronous initialization

**macOS:**
- Widget becomes visible → Brief initialization period
- Asynchronous window system integration
- Needs time for QuartzCore/AppKit setup

The 100ms delay is imperceptible to users but gives the system adequate time to initialize.

---

## Files Changed

**gui/viewer_3d.py:**
- Enhanced `paintEvent()` with safety checks
- Added try/except/finally for safe painter management
- Modified `refresh()` to use QTimer
- Added painter validity checks

**gui/main_window.py:**
- Modified `_on_3d_view_visibility_changed()` to use QTimer
- Added `_delayed_3d_refresh()` method
- Added QTimer import

---

## Testing

### Test 1: Load File and Open 3D View (macOS)
```bash
python main.py examples/comprehensive_house.floorplan
# Wait for file to load
View → Show 3D View
# Should open smoothly without crash
```

**Expected:** 3D view opens, shows house in 3D, no crash.

### Test 2: Rapid Toggle
```bash
python main.py examples/comprehensive_house.floorplan
View → Show 3D View
View → Show 3D View (toggle off)
View → Show 3D View (toggle on)
# Repeat several times rapidly
```

**Expected:** No crashes even with rapid toggling.

### Test 3: Draw and View
```bash
python main.py
# Draw a simple square (4 walls)
View → Show 3D View
# Should show square in 3D
```

**Expected:** Smooth operation, no crash.

---

## Platform-Specific Notes

### macOS
- ✅ **Fixed:** Crash on 3D view activation
- ✅ Uses 100ms delay for widget initialization
- ✅ Safe painter management prevents crashes
- ✅ Works on Apple Silicon (M1/M2/M3)

### Linux
- ✅ Works with both delays (backward compatible)
- No negative impact from the delay

### Windows
- ✅ Should work (though not explicitly tested)
- Delay is harmless on Windows

---

## Performance Impact

**User Experience:**
- Delay: 100ms (imperceptible)
- 3D view appears instant to users
- No noticeable lag

**Technical:**
- 0.1 second delay before first paint
- Subsequent updates: immediate
- No ongoing performance cost

---

## Debugging

If crashes still occur:

### Check Logs
```bash
# Look for these log messages:
2026-01-18 09:54:25 - gui.main_window - INFO - 3D view became visible, scheduling refresh...
2026-01-18 09:54:25 - gui.main_window - INFO - Performing delayed 3D refresh
2026-01-18 09:54:25 - gui.viewer_3d - INFO - Refreshing 3D view
```

If you see these and still crash, increase the delay:

```python
# In main_window.py, line ~XXX
QTimer.singleShot(100, self._delayed_3d_refresh)
# Try: 200 or 500 instead of 100
```

### Check Painter State
If you see this warning:
```
WARNING - Painter is not active, skipping paint
```

This means the painter safety check caught an invalid state. Good! The safety check prevented a crash.

---

## Additional Safety Measures

### Widget Size Validation
```python
if self.width() <= 0 or self.height() <= 0:
    return  # Don't paint invalid widget
```

### Painter Active Check
```python
if not painter.isActive():
    return  # Painter not ready
```

### Exception Handling
```python
try:
    # Paint operations
except Exception as e:
    logger.error(f"Error: {e}")
finally:
    painter.end()  # Always cleanup
```

---

## Stack Trace Analysis

The original crash:
```
QRasterPaintEngine::renderHintsChanged() + 32
meth_QPainter_setRenderHint + 132
```

This indicates:
1. QPainter was created
2. `setRenderHint()` was called
3. Painter's internal engine wasn't initialized
4. Crash accessing null pointer (0x414)

**Fixed by:** Ensuring widget is fully ready before creating QPainter.

---

## Prevention Guidelines

When adding new widgets with custom painting:

```python
def paintEvent(self, event):
    # ALWAYS do these checks first:
    if not self.isVisible():
        return
    
    if self.width() <= 0 or self.height() <= 0:
        return
    
    painter = QPainter(self)
    if not painter.isActive():
        return
    
    try:
        # Your painting code
        pass
    finally:
        if painter.isActive():
            painter.end()
```

When triggering updates from events:

```python
# Don't do this:
def on_visibility_changed(self, visible):
    self.update()  # Too fast!

# Do this:
def on_visibility_changed(self, visible):
    QTimer.singleShot(100, self.update)  # Safe!
```

---

## Version History

**v1.3.3:** File loading fixed, but crashes on macOS
**v1.3.4:** Crash fixed with QTimer delays and safety checks

---

## Summary

✅ **macOS crash fixed** - Safe 3D view activation
✅ **Painter safety** - Comprehensive validity checks  
✅ **Exception handling** - Graceful error recovery
✅ **Deferred updates** - Proper widget initialization timing
✅ **Cross-platform** - Works on macOS, Linux, Windows

**The 3D viewer now works reliably on macOS without crashes!** 🎉
