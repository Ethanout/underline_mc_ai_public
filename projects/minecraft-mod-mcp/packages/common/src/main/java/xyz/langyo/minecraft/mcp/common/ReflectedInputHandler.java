package xyz.langyo.minecraft.mcp.common;

import java.lang.reflect.Field;
import java.lang.reflect.Method;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.TimeUnit;

public class ReflectedInputHandler extends McpMessageHandler implements McpProtocol.MinecraftInput {

    private final RenderThreadExecutor executor;

    public ReflectedInputHandler(RenderThreadExecutor executor) {
        super();
        this.executor = executor;
        this.minecraftInput = this;
    }

    public static void executeOnRenderThread(Runnable task) {
        try {
            Object mc = ReflectionHelper.getMinecraftInstance();
            try {
                java.lang.reflect.Method execute = mc.getClass().getMethod("execute", Runnable.class);
                execute.invoke(mc, task);
                return;
            } catch (NoSuchMethodException e) {}
            try {
                java.lang.reflect.Method m = mc.getClass().getMethod("addScheduledTask", Runnable.class);
                m.invoke(mc, task);
                return;
            } catch (NoSuchMethodException e) {}
            for (java.lang.reflect.Method m : mc.getClass().getMethods()) {
                if ((m.getName().contains("Schedule") || m.getName().contains("schedule"))
                    && m.getParameterCount() == 1
                    && Runnable.class.isAssignableFrom(m.getParameterTypes()[0])) {
                    m.invoke(mc, task);
                    return;
                }
            }
            for (java.lang.reflect.Method m : mc.getClass().getMethods()) {
                if (m.getName().contains("Task") && m.getParameterCount() == 1
                    && Runnable.class.isAssignableFrom(m.getParameterTypes()[0])) {
                    m.invoke(mc, task);
                    return;
                }
            }
            for (java.lang.reflect.Method m : mc.getClass().getMethods()) {
                if (m.getParameterCount() == 1 && Runnable.class.isAssignableFrom(m.getParameterTypes()[0])
                        && java.lang.reflect.Modifier.isPublic(m.getModifiers())) {
                    m.invoke(mc, task);
                    return;
                }
            }
            throw new RuntimeException("No scheduling method found on " + mc.getClass().getName()
                + ". Methods with Runnable: " + java.util.Arrays.toString(
                    java.util.Arrays.stream(mc.getClass().getMethods())
                        .filter(x -> x.getParameterCount() == 1 && Runnable.class.isAssignableFrom(x.getParameterTypes()[0]))
                        .map(java.lang.reflect.Method::getName).toArray()));
        } catch (Exception e) {
            throw new RuntimeException("executeOnRenderThread failed: " + e.getMessage(), e);
        }
    }

    private Object mc() { return ReflectionHelper.getMinecraftInstance(); }

    private long getWindowHandle() {
        Object mc = mc();
        if (ReflectionHelper.hasWindow(mc)) return ReflectionHelper.getWindowHandle(mc);
        return 0;
    }

    private Object getWindow(Object mc) {
        try {
            try { return mc.getClass().getMethod("getWindow").invoke(mc); }
            catch (NoSuchMethodException ignored) {}
            try { return mc.getClass().getMethod("getMainWindow").invoke(mc); }
            catch (NoSuchMethodException ignored) {}
            for (Field f : mc.getClass().getDeclaredFields()) {
                String tn = f.getType().getSimpleName();
                if (tn.contains("Window") || tn.contains("MainWindow")) {
                    try { f.setAccessible(true); return f.get(mc); } catch (Exception ignored) {}
                }
            }
        } catch (Exception ignored) {}
        return null;
    }

    private int getWidth() {
        Object mc = mc();
        Object window = getWindow(mc);
        if (window != null) {
            for (String fname : new String[]{"width", "cachedWidth", "framebufferWidth",
                    "field_198122_i", "field_198131_r", "field_198120_g", "field_198127_n"}) {
                try {
                    Field f = window.getClass().getDeclaredField(fname);
                    f.setAccessible(true);
                    int v = f.getInt(window);
                    if (v > 0) return v;
                } catch (Exception ignored) {}
            }
            try {
                return ((Number) window.getClass().getMethod("getWidth").invoke(window)).intValue();
            } catch (Exception ignored) {}
        }
        int v = ReflectionHelper.getDisplayWidth(mc);
        if (v > 0) return v;
        return ReflectionHelper.getLwjgl2DisplaySize(true);
    }

    private int getHeight() {
        Object mc = mc();
        Object window = getWindow(mc);
        if (window != null) {
            for (String fname : new String[]{"height", "cachedHeight", "framebufferHeight",
                    "field_198123_j", "field_198132_s", "field_198121_h", "field_198128_o"}) {
                try {
                    Field f = window.getClass().getDeclaredField(fname);
                    f.setAccessible(true);
                    int v = f.getInt(window);
                    if (v > 0) return v;
                } catch (Exception ignored) {}
            }
            try {
                return ((Number) window.getClass().getMethod("getHeight").invoke(window)).intValue();
            } catch (Exception ignored) {}
        }
        int v = ReflectionHelper.getDisplayHeight(mc);
        if (v > 0) return v;
        return ReflectionHelper.getLwjgl2DisplaySize(false);
    }

    private static String lastClickResult = "";

    @Override
    public void click(int x, int y, String button) {
        final CountDownLatch latch = new CountDownLatch(1);
        executor.executeOnRenderThread(() -> {
            try {
                int b = "right".equals(button) ? 1 : "middle".equals(button) ? 2 : 0;
                lastClickResult = ReflectionHelper.guiClick(mc(), x, y, b);
                ReflectionHelper.dbg("guiClick: " + lastClickResult);
            } catch (Exception e) { lastClickResult = "{\"error\":\"" + e.getMessage() + "\"}"; }
            latch.countDown();
        });
        try { latch.await(5, TimeUnit.SECONDS); } catch (Exception ignored) {}
    }

    public static String getLastClickResult() { return lastClickResult; }

    @Override
    public void pressKey(String key, float holdSeconds) {
        final int code = GlfwKeys.keyCode(key);
        if (code < 0) {
            System.err.println("[Input] pressKey: unknown key '" + key + "'");
            return;
        }
        final long handle = getWindowHandle();
        if (handle == 0) {
            System.err.println("[Input] pressKey: warning - no window handle cached, will try to resolve during injection for key=" + key);
            // Don't return — guiKeyPress and sendKey have their own handle fallback logic
        }
        final float hold = holdSeconds > 0 ? holdSeconds : 0.03f;
        // Key down on render thread
        executor.executeOnRenderThread(() -> {
            try {
                // Try GUI path first (handles screen key events), fall back to raw keyboard injection
                String result = ReflectionHelper.guiKeyPress(mc(), code, 0, 1, 0);
                if (result == null || result.contains("error")) {
                    // Fallback: direct keyboard handler injection for in-game keys
                    ReflectionHelper.sendKey(handle, code, 1);
                }
                ReflectionHelper.dbg("pressKey down: " + key + " (code=" + code + ") result=" + result);
            } catch (Throwable e) {
                System.err.println("[Input] Key down error: " + e.getMessage());
                if (e instanceof Error) {
                    System.err.println("[Input] Key down: critical error for key=" + key);
                }
            }
        });
        // Key up after delay (on separate thread to avoid freezing render)
        new Thread(() -> {
            try { Thread.sleep((long)(hold * 1000)); } catch (InterruptedException ignored) {}
            executor.executeOnRenderThread(() -> {
                try {
                    String result = ReflectionHelper.guiKeyPress(mc(), code, 0, 0, 0);
                    if (result == null || result.contains("error")) {
                        ReflectionHelper.sendKey(handle, code, 0);
                    }
                    ReflectionHelper.dbg("pressKey up: " + key + " result=" + result);
                } catch (Throwable e) {
                    System.err.println("[Input] Key up error: " + e.getMessage());
                }
            });
        }, "MCP-KeyDelay").start();
    }

    @Override
    public void typeText(String text) {
        executor.executeOnRenderThread(() -> {
            try {
                for (char ch : text.toCharArray()) {
                    String r = ReflectionHelper.guiCharType(mc(), ch, 0);
                    ReflectionHelper.dbg("guiCharType '" + ch + "': " + r);
                    Thread.sleep(30);
                }
            } catch (Exception e) { System.err.println("[Input] Type: " + e.getMessage()); }
        });
    }

    @Override
    public void pasteText(String text) {
        executor.executeOnRenderThread(() -> {
            try {
                String result = ReflectionHelper.pasteText(mc(), text);
                ReflectionHelper.dbg("pasteText: " + result);
            } catch (Exception e) { System.err.println("[Input] Paste: " + e.getMessage()); }
        });
    }

    @Override
    public void scroll(int clicks) {
        executor.executeOnRenderThread(() -> {
            try { ReflectionHelper.sendScroll(getWindowHandle(), clicks * 1.0); }
            catch (Exception ignored) {}
        });
    }

    public void scrollAt(int x, int y, int clicks) {
        executor.executeOnRenderThread(() -> {
            try {
                long h = getWindowHandle();
                ReflectionHelper.setCursorPos(h, x, y);
                Thread.sleep(30);
                // Also send mouse move so MC knows cursor is at (x,y)
                ReflectionHelper.sendMouseMoveInternal(h, x, y);
                Thread.sleep(20);
                ReflectionHelper.sendScroll(h, clicks * 1.0);
            } catch (Exception ignored) {}
        });
    }

    @Override
    public void mouseDrag(int x1, int y1, int x2, int y2, String button) {
        executor.executeOnRenderThread(() -> {
            try {
                int b = "right".equals(button) ? 1 : "middle".equals(button) ? 2 : 0;
                int steps = Math.max(Math.abs(x2 - x1), Math.abs(y2 - y1)) / 10;
                if (steps < 3) steps = 3;
                ReflectionHelper.sendMouseDrag(getWindowHandle(), x1, y1, x2, y2, b, steps);
            } catch (Exception e) { System.err.println("[Input] Drag: " + e.getMessage()); }
        });
    }

    @Override
    public void hotkey(String[] keys) {
        executor.executeOnRenderThread(() -> {
            try {
                long h = getWindowHandle();
                if (h == 0) return;
                int[] codes = new int[keys.length];
                for (int i = 0; i < keys.length; i++) codes[i] = GlfwKeys.keyCode(keys[i]);
                for (int c : codes) { ReflectionHelper.sendKey(h, c, 1); Thread.sleep(5); }
                Thread.sleep(80);
                for (int i = codes.length - 1; i >= 0; i--) ReflectionHelper.sendKey(h, codes[i], 0);
            } catch (Exception e) { System.err.println("[Input] Hotkey: " + e.getMessage()); }
        });
    }

    @Override
    public void setViewAngle(float yaw, float pitch) {
        executor.executeOnRenderThread(() -> {
            try {
                String result = ReflectionHelper.setPlayerRotation(mc(), yaw, pitch);
                ReflectionHelper.dbg("setViewAngle: " + result);
            } catch (Exception e) { System.err.println("[Input] setViewAngle: " + e.getMessage()); }
        });
    }

    @Override
    public void lookDelta(float deltaYaw, float deltaPitch) {
        executor.executeOnRenderThread(() -> {
            try {
                String result = ReflectionHelper.deltaPlayerRotation(mc(), deltaYaw, deltaPitch);
                ReflectionHelper.dbg("lookDelta: " + result);
            } catch (Exception e) { System.err.println("[Input] lookDelta: " + e.getMessage()); }
        });
    }

    @Override
    public void rightClick() {
        executor.executeOnRenderThread(() -> {
            try {
                String result = ReflectionHelper.doRightClick(mc());
                ReflectionHelper.dbg("rightClick: " + result);
            } catch (Exception e) { System.err.println("[Input] rightClick: " + e.getMessage()); }
        });
    }

    @Override
    public byte[] screenshot() {
        if (isOnRenderThread()) {
            return doScreenshot();
        }
        try {
            final byte[][] holder = {null};
            final Exception[] err = {null};
            final java.util.concurrent.CountDownLatch latch = new java.util.concurrent.CountDownLatch(1);
            boolean scheduled = false;
            try {
                Object mc = mc();
                try {
                    java.lang.reflect.Method execute = mc.getClass().getMethod("execute", Runnable.class);
                    execute.invoke(mc, (Runnable) () -> {
                        try { holder[0] = doScreenshot(); }
                        catch (Exception e) { err[0] = e; }
                        latch.countDown();
                    });
                    scheduled = true;
                } catch (NoSuchMethodException e) {
                    try {
                        mc.getClass().getMethod("addScheduledTask", Runnable.class).invoke(mc, (Runnable) () -> {
                            try { holder[0] = doScreenshot(); }
                            catch (Exception ex) { err[0] = ex; }
                            latch.countDown();
                        });
                        scheduled = true;
                    } catch (Exception ignored) {}
                }
            } catch (Exception ignored) {}
            if (scheduled) {
                try { latch.await(15, java.util.concurrent.TimeUnit.SECONDS); } catch (InterruptedException e) {}
                if (holder[0] != null) return holder[0];
                if (err[0] != null) System.err.println("[Input] screenshot: " + err[0].getMessage());
            }
            return doScreenshot();
        } catch (RuntimeException e) {
            System.err.println("[Input] screenshot: " + e.getMessage());
            return null;
        } catch (Exception e) {
            System.err.println("[Input] screenshot: " + e.getMessage());
            return null;
        }
    }

    private boolean isOnRenderThread() {
        return isOnRenderThreadImpl();
    }

    protected boolean isOnRenderThreadImpl() {
        try {
            Object mc = mc();
            try {
                Method m = mc.getClass().getMethod("isSameThread");
                return (Boolean) m.invoke(mc);
            } catch (NoSuchMethodException e) {
                return Thread.currentThread().getName().toLowerCase().contains("client")
                    || Thread.currentThread().getName().toLowerCase().contains("render")
                    || Thread.currentThread().getName().toLowerCase().contains("main");
            }
        } catch (Exception e) { return false; }
    }

    private byte[] doScreenshot() {
        int w = getWidth();
        int h = getHeight();
        if (w <= 0 || h <= 0) {
            return null;
        }
        try {
            byte[] result = ReflectionHelper.takeScreenshot(mc(), w, h);
            return result;
        } catch (RuntimeException e) {
            System.err.println("[Input] doScreenshot: " + e.getMessage());
            return null;
        } catch (Exception e) {
            System.err.println("[Input] doScreenshot: " + e.getMessage());
            return null;
        }
    }

    @Override
    public String executeCommand(String command) {
        return ReflectionHelper.sendCommand(mc(), command);
    }

    @Override
    public String getPlayerInfo() { return ReflectionHelper.getPlayerInfo(mc()); }

    @Override
    public String getWorldInfo() { return ReflectionHelper.getWorldInfo(mc()); }

    public String debugFields() { return ReflectionHelper.debugFields(mc()); }
}
